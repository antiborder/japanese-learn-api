from integrations.dynamodb.kanji import dynamodb_kanji_client
import logging

logger = logging.getLogger(__name__)


def get_kanji(kanji_id: int):
    """
    DynamoDBから漢字情報を取得します。
    """
    return dynamodb_kanji_client.get_kanji_by_id(kanji_id)


def get_kanjis():
    """
    DynamoDBから全ての漢字情報を取得します。
    """
    return dynamodb_kanji_client.get_all_kanjis()