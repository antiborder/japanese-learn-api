# IAM最小権限化の実装内容

## 実装日
2024年（実装日を記入）

## 変更概要

すべてのLambda関数のDynamoDBアクセス権限を、`DynamoDBCrudPolicy`（全権限）から最小権限のカスタムポリシーに変更しました。

## 変更前後の比較

### 変更前
- すべての関数に`DynamoDBCrudPolicy`が適用
- 以下の**すべての権限**が付与されていた：
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

### 変更後
各関数に必要な最小限の権限のみを付与：

| 関数名 | 必要な権限 | 理由 |
|--------|-----------|------|
| **WordsFunction** | `GetItem`, `Query` | 単語データの読み取りのみ |
| **LearnWordsFunction** | `GetItem`, `PutItem`, `Query` | 学習履歴の読み書き |
| **UsersFunction** | `GetItem`, `PutItem`, `UpdateItem`, `DeleteItem`, `Query` | ユーザー設定の完全CRUD |
| **KanjisFunction** | `GetItem`, `Query` | 漢字データの読み取りのみ |
| **SearchFunction** | `Query` | 検索機能（GSIを使用） |
| **SentencesFunction** | `GetItem`, `Query` | 例文データの読み取りのみ |
| **SentenceCompositionFunction** | `GetItem`, `PutItem`, `Query` | クイズ結果の読み書き |

## 主な改善点

### 1. Scan権限の削除
- **KanjisFunction**: Scan権限を削除（コスト削減）
- **SearchFunction**: Scan権限を削除（Queryのみで十分）
- **SentenceCompositionFunction**: Scan権限を削除（コスト削減）

**効果**:
- 意図しない全テーブルスキャンを防止
- DynamoDBの読み取りコストを削減
- パフォーマンスの向上

### 2. 削除権限の制限
- **WordsFunction**: DeleteItem権限なし（読み取り専用）
- **KanjisFunction**: DeleteItem権限なし（読み取り専用）
- **SearchFunction**: DeleteItem権限なし（読み取り専用）
- **SentencesFunction**: DeleteItem権限なし（読み取り専用）
- **SentenceCompositionFunction**: DeleteItem権限なし（削除機能なし）

**効果**:
- コードバグやセキュリティ侵害によるデータ削除を防止
- データ損失のリスクを大幅に削減

### 3. 更新権限の制限
- **WordsFunction**: UpdateItem権限なし（読み取り専用）
- **LearnWordsFunction**: UpdateItem権限なし（PutItemで新規作成のみ）
- **KanjisFunction**: UpdateItem権限なし（読み取り専用）
- **SearchFunction**: UpdateItem権限なし（読み取り専用）
- **SentencesFunction**: UpdateItem権限なし（読み取り専用）
- **SentenceCompositionFunction**: UpdateItem権限なし（PutItemで新規作成のみ）

**効果**:
- 意図しないデータ改ざんを防止
- データの整合性を保護

## 実装されたポリシーの詳細

### WordsFunction
```yaml
Policies:
  - Statement:
    - Effect: Allow
      Action:
        - dynamodb:GetItem
        - dynamodb:Query
      Resource:
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/*
```

### LearnWordsFunction
```yaml
Policies:
  - Statement:
    - Effect: Allow
      Action:
        - dynamodb:GetItem
        - dynamodb:PutItem
        - dynamodb:Query
      Resource:
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/*
```

### UsersFunction
```yaml
Policies:
  - Statement:
    - Effect: Allow
      Action:
        - dynamodb:GetItem
        - dynamodb:PutItem
        - dynamodb:UpdateItem
        - dynamodb:DeleteItem
        - dynamodb:Query
      Resource:
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/*
```

### KanjisFunction
```yaml
Policies:
  - Statement:
    - Effect: Allow
      Action:
        - dynamodb:GetItem
        - dynamodb:Query
      Resource:
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/*
```

### SearchFunction
```yaml
Policies:
  - Statement:
    - Effect: Allow
      Action:
        - dynamodb:Query
      Resource:
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/*
        # すべてのGSIインデックスを明示的に指定
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/name-index
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/english-index
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/vietnamese-index
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/chinese-index
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/korean-index
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/indonesian-index
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/hindi-index
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/character-index
```

### SentencesFunction
```yaml
Policies:
  - Statement:
    - Effect: Allow
      Action:
        - dynamodb:GetItem
        - dynamodb:Query
      Resource:
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/*
```

### SentenceCompositionFunction
```yaml
Policies:
  - Statement:
    - Effect: Allow
      Action:
        - dynamodb:GetItem
        - dynamodb:PutItem
        - dynamodb:Query
      Resource:
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}
        - arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${DynamoDBTable}/index/*
```

## 期待される効果

### セキュリティ向上
1. **侵害時の被害範囲を最小化**: 1つの関数が侵害されても、他のデータは保護される
2. **コードバグによる影響を軽減**: 誤った操作が実行されても、権限エラーで停止
3. **内部犯行のリスクを低減**: 権限外の操作は実行できない

### コスト削減
1. **Scan操作の防止**: 高コストなScan操作を防止
2. **不要な操作の削減**: 必要な操作のみを許可

### 運用の改善
1. **権限の明確化**: 各関数の役割が明確になる
2. **監査の容易化**: 権限を見るだけで、関数の責任範囲が分かる
3. **コンプライアンス**: 最小権限の原則に準拠

## デプロイ方法

1. 変更をコミット:
```bash
git add template.yaml
git commit -m "feat: IAMポリシーを最小権限化"
```

2. SAMでデプロイ:
```bash
sam build
sam deploy
```

3. 動作確認:
   - 各APIエンドポイントが正常に動作することを確認
   - CloudWatch Logsで権限エラーが発生していないことを確認

## 注意事項

### 新しい操作を追加する場合
新しいDynamoDB操作（例: `UpdateItem`、`DeleteItem`）を追加する場合は、`template.yaml`の該当関数のポリシーを更新する必要があります。

### トラブルシューティング
権限エラーが発生した場合:
1. CloudWatch Logsでエラーメッセージを確認
2. 必要な権限を`template.yaml`に追加
3. 再度デプロイ

## 参考資料

- [IAM_MINIMUM_PRIVILEGE_RISKS.md](./IAM_MINIMUM_PRIVILEGE_RISKS.md) - リスクシナリオの詳細
- [DYNAMODB_SECURITY_IMPROVEMENTS.md](./DYNAMODB_SECURITY_IMPROVEMENTS.md) - セキュリティ強化の全体像
- [AWS IAM ポリシーの最小権限の原則](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

