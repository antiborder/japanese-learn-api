"""
NotificationFunction: EventBridgeで毎時0分に実行される。
is_push_active=True のユーザーを走査し、以下の条件を満たす場合にプッシュ通知を送信する:
  - push_hour_jst が現在のJST時刻(時)と一致
  - 復習可能な単語数 > 10
  - 今日の学習進捗が daily_goal 未満
"""

import json
import logging
import os
from datetime import datetime, timezone, timedelta

import boto3
from boto3.dynamodb.conditions import Attr, Key
from pywebpush import webpush, WebPushException

logger = logging.getLogger()
logger.setLevel(logging.INFO)

JST = timezone(timedelta(hours=9))
PUSH_TTL_SECONDS = 6 * 60 * 60
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS = {"sub": "mailto:noreply@nihongo.cloud"}

PUSH_MESSAGES = {
    "en": ("Japanese Study", "You have {n} more questions to reach today's goal!"),
    "ko": ("일본어 학습", "오늘 목표까지 {n}문제 남았습니다!"),
    "zh-Hans": ("日语学习", "距今日目标还有 {n} 题！"),
    "vi": ("Học tiếng Nhật", "Còn {n} câu nữa là đạt mục tiêu hôm nay!"),
    "hi": ("जापानी अध्ययन", "आज के लक्ष्य तक {n} और प्रश्न बाकी हैं!"),
    "id": ("Belajar Bahasa Jepang", "Tinggal {n} soal lagi untuk mencapai target hari ini!"),
}


def get_push_message(lang, daily_remaining):
    title, body_template = PUSH_MESSAGES.get(lang, PUSH_MESSAGES["en"])
    return title, body_template.format(n=daily_remaining)


def lambda_handler(event, context):
    now_utc = datetime.now(timezone.utc)
    now_jst = now_utc.astimezone(JST)
    current_hour_jst = now_jst.hour
    today_jst = now_jst.strftime("%Y-%m-%d")
    now_utc_iso = now_utc.isoformat()

    force_send = bool(event.get("force_send")) if event else False

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["DYNAMODB_TABLE_NAME"])

    # is_push_active=True のユーザー設定を全件スキャン
    users = []
    scan_kwargs = {"FilterExpression": Attr("SK").eq("SETTINGS") & Attr("is_push_active").eq(True)}
    while True:
        response = table.scan(**scan_kwargs)
        users.extend(response["Items"])
        if "LastEvaluatedKey" not in response:
            break
        scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    logger.info(f"Found {len(users)} push-active users")

    for user in users:
        user_pk = user["PK"]
        user_id = user_pk.removeprefix("USER#")
        push_hour_jst = int(user.get("push_hour_jst", 20))
        daily_goal = int(user.get("daily_goal", 10))
        user_lang = user.get("language", "en")

        if not force_send and current_hour_jst != push_hour_jst:
            continue

        # 復習可能単語数をカウント（next_datetime < 現在時刻）
        reviewable_count = 0
        word_kwargs = {
            "KeyConditionExpression": Key("PK").eq(user_pk) & Key("SK").begins_with("WORD#"),
            "FilterExpression": Attr("next_datetime").lt(now_utc_iso),
            "Select": "COUNT",
        }
        while True:
            word_resp = table.query(**word_kwargs)
            reviewable_count += word_resp["Count"]
            if "LastEvaluatedKey" not in word_resp:
                break
            word_kwargs["ExclusiveStartKey"] = word_resp["LastEvaluatedKey"]

        if reviewable_count <= 10:
            logger.info(f"skip {user_id}: reviewable={reviewable_count} <= 10")
            continue

        # 今日の学習進捗を取得
        progress_resp = table.get_item(Key={"PK": user_pk, "SK": f"PROGRESS#{today_jst}"})
        progress_item = progress_resp.get("Item")
        today_count = int(progress_item.get("questions_answered", 0)) if progress_item else 0

        if today_count >= daily_goal:
            logger.info(f"skip {user_id}: daily goal met ({today_count}/{daily_goal})")
            continue

        daily_remaining = daily_goal - today_count

        # プッシュ購読情報を取得
        sub_resp = table.query(
            KeyConditionExpression=Key("PK").eq(user_pk) & Key("SK").begins_with("PUSH_SUB#"),
        )
        subscriptions = sub_resp.get("Items", [])

        if not subscriptions:
            continue

        title, body = get_push_message(user_lang, daily_remaining)
        payload = json.dumps(
            {
                "title": title,
                "body": body,
                "url": f"/{user_lang}/me/dashboard",
            }
        )

        logger.info(
            f"sending push to {user_id}: reviewable={reviewable_count}, "
            f"remaining={daily_remaining}, subs={len(subscriptions)}"
        )

        for sub in subscriptions:
            sub_sk = sub["SK"]
            subscription_info = {
                "endpoint": sub["endpoint"],
                "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
            }
            try:
                webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS,
                    ttl=PUSH_TTL_SECONDS,
                )
                logger.info(f"push sent to {user_id} ({sub_sk})")
            except WebPushException as e:
                status_code = e.response.status_code if e.response is not None else None
                if status_code in (404, 410):
                    table.delete_item(Key={"PK": user_pk, "SK": sub_sk})
                    logger.info(f"deleted expired subscription {sub_sk} for {user_id}")
                else:
                    logger.error(f"ERROR: push failed for {user_id} ({sub_sk}): status={status_code} error={e}")
            except Exception as e:
                logger.error(f"ERROR: unexpected push exception for {user_id} ({sub_sk}): {e}")
