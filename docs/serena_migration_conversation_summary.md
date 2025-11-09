# Serena方式移行に関する会話サマリ（semantic-scholar-mcp）

このドキュメントは、Claudeの会話ログ（`~/.claude/projects/-mnt-ext-hdd1-yoshioka-github-semantic-scholar-mcp/*.jsonl`）に残っている「Serenaと同じ仕組み（YAML→docstring注入）への移行」方針に関する発言を要約したものです。

## 結論（要点）
- ツール説明はYAMLで外部化し（`resources/tool_instructions/<category>/<tool>.yml`）、関数のdocstringへ「Next Steps」を自動注入するSerena方式へ移行する。
- 注入は`inject_yaml_instructions(tool_name, category)`デコレータ（`instruction_loader.py`）で実施する。
- ツール実装は薄いラッパへ簡素化し、API呼び出しは`_with_api_client`/`_call_client_method`等の共通ヘルパに集約する。
- Pythonツールチェーンは`uv`前提（ruff/mypy/pytestの運用整備）。

## 根拠となる会話抜粋（最小限）
- ファイル: `~/.claude/projects/-mnt-ext-hdd1-yoshioka-github-semantic-scholar-mcp/agent-0c9bfa4f.jsonl:2`
  > 「Serenaスタイルのツール説明導入 (2025-10-25)／docstringベースの説明メカニズムへ移行／各ツールに『Next Steps』ガイダンスを追加／外部YAMLテンプレートシステムを実装（`resources/tool_instructions/`）」

- ファイル: `~/.claude/projects/-mnt-ext-hdd1-yoshioka-github-semantic-scholar-mcp/agent-af1c49af.jsonl:4`
  > 関数docstring内に「Next Steps: …」が含まれるコード断片（`batch_get_papers`周辺）— Serena流のガイダンス注入の痕跡。

## 関連する実装ファイル（リポジトリ内）
- `src/semantic_scholar_mcp/instruction_loader.py`
  - YAML読込、`inject_yaml_instructions`実装、Next Steps整形、キャッシュクリア等。
- `src/semantic_scholar_mcp/resources/tool_instructions/**/**/*.yml`
  - 例: `paper/search_papers.yml`, `author/get_author.yml`, `pdf/get_paper_fulltext.yml` など。
- `src/semantic_scholar_mcp/server.py`
  - `@with_tool_instructions` → `@inject_yaml_instructions`への移行作業の痕跡、一部返り値の統一化・薄いラッパ化。

## 変更方針（合意事項の整理）
- YAMLテンプレートを単一の真実源（SSOT）として運用し、LLM向けの使用ガイダンスをdocstringへ注入する。
- 各ツール関数は副作用・冗長な例外処理を避け、共通ヘルパに集約して一貫した挙動にする。
- 返り値仕様（`str`/`ToolResult`）はプロジェクト方針に合わせて全関数で統一する。
- `uv`で品質ゲート（ruff/mypy/pytest）を回すワークフローに統一する。

## 確認済みのログファイル（例）
- `~/.claude/projects/-mnt-ext-hdd1-yoshioka-github-semantic-scholar-mcp/agent-0c9bfa4f.jsonl`
- `~/.claude/projects/-mnt-ext-hdd1-yoshioka-github-semantic-scholar-mcp/agent-af1c49af.jsonl`
- 参考: 直近セッション `ff56395c-4e59-4d76-b648-76ade4a73e44.jsonl`（Serena移行の副作用としてのtry削除後のインデント修正やruff/mypy実行の記録あり）

## 今後のTODO（実務ベース）
- 返り値型の統一（`str`か`ToolResult`か）と、各ツール関数の統一ポリシー適用。
- `@with_tool_instructions`の残存箇所を`@inject_yaml_instructions`へ置換して完全移行。
- `uv run ruff check . --fix` / `uv run mypy src/` / `uv run pytest` による品質ゲートのグリーン化。
- 必要に応じてYAMLテンプレの「Next Steps」を運用ガイドラインに沿って拡充。

---
作成者: 自動生成（Claude会話ログ抽出に基づく要約）
作成日: 2025-11-08
