# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_validate_templates_escopo.py
TITULO: validate-templates.py valida os templates reais (scaffold/templates/)
DATA: 24/11/2026 15:29
MODIFICADO: 24/11/2026 15:29
VERSÃO: 1.0.0
DEPEND: pytest, pyyaml
STATUS: DEV

Bug: o validador (spec 065) só olhava `.specify/templates/` — arquivos do SpecKit
gerados pelo `specify init`, que o projeto não edita — e exigia `template_version`
que o upstream não tem, então `make validate-templates` sempre falhava e os
templates reais em `scaffold/templates/` nunca eram validados. Também não era
recursivo, não aceitava YAML multi-documento e tratava templates Go (Helm) como YAML.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / "scripts" / "validate-templates.py"

_spec = importlib.util.spec_from_file_location("validate_templates_escopo", _SCRIPT)
assert _spec and _spec.loader
vt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vt)


def _validar(raiz: Path, **opcoes) -> object:
    return vt.TemplateValidator(raiz, **opcoes).validate_all()


def test_busca_recursiva(tmp_path: Path) -> None:
    aninhado = tmp_path / "project" / "perfil" / "config"
    aninhado.mkdir(parents=True)
    (aninhado / "quebrado.yml").write_text("chave: [sem fechar\n", encoding="utf-8")
    resultado = _validar(tmp_path, required_frontmatter=(), check_links=False)
    assert resultado.files_checked == 1
    assert any("YAML syntax error" in e.message for e in resultado.errors)


def test_yaml_multidocumento_e_valido(tmp_path: Path) -> None:
    (tmp_path / "objetivo.yaml").write_text(
        "---\n# cabeçalho\nversao: 2\n---\nprojeto:\n  nome: x\n", encoding="utf-8"
    )
    resultado = _validar(tmp_path, required_frontmatter=(), check_links=False)
    assert not resultado.errors, [e.message for e in resultado.errors]


def test_template_go_do_helm_nao_e_validado_como_yaml(tmp_path: Path) -> None:
    helm = tmp_path / "k8s-helm" / "helm" / "templates"
    helm.mkdir(parents=True)
    (helm / "deployment.yaml").write_text(
        'apiVersion: apps/v1\nmetadata:\n  labels:\n    {{- include "x.labels" . | nindent 4 }}\n',
        encoding="utf-8",
    )
    resultado = _validar(tmp_path, required_frontmatter=(), check_links=False)
    assert not resultado.errors, [e.message for e in resultado.errors]


def test_frontmatter_opcional_quando_nao_exigido(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Sem frontmatter\n", encoding="utf-8")
    resultado = _validar(tmp_path, required_frontmatter=(), check_links=False)
    assert not resultado.errors
    assert not resultado.warnings


def test_links_nao_checados_quando_desligado(tmp_path: Path) -> None:
    (tmp_path / "guia.md").write_text(
        "[docs](./docs/do-projeto-gerado.md)\n", encoding="utf-8"
    )
    resultado = _validar(tmp_path, required_frontmatter=(), check_links=False)
    assert not resultado.warnings


def test_caches_ignorados(tmp_path: Path) -> None:
    cache = tmp_path / "perfil" / ".ruff_cache"
    cache.mkdir(parents=True)
    (cache / "lixo.json").write_text("{invalido", encoding="utf-8")
    resultado = _validar(tmp_path, required_frontmatter=(), check_links=False)
    assert resultado.files_checked == 0
    assert not resultado.errors


@pytest.mark.parametrize("opcao", ["--json", None])
def test_cli_valida_scaffold_templates_e_passa(opcao: str | None) -> None:
    """Sem argumentos, a CLI valida scaffold/templates/ — e os templates reais passam."""
    args = [sys.executable, str(_SCRIPT)] + ([opcao] if opcao else [])
    proc = subprocess.run(  # noqa: S603
        args, cwd=_ROOT, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0, proc.stdout[-2000:]
    assert "scaffold/templates" in proc.stdout


def test_template_go_corrompido_e_erro(tmp_path: Path) -> None:
    """`{{ ... }}` quebrado em `{ { ... } }` (formatador de YAML) não renderiza no Helm."""
    helm = tmp_path / "k8s-helm" / "helm" / "templates"
    helm.mkdir(parents=True)
    (helm / "service.yaml").write_text(
        'metadata:\n  name: { { include "x.fullname" . } }\n', encoding="utf-8"
    )
    resultado = _validar(tmp_path, required_frontmatter=(), check_links=False)
    assert any("Go template" in e.message for e in resultado.errors), [
        e.message for e in resultado.errors
    ]


def test_yaml_hibrido_valida_so_o_frontmatter(tmp_path: Path) -> None:
    """objetivo*.yaml v2: frontmatter YAML + corpo Markdown (formato do objetivo_parser)."""
    (tmp_path / "objetivo.yaml").write_text(
        '---\nversion: "2.0"\nproject:\n  name: x\n---\n\n# Objetivo\n\n'
        "<!-- Progressive Disclosure:\n     P0 (essencial): Seções 1-3\n-->\n\n"
        "## 1️⃣ O que este projeto faz? <!-- P0 -->\n\n**Em uma frase**: [x]\n",
        encoding="utf-8",
    )
    resultado = _validar(tmp_path, required_frontmatter=(), check_links=False)
    assert not resultado.errors, [e.message for e in resultado.errors]


def test_yaml_hibrido_com_frontmatter_invalido_e_erro(tmp_path: Path) -> None:
    (tmp_path / "objetivo.yaml").write_text(
        "---\nproject: [sem fechar\n---\n\n# Objetivo\n", encoding="utf-8"
    )
    resultado = _validar(tmp_path, required_frontmatter=(), check_links=False)
    assert any("YAML syntax error" in e.message for e in resultado.errors)
