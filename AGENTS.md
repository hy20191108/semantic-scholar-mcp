# Semantic Scholar MCP

このリポジトリは，Semantic Scholar APIと研究管理機能をMCP toolとして提供するPython packageである．利用者向けの機能と導入方法は`README.md`を入口にする．

## 作業の境界

- 報告は日本語で行い，新しく書くコード，コメント，docstringは英語にする．
- Pythonの環境，依存関係，commandは`uv`で扱う．現行設定と品質条件は`pyproject.toml`と`.github/workflows/ci.yml`，MCPの起動・接続設定は`.mcp.json`から確認し，版，test数，coverage，command列を本ファイルへ複写しない．
- 実装は`src/`，外から確認できる期待動作は`tests/`，人向けの説明は`README.md`または`docs/`，完了履歴と時点状態はGitまたはIssueが持つ．新機能には対応するtest，bug修正には再発を検出するtestを加える．
- APIの挙動や制限は，同梱した`docs/api-specifications/`と現行の公式資料で確認する．古いstatusや作業ログを現行仕様として使わない．
- 共有hostでは，`docker system prune`や`docker volume prune`など，他者の資源にも影響する全体cleanupを実行しない．操作対象をこのprojectの資源へ限定する．

## MCPの契約

- Semantic Scholar API toolの成功時JSON結果はトップレベルに`data`を持つ．paginationでは該当する`total`，`offset`，`limit`，`has_more`を，batchまたはrecommendationでは返却した`data`の要素数を`count`へ入れ，変更時は契約testも同じ変更単位で直す．
- tool説明の`Next Steps`は`src/semantic_scholar_mcp/resources/tool_instructions/**/*.yml`を正本とする．同名Markdownは互換用であり，Markdownだけを更新しない．
- release作業は`docs/RELEASE_PROCESS.md`を入口に，`scripts/release.sh`と`.github/workflows/`の現行実装を照合する．release，tag，publishは明示された場合だけ実行する．
