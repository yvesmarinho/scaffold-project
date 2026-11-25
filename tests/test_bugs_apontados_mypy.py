"""
Testes de regressão — bugs reais encontrados pelo mypy (PR #69).

1. ``IssueTemplateMerger._merge_markdown``: template sem frontmatter (ou com
   frontmatter inválido / não-mapeamento) e arquivo existente com frontmatter
   → ``_deep_merge(None, ...)`` levantava ``TypeError``.
2. ``scripts/manage.py``: ``self._refresh_info(...)`` (coroutine) chamado sem
   ``await`` em ``_save_generated_file`` → painel de info nunca atualizava.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import yaml

from scripts.lib.issue_template_merge import IssueTemplateMerger

_ROOT = Path(__file__).resolve().parent.parent

_EXISTENTE_COM_FM = """---
name: Bug
labels: [bug, meu-label]
---
## Descrição
Texto customizado pelo usuário.
"""


def _issue_file(tmp_path: Path, content: str) -> Path:
    path = tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug_report.md"
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")
    return path


def _frontmatter(text: str) -> dict:
    assert text.startswith("---\n"), text[:80]
    return yaml.safe_load(text.split("---\n")[1])


@pytest.mark.parametrize(
    "template",
    [
        "## Descrição\nSem frontmatter nenhum.\n",
        "---\nname: [quebrado\n---\n## Descrição\n",  # YAML inválido
        "---\n- lista\n- nao-mapeamento\n---\n## Descrição\n",  # não é dict
        "---\nso-texto\n---\n## Descrição\n",  # escalar
    ],
)
def test_template_sem_frontmatter_valido_preserva_o_do_usuario(tmp_path, template):
    path = _issue_file(tmp_path, _EXISTENTE_COM_FM)

    item = IssueTemplateMerger().merge(path, template, interactive=False)

    assert item.status != "error", item.message
    fm = _frontmatter(path.read_text(encoding="utf-8"))
    assert fm["name"] == "Bug"
    assert fm["labels"] == ["bug", "meu-label"]


def test_existente_com_frontmatter_nao_mapeamento_nao_quebra(tmp_path):
    path = _issue_file(tmp_path, "---\n- a\n- b\n---\n## Corpo\n")
    template = "---\nname: Bug\nlabels: [bug]\n---\n## Corpo\n"

    item = IssueTemplateMerger().merge(path, template, interactive=False)

    assert item.status != "error", item.message
    assert _frontmatter(path.read_text(encoding="utf-8"))["name"] == "Bug"


def test_merge_normal_user_wins_continua_funcionando(tmp_path):
    path = _issue_file(tmp_path, _EXISTENTE_COM_FM)
    template = (
        "---\nname: Bug Report\nlabels: [bug]\nassignees: []\n---\n## Descrição\n"
    )

    item = IssueTemplateMerger().merge(path, template, interactive=False)

    assert item.status != "error", item.message
    fm = _frontmatter(path.read_text(encoding="utf-8"))
    assert fm["name"] == "Bug"  # usuário vence
    assert "assignees" in fm  # chave nova do template entra


# ---------------------------------------------------------------------------
# manage.py — coroutines sempre aguardadas (sem depender do textual)
# ---------------------------------------------------------------------------


def _unawaited_self_coroutine_calls(source: str) -> list[str]:
    tree = ast.parse(source)

    def _is_textual_worker(fn: ast.AsyncFunctionDef) -> bool:
        """``@work``/``@work(...)`` devolve Worker: chamar sem await é o uso correto."""
        for dec in fn.decorator_list:
            target = dec.func if isinstance(dec, ast.Call) else dec
            if isinstance(target, ast.Name) and target.id == "work":
                return True
        return False

    async_methods = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and not _is_textual_worker(node)
    }
    awaited: set[int] = {
        id(node.value) for node in ast.walk(tree) if isinstance(node, ast.Await)
    }
    offenders = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
            and node.func.attr in async_methods
            and id(node) not in awaited
        ):
            offenders.append(f"linha {node.lineno}: self.{node.func.attr}()")
    return offenders


def test_detector_acusa_coroutine_sem_await():
    src = (
        "class A:\n"
        "    async def f(self): ...\n"
        "    async def g(self):\n"
        "        self.f()\n"
        "        await self.f()\n"
    )
    assert _unawaited_self_coroutine_calls(src) == ["linha 4: self.f()"]


def test_detector_ignora_workers_do_textual():
    src = (
        "class A:\n"
        "    @work(exclusive=True)\n"
        "    async def f(self): ...\n"
        "    def g(self):\n"
        "        self.f()\n"
    )
    assert _unawaited_self_coroutine_calls(src) == []


def test_manage_py_nao_chama_coroutine_sem_await():
    source = (_ROOT / "scripts" / "manage.py").read_text(encoding="utf-8")
    assert _unawaited_self_coroutine_calls(source) == []
