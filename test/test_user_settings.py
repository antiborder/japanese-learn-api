import pytest


class TestUserSettingsCRUD:
    async def test_get_returns_none_when_not_exists(self, dynamodb_table, users_module):
        from integrations.dynamodb.user_settings import UserSettingsDynamoDB
        db = UserSettingsDynamoDB()
        result = await db.get_user_settings("nonexistent@example.com")
        assert result is None

    async def test_create_and_get(self, dynamodb_table, users_module):
        from integrations.dynamodb.user_settings import UserSettingsDynamoDB
        from common.schemas.user_settings import UserSettingsCreate, ThemeEnum, LanguageEnum
        db = UserSettingsDynamoDB()
        settings = UserSettingsCreate(
            base_level=5, theme=ThemeEnum.SPRING, language=LanguageEnum.EN,
            is_onboarding_modal_closed=False,
        )
        await db.create_user_settings("user@example.com", settings)

        result = await db.get_user_settings("user@example.com")
        assert result is not None
        assert result.user_id == "user@example.com"
        assert result.base_level == 5
        assert result.theme == ThemeEnum.SPRING
        assert result.language == LanguageEnum.EN
        assert result.is_onboarding_modal_closed is False

    async def test_update_partial_fields(self, dynamodb_table, users_module):
        from integrations.dynamodb.user_settings import UserSettingsDynamoDB
        from common.schemas.user_settings import UserSettingsCreate, UserSettingsUpdate, ThemeEnum, LanguageEnum
        db = UserSettingsDynamoDB()
        await db.create_user_settings("user@example.com", UserSettingsCreate(
            base_level=5, theme=ThemeEnum.SPRING, language=LanguageEnum.EN,
            is_onboarding_modal_closed=False,
        ))

        result = await db.update_user_settings(
            "user@example.com",
            UserSettingsUpdate(theme=ThemeEnum.SUMMER, base_level=None, language=None),
        )
        assert result.theme == ThemeEnum.SUMMER
        assert result.base_level == 5           # 変更なし
        assert result.language == LanguageEnum.EN  # 変更なし

    async def test_update_not_existing_raises(self, dynamodb_table, users_module):
        from integrations.dynamodb.user_settings import UserSettingsDynamoDB
        from common.schemas.user_settings import UserSettingsUpdate
        db = UserSettingsDynamoDB()
        with pytest.raises(ValueError):
            await db.update_user_settings("ghost@example.com", UserSettingsUpdate(base_level=3))

    async def test_delete(self, dynamodb_table, users_module):
        from integrations.dynamodb.user_settings import UserSettingsDynamoDB
        from common.schemas.user_settings import UserSettingsCreate, ThemeEnum, LanguageEnum
        db = UserSettingsDynamoDB()
        await db.create_user_settings("user@example.com", UserSettingsCreate(
            base_level=5, theme=ThemeEnum.SPRING, language=LanguageEnum.EN,
            is_onboarding_modal_closed=False,
        ))
        await db.delete_user_settings("user@example.com")

        result = await db.get_user_settings("user@example.com")
        assert result is None

    async def test_update_last_login_at(self, dynamodb_table, users_module):
        from integrations.dynamodb.user_settings import UserSettingsDynamoDB
        from common.schemas.user_settings import UserSettingsCreate, ThemeEnum, LanguageEnum
        db = UserSettingsDynamoDB()
        await db.create_user_settings("user@example.com", UserSettingsCreate(
            base_level=5, theme=ThemeEnum.SPRING, language=LanguageEnum.EN,
            is_onboarding_modal_closed=False,
        ))
        await db.update_last_login_at("user@example.com")

        result = await db.get_user_settings("user@example.com")
        assert result.last_login_at is not None

    async def test_update_last_login_at_no_settings_does_not_raise(self, dynamodb_table, users_module):
        """SETTINGSが存在しない場合は例外を出さずにスキップする"""
        from integrations.dynamodb.user_settings import UserSettingsDynamoDB
        db = UserSettingsDynamoDB()
        await db.update_last_login_at("nobody@example.com")
