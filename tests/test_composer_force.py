# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_composer_force.py
TITULO: ProfileComposer respeita --force (upgrade consegue corrigir template de perfil)
DATA: 24/11/2026 16:09
MODIFICADO: 24/11/2026 16:09
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

Problema: `_apply_profile` pulava qualquer arquivo de perfil que já existisse,
ignorando `--force`. Correções de template (ex.: helm/templates/service.yaml
corrompido, BUG de 24/11/2026) nunca chegavam a projetos já gerados via
`scaffold upgrade --force`. O rollback apaga itens "created" — um arquivo
sobrescrito não pode ser marcado assim.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.composer import ProfileComposer  # noqa: E402

_NOVO = "versao: corrigida\n"


@pytest.fixture
def ambiente(tmp_path: Path, make_project_config):
    raiz = tmp_path / "scaffold"
    (raiz / "tpl" / "perfil-x").mkdir(parents=True)
    (raiz / "tpl" / "perfil-x" / "chart.yaml").write_text(_NOVO, encoding="utf-8")
    descritores = raiz / "profiles"
    descritores.mkdir()
    (descritores / "perfil-x.yaml").write_text(
        "name: perfil-x\nlayer: layer2\ntemplates_path: tpl/perfil-x\n"
        "templates:\n  - path: chart.yaml\n",
        encoding="utf-8",
    )
    cfg = make_project_config("programming", "python")
    cfg.target_dir.mkdir(parents=True, exist_ok=True)
    composer = ProfileComposer(descriptors_dir=descritores, project_root=raiz)
    return composer, cfg, cfg.target_dir / "chart.yaml"


def _item(resultado, caminho: Path):
    return next(i for i in resultado.items if i.path == caminho)


def test_sem_force_preserva_arquivo_divergente_e_avisa(ambiente) -> None:
    composer, cfg, destino = ambiente
    destino.write_text("versao: quebrada\n", encoding="utf-8")

    item = _item(composer.compose(["perfil-x"], cfg), destino)

    assert item.status == "skipped"
    assert destino.read_text(encoding="utf-8") == "versao: quebrada\n"
    assert "--force" in (item.message or "")


def test_force_sobrescreve_divergente_com_backup(ambiente) -> None:
    composer, cfg, destino = ambiente
    destino.write_text("versao: quebrada\n", encoding="utf-8")

    item = _item(composer.compose(["perfil-x"], cfg, force=True), destino)

    assert item.status == "updated"
    assert destino.read_text(encoding="utf-8") == _NOVO
    backup = destino.with_name(destino.name + ".backup")
    assert backup.read_text(encoding="utf-8") == "versao: quebrada\n"


def test_force_nao_toca_arquivo_identico(ambiente) -> None:
    composer, cfg, destino = ambiente
    destino.write_text(_NOVO, encoding="utf-8")

    item = _item(composer.compose(["perfil-x"], cfg, force=True), destino)

    assert item.status == "skipped"
    assert not destino.with_name(destino.name + ".backup").exists()


def test_rollback_restaura_arquivo_sobrescrito(ambiente) -> None:
    composer, cfg, destino = ambiente
    destino.write_text("versao: do usuario\n", encoding="utf-8")
    resultado = composer.compose(["perfil-x"], cfg, force=True)

    composer._rollback(resultado.items)

    assert destino.read_text(encoding="utf-8") == "versao: do usuario\n"
    assert not destino.with_name(destino.name + ".backup").exists()


# --- Ponta a ponta: o cenário do bug do Helm (projeto já gerado) ---------------

_ROOT = Path(__file__).resolve().parent.parent
_SCAFFOLD = _ROOT / "scripts" / "scaffold.py"
_TEMPLATE_SERVICE = (
    _ROOT / "scaffold/templates/project/k8s-helm/helm/templates/service.yaml"
)
_CORROMPIDO = 'metadata:\n  name: { { include "my-app.fullname" . } }\n'


def _scaffold(*args: str, cwd: Path):
    import os
    import subprocess

    env = {**os.environ, "SCAFFOLD_LOGS_DIR": str(cwd / "_logs")}
    return subprocess.run(  # noqa: S603
        [sys.executable, str(_SCAFFOLD), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        stdin=subprocess.DEVNULL,
    )


@pytest.fixture(scope="module")
def projeto_k8s(tmp_path_factory: pytest.TempPathFactory) -> Path:
    alvo = tmp_path_factory.mktemp("k8s")
    proc = _scaffold(
        "new",
        "--ci",
        "--name",
        "demo-k8s",
        "--domain",
        "infrastructure",
        "--language",
        "other",
        "--with-code-profile",
        "k8s-helm",
        "--target-dir",
        str(alvo),
        cwd=alvo,
    )
    assert proc.returncode == 0, proc.stderr[-1500:]
    return alvo / "demo-k8s"


def test_upgrade_sem_force_preserva_service_divergente(projeto_k8s: Path) -> None:
    service = projeto_k8s / "helm/templates/service.yaml"
    service.write_text(_CORROMPIDO, encoding="utf-8")

    proc = _scaffold("upgrade", "--ci", cwd=projeto_k8s)

    assert proc.returncode == 0, proc.stderr[-1500:]
    assert service.read_text(encoding="utf-8") == _CORROMPIDO


def test_upgrade_force_corrige_service_com_backup(projeto_k8s: Path) -> None:
    service = projeto_k8s / "helm/templates/service.yaml"
    service.write_text(_CORROMPIDO, encoding="utf-8")

    proc = _scaffold("upgrade", "--force", "--ci", cwd=projeto_k8s)

    assert proc.returncode == 0, proc.stderr[-1500:]
    assert service.read_text(encoding="utf-8") == _TEMPLATE_SERVICE.read_text(
        encoding="utf-8"
    )
    backup = service.with_name("service.yaml.backup")
    assert backup.read_text(encoding="utf-8") == _CORROMPIDO
