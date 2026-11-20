"""Guard the SDK range used by fresh installs of the published package."""

import sys
from pathlib import Path

from packaging.requirements import Requirement

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def test_dependency_resolver_keeps_the_mcp_sdk_on_v1() -> None:
    project_file = Path(__file__).resolve().parents[1] / "pyproject.toml"
    dependencies = tomllib.loads(project_file.read_text(encoding="utf-8"))["project"][
        "dependencies"
    ]
    sdk = next(req for req in map(Requirement, dependencies) if req.name == "mcp")

    # The server imports mcp.server.fastmcp, which was removed in SDK v2.
    assert "1.12.3" in sdk.specifier
    assert "2.0.0" not in sdk.specifier
