from integrations.dynamodb.kanji import dynamodb_kanji_client
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_kanji(kanji_id: int):
    """
    DynamoDBから漢字情報を取得します。
    """
    return dynamodb_kanji_client.get_kanji_by_id(kanji_id)


def get_kanjis_page(limit: int = 100, cursor: Optional[str] = None):
    """
    DynamoDBから漢字情報を1ページ分だけ取得します（カーソルベース）。

    Args:
        limit: 取得する最大件数
        cursor: 前回のレスポンスで返した next_cursor（先頭ページの場合はNone）

    Returns:
        (このページの漢字リスト, 次ページ用カーソル（最終ページはNone）, 次ページが存在するか)
    """
    return dynamodb_kanji_client.get_kanjis_page(limit=limit, cursor=cursor)
