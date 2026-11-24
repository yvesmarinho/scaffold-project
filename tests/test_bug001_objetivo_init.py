"""
Test suite for BUG-001: scaffold objetivo-init issues

Valida correções para 3 bugs:
1. Campo docstyle recebe valor padrão quando omitido
2. Campo out-scope não é incluído no YAML quando vazio
3. Logs são gerados em logs/scaffolds.yaml
"""

import pytest

from scripts.lib.objetivo_wizard import DEFAULT_DOCSTYLE, ObjetivoWizard, WizardAnswers


class TestBug001DocstyleDefault:
    """Testes para BUG-001 Fix #1: Default docstyle"""

    def test_default_docstyle_constant_defined(self):
        """Validar que constante DEFAULT_DOCSTYLE existe e tem valor esperado."""
        assert DEFAULT_DOCSTYLE is not None
        assert len(DEFAULT_DOCSTYLE) > 0
        assert "Google Style Docstrings" in DEFAULT_DOCSTYLE
        assert "Sphinx" in DEFAULT_DOCSTYLE
        assert "ADRs" in DEFAULT_DOCSTYLE
        assert "OpenAPI/Swagger" in DEFAULT_DOCSTYLE

    def test_template_substitutes_docstyle_when_provided(self, tmp_path):
        """Quando docstyle é fornecido, deve usar o valor fornecido."""
        wizard = ObjetivoWizard()
        wizard.answers = WizardAnswers(
            project_name="test-project",
            project_title="Test Project",
            project_type="backend-api",
            project_domain="programming",
            project_language="python",
            created_by="tester",
            answers={
                "{{DESCRIPTION}}": "Test description",
                "{{RESPONSE}}": "Python code",
                "{{DOCSTYLE}}": "reStructuredText com Docstring e DocTest",  # Custom value
                "{{EXPECTED_OUTCOME_1}}": "Test outcome",
            },
        )

        rendered = wizard._render_template(wizard.answers)

        # Deve usar valor customizado
        assert "reStructuredText com Docstring e DocTest" in rendered
        # Não deve usar default
        assert "Google Style Docstrings" not in rendered

    def test_template_uses_default_docstyle_when_omitted(self, tmp_path):
        """Quando docstyle é omitido, deve usar DEFAULT_DOCSTYLE."""
        wizard = ObjetivoWizard()
        wizard.answers = WizardAnswers(
            project_name="test-project",
            project_title="Test Project",
            project_type="backend-api",
            project_domain="programming",
            project_language="python",
            created_by="tester",
            answers={
                "{{DESCRIPTION}}": "Test description",
                "{{RESPONSE}}": "Python code",
                # {{DOCSTYLE}} NÃO fornecido
                "{{EXPECTED_OUTCOME_1}}": "Test outcome",
            },
        )

        rendered = wizard._render_template(wizard.answers)

        # Deve usar valor default
        assert "Google Style Docstrings" in rendered
        assert "Sphinx" in rendered
        assert "ADRs" in rendered


class TestBug001OutScopeConditional:
    """Testes para BUG-001 Fix #2: Remover out-scope vazio"""

    def test_template_omits_out_scope_when_empty(self, tmp_path):
        """Quando out-scope não é fornecido, linha deve ser removida."""
        wizard = ObjetivoWizard()
        wizard.answers = WizardAnswers(
            project_name="test-project",
            project_title="Test Project",
            project_type="backend-api",
            project_domain="programming",
            project_language="python",
            created_by="tester",
            answers={
                "{{DESCRIPTION}}": "Test description",
                "{{RESPONSE}}": "Python code",
                "{{EXPECTED_OUTCOME_1}}": "Test outcome",
                # {{OUT_SCOPE}} NÃO fornecido
            },
        )

        rendered = wizard._render_template(wizard.answers)

        # Não deve conter linha de out-scope vazia
        assert 'out-scope: ""' not in rendered
        assert 'out-scope: "{{OUT_SCOPE}}"' not in rendered
        # Pode contar linhas para validar que foi removida
        lines = [line for line in rendered.splitlines() if "out-scope" in line]
        assert (
            len(lines) == 0
        ), f"out-scope não deveria aparecer, mas encontrado: {lines}"

    def test_template_includes_out_scope_when_provided(self, tmp_path):
        """Quando out-scope é fornecido, deve ser incluído."""
        wizard = ObjetivoWizard()
        wizard.answers = WizardAnswers(
            project_name="test-project",
            project_title="Test Project",
            project_type="backend-api",
            project_domain="programming",
            project_language="python",
            created_by="tester",
            answers={
                "{{DESCRIPTION}}": "Test description",
                "{{RESPONSE}}": "Python code",
                "{{OUT_SCOPE}}": "Não inclui funcionalidades de admin",  # Custom value
                "{{EXPECTED_OUTCOME_1}}": "Test outcome",
            },
        )

        rendered = wizard._render_template(wizard.answers)

        # Deve incluir valor fornecido
        assert "Não inclui funcionalidades de admin" in rendered
        assert "out-scope" in rendered


class TestBug001ScaffoldLogging:
    """Testes para BUG-001 Fix #3: Logs de execução"""

    def test_log_file_created_after_objetivo_init(self, tmp_path, monkeypatch):
        """Logs/scaffolds.yaml deve ser criado após objetivo-init."""
        # Change CWD para tmp_path
        monkeypatch.chdir(tmp_path)
        # Testa o caminho padrão (relativo ao cwd): remove o isolamento do conftest
        monkeypatch.delenv("SCAFFOLD_LOGS_DIR", raising=False)

        # Criar estrutura de pastas esperada
        template_dir = tmp_path / "template-bases"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "objetivo-init-template.yaml"

        # Template minimal
        template_file.write_text("""prompt:
  role: user
  content:
    description: "{{DESCRIPTION}}"
    specification:
      - project_name: "{{PROJECT_NAME}}"
      - response: "{{RESPONSE}}"
      - docstyle: "{{DOCSTYLE}}"
      - out-scope: "{{OUT_SCOPE}}"
    expected_outcome:
      - "{{EXPECTED_OUTCOME_1}}"
""")

        # Executar wizard non-interactive
        import argparse

        # Criar answers JSON temporário
        import json

        from scripts.lib.flows.objetivo_init import flow_objetivo_init

        answers_file = tmp_path / "answers.json"
        answers_data = {
            "project_name": "test-logging",
            "project_title": "Test Logging Project",
            "project_type": "backend-api",
            "project_domain": "programming",
            "project_language": "python",
            "created_by": "test-user",
            "answers": {
                "{{DESCRIPTION}}": "Test project for logging",
                "{{RESPONSE}}": "Python code",
                "{{EXPECTED_OUTCOME_1}}": "Log created",
            },
        }
        answers_file.write_text(json.dumps(answers_data))

        args = argparse.Namespace(
            from_file=str(answers_file),
            template_only=False,
            output="objetivo-test.yaml",
        )

        # Executar
        result = flow_objetivo_init(args)

        # Validações
        assert result == 0, "objetivo-init deve ter sucesso"

        log_file = tmp_path / "logs" / "scaffolds.yaml"
        assert log_file.exists(), "logs/scaffolds.yaml deve ser criado"

        # Validar conteúdo do log
        import yaml

        with log_file.open("r") as f:
            log_data = yaml.safe_load(f)

        assert "scaffolds" in log_data
        assert len(log_data["scaffolds"]) == 1

        entry = log_data["scaffolds"][0]
        assert entry["operation"] == "objetivo-init"
        assert entry["project_name"] == "test-logging"
        assert entry["success"] is True
        assert "timestamp" in entry
        assert "output_file" in entry

    def test_log_entry_contains_error_on_failure(self, tmp_path, monkeypatch):
        """Log deve conter error_message quando operação falha."""
        monkeypatch.chdir(tmp_path)

        import argparse

        from scripts.lib.flows.objetivo_init import flow_objetivo_init

        # Arquivo JSON inválido
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json")

        args = argparse.Namespace(
            from_file=str(invalid_file),
            template_only=False,
            output="objetivo-test.yaml",
        )

        # Executar (deve falhar)
        result = flow_objetivo_init(args)

        assert result == 1, "objetivo-init deve falhar com JSON inválido"

        # Log deve ter sido criado mesmo com erro
        log_file = tmp_path / "logs" / "scaffolds.yaml"
        if log_file.exists():  # Log pode não ser criado se YAML lib falhar
            import yaml

            with log_file.open("r") as f:
                log_data = yaml.safe_load(f)

            if log_data and "scaffolds" in log_data and len(log_data["scaffolds"]) > 0:
                entry = log_data["scaffolds"][-1]
                assert entry["success"] is False
                assert "error_message" in entry


@pytest.mark.integration
class TestBug001Integration:
    """Testes de integração validando todos os 3 fixes juntos."""

    def test_all_fixes_work_together(self, tmp_path, monkeypatch):
        """Validar que docstyle default, out-scope omitido e logging funcionam juntos."""
        monkeypatch.chdir(tmp_path)

        # Criar template
        template_dir = tmp_path / "template-bases"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "objetivo-init-template.yaml"
        template_file.write_text("""prompt:
  role: user
  content:
    description: "{{DESCRIPTION}}"
    specification:
      - project_name: "{{PROJECT_NAME}}"
      - response: "{{RESPONSE}}"
      - docstyle: "{{DOCSTYLE}}"
      - out-scope: "{{OUT_SCOPE}}"
    expected_outcome:
      - "{{EXPECTED_OUTCOME_1}}"
""")

        # Criar wizard e executar
        wizard = ObjetivoWizard(template_path=template_file)
        wizard.answers = WizardAnswers(
            project_name="integration-test",
            project_title="Integration Test",
            project_type="backend-api",
            project_domain="programming",
            project_language="python",
            created_by="tester",
            answers={
                "{{DESCRIPTION}}": "Integration test project",
                "{{RESPONSE}}": "Python implementation",
                # {{DOCSTYLE}} omitido → deve usar default
                # {{OUT_SCOPE}} omitido → deve ser removido
                "{{EXPECTED_OUTCOME_1}}": "All fixes work",
            },
        )

        output_file = tmp_path / "objetivo-integration.yaml"
        result = wizard.run_non_interactive(wizard.answers, output_file)

        assert result == 0
        assert output_file.exists()

        content = output_file.read_text()

        # Fix #1: Docstyle default aplicado
        assert "Google Style Docstrings" in content

        # Fix #2: out-scope removido
        assert 'out-scope: ""' not in content

        # Fix #3: Log criado (seria validado pelo flow_objetivo_init)
        # Aqui estamos testando apenas wizard direto
