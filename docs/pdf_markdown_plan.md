# 開発計画: PDF→Markdown機能

- **目的**  
  Semantic Scholar MCPサーバーにPyMuPDF4LLMを統合し、論文PDFをMarkdownとして取得・応答する`get_markdown_from_pdf`ツールを追加する。

- **タスク概要**  
  - 依存関係追加: `pyproject.toml`へ`pymupdf4llm`等を追記し、ライセンス注意をREADMEに記載。  
  - サービス実装: `src/semantic_scholar_mcp/pdf_processor.py`（仮）に`get_markdown_from_pdf`処理を実装。内部ヘルパーは以下の3関数に統一。  
    - `_resolve_open_access_pdf_url`: Semantic Scholar APIからオープンアクセスPDF URLを取得  
    - `_fetch_pdf_to_disk`: URLからPDFをダウンロードし、保存パスを返却  
    - `_generate_markdown_artifacts`: PyMuPDF4LLMでMarkdown／チャンクを生成し、成果物を書き出す  
  - MCPツール登録: `server.py`で`@mcp.tool()`として公開し、引数は`paper_id`, `output_mode`（全文/チャンク）, `include_images`, `max_pages`, `force_refresh`を想定。  
  - 設定拡張: `core/config`に`pdf_processing`設定（最大サイズ、キャッシュディレクトリ、TTLなど）を追加し、`.env`から上書き可能にする。デフォルトのキャッシュ保存先は`.semantic_scholar_mcp/pdf`、Markdown出力は`.semantic_scholar_mcp/md`に保存。Serenaと同様、構成値は
    1. `.serena/project.yml`（プロジェクト設定）  
    2. `.env`（環境変数）  
    3. コード上のデフォルト  
    の優先順で決まるように統一。  
  - エラーハンドリング: 非公開論文、サイズ超過、変換失敗などに対して一貫したエラーコードを返す。

- **ストレージ設計**
  - `.semantic_scholar_mcp/artifacts/pdfs/{prefix}/{paper_hash}.pdf`: `paper_id`をSHA-1ハッシュ化し、先頭2文字をプレフィックスディレクトリとして保存（Serenaのキャッシュ分割パターンに倣う）。再取得時はサイズ・ハッシュ検証で破損チェック。
  - `.semantic_scholar_mcp/artifacts/markdown/{prefix}/{paper_hash}.md`: Markdown全文を保存。チャンクは`.semantic_scholar_mcp/artifacts/markdown/{prefix}/{paper_hash}.chunks.json`に書き出し、Serenaの`.serena/memories`同様に編集・再利用可能とする。
  - `.semantic_scholar_mcp/cache/index.json`: ファイルとメタデータ（最終更新日時、ページ数、使用オプション、ハッシュ）を追跡し、不要ファイルのクリーンアップに利用。Serenaの`document_symbols_cache`と同じく定期メンテナンスを想定。
  - これらディレクトリは`.gitignore`へ追加し、Serena同様にユーザー環境ごとの一時ファイル扱いとする。
    - `PDF_PROCESSING__ARTIFACT_TTL_HOURS`でTTLを指定し、定期的に自動クリーンアップ。
    - `cleanup_pdf_cache()`ヘルパーを呼び出すことで手動クリーンアップも実行可能。

- **テスト計画**  
  - ユニットテスト: `_render_pdf_markdown`など変換ロジックをモック／サンプルPDFで検証。  
  - 統合テスト: MCPツール経由でオープンアクセスPDFのMarkdown/チャンク取得、異常系（リンクなし・タイムアウト等）を確認。  
  - 追加: テスト用軽量PDFフィクスチャを`tests/resources`に配置し、CIで実行時間を抑える。
  - 対応済み: `include_images=True` 時のAPI仕様に合わせ、`pymupdf4llm.to_markdown`へ渡すキーワードを `image_path` に更新し、関連オプションを再確認する。

- **ドキュメント更新**
  - READMEにツールの概要・使用例・制限事項（オープンアクセス限定、PyMuPDFライセンス）を追記。
  - CLAUDE.mdやその他MCPクライアント向けガイドがあれば、利用方法と設定例を追加。
    - CLIサンプル（チャンクのみレスポンス、画像抽出、キャッシュクリーンアップ）を掲載。
    - PyMuPDF商用ライセンスFAQへの導線を明示。
  - `docs/`にSerenaの保存レイアウトとの対応表を追加し、開発者が運用意図を理解しやすくする。

- **リスクと対策**  
  - PyMuPDFライセンス（AGPL）: 商用利用が想定される場合は利用者に注意喚起。  
  - 大容量PDF: サイズ/ページ制限とタイムアウト設定で負荷を抑制。  
  - キャッシュ管理: キャッシュTTL設定と再取得フラグで整合性維持。インデックスファイルを活用し、Serena同様に定期クリーニングを自動化。
