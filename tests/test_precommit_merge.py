"""
Testes para precommit_merge.py (Sprint 4 - P2 Coverage Expansion)

Testes unitários para PreCommitMerger.
"""

from pathlib import Path

import yaml

from scripts.lib.precommit_merge import PreCommitMerger


class TestPreCommitMerger:
    """Testes para PreCommitMerger."""

    def test_can_merge_precommit_config(self):
        """Teste: Detecta .pre-commit-config.yaml na raiz."""
        merger = PreCommitMerger()

        assert merger.can_merge(Path(".pre-commit-config.yaml"))
        assert merger.can_merge(Path("/project/.pre-commit-config.yaml"))

    def test_cannot_merge_other_yaml(self):
        """Teste: Não detecta outros arquivos YAML."""
        merger = PreCommitMerger()

        assert not merger.can_merge(Path("config.yaml"))
        assert not merger.can_merge(Path(".github/workflows/ci.yml"))
        assert not merger.can_merge(Path("docker-compose.yml"))

    def test_merge_adds_new_repo(self, tmp_path):
        """Teste: Adiciona novo repo ausente."""
        merger = PreCommitMerger()
        existing = tmp_path / ".pre-commit-config.yaml"

        existing_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
"""

        template_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
"""

        existing.write_text(existing_content, encoding="utf-8")
        result = merger.merge(existing, template_content, interactive=False)

        assert result.status == "merged"
        merged_data = yaml.safe_load(existing.read_text(encoding="utf-8"))
        assert len(merged_data["repos"]) == 2
        assert merged_data["repos"][1]["repo"] == "https://github.com/psf/black"

    def test_merge_updates_repo_version(self, tmp_path):
        """Teste: Atualiza versão (rev) de repo existente."""
        merger = PreCommitMerger()
        existing = tmp_path / ".pre-commit-config.yaml"

        existing_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
"""

        template_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
"""

        existing.write_text(existing_content, encoding="utf-8")
        result = merger.merge(existing, template_content, interactive=False)

        assert result.status == "merged"
        merged_data = yaml.safe_load(existing.read_text(encoding="utf-8"))
        assert merged_data["repos"][0]["rev"] == "v4.6.0"

    def test_merge_adds_new_hook(self, tmp_path):
        """Teste: Adiciona novo hook em repo existente."""
        merger = PreCommitMerger()
        existing = tmp_path / ".pre-commit-config.yaml"

        existing_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
"""

        template_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
"""

        existing.write_text(existing_content, encoding="utf-8")
        result = merger.merge(existing, template_content, interactive=False)

        assert result.status == "merged"
        merged_data = yaml.safe_load(existing.read_text(encoding="utf-8"))
        hooks = merged_data["repos"][0]["hooks"]
        assert len(hooks) == 2
        assert hooks[1]["id"] == "end-of-file-fixer"

    def test_merge_preserves_custom_repo(self, tmp_path):
        """Teste: Preserva repo customizado não presente no template."""
        merger = PreCommitMerger()
        existing = tmp_path / ".pre-commit-config.yaml"

        existing_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
  - repo: https://github.com/custom/my-hooks
    rev: v1.0.0
    hooks:
      - id: custom-check
"""

        template_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
"""

        existing.write_text(existing_content, encoding="utf-8")
        result = merger.merge(existing, template_content, interactive=False)

        assert result.status == "skipped"  # Sem mudanças, repo custom preservado

    def test_merge_preserves_custom_hook(self, tmp_path):
        """Teste: Preserva hook customizado em repo existente."""
        merger = PreCommitMerger()
        existing = tmp_path / ".pre-commit-config.yaml"

        existing_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: my-custom-hook
"""

        template_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
"""

        existing.write_text(existing_content, encoding="utf-8")
        result = merger.merge(existing, template_content, interactive=False)

        assert result.status == "skipped"  # Hook custom preservado
        merged_data = yaml.safe_load(existing.read_text(encoding="utf-8"))
        hooks = merged_data["repos"][0]["hooks"]
        assert len(hooks) == 2
        assert hooks[1]["id"] == "my-custom-hook"

    def test_merge_unions_hook_args(self, tmp_path):
        """Teste: Faz união de args em hooks com mesmo ID."""
        merger = PreCommitMerger()
        existing = tmp_path / ".pre-commit-config.yaml"

        existing_content = """repos:
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        args: [--line-length=88]
"""

        template_content = """repos:
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        args: [--check, --diff]
"""

        existing.write_text(existing_content, encoding="utf-8")
        result = merger.merge(existing, template_content, interactive=False)

        assert result.status == "merged"
        merged_data = yaml.safe_load(existing.read_text(encoding="utf-8"))
        args = merged_data["repos"][0]["hooks"][0]["args"]
        assert "--line-length=88" in args
        assert "--check" in args
        assert "--diff" in args

    def test_skip_when_no_changes(self, tmp_path):
        """Teste: Skip quando não há mudanças."""
        merger = PreCommitMerger()
        existing = tmp_path / ".pre-commit-config.yaml"

        content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
"""

        existing.write_text(content, encoding="utf-8")
        result = merger.merge(existing, content, interactive=False)

        assert result.status == "skipped"
        assert (
            "mudan" in result.message.lower()
        )  # Aceita "sem mudanças" ou "nenhuma mudança"

    def test_creates_backup(self, tmp_path):
        """Teste: Cria backup antes de mergear."""
        merger = PreCommitMerger()
        existing = tmp_path / ".pre-commit-config.yaml"

        existing_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
"""

        template_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
"""

        existing.write_text(existing_content, encoding="utf-8")
        merger.merge(existing, template_content, interactive=False)

        backup = tmp_path / ".pre-commit-config.yaml.backup"
        assert backup.exists()
        assert "v4.4.0" in backup.read_text(encoding="utf-8")

    def test_handles_invalid_yaml_structure(self, tmp_path):
        """Teste: Lida com estrutura YAML inválida."""
        merger = PreCommitMerger()
        existing = tmp_path / ".pre-commit-config.yaml"

        invalid_content = """invalid: yaml
without: repos
"""

        template_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
"""

        existing.write_text(invalid_content, encoding="utf-8")
        result = merger.merge(existing, template_content, interactive=False)

        assert result.status == "skipped"
        assert "inválida" in result.message.lower()
