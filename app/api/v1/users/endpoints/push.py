from fastapi import APIRouter, Depends
from pydantic import BaseModel
from integrations.dynamodb import push_subscriptions_db, daily_progress_db
from common.auth import get_current_user_id

router = APIRouter()


class PushSubscribeRequest(BaseModel):
    endpoint: str
    keys: dict  # {"p256dh": "...", "auth": "..."}


class PushUnsubscribeRequest(BaseModel):
    endpoint: str


@router.post("/push/subscribe")
async def subscribe_push(
    body: PushSubscribeRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    await push_subscriptions_db.save(
        user_id=current_user_id,
        endpoint=body.endpoint,
        p256dh=body.keys["p256dh"],
        auth=body.keys["auth"],
    )
    return {"status": "subscribed"}


@router.post("/push/unsubscribe")
async def unsubscribe_push(
    body: PushUnsubscribeRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    await push_subscriptions_db.delete(user_id=current_user_id, endpoint=body.endpoint)
    return {"status": "unsubscribed"}


@router.get("/push/prompt-eligibility")
async def get_push_prompt_eligibility(
    current_user_id: str = Depends(get_current_user_id),
):
    """
    プッシュ通知オプトインバナーの表示可否を返す。
    ユーザーが2日以上学習している場合のみ eligible=True。
    """
    progress_items = daily_progress_db.get_all(current_user_id)
    eligible = len(progress_items) >= 2
    return {"eligible": eligible}
