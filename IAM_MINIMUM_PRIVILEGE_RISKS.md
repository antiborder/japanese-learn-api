# IAM最小権限化が軽減するリスク - 実例

## 現状の問題点

現在、すべてのLambda関数に`DynamoDBCrudPolicy`が適用されており、以下の**すべての権限**が付与されています：

- `dynamodb:GetItem`
- `dynamodb:PutItem`
- `dynamodb:UpdateItem`
- `dynamodb:DeleteItem`
- `dynamodb:Query`
- `dynamodb:Scan`
- `dynamodb:BatchGetItem`
- `dynamodb:BatchWriteItem`
- `dynamodb:DescribeTable`
- その他すべてのDynamoDB操作

## リスクシナリオと実例

### シナリオ1: コードバグによる意図しないデータ削除

**状況**: 
- `SearchFunction`は本来、単語を検索するだけの読み取り専用機能
- しかし、現在は`DeleteItem`権限も持っている

**攻撃例**:
```python
# バグのあるコード例（SearchFunction内）
def search_words(self, query: str):
    # 検索処理...
    results = self.table.query(...)
    
    # バグ: 誤って削除処理を実行してしまった
    for item in results:
        self.table.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})  # 危険！
```

**結果**:
- 検索機能から誤って全単語データが削除される
- データベース全体が破壊される可能性

**最小権限化による軽減**:
- `SearchFunction`に`DeleteItem`権限を付与しない
- バグがあっても削除操作は実行されず、エラーで停止
- データ損失を防止

---

### シナリオ2: セキュリティ侵害による権限悪用

**状況**:
- 攻撃者が`WordsFunction`のコードにアクセスできる脆弱性を発見
- または、Lambda関数の実行ロールの認証情報が漏洩

**攻撃例**:
```python
# 攻撃者が注入した悪意のあるコード
def get_word_by_id(self, word_id: int):
    # 本来の処理...
    word = self.table.get_item(...)
    
    # 攻撃者が追加した悪意のあるコード
    # すべてのユーザーデータを削除
    all_users = self.table.scan(
        FilterExpression='begins_with(PK, :pk)',
        ExpressionAttributeValues={':pk': 'USER#'}
    )
    for user in all_users['Items']:
        self.table.delete_item(Key={'PK': user['PK'], 'SK': user['SK']})
    
    return word
```

**結果**:
- 単語取得機能から、すべてのユーザーの学習履歴が削除される
- ユーザー設定、進捗データがすべて失われる
- サービスが完全に停止

**最小権限化による軽減**:
- `WordsFunction`に`DeleteItem`権限を付与しない
- 攻撃コードが実行されても、権限エラーで停止
- 被害を最小限に抑制

---

### シナリオ3: 内部犯行によるデータ改ざん

**状況**:
- 開発者が誤って、または悪意を持ってコードを変更
- `KanjisFunction`（読み取り専用）からデータを改ざん

**攻撃例**:
```python
# KanjisFunction内（本来は読み取り専用）
def get_kanji(self, kanji_id: str):
    kanji = self.table.get_item(...)
    
    # 悪意のある変更: 漢字データを改ざん
    self.table.update_item(
        Key={'PK': 'KANJI', 'SK': kanji_id},
        UpdateExpression='SET meaning = :bad_meaning',
        ExpressionAttributeValues={':bad_meaning': '悪意のある意味'}
    )
    
    return kanji
```

**結果**:
- 漢字の意味が改ざんされる
- 学習コンテンツの信頼性が失われる
- ユーザーに誤った情報を提供

**最小権限化による軽減**:
- `KanjisFunction`に`UpdateItem`権限を付与しない
- 改ざん操作は実行されず、エラーで停止
- データの整合性を保護

---

### シナリオ4: サードパーティライブラリの脆弱性悪用

**状況**:
- 使用しているPythonライブラリにセキュリティ脆弱性が発見
- 攻撃者がその脆弱性を悪用してLambda関数内でコードを実行

**攻撃例**:
```python
# 脆弱なライブラリを使用
import vulnerable_library

# 攻撃者がリクエストに悪意のあるペイロードを注入
def search_words(self, query: str):
    # 脆弱なライブラリが悪意のあるコードを実行
    result = vulnerable_library.process(query)  # ここでコードインジェクション
    
    # 攻撃者が実行したコード:
    # すべての学習履歴を削除
    self.table.scan()  # 全データを取得
    # ... 削除処理 ...
```

**結果**:
- サードパーティライブラリの脆弱性から、データベース全体が侵害される
- すべてのデータが削除または改ざんされる

**最小権限化による軽減**:
- 各関数に必要な最小限の権限のみを付与
- たとえコードが実行されても、権限外の操作は失敗
- 被害範囲を限定

---

### シナリオ5: 設定ミスによる誤操作

**状況**:
- 開発者が誤って、読み取り専用の関数から書き込み操作を実行するコードを追加

**攻撃例**:
```python
# SentencesFunction（読み取り専用のはず）
def get_sentence(self, sentence_id: int):
    sentence = self.table.get_item(...)
    
    # 開発者の誤り: テスト用のコードを本番に残してしまった
    # すべての例文を削除してしまう
    if os.getenv('ENV') == 'production':  # 条件を間違えた
        self.table.scan()  # 全データを取得
        # ... 削除処理 ...
    
    return sentence
```

**結果**:
- 本番環境で全例文データが削除される
- サービスが機能不全に

**最小権限化による軽減**:
- `SentencesFunction`に`DeleteItem`権限がないため、エラーで停止
- データ損失を防止
- 設定ミスによる影響を最小化

---

### シナリオ6: コスト爆発（DynamoDB Scan操作の悪用）

**状況**:
- `SearchFunction`は特定のGSI（Global Secondary Index）でのみQueryを行うべき
- しかし、現在は`Scan`権限も持っている

**攻撃例**:
```python
# バグまたは悪意のあるコード
def search_words(self, query: str):
    # 誤ってScanを使用（非常に高コスト）
    # テーブル全体をスキャンしてしまう
    response = self.table.scan()  # 危険！全データを読み込む
    
    # または、悪意のある攻撃者が大量のScanリクエストを送信
    for i in range(10000):
        self.table.scan()  # コスト爆発
```

**結果**:
- DynamoDBの読み取りユニットが大量に消費される
- 月額コストが数万円〜数十万円に跳ね上がる
- サービスが経済的に成り立たなくなる

**最小権限化による軽減**:
- `SearchFunction`に`Scan`権限を付与しない
- Queryのみを許可（GSIを使用した効率的な検索）
- コストを制御

---

## 最小権限化の効果まとめ

| リスク | 現状（全権限） | 最小権限化後 |
|--------|---------------|-------------|
| コードバグによる削除 | ✅ 実行可能（危険） | ❌ 権限エラーで停止 |
| セキュリティ侵害 | ✅ 全データ操作可能 | ❌ 必要最小限の操作のみ |
| 内部犯行 | ✅ 全データ改ざん可能 | ❌ 権限外操作は失敗 |
| ライブラリ脆弱性 | ✅ 全データ侵害可能 | ❌ 被害範囲を限定 |
| 設定ミス | ✅ 誤操作が実行される | ❌ エラーで停止 |
| コスト爆発 | ✅ Scan操作が可能 | ❌ Queryのみ許可 |

## 実装後の期待効果

1. **セキュリティ侵害時の被害範囲を最小化**
   - 1つの関数が侵害されても、他のデータは保護される
   - 攻撃者が実行できる操作が制限される

2. **人的ミスによる影響を軽減**
   - バグや設定ミスがあっても、権限外の操作は実行されない
   - データ損失のリスクを大幅に削減

3. **コスト管理**
   - 不要な操作（Scanなど）を防止
   - 予期しないコスト増加を回避

4. **コンプライアンス**
   - 最小権限の原則に準拠
   - セキュリティ監査で評価が向上

5. **運用の透明性**
   - 各関数の役割が明確になる
   - 権限を見るだけで、関数の責任範囲が分かる

