import boto3
import os
import logging

logger = logging.getLogger(__name__)

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
SES_FROM_EMAIL = os.environ.get("SES_FROM_EMAIL", "noreply@nihongo.cloud")
AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")

CATEGORY_LABELS = {
    "feature_request": "Feature Request / 要望",
    "question": "Question / 質問",
    "bug_report": "Bug Report / バグ報告",
    "other": "Other / その他",
}


def send_contact_notification(contact_id: str, category: str, email: str, subject: str, body: str, lang: str) -> None:
    ses = boto3.client("ses", region_name=AWS_REGION)
    category_label = CATEGORY_LABELS.get(category, category)

    email_subject = f"[nihongo.cloud お問い合わせ] {category_label} - {subject}"
    email_body = f"""新しいお問い合わせが届きました。

ID:       {contact_id}
カテゴリ: {category_label}
件名:     {subject}
送信者:   {email}
言語:     {lang}

--- メッセージ ---
{body}
-----------------

このメールに返信すると、送信者（{email}）に直接届きます。
"""

    ses.send_email(
        Source=SES_FROM_EMAIL,
        Destination={"ToAddresses": [ADMIN_EMAIL]},
        ReplyToAddresses=[email],
        Message={
            "Subject": {"Data": email_subject, "Charset": "UTF-8"},
            "Body": {"Text": {"Data": email_body, "Charset": "UTF-8"}},
        },
    )
    logger.info(f"Contact notification sent for {contact_id}")
