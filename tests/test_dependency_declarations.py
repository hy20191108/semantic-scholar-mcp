"""Dependency declarations must exclude releases the package cannot run with.

Installs that bypass uv.lock (pip, ``uvx --from git+...``) resolve the newest
versions that pyproject.toml allows, so open-ended ranges break the server as
soon as an incompatible major release appears upstream.
"""

import sys
from pathlib import Path

import pytest
from packaging.requirements import Requirement

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _requirements() -> dict[str, Requirement]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    reqs = (Requirement(spec) for spec in data["project"]["dependencies"])
    return {req.name.lower(): req for req in reqs}


def test_pymupdf_is_declared_for_direct_fitz_import() -> None:
    # pdf_processor.py imports fitz (PyMuPDF) directly; pymupdf4llm 2.0 no
    # longer pulls PyMuPDF in as its own dependency.
    assert "pymupdf" in _requirements()


@pytest.mark.parametrize(
    ("name", "first_unsupported"),
    [
        # server.py imports mcp.server.fastmcp, which mcp 2.0 removed.
        ("mcp", "2.0.0"),
        # pymupdf4llm 2.0 changed its dependency set; 1.x is the tested line.
        ("pymupdf4llm", "2.0"),
    ],
)
def test_dependency_excludes_unsupported_major(
    name: str, first_unsupported: str
) -> None:
    req = _requirements()[name]
    assert not req.specifier.contains(first_unsupported, prereleases=True)
