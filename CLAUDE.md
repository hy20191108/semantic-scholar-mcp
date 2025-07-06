> 公式MCP Python SDK（FastMCP統合版）の使用を推奨します　おｋ

● 了解しました。公式MCP Python SDK（FastMCP統合版）を使用してSemantic Scholar
  MCPサーバーを実装する計画を立てます。
  ⎿  User rejected Claude's plan:
     ╭─────────────────────────────────────────────────────────────────╮
     │ Semantic Scholar MCP サーバー実装計画（公式SDK版）              │
     │                                                                 │
     │ 公式MCP Python SDK（FastMCP統合版）を使用してSemantic Scholar   │
     │ MCPサーバーを実装します。                                       │
     │                                                                 │
     │ プロジェクト構造:                                               │
     │                                                                 │
     │ semantic-scholar-mcp/                                           │
     │ ├── pyproject.toml          # uv用プロジェクト設定              │
     │ ├── README.md              # ドキュメント                       │
     │ ├── LICENSE                # MITライセンス                      │
     │ ├── .gitignore            # Git除外設定                         │
     │ ├── .env.example          # 環境変数のサンプル                  │
     │ ├── src/                                                        │
     │ │   └── semantic_scholar_mcp/                                   │
     │ │       ├── __init__.py                                         │
     │ │       ├── __main__.py    # エントリーポイント                 │
     │ │       ├── server.py      # MCPサーバー実装                    │
     │ │       ├── client.py      # Semantic Scholar APIクライアント   │
     │ │       └── models.py      # データモデル定義                   │
     │ └── tests/                                                      │
     │     ├── __init__.py                                             │
     │     └── test_client.py                                          │
     │                                                                 │
     │ 実装内容:                                                       │
     │                                                                 │
     │ 1. pyproject.toml                                               │
     │                                                                 │
     │ [build-system]                                                  │
     │ requires = ["hatchling"]                                        │
     │ build-backend = "hatchling.build"                               │
     │                                                                 │
     │ [project]                                                       │
     │ name = "semantic-scholar-mcp"                                   │
     │ version = "0.1.0"                                               │
     │ description = "MCP server for Semantic Scholar API integration" │
     │ readme = "README.md"                                            │
     │ requires-python = ">=3.10"                                      │
     │ license = {text = "MIT"}                                        │
     │ dependencies = [                                                │
     │     "mcp[cli]>=1.2.1",                                          │
     │     "httpx>=0.27.0",                                            │
     │     "pydantic>=2.0",                                            │
     │     "python-dotenv>=1.0.0",                                     │
     │ ]                                                               │
     │                                                                 │
     │ [project.scripts]                                               │
     │ semantic-scholar-mcp = "semantic_scholar_mcp:main"              │
     │                                                                 │
     │ [tool.uv]                                                       │
     │ dev-dependencies = [                                            │
     │     "pytest>=8.0",                                              │
     │     "pytest-asyncio>=0.23",                                     │
     │ ]                                                               │
     │                                                                 │
     │ 2. 主要な機能（Tools）                                          │
     │                                                                 │
     │ 1. 論文検索系                                                   │
     │   - search_papers - キーワードでの論文検索（bulk search使用）   │
     │   - get_paper - 論文IDで詳細情報取得                            │
     │   - get_citations - 論文の引用リスト取得                        │
     │   - get_references - 論文の参考文献リスト取得                   │
     │   - batch_get_papers - 複数論文の一括取得                       │
     │ 2. 著者検索系                                                   │
     │   - search_authors - 著者名での検索                             │
     │   - get_author - 著者IDで詳細情報取得                           │
     │   - get_author_papers - 著者の論文リスト取得                    │
     │ 3. 推薦機能                                                     │
     │   - get_recommendations - 類似論文の推薦取得                    │
     │                                                                 │
     │ 3. リソース（Resources）                                        │
     │                                                                 │
     │ - paper://{paper_id} - 論文情報の読み取り専用アクセス           │
     │ - author://{author_id} - 著者情報の読み取り専用アクセス         │
     │                                                                 │
     │ 4. プロンプト（Prompts）                                        │
     │                                                                 │
     │ - literature_review - 文献レビュー作成テンプレート              │
     │ - paper_summary - 論文要約生成テンプレート                      │
     │                                                                 │
     │ 実装手順:                                                       │
     │                                                                 │
     │ 1. プロジェクト初期化                                           │
     │ uv init semantic-scholar-mcp                                    │
     │ cd semantic-scholar-mcp                                         │
     │ uv add "mcp[cli]" httpx pydantic python-dotenv                  │
     │ 2. APIクライアント実装（client.py）                             │
     │   - Semantic Scholar APIのラッパークラス                        │
     │   - 認証ヘッダー（オプション）: x-api-key                       │
     │   - エラーハンドリングとレート制限対応                          │
     │   - 非同期HTTPクライアント使用                                  │
     │ 3. MCPサーバー実装（server.py）                                 │
     │ from mcp.server.fastmcp import FastMCP                          │
     │                                                                 │
     │ mcp = FastMCP(name="semantic-scholar-mcp")                      │
     │                                                                 │
     │ @mcp.tool()                                                     │
     │ async def search_papers(query: str, limit: int = 10) -> dict:   │
     │     """Search for academic papers"""                            │
     │     # 実装                                                      │
     │ 4. 環境変数設定（.env.example）                                 │
     │ # Optional: Semantic Scholar API Key                            │
     │ SEMANTIC_SCHOLAR_API_KEY=your-api-key-here                      │
     │ 5. テスト実行                                                   │
     │ # MCPインスペクターでテスト                                     │
     │ uv run mcp dev src/semantic_scholar_mcp/server.py               │
     │ 6. パッケージビルドとPyPI公開                                   │
     │ uv build                                                        │
     │ twine upload dist/*                                             │
     │                                                                 │
     │ インストールと使用:                                             │
     │                                                                 │
     │ 1. PyPI公開後のインストール                                     │
     │ claude mcp add semantic-scholar -- uvx semantic-scholar-mcp     │
     │ 2. 環境変数付きインストール                                     │
     │ claude mcp add-json --scope=user semantic-scholar '{            │
     │   "command": "uvx",                                             │
     │   "args": ["semantic-scholar-mcp"],                             │
     │   "env": {                                                      │
     │     "SEMANTIC_SCHOLAR_API_KEY": "your-api-key"                  │
     │   }                                                             │
     │ }'                                                              │
     │                                                                 │
     │ 特徴:                                                           │
     │                                                                 │
     │ - 公式SDKによる安定した実装                                     │
     │ - APIキーはオプション（なくても基本機能は動作）                 │
     │ - 効率的なbulk searchエンドポイント使用                         │
     │ - fieldsパラメータで必要なデータのみ取得                        │
     │ - 非同期処理でパフォーマンス最適化                              │
     │                                                                 │
     │ この実装により、Claude DesktopやCursorから簡単にSemantic        │
     │ Scholarの学術論文データベースにアクセスできるようになります。   │
     ╰─────────────────────────────────────────────────────────────────╯

> クラスの型ヒントを整理して企業レベルのコードにしてください．また，ドキュメント
  やＵＭＬなどを用意し，産業レベルのコードにすること．加えて，動作チェックを行う
  こと．タスクを作成し，三つのサブエージェントで並列処理をしてください．

● 企業レベルのSemantic Scholar MCPサーバーを実装するため、タスクを作成して3つのサ
  ブエージェントで並列処理を行います。

● Update Todos
  ⎿  ☐ プロジェクト構造とビルド設定の作成（pyproject.toml、ディレクトリ構造）
     ☐ 型ヒント付きデータモデルの設計と実装（Pydantic、型エイリアス）
     ☐ Semantic Scholar APIクライアントの実装（非同期、エラーハンドリング）
     ☐ MCPサーバー本体の実装（Tools、Resources、Prompts）
     ☐ 単体テストとintegrationテストの実装
     ☐ 動作チェックとMCPインスペクターでのテスト
     ☐ 包括的なドキュメント作成（README、API仕様、使用例）
     ☐ UMLダイアグラムの生成（クラス図、シーケンス図）
     ☐ CI/CD設定とGitHub Actionsワークフロー

図はmermaidで作成してください．
ただし，UMLはplantumlで作成してください．

## Semantic Scholar API 使用ガイド (2024年版)

### 認証とレート制限

#### 非認証アクセス
- レート制限: 5分間に5,000リクエスト（共有プール）
- ほとんどのエンドポイントは認証なしで利用可能
- すべての非認証ユーザー間で共有されるため、混雑時は制限に達しやすい

#### 認証アクセス
- APIキーを使用した認証を推奨
- 初期レート制限: 
  - `/paper/batch`, `/paper/search`, `/recommendations`: 1 RPS
  - その他のエンドポイント: 10 RPS
- APIキーはメールで受け取り、他者と共有しないこと

#### ベストプラクティス
- すべてのリクエストにAPIキーを含める
- エクスポネンシャルバックオフ戦略を使用する
- 必要なフィールドのみを指定してレスポンスを最適化
- 2024年以降、認証済みリクエストの使用を強く推奨

### Python実装例

```python
# 公式のSemantic Scholar Python クライアント（非公式ライブラリ）
from semanticscholar import SemanticScholar

# クライアントのインスタンス化
sch = SemanticScholar(api_key="YOUR_API_KEY")

# 論文の取得
paper = sch.get_paper('10.1093/mind/lix.236.433')
print(paper.title)

# バルク検索の使用（効率的）
results = sch.search_paper('machine learning', limit=100)
```

### 重要な注意事項
- レート制限に達した場合は、エクスポネンシャルバックオフで再試行
- 大量のデータが必要な場合は、Datasets APIを使用してローカルで処理
- fieldsパラメータで必要なデータのみを取得し、パフォーマンスを向上

## Python MCP サーバー実装ガイド (FastMCP 2024年版)

### MCPとは

Model Context Protocol (MCP)は、2024年11月にAnthropicによって導入された、LLMに外部ツールやリソースを提供する標準化された方法です。「AIのUSB-Cポート」とも呼ばれ、LLMとリソースを統一的に接続します。

### FastMCPフレームワーク

FastMCP 1.0は2024年に公式MCP Python SDKに統合されました。現在はFastMCP 2.0が活発にメンテナンスされており、MCPエコシステムで作業するための完全なツールキットを提供しています。

#### 主要機能
- **Resources**: データの公開（GETエンドポイントのような役割）
- **Tools**: 機能の提供（POSTエンドポイントのような役割）
- **Prompts**: LLMインタラクションの再利用可能なテンプレート

### 実装例

```python
from mcp.server.fastmcp import FastMCP

# サーバーの作成
server = FastMCP("My Calculator Server")

# ツールの定義（デコレータを使用）
@server.tool(
    name="evaluate_expression",
    description="数式を評価して結果を返す"
)
def evaluate_expression(expression: str) -> float:
    """数式を評価して結果を返します。"""
    return eval(expression)  # 実際の実装ではより安全な方法を使用

# リソースの定義
@server.resource("config://settings")
async def get_settings():
    return {"version": "1.0", "features": ["math", "eval"]}

# プロンプトの定義
@server.prompt("calculation_help")
def calculation_prompt():
    return "I can help you with mathematical calculations."
```

### 高度な機能

#### Contextオブジェクト
MCP機能へのアクセスを提供し、以下が可能：
- 進捗報告
- デバッグ情報の送信
- サーバー機能へのアクセス

#### 構造化出力
Pydanticモデルを使用した複雑なデータ構造のサポート：

```python
from pydantic import BaseModel

class CalculationResult(BaseModel):
    expression: str
    result: float
    steps: List[str]

@server.tool()
def complex_calculation(expression: str) -> CalculationResult:
    # 実装
    pass
```

### セットアップと環境

#### 要件
- Python 3.10以上
- uvパッケージマネージャー（推奨）

#### インストール
```bash
# uvを使用したインストール
uv add "mcp[cli]"

# プロジェクトの初期化
uv init my-mcp-server
cd my-mcp-server
uv add "mcp[cli]" httpx pydantic
```

### デプロイメントとテスト

#### MCPインスペクターでのテスト
```bash
uv run mcp dev src/my_server.py
```

#### Claude Desktopへの統合
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uvx",
      "args": ["my-mcp-server"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

### ベストプラクティス

1. **型ヒントとドキュメント**: FastMCPは型ヒントとdocstringを活用して自動的にツール定義を強化
2. **エラーハンドリング**: 適切な例外処理とユーザーフレンドリーなエラーメッセージ
3. **非同期処理**: I/O操作には async/await を使用
4. **テスト**: 組み込みのテストツールを活用
5. **認証**: 本番環境では適切な認証システムを実装

### 2024年の重要な変更点

- FastMCP 1.0が公式SDKに統合
- FastMCP 2.0は完全なエコシステムを提供（クライアントライブラリ、認証システム、デプロイツール等）
- 主要AIプラットフォームとの統合が強化
- プロダクション対応のインフラストラクチャパターンが確立