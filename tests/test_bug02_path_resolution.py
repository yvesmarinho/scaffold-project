"""
test_bug02_path_resolution.py — Testes para BUG-02 (compose path resolution).

Valida que target_dir e shared_dir são sempre resolvidos como caminhos absolutos,
independentemente do diretório de trabalho atual.
"""

import os
from pathlib import Path
from unittest.mock import patch

from scripts.lib.ui import collect_project_info


class TestBug02PathResolution:
    """Testes para validar correção do BUG-02."""

    def test_target_dir_resolved_as_absolute_ci_mode(self, tmp_path):
        """
        BUG-02: target_dir deve ser resolvido como caminho absoluto no modo CI.

        Cenário: compose executado de subdiretório de um projeto.
        Esperado: target_dir é caminho absoluto, não relativo ao CWD.
        """
        # Simular execução de subdiretório
        project_dir = tmp_path / "existing-project"
        project_dir.mkdir()
        subdir = project_dir / "src"
        subdir.mkdir()

        # Caminho relativo que seria interpretado incorretamente sem .resolve()
        target_rel = Path("../new-project")

        overrides = {
            "name": "test-project",
            "domain": "programming",
            "language": "python",
            "target_dir": str(target_rel),
        }

        # Executar de dentro do subdiretório
        original_cwd = Path.cwd()
        try:
            os.chdir(subdir)

            config = collect_project_info(ci_mode=True, **overrides)

            # Validar que target_dir é absoluto
            assert (
                config.target_dir.is_absolute()
            ), f"BUG-02: target_dir deve ser absoluto, mas é relativo: {config.target_dir}"

            # Validar que não contém componentes '..' (foi normalizado)
            assert (
                ".." not in config.target_dir.parts
            ), f"BUG-02: target_dir não deve conter '..': {config.target_dir}"

        finally:
            os.chdir(original_cwd)

    def test_shared_dir_resolved_as_absolute_ci_mode(self, tmp_path):
        """
        BUG-02: shared_dir deve ser resolvido como caminho absoluto no modo CI.
        """
        shared_rel = Path("../shared-files")

        overrides = {
            "name": "test-project",
            "domain": "programming",
            "language": "python",
            "shared_dir": str(shared_rel),
        }

        # Executar de subdiretório
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        original_cwd = Path.cwd()
        try:
            os.chdir(subdir)

            config = collect_project_info(ci_mode=True, **overrides)

            # Validar que shared_dir é absoluto
            assert (
                config.shared_dir.is_absolute()
            ), f"BUG-02: shared_dir deve ser absoluto, mas é relativo: {config.shared_dir}"

            # Validar que não contém componentes '..'
            assert (
                ".." not in config.shared_dir.parts
            ), f"BUG-02: shared_dir não deve conter '..': {config.shared_dir}"

        finally:
            os.chdir(original_cwd)

    def test_target_dir_with_tilde_expansion(self, tmp_path):
        """
        BUG-02: target_dir com ~ deve ser expandido E resolvido.
        """
        overrides = {
            "name": "test-project",
            "domain": "programming",
            "language": "python",
            "target_dir": "~/projects",
        }

        config = collect_project_info(ci_mode=True, **overrides)

        # Validar que tilde foi expandido
        assert "~" not in str(
            config.target_dir
        ), f"BUG-02: tilde não foi expandido: {config.target_dir}"

        # Validar que é absoluto
        assert (
            config.target_dir.is_absolute()
        ), f"BUG-02: target_dir deve ser absoluto: {config.target_dir}"

    def test_absolute_target_dir_unchanged(self, tmp_path):
        """
        BUG-02: target_dir já absoluto deve permanecer inalterado.
        """
        absolute_target = tmp_path / "my-project"

        overrides = {
            "name": "test-project",
            "domain": "programming",
            "language": "python",
            "target_dir": str(absolute_target),
        }

        config = collect_project_info(ci_mode=True, **overrides)

        # Validar que caminho absoluto foi preservado (mas normalizado)
        assert config.target_dir.is_absolute()
        assert config.target_dir == absolute_target.resolve()

    @patch("scripts.lib.ui.Prompt.ask")
    def test_target_dir_resolved_interactive_mode(self, mock_prompt, tmp_path):
        """
        BUG-02: target_dir deve ser resolvido no modo interativo também.
        """
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        # Simular respostas do usuário
        target_rel = Path("../output")
        mock_prompt.side_effect = [
            "test-project",  # name
            "Test Project",  # title
            "Test description",  # description
            "1",  # domain (1=programming)
            "1",  # language (1=python)
            "1",  # ai_assistant (1=both)
            "",  # github_repo
            str(tmp_path / "shared"),  # shared_dir (via CopilotPlugin.collect_config)
            str(target_rel),  # target_dir
            "1",  # extra_profiles mode
            "1",  # layer2 profile (skip)
        ]

        original_cwd = Path.cwd()
        try:
            os.chdir(subdir)

            config = collect_project_info(ci_mode=False)

            # Validar que target_dir é absoluto
            assert (
                config.target_dir.is_absolute()
            ), f"BUG-02: target_dir deve ser absoluto em modo interativo: {config.target_dir}"

            # Validar que não contém '..'
            assert ".." not in config.target_dir.parts

        finally:
            os.chdir(original_cwd)

    def test_regression_compose_from_project_subdirectory(self, tmp_path):
        """
        BUG-02: Teste de regressão — compose executado de poc/tst-python-fastapi/.

        Este é o cenário original que descobriu o bug:
        1. Usuario está em poc/tst-python-fastapi/
        2. Executa: scaffold.py --compose python-fastapi --output ../new-project
        3. Arquivos devem ser criados em ../new-project (absoluto), não em ./new-project
        """
        # Simular estrutura: repo/poc/tst-python-fastapi/
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        poc_dir = repo_root / "poc"
        poc_dir.mkdir()
        test_project_dir = poc_dir / "tst-python-fastapi"
        test_project_dir.mkdir()

        # Caminho relativo de dentro de tst-python-fastapi/
        output_rel = Path("../new-project")

        overrides = {
            "name": "new-project",
            "domain": "programming",
            "language": "python",
            "target_dir": str(output_rel),
        }

        # Executar de dentro de tst-python-fastapi/
        original_cwd = Path.cwd()
        try:
            os.chdir(test_project_dir)

            config = collect_project_info(ci_mode=True, **overrides)

            # Validar que target_dir aponta para poc/ (não tst-python-fastapi/)
            expected_target = poc_dir.resolve()
            assert config.target_dir.is_absolute()
            # O caminho resolvido deve ser poc_dir, não test_project_dir
            assert config.target_dir.parent != test_project_dir.resolve()
            assert config.target_dir == expected_target / "new-project"

        finally:
            os.chdir(original_cwd)


def test_bug02_documented():
    """
    Meta-teste: validar que BUG-02 está documentado.
    """
    bug_doc = Path(__file__).parent.parent / "docs" / "TODO.md"
    assert bug_doc.exists(), "docs/TODO.md não encontrado"

    content = bug_doc.read_text(encoding="utf-8")
    assert "BUG-02" in content, "BUG-02 não está documentado em TODO.md"
    assert "path resolution" in content.lower(), "TODO.md não menciona path resolution"
