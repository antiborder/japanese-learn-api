import boto3
import os
import logging
from typing import Optional
from fastapi import HTTPException
from common.utils.pagination_cursor import encode_cursor, decode_cursor

logger = logging.getLogger(__name__)


class DynamoDBKanjiClient:
    def __init__(self):
        self.table_name = os.getenv("DYNAMODB_TABLE_NAME", "japanese-learn-table")
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)

    def get_kanji_by_id(self, kanji_id: int):
        try:
            response = self.table.get_item(Key={"PK": "KANJI", "SK": str(kanji_id)})
            item = response.get("Item")
            if not item:
                raise HTTPException(status_code=404, detail="Kanji not found")

            # idフィールドを追加
            item["id"] = kanji_id
            return item
        except Exception as e:
            logger.error(f"Error getting kanji {kanji_id} from DynamoDB: {str(e)}")
            raise

    def get_all_kanjis(self):
        try:
            response = self.table.query(KeyConditionExpression="PK = :pk", ExpressionAttributeValues={":pk": "KANJI"})
            items = response.get("Items", [])
            # 各アイテムにidフィールドを追加
            for item in items:
                kanji_id = int(item["SK"])
                item["id"] = kanji_id
            return items
        except Exception as e:
            logger.error(f"Error getting all kanjis from DynamoDB: {str(e)}")
            raise

    def get_kanjis_page(self, limit: int = 100, cursor: Optional[str] = None) -> tuple[list, Optional[str], bool]:
        """
        漢字情報を1ページ分だけ取得します（カーソルベース）。

        以前はDynamoDBの「KANJI」パーティション全体を毎回読み切ってからPython側で
        skip/limitを適用していたため、漢字数が2,000件を超える規模になった際に
        必ずタイムアウトするようになっていた（sitemap生成が504で失敗し、
        kanjiページがサイトマップから欠落する原因になっていた）。
        その後skip/limitをこの関数内で打ち切る改善を入れたが、skipが大きいページは
        結局「先頭からskip件目まで」を毎回読み直す必要があり、依然として遅かった。
        ここではDynamoDB自身のカーソル（ExclusiveStartKey）をそのままAPIの外に
        `cursor`として渡すことで、どのページであっても「前回の続きから limit+1件」
        だけを読めば済むようにしている。

        Args:
            limit: 取得する最大件数
            cursor: 前回のレスポンスで返した next_cursor（先頭ページの場合はNone）

        Returns:
            (このページの漢字リスト, 次ページ用カーソル（最終ページはNone）, 次ページが存在するか)
        """
        try:
            needed = limit + 1  # 次ページの有無を判定するため1件多く読む
            all_items = []
            last_evaluated_key = decode_cursor(cursor)

            while len(all_items) < needed:
                query_params = {
                    "KeyConditionExpression": "PK = :pk",
                    "ExpressionAttributeValues": {":pk": "KANJI"},
                    "Limit": limit,
                }

                if last_evaluated_key:
                    query_params["ExclusiveStartKey"] = last_evaluated_key

                response = self.table.query(**query_params)
                all_items.extend(response.get("Items", []))

                last_evaluated_key = response.get("LastEvaluatedKey")
                if not last_evaluated_key:
                    break

            has_next = len(all_items) > limit
            page_items = all_items[:limit]

            next_cursor = None
            if has_next and page_items:
                last_item = page_items[-1]
                next_cursor = encode_cursor({"PK": last_item["PK"], "SK": last_item["SK"]})

            # このページ分のみにidフィールドを追加
            for item in page_items:
                item["id"] = int(item["SK"])

            return page_items, next_cursor, has_next
        except Exception as e:
            logger.error(f"Error getting kanjis from DynamoDB: {str(e)}")
            raise

    def get_components_by_kanji_id(self, kanji_id: str):
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk", ExpressionAttributeValues={":pk": f"KANJI#{kanji_id}"}
            )
            items = response.get("Items", [])
            result = []
            for item in items:
                # SKは "COMPONENT#{component_id}" 形式
                component_id = item["SK"].replace("COMPONENT#", "")
                component_char = item.get("component_char")
                result.append({"component_id": component_id, "component_char": component_char})
            return result
        except Exception as e:
            logger.error(f"Error getting components for kanji {kanji_id} from DynamoDB: {str(e)}")
            raise

    def get_words_by_kanji_id(self, kanji_id: int):
        """
        指定された漢字IDに関連する単語を取得します
        """
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk", ExpressionAttributeValues={":pk": f"KANJI#{kanji_id}"}
            )

            items = response.get("Items", [])
            words = []

            for item in items:
                try:
                    # SKからWORD#を除去してIDを取得
                    word_id = int(item["SK"].replace("WORD#", ""))
                    word = {"id": word_id}
                    words.append(word)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting word item {item['SK']}: {str(e)}")
                    continue

            return words

        except Exception as e:
            logger.error(f"Error getting words for kanji {kanji_id} from DynamoDB: {str(e)}")
            raise


dynamodb_kanji_client = DynamoDBKanjiClient()
