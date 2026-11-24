"""
test_scaffold_objetivo.py — Integration tests for objetivo commands in scaffold.py

Tests the integration between scaffold.py and objetivo.yaml workflows:
- objetivo-validate: validates objetivo.yaml v2.0
- objetivo-generate: generates technical YAML from objetivo.yaml
- objetivo-migrate: migrates v1.0 → v2.0

Spec: specs/066-objetivo-yaml-v2/spec.md
Task: T024
"""

import subprocess
from pathlib import Path

import pytest


class TestScaffoldObjetivo:
    """Integration tests for scaffold.py objetivo commands."""

    @pytest.fixture
    def valid_objetivo_v2(self, tmp_path):
        """Create a valid v2.0 objetivo.yaml file."""
        content = """---
version: "2.0"
project:
  name: test-project
  title: Test Project
  type: backend-api
  domain: programming
  language: python
---

## 1️⃣ O que este projeto faz?

Este é um sistema de teste que processa dados automaticamente.

## 2️⃣ Qual problema resolve?

Atualmente, usuários gastam 2 horas processando dados manualmente,
com alta taxa de erros (15%).

## 3️⃣ Escopo do Projeto

**Incluído ✅**:
- Processamento automático de dados (P0)
- Interface web para monitoramento (P1)

**Excluído ❌**:
- Integração com sistema legado X

## 4️⃣ Restrições e Contexto

**Restrições de Negócio**:
- Budget: R$ 50k
- Prazo: 3 meses

## 5️⃣ Usuários e Personas

**Analista de Dados** (usuário principal):
- Necessita: automatizar processamento de dados
- Dores: processo manual lento e propenso a erros

## 6️⃣ Requisitos de Segurança

- Autenticação via OAuth2
- Logs de auditoria

## 7️⃣ Tecnologias e Decisões

**Stack Técnico**:
- Backend: Python 3.12 + FastAPI
- Database: PostgreSQL 15

**Decisões Arquiteturais**:
- D-01: Usar FastAPI (justificativa: performance + async)

## 8️⃣ Riscos e Dependências

**Riscos P0**:
- Integração com API externa pode ter instabilidade

## 9️⃣ Métricas de Sucesso

- Redução de tempo: de 2h para 15min (≥85%)
- Taxa de erro: <1%
"""
        file_path = tmp_path / "objetivo.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def invalid_objetivo_v2(self, tmp_path):
        """Create an invalid v2.0 objetivo.yaml (missing required sections)."""
        content = """---
version: "2.0"
project:
  name: test-project
---

## 1️⃣ O que este projeto faz?

Descrição curta demais.
"""
        file_path = tmp_path / "objetivo-invalid.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def valid_objetivo_v1(self, tmp_path):
        """Create a valid v1.0 objetivo.yaml file."""
        content = """---
feature:
  name: "test-feature"
  branch: "001-test-feature"

negocio:
  problema:
    descricao: "Usuários precisam processar dados automaticamente."
    impacto_atual: "Sem automação, tempo de processamento aumenta 50%."

produto:
  visao_alto_nivel: |
    Sistema automatizado que processa dados via interface web,
    reduzindo tempo de 2h para 15min.

  jornadas_criticas:
    - journey: "Processar dados automaticamente"
      priority: "P0"

decisoes_iniciais:
  - id: "D-01"
    decision: "Usar FastAPI (performance + async)"
"""
        file_path = tmp_path / "objetivo-v1.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def scaffold_path(self):
        """Path to scaffold.py script."""
        return Path(__file__).parent.parent / "scripts" / "scaffold.py"

    # Test 1: objetivo-validate on valid file → exit 0
    def test_objetivo_validate_valid_file(
        self, scaffold_path, valid_objetivo_v2, tmp_path
    ):
        """Test that objetivo-validate exits 0 on valid file."""
        result = subprocess.run(
            [
                "python",
                str(scaffold_path),
                "objetivo-validate",
                "--file",
                str(valid_objetivo_v2),
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert (
            result.returncode == 0
        ), f"Expected exit 0, got {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        assert "✅ Válido" in result.stdout or "sem erros" in result.stdout.lower()

    # Test 2: objetivo-validate on invalid file → exit 1 + error message
    def test_objetivo_validate_invalid_file(
        self, scaffold_path, invalid_objetivo_v2, tmp_path
    ):
        """Test that objetivo-validate exits 1 on invalid file with error messages."""
        result = subprocess.run(
            [
                "python",
                str(scaffold_path),
                "objetivo-validate",
                "--file",
                str(invalid_objetivo_v2),
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert (
            result.returncode == 1
        ), f"Expected exit 1, got {result.returncode}\nstdout:\n{result.stdout}"
        assert "❌" in result.stdout or "erro" in result.stdout.lower()
        # Should mention missing sections
        assert "seção" in result.stdout.lower() or "section" in result.stdout.lower()

    # Test 3: objetivo-validate on missing file → exit 1
    def test_objetivo_validate_missing_file(self, scaffold_path, tmp_path):
        """Test that objetivo-validate exits 1 when file not found."""
        result = subprocess.run(
            [
                "python",
                str(scaffold_path),
                "objetivo-validate",
                "--file",
                "nonexistent.yaml",
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert result.returncode == 1
        assert (
            "não encontrado" in result.stdout.lower()
            or "not found" in result.stdout.lower()
        )

    # Test 4: objetivo-generate → spec.yaml created
    def test_objetivo_generate_creates_spec(
        self, scaffold_path, valid_objetivo_v2, tmp_path
    ):
        """Test that objetivo-generate creates spec YAML file."""
        output_file = tmp_path / "objetivo-spec.yaml"

        result = subprocess.run(
            [
                "python",
                str(scaffold_path),
                "objetivo-generate",
                "--input",
                str(valid_objetivo_v2),
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert (
            result.returncode == 0
        ), f"Expected exit 0, got {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        assert output_file.exists(), "Output file not created"

        # Check generated file content
        content = output_file.read_text(encoding="utf-8")
        assert "# ⚠️  GERADO AUTOMATICAMENTE" in content
        assert "project:" in content
        assert "name: test-project" in content
        assert "specification:" in content

    # Test 5: objetivo-generate on invalid file → exit 1
    def test_objetivo_generate_invalid_file(
        self, scaffold_path, invalid_objetivo_v2, tmp_path
    ):
        """Test that objetivo-generate exits 1 on invalid file."""
        output_file = tmp_path / "spec.yaml"

        result = subprocess.run(
            [
                "python",
                str(scaffold_path),
                "objetivo-generate",
                "--input",
                str(invalid_objetivo_v2),
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert result.returncode == 1
        assert (
            not output_file.exists()
        ), "Output file should not be created on invalid input"

    # Test 6: objetivo-migrate → v2 created, v1 backed up
    def test_objetivo_migrate_creates_v2(
        self, scaffold_path, valid_objetivo_v1, tmp_path
    ):
        """Test that objetivo-migrate creates v2 file with --auto flag."""
        # Copy v1 file to objetivo.yaml (standard name)
        objetivo_file = tmp_path / "objetivo.yaml"
        objetivo_file.write_text(valid_objetivo_v1.read_text(), encoding="utf-8")

        backup_file = tmp_path / "objetivo.yaml.v1"

        result = subprocess.run(
            [
                "python",
                str(scaffold_path),
                "objetivo-migrate",
                "--file",
                str(objetivo_file),
                "--auto",  # Auto-accept to avoid interactive prompt
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert (
            result.returncode == 0
        ), f"Expected exit 0, got {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        assert backup_file.exists(), "Backup file (.v1) not created"

        # Check migrated file has v2.0 format
        migrated_content = objetivo_file.read_text(encoding="utf-8")
        assert (
            'version: "2.0"' in migrated_content or "version: '2.0'" in migrated_content
        )
        assert "## 1️⃣" in migrated_content
        assert "## 2️⃣" in migrated_content

    # Test 7: objetivo-migrate on already v2.0 → error
    def test_objetivo_migrate_already_v2(
        self, scaffold_path, valid_objetivo_v2, tmp_path
    ):
        """Test that objetivo-migrate exits 1 when file is already v2.0."""
        result = subprocess.run(
            [
                "python",
                str(scaffold_path),
                "objetivo-migrate",
                "--file",
                str(valid_objetivo_v2),
                "--auto",
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert result.returncode == 1
        assert "já" in result.stdout.lower() or "already" in result.stdout.lower()

    # Test 8: Help text includes new commands
    def test_scaffold_help_includes_objetivo_commands(self, scaffold_path):
        """Test that scaffold.py --help includes objetivo commands."""
        result = subprocess.run(
            ["python", str(scaffold_path), "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        help_text = result.stdout

        # Should mention the new commands (either as subcommands or flags)
        assert "objetivo" in help_text.lower()
        # At least one of these should be mentioned
        assert any(
            cmd in help_text
            for cmd in [
                "objetivo-validate",
                "objetivo-generate",
                "objetivo-migrate",
            ]
        )
