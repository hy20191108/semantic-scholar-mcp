# Serena 準拠移行ステータス（2025-11-08）

本ドキュメントは、semantic-scholar-mcp の Serena 準拠状況を最新の作業内容に基づき要約するものです。

## 決定事項（合意済みの方針）
- 実行後ガイダンス: 同梱する（返り値に `instructions` キー）
- 表示の主眼: 実行前のツール説明（docstring/ツール説明に Next Steps 注入）
- 返り値の粒度: トップレベルは極力 `data/total/offset/limit/has_more` に統一
- Lint/Type: `src/` は ruff/mypy を通過。`scripts/**` は Ruff 対象外に設定
- ドキュメント: YAML を SSOT（唯一の真実源）。README/CLAUDE.md は仕組み説明に縮約（Markdownテンプレは必要最小限）

## 現状（2025-11-08 時点）
- ツール登録: 24（起動スモーク OK）／プロンプト: 3／リソース: 0
- YAML 注入: 全ツールに `@inject_yaml_instructions(tool, category)` を適用済み
- 実行後ガイダンス: 返り値が dict でも JSON 文字列でも `instructions` を同梱（安全化済み）
- 返り値形式: 主要ツールは `json.dumps(..., ensure_ascii=False, indent=2)` に統一
  - `search_papers` は PaginatedResponse を `model_dump()` して `data/total/offset/limit` を返却
  - 一部ツールは `data` 直下への統一が未完（順次統一予定）
- Lint/Type: `uv run ruff check .` All checks passed（scripts 除外）。`uv run mypy src/` Success

## 代表スモーク（匿名モード）
- `search_papers(query="transformer", limit=1)` → 429 後の自動リトライで 200、JSON＋`instructions`
- `get_paper(<paperId>)` → 200、JSON＋`instructions`
- `check_api_key_status()` → ローカル構成診断を JSON で返却＋`instructions`

## 未完了タスク（優先順）
1. 返り値スキーマの完全統一
   - すべてのツールでトップレベル `data/...` に整理（`citations/references/authors/...` 等は `data` 配下へ）
   - `total/offset/limit/has_more` は取得可能な範囲で付与
2. docstring（Returns）の統一
   - 「JSON文字列（トップレベルに `data/...`）」の表記へ揃える
3. 初期インストラクション（任意）
   - FastMCP(instructions=...) に学術検索の原則・rate limit配慮等の短文を設定
4. ドキュメント縮約
   - README/CLAUDE.md を「仕組みと運用」に再編（指示本文は YAML のみ）

## 差分概要（主な変更）
- `src/semantic_scholar_mcp/server.py`
  - YAML注入（全ツール）／実行後 `instructions` 同梱の安全化
  - 主要ツールの返り値を JSON 文字列へ統一
  - 起動・スモークの安定化
- `src/semantic_scholar_mcp/instruction_loader.py`
  - YAML ローダ／`inject_yaml_instructions`／Next Steps 整形
- `src/semantic_scholar_mcp/resources/tool_instructions/**`
  - 24ツール分の YAML（SSOT）
- `pyproject.toml`
  - Ruff の exclude に `scripts/**` を追加

## 次の一手（実装プラン）
1) 返り値統一: 全ツールで `data/…` へ収束（段階リリース）
2) docstring 更新: Returns 節を JSON構造に合わせて明確化
3) 必要に応じて初期インストラクションを FastMCP に設定
4) 最終ゲート: `ruff/mypy/pytest` でグリーン維持

---
更新者: 自動生成（作業ログに基づく）
タイムスタンプ: 2025-11-08
