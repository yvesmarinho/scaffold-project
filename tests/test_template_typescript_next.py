# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_template_typescript_next.py
TITULO: O template typescript-next gera um projeto que passa em tsc, jest, lint e build
DATA: 26/11/2026 15:05
MODIFICADO: 26/11/2026 16:49
VERSÃO: 1.0.0
DEPEND: pytest, yaml; (opcional) pnpm + rede para o teste de ponta a ponta
STATUS: DEV

Em 26/11/2026, ao avaliar os PRs #80–#82 do dependabot, um projeto recém-gerado
com o perfil falhava nas quatro checagens:

- ``jest.config.ts`` com as chaves inexistentes ``setupFilesAfterEach`` e
  ``coverageThresholds`` (tsc e build);
- ``jest-environment-jsdom`` 29 com ``jest`` 30 (tipos incompatíveis);
- teste da rota em jsdom: ``Request is not defined``;
- ``next lint`` (obsoleto) com ESLint 10: opções removidas, lint e build abortam;
- campo ``"pnpm"`` do package.json ignorado pelo pnpm >= 10 (overrides perdidos).

Os testes estáticos rodam sempre. O de ponta a ponta instala as dependências
(rede) e só roda com ``SCAFFOLD_TEST_NODE_TEMPLATES=1`` e ``pnpm`` no PATH.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
_TPL = _ROOT / "scaffold" / "templates" / "project" / "typescript-next"
_DESCRIPTOR = _ROOT / "scaffold" / "profiles" / "typescript-next.yaml"


def _pkg() -> dict:
    return json.loads((_TPL / "package.json").read_text(encoding="utf-8"))


def _major(spec: str) -> int:
    m = re.search(r"\d+", spec)
    assert m, spec
    return int(m.group())


def _declarados() -> set[str]:
    d = yaml.safe_load(_DESCRIPTOR.read_text(encoding="utf-8"))
    return {e["path"] for e in d["templates"] if not e.get("generated")}


# ---------------------------------------------------------------------------
# Estáticos
# ---------------------------------------------------------------------------


def test_jest_config_usa_chaves_validas() -> None:
    texto = (_TPL / "jest.config.ts").read_text(encoding="utf-8")
    assert "setupFilesAfterEnv" in texto
    assert "setupFilesAfterEach" not in texto
    assert re.search(r"\bcoverageThreshold\b", texto)
    assert "coverageThresholds" not in texto


def test_jest_e_ambiente_jsdom_na_mesma_major() -> None:
    dev = _pkg()["devDependencies"]
    assert _major(dev["jest"]) == _major(dev["jest-environment-jsdom"])


def test_teste_da_rota_roda_em_ambiente_node() -> None:
    texto = (_TPL / "tests" / "unit" / "health.test.ts").read_text(encoding="utf-8")
    assert "@jest-environment node" in texto


def test_lint_usa_eslint_cli_com_flat_config() -> None:
    scripts = _pkg()["scripts"]
    assert "next lint" not in scripts["lint"]
    assert "next lint" not in scripts["lint:fix"]
    assert (_TPL / "eslint.config.mjs").is_file()
    assert not (_TPL / ".eslintrc.json").exists()


def test_eslint_compativel_com_os_plugins_do_next() -> None:
    """eslint-plugin-import/react/jsx-a11y declaram suporte só até o ESLint 9."""
    dev = _pkg()["devDependencies"]
    assert _major(dev["eslint"]) == 9
    assert _major(dev["eslint-config-next"]) >= 16  # flat config nativo


def test_build_nao_roda_o_lint_legado() -> None:
    texto = (_TPL / "next.config.ts").read_text(encoding="utf-8")
    assert re.search(r"ignoreDuringBuilds:\s*true", texto)


def test_overrides_do_pnpm_no_workspace() -> None:
    assert "pnpm" not in _pkg(), "campo 'pnpm' é ignorado pelo pnpm >= 10"
    ws = yaml.safe_load((_TPL / "pnpm-workspace.yaml").read_text(encoding="utf-8"))
    assert ws["overrides"] == _pkg()["overrides"]


def test_dockerfile_copia_workspace_antes_do_install() -> None:
    texto = (_TPL / "Dockerfile").read_text(encoding="utf-8")
    copy = next(
        linha
        for linha in texto.splitlines()
        if "package.json" in linha and "COPY" in linha
    )
    assert "pnpm-workspace.yaml" in copy


def test_descritor_declara_os_arquivos_do_template() -> None:
    declarados = _declarados()
    assert "eslint.config.mjs" in declarados
    assert "pnpm-workspace.yaml" in declarados
    assert ".eslintrc.json" not in declarados
    # .gitignore do projeto vem dos templates base; o do perfil nunca é copiado
    reais = {p.relative_to(_TPL).as_posix() for p in _TPL.rglob("*") if p.is_file()} - {
        ".gitignore"
    }
    assert declarados == reais, {
        "declarado sem arquivo": sorted(declarados - reais),
        "arquivo sem declaração": sorted(reais - declarados),
    }


def test_skill_nao_ensina_config_quebrada() -> None:
    """O SKILL.md vai para .github/skills/ e orienta a IA do projeto gerado."""
    skill = _ROOT / "scaffold" / "templates" / "skills" / "typescript-next" / "SKILL.md"
    texto = skill.read_text(encoding="utf-8")
    assert "setupFilesAfterEach" not in texto
    assert ".eslintrc.json" not in texto
    assert "@jest-environment node" in texto
    assert '"jest-environment-jsdom": "^29' not in texto


# ---------------------------------------------------------------------------
# Ponta a ponta (opt-in: rede + pnpm)
# ---------------------------------------------------------------------------

_PNPM = shutil.which("pnpm")


@pytest.mark.slow
@pytest.mark.requires_network
@pytest.mark.skipif(
    os.environ.get("SCAFFOLD_TEST_NODE_TEMPLATES") != "1" or _PNPM is None,
    reason="defina SCAFFOLD_TEST_NODE_TEMPLATES=1 (requer pnpm e rede)",
)
def test_projeto_gerado_passa_tsc_jest_lint_build(tmp_path: Path) -> None:
    # Copia só o que o descritor declara, como o composer faz
    proj = tmp_path / "ts-next"
    for rel in _declarados():
        destino = proj / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        texto = (_TPL / rel).read_text(encoding="utf-8")
        destino.write_text(texto.replace("{project_name}", "ts-next"), "utf-8")
    env = {**os.environ, "CI": "1", "NEXT_TELEMETRY_DISABLED": "1"}
    etapas = [
        ["install", "--ignore-scripts", "--no-frozen-lockfile"],
        ["exec", "tsc", "--noEmit"],
        ["exec", "jest", "--passWithNoTests"],
        ["lint"],
        ["exec", "next", "build"],
    ]
    for args in etapas:
        proc = subprocess.run(  # noqa: S603
            [str(_PNPM), *args],
            cwd=proj,
            env=env,
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert (
            proc.returncode == 0
        ), f"pnpm {' '.join(args)}:\n{proc.stdout[-3000:]}{proc.stderr[-2000:]}"
