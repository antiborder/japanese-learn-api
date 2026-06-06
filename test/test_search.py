from conftest import insert_words


class TestSearchWords:
    async def test_search_by_name_exact_match(self, dynamodb_table, search_module):
        from integrations.dynamodb_integration import SearchDynamoDBClient

        insert_words(
            dynamodb_table,
            [
                {"id": 1, "name": "犬", "level": 1, "english": "dog"},
                {"id": 2, "name": "猫", "level": 1, "english": "cat"},
            ],
        )
        client = SearchDynamoDBClient()
        results = client.search_words(query="犬", language="en")

        assert len(results) == 1
        assert results[0]["name"] == "犬"
        assert results[0]["id"] == 1

    async def test_search_by_english_exact_match(self, dynamodb_table, search_module):
        from integrations.dynamodb_integration import SearchDynamoDBClient

        insert_words(
            dynamodb_table,
            [
                {"id": 1, "name": "犬", "level": 1, "english": "dog"},
                {"id": 2, "name": "猫", "level": 1, "english": "cat"},
            ],
        )
        client = SearchDynamoDBClient()
        results = client.search_words(query="dog", language="en")

        assert len(results) == 1
        assert results[0]["english"] == "dog"

    async def test_search_deduplicates_name_and_english_match(self, dynamodb_table, search_module):
        """nameとenglishの両方にマッチしても重複しない"""
        from integrations.dynamodb_integration import SearchDynamoDBClient

        insert_words(dynamodb_table, [{"id": 1, "name": "dog", "level": 1, "english": "dog"}])
        client = SearchDynamoDBClient()
        results = client.search_words(query="dog", language="en")

        assert len(results) == 1

    async def test_search_no_match_returns_empty(self, dynamodb_table, search_module):
        from integrations.dynamodb_integration import SearchDynamoDBClient

        insert_words(dynamodb_table, [{"id": 1, "name": "犬", "level": 1, "english": "dog"}])
        client = SearchDynamoDBClient()
        results = client.search_words(query="xyz_no_match", language="en")

        assert results == []

    async def test_get_total_count(self, dynamodb_table, search_module):
        from integrations.dynamodb_integration import SearchDynamoDBClient

        insert_words(
            dynamodb_table,
            [
                {"id": 1, "name": "犬", "level": 1, "english": "dog"},
                {"id": 2, "name": "犬猫", "level": 1, "english": "dogs"},
            ],
        )
        client = SearchDynamoDBClient()
        count = client.get_total_count(query="犬", language="en")

        assert count == 1  # "犬"の完全一致のみ

    async def test_limit_and_offset(self, dynamodb_table, search_module):
        from integrations.dynamodb_integration import SearchDynamoDBClient

        insert_words(dynamodb_table, [{"id": 1, "name": "word1", "level": 1, "english": "english1"}])
        client = SearchDynamoDBClient()
        results = client.search_words(query="word1", language="en", limit=10, offset=0)
        assert len(results) == 1

        offset_results = client.search_words(query="word1", language="en", limit=10, offset=1)
        assert len(offset_results) == 0
