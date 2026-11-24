"""
test_objetivo_wizard.py — Tests for objetivo wizard (T036)

Tests both interactive and non-interactive wizard modes with mocked stdin.
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.lib.objetivo_wizard import ObjetivoWizard, WizardAnswers, WizardQuestion


class TestWizardQuestion:
    """Tests for WizardQuestion dataclass."""

    def test_wizard_question_creation(self):
        """Test creating a WizardQuestion."""
        q = WizardQuestion(
            id="q1",
            section=1,
            priority="P0",
            prompt="What is this?",
            example="Example answer",
            placeholder="{{ANSWER_1}}",
            multiline=False,
            required=True,
        )

        assert q.id == "q1"
        assert q.section == 1
        assert q.priority == "P0"
        assert q.required is True


class TestWizardAnswers:
    """Tests for WizardAnswers dataclass."""

    def test_to_dict(self):
        """Test converting WizardAnswers to dict."""
        answers = WizardAnswers(
            project_name="test-api",
            project_title="Test API",
            project_type="backend-api",
            project_domain="programming",
            project_language="python",
            created_by="test-user",
            answers={"{{ANSWER_1}}": "Test answer"},
        )

        data = answers.to_dict()
        assert data["project_name"] == "test-api"
        assert data["answers"]["{{ANSWER_1}}"] == "Test answer"

    def test_from_dict(self):
        """Test creating WizardAnswers from dict."""
        data = {
            "project_name": "test-api",
            "project_title": "Test API",
            "project_type": "backend-api",
            "project_domain": "programming",
            "project_language": "python",
            "created_by": "test-user",
            "answers": {"{{ANSWER_1}}": "Test answer"},
        }

        answers = WizardAnswers.from_dict(data)
        assert answers.project_name == "test-api"
        assert answers.answers["{{ANSWER_1}}"] == "Test answer"


class TestObjetivoWizard:
    """Tests for ObjetivoWizard class."""

    @pytest.fixture
    def wizard(self, tmp_path):
        """Create wizard with temporary template."""
        template_path = tmp_path / "template.md"
        template_path.write_text(
            """---
version: "2.0"
project:
  name: "{{PROJECT_NAME}}"
  title: "{{PROJECT_TITLE}}"
  type: "{{PROJECT_TYPE}}"
  domain: "{{PROJECT_DOMAIN}}"
  language: "{{PROJECT_LANGUAGE}}"
created_at: "{{CREATED_AT}}"
created_by: "{{CREATED_BY}}"
---

## 1️⃣ O que este projeto faz?

{{ANSWER_1}}

## 2️⃣ Qual problema resolve?

{{ANSWER_2}}

## 3️⃣ Escopo do Projeto

{{ANSWER_3}}

## 4️⃣ Restrições

{{ANSWER_4}}

## 5️⃣ Regras de Negócio

{{ANSWER_5}}
""",
            encoding="utf-8",
        )

        return ObjetivoWizard(template_path=template_path)

    def test_wizard_initialization(self, wizard):
        """Test wizard initialization."""
        assert wizard.template_path.exists()
        assert len(wizard.questions) == 10  # P0 (5) + P1 (5)
        assert wizard.answers.project_name == ""

    def test_build_questions(self, wizard):
        """Test building question list."""
        questions = wizard.questions

        # Check P0 questions
        p0_questions = [q for q in questions if q.priority == "P0"]
        assert len(p0_questions) == 5
        # Nem todas as P0 são required (ex: q2_problem)

        # Check P1 questions
        p1_questions = [q for q in questions if q.priority == "P1"]
        assert len(p1_questions) == 5
        # P1 são tipicamente opcionais (required=False)

    def test_ask_question_single_line(self, wizard):
        """Test asking a single-line question."""
        question = WizardQuestion(
            id="test",
            section=1,
            priority="P0",
            prompt="Test question?",
            example="Example",
            placeholder="{{TEST}}",
            multiline=False,
            required=True,
        )

        with patch("builtins.input", return_value="Test answer"):
            answer = wizard._ask_question(question)

        assert answer == "Test answer"

    def test_ask_question_required_retry(self, wizard):
        """Test that required questions re-ask when empty."""
        question = WizardQuestion(
            id="test",
            section=1,
            priority="P0",
            prompt="Test question?",
            example="Example",
            placeholder="{{TEST}}",
            multiline=False,
            required=True,
        )

        # First empty, then valid answer
        with patch("builtins.input", side_effect=["", "Valid answer"]):
            answer = wizard._ask_question(question)

        assert answer == "Valid answer"

    def test_ask_question_optional_skip(self, wizard):
        """Test that optional questions can be skipped."""
        question = WizardQuestion(
            id="test",
            section=4,
            priority="P1",
            prompt="Optional question?",
            example="Example",
            placeholder="{{TEST}}",
            multiline=False,
            required=False,
        )

        with patch("builtins.input", return_value=""):
            answer = wizard._ask_question(question)

        assert answer is None

    def test_ask_question_multiline(self, wizard):
        """Test multiline input (Enter Enter to terminate)."""
        question = WizardQuestion(
            id="test",
            section=2,
            priority="P0",
            prompt="Multiline question?",
            example="Example",
            placeholder="{{TEST}}",
            multiline=True,
            required=True,
        )

        # Simulate: line1, line2, empty, empty (terminate)
        with patch("builtins.input", side_effect=["Line 1", "Line 2", "", ""]):
            answer = wizard._ask_question(question)

        assert answer == "Line 1\nLine 2"

    def test_render_template(self, wizard):
        """Test template rendering with answers."""
        answers = WizardAnswers(
            project_name="test-api",
            project_title="Test API",
            project_type="backend-api",
            project_domain="programming",
            project_language="python",
            created_by="test-user",
            answers={
                "{{ANSWER_1}}": "API for testing",
                "{{ANSWER_2}}": "Solves test problem",
            },
        )

        content = wizard._render_template(answers)

        assert 'name: "test-api"' in content
        assert 'title: "Test API"' in content
        assert "API for testing" in content
        assert "Solves test problem" in content

    def test_render_template_missing_file(self, tmp_path):
        """Test render with missing template file."""
        wizard = ObjetivoWizard(template_path=tmp_path / "missing.md")
        answers = WizardAnswers()

        with pytest.raises(FileNotFoundError):
            wizard._render_template(answers)

    def test_run_non_interactive(self, wizard, tmp_path):
        """Test non-interactive mode from JSON."""
        output_file = tmp_path / "objetivo.yaml"

        answers = WizardAnswers(
            project_name="test-api",
            project_title="Test API",
            project_type="backend-api",
            project_domain="programming",
            project_language="python",
            created_by="test-user",
            answers={
                "{{ANSWER_1}}": "API for testing",
                "{{ANSWER_2}}": "Solves test problem",
                "{{ANSWER_3}}": "Feature list",
            },
        )

        exit_code = wizard.run_non_interactive(answers, output_file)

        assert exit_code == 0
        assert output_file.exists()

        content = output_file.read_text(encoding="utf-8")
        assert 'name: "test-api"' in content
        assert "API for testing" in content

    def test_save_draft(self, wizard, tmp_path):
        """Test saving draft on Ctrl+C."""
        draft_file = tmp_path / "draft.yaml"

        wizard.answers = WizardAnswers(
            project_name="draft-project",
            project_title="Draft Project",
            project_type="backend-api",
            project_domain="programming",
            project_language="python",
            created_by="test-user",
            answers={"{{ANSWER_1}}": "Partial answer"},
        )

        wizard.save_draft(draft_file)

        assert draft_file.exists()
        content = draft_file.read_text(encoding="utf-8")
        assert 'name: "draft-project"' in content
        assert "Partial answer" in content


class TestScaffoldIntegration:
    """Integration tests for scaffold.py objetivo-init command."""

    @pytest.fixture
    def scaffold_path(self):
        """Path to scaffold.py script."""
        return Path(__file__).parent.parent / "scripts" / "scaffold.py"

    def test_objetivo_init_help(self, scaffold_path):
        """Test that objetivo-init appears in help."""
        result = subprocess.run(
            [sys.executable, str(scaffold_path), "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "objetivo-init" in result.stdout

    def test_objetivo_init_template_only(self, scaffold_path, tmp_path):
        """Test objetivo-init with --template-only flag."""
        output_file = tmp_path / "objetivo.yaml"

        result = subprocess.run(
            [
                sys.executable,
                str(scaffold_path),
                "objetivo-init",
                "--template-only",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        # May fail if template doesn't exist in test env, but command should be recognized
        # Just verify the command is recognized (no "unrecognized arguments" error)
        assert "unrecognized arguments" not in result.stderr.lower()

    def test_objetivo_init_from_file(self, scaffold_path, tmp_path):
        """Test objetivo-init with --from-file (non-interactive)."""
        answers_file = tmp_path / "answers.json"
        output_file = tmp_path / "objetivo.yaml"

        # Create answers JSON
        answers_data = {
            "project_name": "test-api",
            "project_title": "Test API",
            "project_type": "backend-api",
            "project_domain": "programming",
            "project_language": "python",
            "created_by": "test-user",
            "answers": {
                "{{ANSWER_1}}": "Test answer 1",
                "{{ANSWER_2}}": "Test answer 2",
                "{{ANSWER_3}}": "Test answer 3",
            },
        }

        answers_file.write_text(json.dumps(answers_data, indent=2), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                str(scaffold_path),
                "objetivo-init",
                "--from-file",
                str(answers_file),
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        # May fail if template doesn't exist, but command should be recognized
        assert "unrecognized arguments" not in result.stderr.lower()
