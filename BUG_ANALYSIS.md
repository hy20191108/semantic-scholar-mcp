# メモリ管理アクティベーション バグ分析

## 発見された問題

### 問題1: プロジェクト登録キーの不一致

**場所**: `src/semantic_scholar_mcp/agent.py` の `activate_project()` メソッド

**問題の詳細**:

プロジェクトのアクティベーションと登録のロジックに矛盾があります。

```python
# Line 125: 登録されたプロジェクト名で検索
if project_path_or_name in self._registered_projects:
    project_path = self._registered_projects[project_path_or_name]
```

しかし、プロジェクトを登録する際は:

```python
# Line 175-177: 異なる条件チェック
if project_path_or_name not in self._registered_projects:
    project_name = project.project_name  # YAMLから読み込まれた名前
    self.register_project(project_name, project_path)
```

### 問題のシナリオ

#### シナリオA: パスでアクティベート
1. ユーザーが `/tmp/my_project` でプロジェクトをアクティブ
2. `project_path_or_name = "/tmp/my_project"`
3. Line 125の条件 = **FALSE** (未登録)
4. パスとして処理される (Line 130)
5. プロジェクトをロード、`project.project_name = "My Research"`
6. Line 175の条件 = **TRUE**
7. `register_project("My Research", "/tmp/my_project")`
8. **登録キー = "My Research"** (パスではない)

#### シナリオB: 次回同じパスでアクティベート
1. ユーザーが再び `/tmp/my_project` でアクティブ
2. `project_path_or_name = "/tmp/my_project"`
3. Line 125の条件 = **FALSE** (キー"/tmp/my_project"は存在しない、"My Research"のみ)
4. **再びパスとして処理される** (不要なロード)
5. Line 175の条件 = **FALSE** (今度は"My Research"が存在)
6. 登録はスキップ

**問題**: パスでアクティベートした後、同じパスでアクティベートすると毎回ロードが発生（キャッシュが効かない）

### 問題2: create_project後のactivate判定のバグ

**場所**: `src/semantic_scholar_mcp/agent.py` の `create_project()` メソッド (Line 225-263)

```python
def create_project(
    self,
    project_root: str | Path,
    project_name: str,
    research_topic: str | None = None,
    activate: bool = True,
    **kwargs,
) -> Project:
    project = Project.create(
        project_root=project_root,
        project_name=project_name,
        research_topic=research_topic,
        **kwargs,
    )

    # Register the project
    self.register_project(project_name, project.project_root)

    # Activate if requested
    if activate:
        self._active_project = project
        logger.info(f"Created and activated project '{project_name}'")
    else:
        logger.info(f"Created project '{project_name}'")

    return project
```

**問題**: `activate=True` の場合、プロジェクトは登録されるが、**`_is_newly_created` フラグが正しく伝播されない**可能性がある

### 問題3: メモリツールのエラーハンドリング不足

**場所**: `src/semantic_scholar_mcp/server.py` のメモリツール関数 (Line 2025-2299)

```python
@mcp.tool()
@mcp_error_handler(tool_name="write_memory")
async def write_memory(
    memory_name: str,
    content: str,
    max_chars: int = Field(
        default=100000, description="Maximum characters allowed in memory content"
    ),
) -> str:
    if research_agent is None:
        return json.dumps(
            {
                "success": False,
                "error": "ResearchAgent not initialized. Please restart the server.",
            },
            ensure_ascii=False,
        )

    from .tools.memory_tools import WriteMemoryTool

    tool = research_agent.get_tool(WriteMemoryTool)
    result = tool.apply(memory_name=memory_name, content=content, max_chars=max_chars)
    return json.dumps({"success": True, "data": result}, ensure_ascii=False)
```

**問題**:
- `research_agent is None` のチェックのみ
- **プロジェクトがアクティブかどうかのチェックがない**
- `tool.apply()` で `RuntimeError` が発生する可能性があるが、明示的なハンドリングがない

`tools/base.py` の `memories_manager` プロパティ:

```python
@property
def memories_manager(self) -> "MemoriesManager":
    if self._agent is None:
        raise RuntimeError("Tool has no agent instance")

    project = self._agent.get_active_project()
    if project is None:
        raise RuntimeError("No active project; please activate a project first")

    return project.memories_manager
```

**問題**: プロジェクトが未アクティブの場合、ユーザーフレンドリーでないエラーメッセージが表示される

## 推奨される修正

### 修正1: プロジェクト登録の一貫性確保

`activate_project()` メソッドを修正し、パスでアクティベートした場合も適切にキャッシュされるようにする。

**提案**:
- パスでアクティベートした場合、パスもキーとして登録する
- または、パスを正規化して常に同じキーを使用する

### 修正2: メモリツールのエラーハンドリング改善

`server.py` のメモリツール関数に、プロジェクトアクティブチェックを追加する。

**提案**:
```python
async def write_memory(...) -> str:
    if research_agent is None:
        return json.dumps({
            "success": False,
            "error": "ResearchAgent not initialized."
        }, ensure_ascii=False)

    # 追加: プロジェクトアクティブチェック
    if research_agent.get_active_project() is None:
        return json.dumps({
            "success": False,
            "error": "No project is active. Please use activate_project or create_project first."
        }, ensure_ascii=False)

    # ... 以降の処理
```

### 修正3: activate_projectのロジック改善

両方のキー（プロジェクト名とパス）でプロジェクトを検索できるようにする。

## 再現手順

1. サーバー起動
2. `write_memory` を呼び出す（プロジェクト未アクティブ）
   - **期待**: わかりやすいエラーメッセージ
   - **実際**: RuntimeError が発生（@mcp_error_handlerでキャッチされるが不明瞭）

3. `/tmp/test_project` でプロジェクトを作成＆アクティブ
4. 同じパス `/tmp/test_project` で再度アクティブ
   - **期待**: キャッシュされたプロジェクトを使用
   - **実際**: 毎回Project.load()が実行される

## 影響度

- **低**: テストは全てパス（基本機能は動作）
- **中**: ユーザーエクスペリエンスに影響（エラーメッセージ、パフォーマンス）
- **高**: 特定のシナリオで混乱を引き起こす可能性

## 次のステップ

1. Serena MCPツールで詳細なコード分析
2. 修正の実装
3. 新しいテストケースの追加（パスでのアクティベーション、エラーハンドリング）
4. 既存テストの実行確認
