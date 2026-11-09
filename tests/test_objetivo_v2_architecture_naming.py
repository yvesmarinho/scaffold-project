# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_objetivo_v2_architecture_naming.py
TITULO: objetivo v2 — seções de Arquitetura e Padrões de Nomenclatura
DATA: 09/11/2026 17:25
MODIFICADO: 09/11/2026 17:11
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

Melhoria de docs/planning/lembrete.md: "corrigir o objetivo-init-V2.yaml para adicionar
a sessão infrastructure e architecture; padrão de nomenclatura de pastas e arquivos;
padrão de nomenclatura de objetos, classes e funções".
"""

from __future__ import annotations

import pytest

from scripts.lib.objetivo_wizard import ObjetivoWizard, WizardAnswers, naming_conventions


def _render(language: str, **overrides: str) -> str:
    answers = WizardAnswers(
        project_name="demo",
        project_title="Demo",
        project_type="cli-tool",
        project_domain="programming",
        project_language=language,
        created_by="tester",
        answers=dict(overrides),
    )
    return ObjetivoWizard()._render_template(answers)


def test_template_tem_secoes_de_infra_arquitetura_e_nomenclatura():
    content = _render("python")
    assert "### Infraestrutura" in content
    assert "## 🔟 Arquitetura" in content
    assert "## 1️⃣1️⃣ Padrões de Nomenclatura" in content


def test_arquitetura_default_em_camadas():
    content = _render("python")
    for layer in ("Presentation", "Application", "Domain", "Infrastructure"):
        assert layer in content


def test_nomenclatura_python():
    content = _render("python")
    assert "snake_case.py" in content
    assert "PascalCase" in content
    assert "UPPER_SNAKE_CASE" in content


def test_nomenclatura_typescript():
    content = _render("typescript")
    assert "kebab-case.ts" in content
    assert "PascalCase.tsx" in content
    assert "camelCase" in content


def test_linguagem_desconhecida_usa_padrao_generico():
    content = _render("cobol")
    assert "## 1️⃣1️⃣ Padrões de Nomenclatura" in content
    assert "kebab-case" in content  # pastas, docs e scripts


def test_resposta_do_usuario_sobrescreve_default():
    content = _render("python", **{"{{ARCHITECTURE}}": "Hexagonal pura"})
    assert "Hexagonal pura" in content
    assert "Presentation" not in content.split("## 🔟 Arquitetura")[1].split("##")[0]


def test_sem_placeholders_remanescentes():
    content = _render("python")
    assert "{{ARCHITECTURE}}" not in content
    assert "{{NAMING_CONVENTIONS}}" not in content


@pytest.mark.parametrize("bad", ["", None, 123])
def test_naming_conventions_entrada_invalida_cai_no_generico(bad):
    assert "kebab-case" in naming_conventions(bad)  # type: ignore[arg-type]


def test_naming_conventions_case_insensitive():
    assert naming_conventions("Python") == naming_conventions("python")
