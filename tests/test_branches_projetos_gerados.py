"""
Testes — estrutura de branches main/dev/release nos projetos gerados (spec 067).

Decisão do usuário (24/11/2026 e 25/11/2026):
- main + dev; PRs de feature → dev; dev → main só com CI verde;
- fases em ``release/faseN``;
- o gerador cria ``dev`` localmente, ajusta os gatilhos de CI e, havendo remoto
  GitHub e ``gh`` autenticado, publica as branches, define ``dev`` como default e
  protege ``main`` (pulável com ``--no-github-setup``).

Toda falha da etapa ``gh`` é aviso (status ``skipped``), nunca erro de geração.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.lib import git as git_mod
from scripts.lib import github_setup
from scripts.lib.github_setup import (
    InvalidGithubRepoError,
    build_protection_payload,
    configure_github_branches,
    parse_github_slug,
    required_checks_for,
)

_GIT = shutil.which("git") or "git"
_TEMPLATES = Path(__file__).resolve().parent.parent / "scaffold" / "templates"
_GIT_VALIDATION = (
    _TEMPLATES / "base-configs" / "common" / "workflows" / "git-validation.yml"
)


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        [_GIT, *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo_com_commit(make_project_config):
    """Projeto com git init + commit inicial, como o fluxo new_project deixa."""
    cfg = make_project_config("programming", "python")
    cfg.project_path.mkdir(parents=True, exist_ok=True)
    assert git_mod.init_repository(cfg).status == "created"
    (cfg.project_path / "README.md").write_text("x\n", encoding="utf-8")
    assert git_mod.create_initial_commit(cfg).status == "created"
    return cfg


# ---------------------------------------------------------------------------
# Branch dev local
# ---------------------------------------------------------------------------


def test_cria_dev_no_mesmo_commit_da_main_e_faz_checkout(repo_com_commit):
    item = git_mod.create_dev_branch(repo_com_commit)

    path = repo_com_commit.project_path
    assert item.status == "created"
    assert _git(path, "rev-parse", "dev") == _git(path, "rev-parse", "main")
    assert _git(path, "branch", "--show-current") == "dev"


def test_dev_existente_e_idempotente(repo_com_commit):
    git_mod.create_dev_branch(repo_com_commit)

    item = git_mod.create_dev_branch(repo_com_commit)

    assert item.status == "skipped"
    assert "dev" in item.message


def test_dev_sem_repositorio_e_skipped(make_project_config):
    cfg = make_project_config("programming", "python")
    cfg.project_path.mkdir(parents=True, exist_ok=True)

    item = git_mod.create_dev_branch(cfg)

    assert item.status == "skipped"


def test_dev_sem_commit_inicial_e_skipped(make_project_config):
    """Repositório sem commits: não há main para ramificar — não pode virar erro."""
    cfg = make_project_config("programming", "python")
    cfg.project_path.mkdir(parents=True, exist_ok=True)
    git_mod.init_repository(cfg)

    item = git_mod.create_dev_branch(cfg)

    assert item.status == "skipped"


# ---------------------------------------------------------------------------
# Slug do repositório GitHub
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/org/repo",
        "https://github.com/org/repo.git",
        "https://github.com/org/repo/",
        "git@github.com:org/repo.git",
        "ssh://git@github.com/org/repo.git",
    ],
)
def test_slug_de_urls_github_validas(url):
    assert parse_github_slug(url) == "org/repo"


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        "https://gitlab.com/org/repo",
        "https://github.com/org",
        "https://github.com/",
        "nao-e-url",
        "https://github.com/org/repo/extra",
    ],
)
def test_slug_invalido_levanta_excecao_semantica(url):
    with pytest.raises(InvalidGithubRepoError):
        parse_github_slug(url)


def test_slug_none_levanta_excecao_semantica():
    with pytest.raises(InvalidGithubRepoError):
        parse_github_slug(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Payload de proteção e checks obrigatórios
# ---------------------------------------------------------------------------


def test_payload_protecao_exige_pr_e_checks_strict():
    payload = build_protection_payload(["Validation Summary", "ci"], strict=True)

    assert payload["required_status_checks"] == {
        "strict": True,
        "contexts": ["Validation Summary", "ci"],
    }
    assert payload["required_pull_request_reviews"] is not None
    assert payload["enforce_admins"] is False
    assert payload["restrictions"] is None
    assert payload["allow_force_pushes"] is False
    assert payload["allow_deletions"] is False


def test_payload_sem_checks_nao_exige_status():
    """Sem workflows não há check a exigir: GitHub travaria o merge para sempre."""
    payload = build_protection_payload([], strict=True)

    assert payload["required_status_checks"] is None


def test_payload_rejeita_checks_vazios_ou_duplicados():
    with pytest.raises(ValueError):
        build_protection_payload(["ci", ""], strict=True)
    with pytest.raises(ValueError):
        build_protection_payload(["ci", "ci"], strict=True)


def test_checks_obrigatorios_seguem_workflows_existentes(tmp_path: Path):
    wf = tmp_path / ".github" / "workflows"
    assert required_checks_for(tmp_path) == []

    wf.mkdir(parents=True)
    (wf / "git-validation.yml").write_text("x", encoding="utf-8")
    assert required_checks_for(tmp_path) == ["Validation Summary"]

    (wf / "ci.yml").write_text("x", encoding="utf-8")
    assert required_checks_for(tmp_path) == ["Validation Summary", "ci"]


# ---------------------------------------------------------------------------
# configure_github_branches — falhas viram aviso, nunca erro
# ---------------------------------------------------------------------------


class _Runner:
    """Runner falso: registra comandos e falha nos que casarem com ``fail_on``."""

    def __init__(self, fail_on: str | None = None, exc: Exception | None = None):
        self.calls: list[list[str]] = []
        self.fail_on = fail_on
        self.exc = exc

    def __call__(self, cmd: list[str], cwd: Path, input_text: str | None = None):
        self.calls.append(cmd)
        joined = " ".join(cmd)
        if self.fail_on and self.fail_on in joined:
            if self.exc is not None:
                raise self.exc
            return subprocess.CompletedProcess(cmd, 1, "", "falhou")
        return subprocess.CompletedProcess(cmd, 0, "", "")


@pytest.fixture
def cfg_com_repo(repo_com_commit):
    repo_com_commit.github_repo = "https://github.com/org/repo"
    git_mod.create_dev_branch(repo_com_commit)
    return repo_com_commit


def test_sem_repo_configurado_e_skipped(repo_com_commit):
    runner = _Runner()

    item = configure_github_branches(repo_com_commit, runner=runner)

    assert item.status == "skipped"
    assert runner.calls == []


def test_repo_nao_github_e_skipped(cfg_com_repo):
    cfg_com_repo.github_repo = "https://gitlab.com/org/repo"
    runner = _Runner()

    item = configure_github_branches(cfg_com_repo, runner=runner)

    assert item.status == "skipped"
    assert runner.calls == []


def test_gh_ausente_e_skipped(cfg_com_repo, monkeypatch):
    monkeypatch.setattr(github_setup.shutil, "which", lambda name: None)
    runner = _Runner()

    item = configure_github_branches(cfg_com_repo, runner=runner)

    assert item.status == "skipped"
    assert "gh" in item.message
    assert runner.calls == []


def test_gh_nao_autenticado_e_skipped(cfg_com_repo):
    runner = _Runner(fail_on="auth status")

    item = configure_github_branches(cfg_com_repo, runner=runner)

    assert item.status == "skipped"
    assert not any("push" in c for c in runner.calls)


def test_repo_remoto_inexistente_e_skipped(cfg_com_repo):
    runner = _Runner(fail_on="repo view")

    item = configure_github_branches(cfg_com_repo, runner=runner)

    assert item.status == "skipped"
    assert not any("push" in c for c in runner.calls)


def test_timeout_de_rede_e_skipped(cfg_com_repo):
    runner = _Runner(
        fail_on="push", exc=subprocess.TimeoutExpired(cmd="git push", timeout=60)
    )

    item = configure_github_branches(cfg_com_repo, runner=runner)

    assert item.status == "skipped"
    assert "push" in item.message


def test_falha_na_protecao_e_skipped_e_nao_esconde_etapa(cfg_com_repo):
    runner = _Runner(fail_on="protection")

    item = configure_github_branches(cfg_com_repo, runner=runner)

    assert item.status == "skipped"
    assert "prote" in item.message.lower()


def test_fluxo_completo_publica_define_default_e_protege_main(cfg_com_repo):
    wf = cfg_com_repo.project_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "git-validation.yml").write_text("x", encoding="utf-8")
    runner = _Runner()

    item = configure_github_branches(cfg_com_repo, runner=runner)

    assert item.status == "created", item.message
    joined = [" ".join(c) for c in runner.calls]
    push = next(j for j in joined if " push " in f" {j} ")
    assert "main" in push and "dev" in push and "--tags" in push
    assert any("--default-branch dev" in j for j in joined)
    prot = [j for j in joined if "branches/main/protection" in j]
    assert prot and "PUT" in prot[0]
    # ordem: push antes de default-branch antes da proteção
    i_push = joined.index(push)
    i_def = next(i for i, j in enumerate(joined) if "--default-branch" in j)
    i_prot = joined.index(prot[0])
    assert i_push < i_def < i_prot


# ---------------------------------------------------------------------------
# Gatilhos de CI e validação de nome de branch
# ---------------------------------------------------------------------------


def _branch_pattern() -> str:
    text = _GIT_VALIDATION.read_text(encoding="utf-8")
    match = re.search(r"pattern = r'(\^\(\?:[^']*)'", text)
    assert match, "padrão de branch não encontrado em git-validation.yml"
    return match.group(1)


@pytest.mark.parametrize(
    "branch", ["dev", "release/fase1", "release/fase12", "feature/042-login", "fix/x"]
)
def test_validacao_aceita_branches_do_modelo(branch):
    assert re.match(_branch_pattern(), branch)


@pytest.mark.parametrize("branch", ["release/foo", "release/", "develop2", "feat/x"])
def test_validacao_rejeita_branches_fora_do_modelo(branch):
    assert not re.match(_branch_pattern(), branch)


def test_git_validation_ignora_push_em_dev_e_release():
    data = yaml.safe_load(_GIT_VALIDATION.read_text(encoding="utf-8"))
    ignored = data[True]["push"]["branches-ignore"]  # "on" vira True no YAML 1.1
    assert "dev" in ignored
    assert "release/**" in ignored


@pytest.mark.parametrize("language", ["python", "typescript", "go"])
def test_ci_infra_dispara_em_main_dev_e_release(language, make_project_config):
    from scripts.lib import infra

    cfg = make_project_config("programming", language)
    assert infra.generate_ci_workflow(cfg).status == "created"
    ci = cfg.target_dir / ".github" / "workflows" / "ci.yml"
    data = yaml.safe_load(ci.read_text(encoding="utf-8"))
    for event in ("push", "pull_request"):
        branches = data[True][event]["branches"]
        assert "dev" in branches and "release/**" in branches and "main" in branches


def test_workflows_de_seguranca_disparam_em_dev_e_release():
    from scripts.lib import project

    src = Path(project.__file__).read_text(encoding="utf-8")
    assert "develop ]" not in src
    assert src.count("branches: [ main, master, dev, 'release/**' ]") >= 3


# ---------------------------------------------------------------------------
# Integração — fluxo --new (CLI real, gh falso no PATH: sem rede)
# ---------------------------------------------------------------------------

_SCAFFOLD = Path(__file__).resolve().parent.parent / "scripts" / "scaffold.py"


def _fake_gh(bin_dir: Path, marker: Path) -> None:
    """gh falso: registra a chamada; ``auth status`` ok, ``repo view`` falha."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text(
        "#!/bin/sh\n"
        f'echo "$@" >> "{marker}"\n'
        'if [ "$1" = "repo" ] && [ "$2" = "view" ]; then exit 1; fi\n'
        "exit 0\n",
        encoding="utf-8",
    )
    gh.chmod(0o755)


def _run_new(
    tmp_path: Path, *extra: str
) -> tuple[subprocess.CompletedProcess, Path, Path]:
    import os
    import sys

    marker = tmp_path / "gh-calls.txt"
    _fake_gh(tmp_path / "bin", marker)
    env = {**os.environ, "PATH": f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}"}
    target = tmp_path / "proj"
    result = subprocess.run(
        [
            sys.executable,
            str(_SCAFFOLD),
            "--new",
            "--ci",
            "--no-log",
            "--name",
            "proj",
            "--domain",
            "programming",
            "--language",
            "python",
            "--ai-assistant",
            "none",
            "--target-dir",
            str(target),
            *extra,
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
        check=False,
    )
    return result, target, marker


@pytest.mark.integration
def test_new_cria_dev_e_deixa_checkout_em_dev(tmp_path: Path):
    result, target, marker = _run_new(tmp_path)

    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    assert _git(target, "branch", "--show-current") == "dev"
    assert _git(target, "rev-parse", "dev") == _git(target, "rev-parse", "main")
    assert not marker.exists(), "sem --repo o gh não pode ser chamado"


@pytest.mark.integration
def test_new_com_repo_tenta_gh_e_falha_vira_aviso(tmp_path: Path):
    result, _target, marker = _run_new(
        tmp_path, "--repo", "https://github.com/org/proj"
    )

    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    calls = marker.read_text(encoding="utf-8")
    assert "auth status" in calls and "repo view" in calls


@pytest.mark.integration
def test_new_no_github_setup_nao_chama_gh(tmp_path: Path):
    result, target, marker = _run_new(
        tmp_path, "--repo", "https://github.com/org/proj", "--no-github-setup"
    )

    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    assert not marker.exists()
    assert _git(target, "branch", "--show-current") == "dev"
