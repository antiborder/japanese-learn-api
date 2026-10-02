import base64
import json
from typing import Any, Dict, Optional


def encode_cursor(key: Optional[Dict[str, Any]]) -> Optional[str]:
    """DynamoDBの主キー（PK/SK）を、APIレスポンスに載せられる不透明な文字列に変換する"""
    if not key:
        return None
    raw = json.dumps(key, sort_keys=True)
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def decode_cursor(cursor: Optional[str]) -> Optional[Dict[str, Any]]:
    """encode_cursorで作った文字列を、DynamoDBのExclusiveStartKeyに戻す。

    不正な値が渡された場合はNoneを返し、先頭ページから取得させる（例外にしない）。
    """
    if not cursor:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        return json.loads(raw)
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return None
