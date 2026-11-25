"""
Testes — Copilot P0 (docs/analysis/ANALISE-vscode-copilot-customization.md).

Decisões do usuário (25/11/2026):
- harness "Só Copilot": sem prompt files nem ``handoffs`` (exclusivos do Local);
  rituais de sessão e perfis de domínio viram skills em ``.github/skills/``;
- agents herdados: remover os ``speckit.*`` (e handoffs para eles), manter os demais.
- settings: ``chat.mcp.autostart`` com valor do enum documentado;
  ``github.copilot.chat.enableMcp`` (inexistente) e
  ``chat.promptFilesRecommendations`` (prompts inexistentes) removidos.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
_SCAFFOLD = _ROOT / "scripts" / "scaffold.py"
_SPECKIT = _ROOT / "scaffold" / "templates" / "speckit"
_SKILLS = _ROOT / "scaffold" / "templates" / "skills"
_SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SESSION_SKILLS = ("session-start", "session-end", "session-start-first")
_AUTOSTART_VALUES = {"never", "onlyNew", "newAndOutdated"}


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, f"{path} sem frontmatter YAML"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict), f"{path}: frontmatter não é mapeamento"
    return data


# ---------------------------------------------------------------------------
# Templates (fonte)
# ---------------------------------------------------------------------------


def test_nao_ha_agents_nem_prompts_speckit_nos_templates():
    assert not list((_SPECKIT / "agents").glob("speckit.*.agent.md"))
    assert not (_SPECKIT / "prompts").exists()


def test_nenhum_agent_usa_handoffs():
    offenders = [
        p.name
        for p in (_SPECKIT / "agents").glob("*.agent.md")
        if "handoffs" in _frontmatter(p)
    ]
    assert offenders == []


def test_nenhum_agent_referencia_speckit_agent():
    offenders = [
        p.name
        for p in (_SPECKIT / "agents").glob("*.agent.md")
        if re.search(r"agent:\s*speckit\.", p.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def _skill_dirs() -> list[Path]:
    return sorted(p for p in _SKILLS.iterdir() if p.is_dir())


def test_skills_de_sessao_e_perfis_existem():
    names = {p.name for p in _skill_dirs()}
    expected = set(_SESSION_SKILLS) | {
        "devops-programming",
        "devops-infrastructure",
        "devops-analysis",
        "devops-security",
        "python-fastapi",
        "python-flask",
        "typescript-next",
        "k8s-helm",
        "terraform-aws",
    }
    assert expected <= names


@pytest.mark.parametrize("skill_dir", _skill_dirs() if _SKILLS.is_dir() else [])
def test_frontmatter_de_skill_valido(skill_dir: Path):
    skill = skill_dir / "SKILL.md"
    assert skill.is_file()
    fm = _frontmatter(skill)
    assert fm.get("name") == skill_dir.name, "name deve ser igual ao diretório"
    assert _SKILL_NAME_RE.match(fm["name"]) and len(fm["name"]) <= 64
    desc = fm.get("description")
    assert isinstance(desc, str) and desc.strip() and len(desc) <= 1024
    assert "mode" not in fm, "campo 'mode' é de prompt file, não de skill"
    assert ".prompt.md" not in skill.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Settings VS Code
# ---------------------------------------------------------------------------


def test_settings_globais_sem_chaves_invalidas():
    from scripts.lib.vscode import _SETTINGS_GLOBAL

    assert "github.copilot.chat.enableMcp" not in _SETTINGS_GLOBAL
    assert "chat.promptFilesRecommendations" not in _SETTINGS_GLOBAL
    assert _SETTINGS_GLOBAL.get("chat.mcp.autostart") in _AUTOSTART_VALUES


# ---------------------------------------------------------------------------
# Projeto gerado (CLI real)
# ---------------------------------------------------------------------------


def _generate(tmp_path: Path, ai: str) -> Path:
    # --shared-dir vazio: reproduz o CI (sem .copilot-shared), onde
    # .copilot-rules.md é copiado do repositório em vez de virar symlink.
    shared = tmp_path / "shared-vazio"
    shared.mkdir(exist_ok=True)
    target = tmp_path / f"proj-{ai}"
    env = {**os.environ, "PATH": os.environ["PATH"]}
    result = subprocess.run(
        [
            sys.executable,
            str(_SCAFFOLD),
            "--new",
            "--ci",
            "--no-log",
            "--name",
            f"proj-{ai}",
            "--domain",
            "programming",
            "--language",
            "python",
            "--ai-assistant",
            ai,
            "--shared-dir",
            str(shared),
            "--target-dir",
            str(target),
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    return target


@pytest.fixture(scope="module")
def projeto_copilot(tmp_path_factory) -> Path:
    return _generate(tmp_path_factory.mktemp("p0"), "copilot")


@pytest.fixture(scope="module")
def projeto_claude(tmp_path_factory) -> Path:
    return _generate(tmp_path_factory.mktemp("p0c"), "claude")


@pytest.mark.integration
def test_copilot_recebe_skills_de_sessao_e_perfis(projeto_copilot: Path):
    skills = projeto_copilot / ".github" / "skills"
    for name in (*_SESSION_SKILLS, "devops-programming", "devops-security"):
        skill = skills / name / "SKILL.md"
        assert skill.is_file(), name
        assert _frontmatter(skill)["name"] == name


@pytest.mark.integration
def test_projeto_gerado_sem_prompt_files(projeto_copilot: Path):
    assert not (projeto_copilot / ".github" / "prompts").exists()


@pytest.mark.integration
def test_agents_gerados_sem_handoffs(projeto_copilot: Path):
    agents = list((projeto_copilot / ".github" / "agents").glob("*.agent.md"))
    assert agents, "agents customizados devem continuar sendo copiados"
    assert all("handoffs" not in _frontmatter(a) for a in agents)


@pytest.mark.integration
def test_settings_gerado_valido(projeto_copilot: Path):
    settings = json.loads(
        (projeto_copilot / ".vscode" / "settings.json").read_text(encoding="utf-8")
    )
    assert "github.copilot.chat.enableMcp" not in settings
    assert "chat.promptFilesRecommendations" not in settings
    assert settings.get("chat.mcp.autostart") in _AUTOSTART_VALUES


@pytest.mark.integration
def test_nenhuma_referencia_a_prompts_nos_arquivos_de_ia(projeto_copilot: Path):
    candidates = [
        projeto_copilot / ".github" / "copilot-instructions.md",
        *projeto_copilot.glob(".copilot-rules*.md"),
        *(projeto_copilot / ".github" / "skills").glob("*/SKILL.md"),
    ]
    offenders = [
        str(p.relative_to(projeto_copilot))
        for p in candidates
        if p.is_file() and ".github/prompts" in p.read_text(encoding="utf-8")
    ]
    assert offenders == []


@pytest.mark.integration
def test_claude_recebe_perfis_mas_nao_skills_de_sessao(projeto_claude: Path):
    """Claude já tem os rituais em .claude/commands; perfis valem para toda IA."""
    skills = projeto_claude / ".github" / "skills"
    assert (skills / "devops-programming" / "SKILL.md").is_file()
    assert not (skills / "session-start").exists()
    assert (projeto_claude / ".claude" / "commands" / "session-start..md").is_file()
