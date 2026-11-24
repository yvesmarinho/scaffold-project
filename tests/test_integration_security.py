"""
tests/test_integration_security.py — IMP-46 (Nível 1 — AppSec)

Validações de segurança ortogonais a todos os templates.
Roda sem dependências extras além do pytest.

Verifica por template:
  1. .gitignore cobre padrões sensíveis (.env*, *.key, *.pem, secrets/)
  2. Nenhum secret/credencial hardcoded no conteúdo dos arquivos
  3. Arquivo .env não está versionado (somente .env.example quando existir)
  4. YAML/TOML de configuração é válido (parseable sem erros)
"""

from __future__ import annotations

import re

import pytest
import yaml

from tests.helpers.fake_project import TEMPLATES_DIR, FakeProject, expand_template

# ---------------------------------------------------------------------------
# Padrões de secrets que NUNCA devem aparecer em templates
# ---------------------------------------------------------------------------

# Regex que detectam secrets hardcoded típicos
_SECRET_PATTERNS: list[tuple[str, str]] = [
    (r'password\s*=\s*["\'][^"\']{4,}["\']', "password atribuído inline"),
    (r'secret_key\s*=\s*["\'][^"\']{4,}["\']', "secret_key atribuído inline"),
    (r'api_key\s*=\s*["\'][^"\']{8,}["\']', "api_key atribuído inline"),
    (r"AWS_SECRET_ACCESS_KEY\s*=\s*[A-Za-z0-9/+]{20,}", "AWS secret key hardcoded"),
    (r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "chave privada no arquivo"),
]

# Extensões a escanear para secrets
_SCAN_EXTS: frozenset[str] = frozenset(
    {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".json",
        ".toml",
        ".yml",
        ".yaml",
        ".env",
        ".sh",
        ".tf",
        ".tfvars",
        ".md",
        "",  # Makefile, Dockerfile
    }
)

# Arquivos que PODEM conter exemplos de token (não são secrets reais)
_ALLOWLISTED_FILES: frozenset[str] = frozenset(
    {
        ".env.example",
        "README.md",
        "RUNBOOK.md",
    }
)

# .gitignore deve cobrir estes padrões em templates que contenham código
_GITIGNORE_REQUIRED: list[str] = [".env", "*.key", "*.pem"]

# Todos os templates (independente de existir no disco neste momento)
_ALL_PROFILES: list[str] = [
    "python-fastapi",
    "python-flask",
    "typescript-next",
    "k8s-helm",
    "terraform-aws",
    "data-pipeline-airflow",
    "data-warehouse-dbt",
    "lgpd-baseline",
    "soc2-baseline",
]

# Profiles que possuem .gitignore (templates com código executável)
_PROFILES_WITH_GITIGNORE: list[str] = [
    "python-fastapi",
    "python-flask",
    "typescript-next",
]

# YAML/TOML de configuração a validar por perfil
_CONFIG_FILES: dict[str, list[str]] = {
    "python-fastapi": ["pyproject.toml", "docker-compose.yml"],
    "python-flask": ["pyproject.toml", "docker-compose.yml"],
    "typescript-next": ["package.json", "docker-compose.yml", "tsconfig.json"],
    "k8s-helm": [
        "helm/Chart.yaml",
        "helm/values.yaml",
        "helm/values-staging.yaml",
        "helm/values-prod.yaml",
    ],
    "terraform-aws": [],  # HCL — não validado com yaml
    "data-pipeline-airflow": ["airflow/requirements-airflow.txt"],  # só estrutura
    "data-warehouse-dbt": [],
    "lgpd-baseline": [],
    "soc2-baseline": [],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _skip_if_missing(profile: str):
    if not (TEMPLATES_DIR / profile).is_dir():
        pytest.skip(f"Template '{profile}' não encontrado em {TEMPLATES_DIR}")


def _scan_secrets(proj: FakeProject) -> list[str]:
    """
    Escaneia todos os arquivos de texto do projeto por padrões de secret.
    Retorna lista de violações no formato 'arquivo:linha: descrição'.
    """
    violations: list[str] = []
    for f in proj.text_files():
        if f.suffix not in _SCAN_EXTS:
            continue
        if f.name in _ALLOWLISTED_FILES:
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            for lineno, line in enumerate(lines, 1):
                for pattern, description in _SECRET_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        rel = f.relative_to(proj.root)
                        violations.append(f"{rel}:{lineno}: {description}")
                        break  # uma violação por linha é suficiente
        except OSError as exc:
            # arquivo ilegível não pode esconder segredo: registra como violação
            violations.append(f"{f.relative_to(proj.root)}: ilegível ({exc})")
    return violations


# ---------------------------------------------------------------------------
# Fixture compartilhada: expande todos os templates uma vez por sessão
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", params=_ALL_PROFILES)
def any_proj(request, tmp_path_factory) -> FakeProject:
    profile = request.param
    _skip_if_missing(profile)
    dest = tmp_path_factory.mktemp(profile)
    return expand_template(profile, dest)


# ---------------------------------------------------------------------------
# Testes parametrizados — todos os templates
# ---------------------------------------------------------------------------


class TestAllTemplatesSecurityBaseline:
    """Checks de segurança que se aplicam a TODOS os templates disponíveis."""

    def test_no_hardcoded_secrets(self, any_proj: FakeProject):
        """Nenhum arquivo deve conter credenciais hardcoded."""
        violations = _scan_secrets(any_proj)
        assert (
            not violations
        ), f"[{any_proj.profile}] Possíveis secrets detectados:\n" + "\n".join(
            f"  {v}" for v in violations[:10]
        )

    def test_no_dot_env_committed(self, any_proj: FakeProject):
        """Um arquivo .env (não .env.example) não deve existir no template."""
        dot_env = any_proj.file(".env")
        assert not dot_env.exists(), (
            f"[{any_proj.profile}] .env está presente no template "
            "(somente .env.example deve ser versionado)"
        )

    def test_no_private_keys(self, any_proj: FakeProject):
        """Nenhum arquivo .key, .pem ou .p12 deve existir."""
        bad_files = [
            f
            for f in any_proj.root.rglob("*")
            if f.is_file() and f.suffix in {".key", ".pem", ".p12", ".pfx", ".jks"}
        ]
        assert (
            not bad_files
        ), f"[{any_proj.profile}] Chaves privadas encontradas: " + ", ".join(
            str(f.relative_to(any_proj.root)) for f in bad_files
        )


# ---------------------------------------------------------------------------
# Testes específicos — templates com código executável (.gitignore obrigatório)
# ---------------------------------------------------------------------------


class TestGitignoreInCodeTemplates:
    """Templates com código devem ter .gitignore cobrindo padrões sensíveis."""

    @pytest.fixture(
        scope="class",
        params=_PROFILES_WITH_GITIGNORE,
    )
    def code_proj(self, request, tmp_path_factory) -> FakeProject:
        profile = request.param
        _skip_if_missing(profile)
        return expand_template(profile, tmp_path_factory.mktemp(f"gi_{profile}"))

    def test_gitignore_exists(self, code_proj: FakeProject):
        code_proj.assert_file_exists(".gitignore")

    def test_gitignore_covers_dotenv(self, code_proj: FakeProject):
        code_proj.assert_gitignore_covers(".env")

    def test_gitignore_covers_key_files(self, code_proj: FakeProject):
        code_proj.assert_gitignore_covers("*.key")

    def test_gitignore_covers_pem_files(self, code_proj: FakeProject):
        code_proj.assert_gitignore_covers("*.pem")


# ---------------------------------------------------------------------------
# Testes de validade de YAML/JSON por perfil
# ---------------------------------------------------------------------------


class TestConfigFilesAreValid:
    """Arquivos de configuração devem ser parseáveis sem erros."""

    @pytest.mark.parametrize(
        "profile,config_file",
        [(profile, cfg) for profile, cfgs in _CONFIG_FILES.items() for cfg in cfgs],
    )
    def test_config_file_parseable(
        self, tmp_path_factory, profile: str, config_file: str
    ):
        _skip_if_missing(profile)
        proj = expand_template(profile, tmp_path_factory.mktemp(f"cfg_{profile}"))

        f = proj.file(config_file)
        if not f.exists():
            pytest.skip(f"[{profile}] {config_file} não encontrado após expansão")

        suffix = f.suffix
        content = f.read_text(encoding="utf-8")

        if suffix in {".yaml", ".yml"}:
            try:
                parsed = yaml.safe_load(content)
                assert parsed is not None, f"[{profile}] {config_file} vazio ou nulo"
            except yaml.YAMLError as e:
                pytest.fail(f"[{profile}] {config_file} YAML inválido: {e}")

        elif suffix == ".json":
            import json

            try:
                parsed = json.loads(content)
                assert isinstance(parsed, (dict, list))
            except json.JSONDecodeError as e:
                pytest.fail(f"[{profile}] {config_file} JSON inválido: {e}")

        elif suffix == ".toml":
            try:
                import tomllib  # Python 3.11+
            except ImportError:
                try:
                    import tomli as tomllib  # type: ignore[no-redef]
                except ImportError:
                    pytest.skip("tomllib/tomli não disponível; skip TOML validation")
            try:
                tomllib.loads(content)
            except Exception as e:
                pytest.fail(f"[{profile}] {config_file} TOML inválido: {e}")
