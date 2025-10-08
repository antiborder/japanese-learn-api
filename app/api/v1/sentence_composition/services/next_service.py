import logging
from typing import Dict, Optional
from integrations.dynamodb_integration import DynamoDBSentenceCompositionClient
from services.sentence_selector import SentenceSelector

logger = logging.getLogger(__name__)

class NextService:
    def __init__(self):
        self.db_client = DynamoDBSentenceCompositionClient()
        self.sentence_selector = SentenceSelector()

    async def get_next_sentence(self, user_id: Optional[str], level: int) -> Optional[Dict]:
        """次に学習すべき文を取得します"""
        try:
            # ①指定レベルの文を全て取得
            level_sentences = await self.db_client.get_level_sentences(level)
            if not level_sentences:
                logger.info(f"No sentences found for level {level}")
                return None
            
            # user_idがない場合（未認証）はランダムに選択
            if not user_id:
                import random
                selected_item = random.choice(level_sentences)
                sentence_id = int(selected_item['SK'])
                logger.info(f"User not authenticated, returning random sentence {sentence_id} for level {level}")
                sentence_detail = await self.db_client.get_sentence_detail(sentence_id)
                return sentence_detail
            
            # ②ユーザーの学習履歴を取得
            user_sentences = await self.db_client.get_user_sentences(user_id)
            
            # ③文選定
            result = self.sentence_selector.select_next_sentence(
                level_sentences, 
                user_sentences, 
                user_id, 
                level
            )
            
            if not result:
                logger.info(f"No sentence selected for user {user_id}, level {level}")
                return None
            
            # 復習可能な文がない場合の処理
            if result.get('no_sentence_available'):
                return {
                    'no_sentence_available': True,
                    'next_available_datetime': result['next_available_datetime']
                }
            
            # ④文の詳細情報を取得
            sentence_id = result['answer_sentence_id']
            sentence_detail = await self.db_client.get_sentence_detail(sentence_id)
            
            logger.info(f"Successfully retrieved next sentence {sentence_id} for user {user_id}, level {level}")
            return sentence_detail
            
        except Exception as e:
            logger.error(f"Error getting next sentence for user {user_id}, level {level}: {str(e)}", exc_info=True)
            raise
