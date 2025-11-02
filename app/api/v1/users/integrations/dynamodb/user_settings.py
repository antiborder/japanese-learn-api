import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from .base import DynamoDBBase
from common.schemas.user_settings import UserSettingsCreate, UserSettingsUpdate, UserSettingsResponse

logger = logging.getLogger(__name__)

class UserSettingsDynamoDB(DynamoDBBase):
    def __init__(self):
        super().__init__()

    async def get_user_settings(self, user_id: str) -> Optional[UserSettingsResponse]:
        """
        ユーザーの設定を取得する
        """
        try:
            response = self.table.get_item(
                Key={
                    'PK': f"USER#{user_id}",
                    'SK': 'SETTINGS'
                }
            )
            
            if 'Item' not in response:
                return None
                
            item = response['Item']
            return UserSettingsResponse(
                user_id=user_id,
                base_level=item['base_level'],
                theme=item['theme'],
                language=item['language'],
                is_onboarding_modal_closed=item.get('is_onboarding_modal_closed', False),
                created_at=item['created_at'],
                updated_at=item['updated_at']
            )
        except Exception as e:
            logger.error(f"Error getting user settings for user {user_id}: {str(e)}")
            raise

    async def create_user_settings(self, user_id: str, settings: UserSettingsCreate) -> UserSettingsResponse:
        """
        ユーザーの設定を作成する
        """
        try:
            now = datetime.now(timezone.utc).isoformat()
            
            item = {
                'PK': f"USER#{user_id}",
                'SK': 'SETTINGS',
                'base_level': settings.base_level,
                'theme': settings.theme.value,
                'language': settings.language.value,
                'is_onboarding_modal_closed': settings.is_onboarding_modal_closed,
                'created_at': now,
                'updated_at': now
            }
            
            self.table.put_item(Item=item)
            
            return UserSettingsResponse(
                user_id=user_id,
                base_level=settings.base_level,
                theme=settings.theme,
                language=settings.language,
                is_onboarding_modal_closed=settings.is_onboarding_modal_closed,
                created_at=now,
                updated_at=now
            )
        except Exception as e:
            logger.error(f"Error creating user settings for user {user_id}: {str(e)}")
            raise

    async def update_user_settings(self, user_id: str, settings: UserSettingsUpdate) -> UserSettingsResponse:
        """
        ユーザーの設定を更新する
        """
        try:
            # 既存の設定を取得
            existing_settings = await self.get_user_settings(user_id)
            if not existing_settings:
                raise ValueError(f"User settings not found for user {user_id}")
            
            # 更新するフィールドのみを準備
            update_expression_parts = []
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            if settings.base_level is not None:
                update_expression_parts.append("#base_level = :base_level")
                expression_attribute_values[":base_level"] = settings.base_level
                expression_attribute_names["#base_level"] = "base_level"
            
            if settings.theme is not None:
                update_expression_parts.append("#theme = :theme")
                expression_attribute_values[":theme"] = settings.theme.value
                expression_attribute_names["#theme"] = "theme"
            
            if settings.language is not None:
                update_expression_parts.append("#language = :language")
                expression_attribute_values[":language"] = settings.language.value
                expression_attribute_names["#language"] = "language"
            
            if settings.is_onboarding_modal_closed is not None:
                update_expression_parts.append("#is_onboarding_modal_closed = :is_onboarding_modal_closed")
                expression_attribute_values[":is_onboarding_modal_closed"] = settings.is_onboarding_modal_closed
                expression_attribute_names["#is_onboarding_modal_closed"] = "is_onboarding_modal_closed"
            
            if not update_expression_parts:
                # 更新するフィールドがない場合は既存の設定を返す
                return existing_settings
            
            update_expression_parts.append("#updated_at = :updated_at")
            expression_attribute_values[":updated_at"] = datetime.now(timezone.utc).isoformat()
            expression_attribute_names["#updated_at"] = "updated_at"
            
            update_expression = "SET " + ", ".join(update_expression_parts)
            
            self.table.update_item(
                Key={
                    'PK': f"USER#{user_id}",
                    'SK': 'SETTINGS'
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ExpressionAttributeNames=expression_attribute_names
            )
            
            # 更新後の設定を取得して返す
            return await self.get_user_settings(user_id)
            
        except Exception as e:
            logger.error(f"Error updating user settings for user {user_id}: {str(e)}")
            raise

    async def delete_user_settings(self, user_id: str) -> bool:
        """
        ユーザーの設定を削除する
        """
        try:
            self.table.delete_item(
                Key={
                    'PK': f"USER#{user_id}",
                    'SK': 'SETTINGS'
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting user settings for user {user_id}: {str(e)}")
            raise
