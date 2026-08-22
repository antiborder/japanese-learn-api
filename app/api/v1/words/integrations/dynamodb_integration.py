import boto3
import os
import logging
from typing import List, Dict, Optional
from botocore.exceptions import ClientError
from fastapi import HTTPException
from common.utils.pagination_cursor import encode_cursor, decode_cursor

logger = logging.getLogger(__name__)


class DynamoDBClient:
    def __init__(self):
        self.table_name = os.getenv("DYNAMODB_TABLE_NAME", "japanese-learn-table")
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)

    def get_words_page(
        self, limit: int = 100, level: Optional[int] = None, cursor: Optional[str] = None
    ) -> tuple[List[Dict], Optional[str], bool]:
        """
        単語一覧を1ページ分だけ取得します（カーソルベース、レベルフィルタ対応）。

        以前はDynamoDBの「WORD」パーティション全体を毎回読み切ってからPython側で
        skip/limitを適用していたため、単語数が数千件規模になった際に必ずタイムアウト
        するようになっていた（sitemap生成が504で失敗し、wordページがサイトマップから
        欠落する原因になっていた）。
        その後skip/limitをこの関数内で打ち切る改善を入れたが、skipが大きいページ
        （＝サイトマップが末尾に近づくほど）は結局「先頭からskip件目まで」を毎回
        読み直す必要があり、依然としてタイムアウトしていた。
        ここではDynamoDB自身のカーソル（ExclusiveStartKey）をそのままAPIの外に
        `cursor`として渡すことで、どのページであっても「前回の続きから limit+1件」
        だけを読めば済むようにしている。

        Args:
            limit: 取得する最大件数
            level: レベルフィルタ（オプション）
            cursor: 前回のレスポンスで返した next_cursor（先頭ページの場合はNone）

        Returns:
            (このページの単語リスト, 次ページ用カーソル（最終ページはNone）, 次ページが存在するか)
        """
        try:
            needed = limit + 1  # 次ページの有無を判定するため1件多く読む
            all_items: List[Dict] = []
            last_evaluated_key = decode_cursor(cursor)

            while len(all_items) < needed:
                query_params = {
                    "KeyConditionExpression": "PK = :pk",
                    "ExpressionAttributeValues": {":pk": "WORD"},
                    "Limit": limit,
                }

                # レベルフィルタを適用
                if level is not None:
                    query_params["FilterExpression"] = "#level = :level"
                    query_params["ExpressionAttributeNames"] = {"#level": "level"}
                    query_params["ExpressionAttributeValues"][":level"] = level

                if last_evaluated_key:
                    query_params["ExclusiveStartKey"] = last_evaluated_key

                response = self.table.query(**query_params)
                all_items.extend(response.get("Items", []))

                last_evaluated_key = response.get("LastEvaluatedKey")
                if not last_evaluated_key:
                    break

            has_next = len(all_items) > limit
            page_raw_items = all_items[:limit]

            # 次ページ用カーソルは、このページの最後のアイテムの主キーそのもの。
            # DynamoDB内部の読み取り単位（Limit分の内部ページ）とは無関係に、
            # 「このページの最後の1件」から続きを取得できる。
            next_cursor = None
            if has_next and page_raw_items:
                last_item = page_raw_items[-1]
                next_cursor = encode_cursor({"PK": last_item["PK"], "SK": last_item["SK"]})

            # アイテムを変換（このページ分のみ）
            words = []
            for item in page_raw_items:
                try:
                    word = self._convert_dynamodb_to_model(item)
                    words.append(word)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting item {item['SK']}: {str(e)}")
                    continue

            return words, next_cursor, has_next
        except ClientError as e:
            logger.error(f"Error getting words from DynamoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    def get_word_by_id(self, word_id: int) -> Optional[Dict]:
        """
        指定されたIDの単語を取得します
        """
        try:
            response = self.table.get_item(Key={"PK": "WORD", "SK": str(word_id)})

            item = response.get("Item")
            if not item:
                raise HTTPException(status_code=404, detail="Word not found")

            return self._convert_dynamodb_to_model(item)

        except ClientError as e:
            logger.error(f"Error getting word {word_id} from DynamoDB: {str(e)}")
            raise
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting word {word_id}: {str(e)}")
            raise

    def get_kanjis_by_word_id(self, word_id: int) -> List[Dict]:
        """
        指定された単語IDに関連する漢字を取得します
        """
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk", ExpressionAttributeValues={":pk": f"WORD#{word_id}"}
            )

            items = response.get("Items", [])
            kanjis = []

            for item in items:
                try:
                    # SKからKANJI#を除去してIDを取得
                    kanji_id = int(item["SK"].replace("KANJI#", ""))
                    kanji = {"id": kanji_id, "char": item.get("kanji", "")}
                    kanjis.append(kanji)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting kanji item {item['SK']}: {str(e)}")
                    continue

            return kanjis

        except ClientError as e:
            logger.error(f"Error getting kanjis for word {word_id} from DynamoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting kanjis for word {word_id}: {str(e)}")
            raise

    def _convert_dynamodb_to_model(self, item: Dict) -> Dict:
        """
        DynamoDBのアイテムをモデル形式に変換します
        """
        return {
            "id": int(item["SK"]),
            "name": item.get("name", ""),
            "hiragana": item.get("hiragana", ""),
            "is_katakana": bool(int(item.get("is_katakana", 0))),
            "level": int(item.get("level", 0)),
            "english": item.get("english", ""),
            "vietnamese": item.get("vietnamese", ""),
            "chinese": item.get("chinese"),
            "korean": item.get("korean"),
            "indonesian": item.get("indonesian"),
            "hindi": item.get("hindi"),
            "lexical_category": item.get("lexical_category", ""),
            "accent_up": int(item.get("accent_up")) if item.get("accent_up") else None,
            "accent_down": int(item.get("accent_down")) if item.get("accent_down") else None,
        }


dynamodb_client = DynamoDBClient()
