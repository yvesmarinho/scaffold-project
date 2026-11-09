"""
objetivo_wizard.py — Interactive wizard for creating objetivo.yaml v2.0

Provides a guided CLI experience for creating objetivo.yaml files without
manually editing the template. Supports:
- Progressive disclosure (P0 required, P1/P2 optional)
- Keyboard navigation (Ctrl+C for draft, Ctrl+Z to go back)
- Rich formatting (with fallback to print())
- Non-interactive mode (from JSON file)

Spec: specs/066-objetivo-yaml-v2/spec.md
Tasks: T025-T036
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Try to import Rich for fancy UI (fallback to print() if not available)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None  # type: ignore


# =============================================================================
# Constants (BUG-001 Fix #1: Default docstyle)
# =============================================================================

DEFAULT_DOCSTYLE = (
    "Google Style Docstrings com type hints completos, "
    "Sphinx para geração de docs, "
    "ADRs para decisões arquiteturais, "
    "OpenAPI/Swagger para documentação de API"
)

DEFAULT_ARCHITECTURE = """\
**Estilo**: camadas com DDD leve e Ports/Adapters simplificado.

- **Presentation** (CLI/UI) → sem regra de negócio
- **Application** (casos de uso/orquestração) → depende de abstrações
- **Domain** (entidades, value objects, regras) → sem dependência de frameworks
- **Infrastructure** (filesystem, Git, APIs, parsers, exporters) → adapters

**Decisões**: registrar em `docs/decisions/` (ADRs); visão geral em `docs/architecture/overview.md`."""

_NAMING_COMMON = """\
- **Pastas**: `kebab-case/` — código em `src/`, scripts em `scripts/`, testes em `tests/`, docs em `docs/`
- **Markdown**: `SCREAMING_SNAKE.md` ou `kebab-case.md`
- **JSON / Shell**: `kebab-case.json`, `kebab-case.sh`
- **Branches**: `feat NNN-nome-da-feature`, `fix-descricao`, `docs-descricao`"""

_NAMING_BY_LANGUAGE = {
    "python": """\
- **Arquivos/módulos**: `snake_case.py`; testes `test_<modulo>.py`
- **Classes / exceções**: `PascalCase` (exceções com sufixo `Error`)
- **Funções, métodos, variáveis**: `snake_case`
- **Constantes**: `UPPER_SNAKE_CASE`
- **Privados**: prefixo `_`""",
    "typescript": """\
- **Arquivos**: `kebab-case.ts`; componentes `PascalCase.tsx`; testes `*.test.ts`
- **Classes, interfaces, types**: `PascalCase` (erros com sufixo `Error`)
- **Funções, métodos, variáveis**: `camelCase`
- **Constantes**: `UPPER_SNAKE_CASE`""",
}


def naming_conventions(language: str) -> str:
    """
    Padrão de nomenclatura (pastas, arquivos, classes, funções) para a linguagem.

    :param language: Linguagem principal do projeto (case-insensitive).
    :type language: str
    :return: Bloco Markdown; linguagem desconhecida/inválida → só o padrão comum.
    :rtype: str

    :Example:

    >>> "snake_case.py" in naming_conventions("Python")
    True
    """
    key = language.strip().lower() if isinstance(language, str) else ""
    specific = _NAMING_BY_LANGUAGE.get(key)
    return f"{_NAMING_COMMON}\n{specific}" if specific else _NAMING_COMMON


@dataclass
class WizardQuestion:
    """Represents a single question in the wizard.

    Attributes:
        id: Unique identifier (e.g., "q1_what")
        section: Section number (1-9)
        priority: P0 (required), P1 (recommended), P2 (optional)
        prompt: Question text to display
        example: Example answer to show
        placeholder: Placeholder for template (e.g., "{{ANSWER_1}}")
        multiline: Whether to accept multiline input
        required: Whether answer is required
        validation: Optional validation function
    """
    id: str
    section: int
    priority: str  # "P0" | "P1" | "P2"
    prompt: str
    example: str
    placeholder: str
    multiline: bool = False
    required: bool = True
    validation: Optional[callable] = None


@dataclass
class WizardAnswers:
    """Stores answers collected from the wizard."""
    project_name: str = ""
    project_title: str = ""
    project_type: str = ""
    project_domain: str = ""
    project_language: str = ""
    created_by: str = ""
    answers: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "project_name": self.project_name,
            "project_title": self.project_title,
            "project_type": self.project_type,
            "project_domain": self.project_domain,
            "project_language": self.project_language,
            "created_by": self.created_by,
            "answers": self.answers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WizardAnswers:
        """Create from dictionary (for non-interactive mode)."""
        return cls(
            project_name=data.get("project_name", ""),
            project_title=data.get("project_title", ""),
            project_type=data.get("project_type", ""),
            project_domain=data.get("project_domain", ""),
            project_language=data.get("project_language", ""),
            created_by=data.get("created_by", ""),
            answers=data.get("answers", {}),
        )


class ObjetivoWizard:
    """Interactive wizard for creating objetivo.yaml v2.0 files.

    Usage:
        wizard = ObjetivoWizard()
        wizard.run()  # Interactive mode

        # OR non-interactive mode:
        answers = WizardAnswers.from_dict(json.load(open("answers.json")))
        wizard.run_non_interactive(answers)
    """

    def __init__(self, template_path: Optional[Path] = None):
        """Initialize the wizard.

        Args:
            template_path: Path to template base (default: scaffold/templates/objetivo/objetivo-v2-template.yaml)
        """
        self.template_path = template_path or (
            Path(__file__).parent.parent.parent / "scaffold" / "templates" / "objetivo" / "objetivo-v2-template.yaml"
        )
        self.answers = WizardAnswers()
        self.answer_stack: list[tuple[WizardQuestion, str]] = []  # For Ctrl+Z (undo)
        self.questions = self._build_questions()

    def _build_questions(self) -> list[WizardQuestion]:
        """Build the list of questions to ask.

        Returns:
            List of WizardQuestion objects

        Implementation in T027-T028.
        """
        questions = []

        # P0 Questions (Required) - T027
        questions.append(WizardQuestion(
            id="q1_what",
            section=1,
            priority="P0",
            prompt="O que este projeto faz? (descreva em 1 frase clara)",
            example="Sistema automatizado de deploy que permite equipes DevOps configurar e executar deploys via interface web/CLI, com rollback automático em caso de falha.",
            placeholder="{{DESCRIPTION}}",
            multiline=False,
            required=True,
        ))

        questions.append(WizardQuestion(
            id="q2_problem",
            section=2,
            priority="P0",
            prompt="Qual limitação/problema atual está sendo melhorado? (1-2 parágrafos)",
            example="Sistema atual: deploys manuais levam 2-3h com 15% de erro. Performance degrada em 50%, custos operacionais +R$ 30k/mês. Falta automação e padronização.",
            placeholder="{{ANSWER_2}}",
            multiline=True,
            required=False,  # Condicional: apenas para projetos "update"
        ))

        questions.append(WizardQuestion(
            id="q3_scope_included",
            section=3,
            priority="P0",
            prompt="O que está NO escopo? (liste features incluídas, Enter vazio para terminar)",
            example="Processamento automático de dados (P0)\nInterface web para monitoramento (P1)\nNotificações por email (P2)",
            placeholder="{{FEATURE}}",  # Will expand to FEATURE_1, FEATURE_2, etc
            multiline=True,
            required=True,
        ))

        # P1 Questions (Recommended) - T028
        questions.append(WizardQuestion(
            id="q4_constraints",
            section=4,
            priority="P1",
            prompt="Há restrições técnicas? (performance, segurança, compliance - Enter vazio para pular)",
            example="Budget: R$ 50k\nPrazo: 3 meses\nDeve ser compatível com LGPD\nPerformance: <200ms p95",
            placeholder="{{CONSTRAINT}}",  # Will expand to CONSTRAINT_1, CONSTRAINT_2, etc
            multiline=True,
            required=False,
        ))

        questions.append(WizardQuestion(
            id="q5_business_rules",
            section=5,
            priority="P1",
            prompt="Há regras de negócio complexas? (Enter vazio para pular)",
            example="Usuários premium têm acesso a features avançadas\nDados devem ser retidos por 7 anos\nCálculo de desconto: 10% para >100 unidades, 20% para >1000",
            placeholder="{{RULE}}",  # Will expand to RULE_1, RULE_2, RULE_3
            multiline=True,
            required=False,
        ))

        # Campos adicionais para objetivo-init.yaml
        questions.append(WizardQuestion(
            id="q6_response",
            section=6,
            priority="P0",
            prompt="Tipo de solução técnica (linguagem, framework, padrões)",
            example="código python, com conexão PostgreSQL, usando SQLAlchemy e Alembic",
            placeholder="{{RESPONSE}}",
            multiline=False,
            required=True,
        ))

        questions.append(WizardQuestion(
            id="q7_docstyle",
            section=7,
            priority="P1",
            prompt="Padrão de documentação (Enter vazio para pular)",
            example="reStructuredText com Docstring e DocTest",
            placeholder="{{DOCSTYLE}}",
            multiline=False,
            required=False,
        ))

        questions.append(WizardQuestion(
            id="q8_infrastructure",
            section=8,
            priority="P1",
            prompt="Infraestrutura necessária (servidores, DBs, containers)",
            example="Servidor PostgreSQL em wfdb02.vya.digital\nAplicação em container Docker",
            placeholder="{{INFRASTRUCTURE}}",  # Will expand to INFRASTRUCTURE_1, INFRASTRUCTURE_2, etc
            multiline=True,
            required=False,
        ))

        questions.append(WizardQuestion(
            id="q9_profiles",
            section=9,
            priority="P1",
            prompt="Perfis/roles necessários (dba, devops, etc)",
            example="dba_architect (expert)\npython_developer (senior)\ndevops_engineer (intermediate)",
            placeholder="{{PROFILE_ROLE_1}}",
            multiline=True,
            required=False,
        ))

        questions.append(WizardQuestion(
            id="q10_expected_outcome",
            section=10,
            priority="P0",
            prompt="Resultados esperados mensuráveis",
            example="100% dos dados migrados com zero erros de FK\nTempo de migração <2h\nZero exposição de dados sensíveis",
            placeholder="{{EXPECTED_OUTCOME}}",  # Will expand to EXPECTED_OUTCOME_1, EXPECTED_OUTCOME_2, etc
            multiline=True,
            required=True,
        ))

        return questions

    def _ask_question(self, question: WizardQuestion) -> Optional[str]:
        """Ask a single question and return the answer.

        Args:
            question: WizardQuestion to ask

        Returns:
            Answer string, or None if skipped (for optional questions)

        Raises:
            KeyboardInterrupt: If Ctrl+C pressed
            EOFError: If Ctrl+Z pressed (signal to go back)

        Implementation in T026.
        """
        # Print question prompt
        self._print(f"\n[bold cyan]{question.prompt}[/bold cyan]")

        # Show example if available
        if question.example:
            self._print(f"[dim]Exemplo: {question.example}[/dim]\n")

        # Handle multiline input
        if question.multiline:
            self._print("[dim](Digite Enter duas vezes para terminar)[/dim]")
            lines = []
            empty_count = 0

            while True:
                try:
                    line = input("  ")

                    if not line.strip():
                        empty_count += 1
                        if empty_count >= 2:  # Two consecutive empty lines
                            break
                    else:
                        empty_count = 0
                        lines.append(line)

                except EOFError:  # Ctrl+D or Ctrl+Z
                    raise EOFError("Go back to previous question")
                except KeyboardInterrupt:  # Ctrl+C
                    raise

            answer = "\n".join(lines).strip()
        else:
            # Single line input
            try:
                if HAS_RICH and console:
                    answer = Prompt.ask("  Resposta").strip()
                else:
                    answer = input("  Resposta: ").strip()
            except EOFError:
                raise EOFError("Go back to previous question")
            except KeyboardInterrupt:
                raise

        # Validate required fields
        if question.required and not answer:
            self._print("[yellow]⚠️  Esta pergunta é obrigatória. Tente novamente.[/yellow]")
            return self._ask_question(question)  # Re-ask

        # If empty and optional, return None
        if not answer and not question.required:
            return None

        # Custom validation
        if question.validation and answer:
            try:
                question.validation(answer)
            except ValueError as e:
                self._print(f"[yellow]⚠️  {e}[/yellow]")
                return self._ask_question(question)  # Re-ask

        return answer

    def _render_template(self, answers: WizardAnswers) -> str:
        """Render the template with collected answers.

        Args:
            answers: WizardAnswers with collected data

        Returns:
            Rendered objetivo-init.yaml content as string (YAML puro)

        Implementation in T029.
        """
        # Read template
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        template = self.template_path.read_text(encoding='utf-8')

        # 1. Substitute metadata placeholders in frontmatter
        template = template.replace('"{{PROJECT_NAME}}"', f'"{answers.project_name}"')
        template = template.replace('{{PROJECT_NAME}}', answers.project_name)
        template = template.replace('"{{PROJECT_TITLE}}"', f'"{answers.project_title}"')
        template = template.replace('{{PROJECT_TITLE}}', answers.project_title)
        template = template.replace('"{{PROJECT_TYPE}}"', f'"{answers.project_type}"')
        template = template.replace('{{PROJECT_TYPE}}', answers.project_type)
        template = template.replace('"{{PROJECT_DOMAIN}}"', f'"{answers.project_domain}"')
        template = template.replace('{{PROJECT_DOMAIN}}', answers.project_domain)
        template = template.replace('"{{PROJECT_LANGUAGE}}"', f'"{answers.project_language}"')
        template = template.replace('{{PROJECT_LANGUAGE}}', answers.project_language)
        template = template.replace('"{{CREATED_BY}}"', f'"{answers.created_by}"')
        template = template.replace('{{CREATED_BY}}', answers.created_by)

        # Add created_at timestamp
        from datetime import datetime
        created_at = datetime.now().strftime("%Y-%m-%d")
        template = template.replace('"{{CREATED_AT}}"', f'"{created_at}"')
        template = template.replace('{{CREATED_AT}}', created_at)

        # 2. Process answers - expand multiline placeholders
        # Map question IDs to placeholders using question definitions
        question_map = {q.id: q.placeholder for q in self.questions}
        processed_placeholders = {}

        for question_id, value in answers.answers.items():
            if not value:
                continue

            # Se a chave já é um placeholder (ex: "{{DESCRIPTION}}"), usá-la diretamente.
            # Isso suporta tanto question IDs ("q1_what") quanto placeholders diretos.
            if question_id.startswith("{{") and question_id.endswith("}}"):
                placeholder = question_id
            else:
                placeholder = question_map.get(question_id, f"{{{{{question_id.upper()}}}}}")
            base_placeholder = placeholder.replace('{{', '').replace('}}', '')

            if '\n' in value and base_placeholder in ['FEATURE', 'RULE', 'CONSTRAINT', 'INFRASTRUCTURE', 'EXPECTED_OUTCOME']:
                # Split multiline value into individual items
                lines = [line.strip() for line in value.split('\n') if line.strip()]

                # Create numbered placeholders with markdown list formatting
                for i, line in enumerate(lines, start=1):
                    numbered_placeholder = f"{{{{{base_placeholder}_{i}}}}}"
                    # Add markdown list prefix if this is a list-type placeholder
                    if base_placeholder in ['FEATURE', 'CONSTRAINT', 'INFRASTRUCTURE', 'EXPECTED_OUTCOME']:
                        processed_placeholders[numbered_placeholder] = f"- {line}"
                    else:
                        processed_placeholders[numbered_placeholder] = line
            else:
                # Single value placeholder
                processed_placeholders[placeholder] = value

        # 3. Substitute all processed placeholders
        for placeholder, value in processed_placeholders.items():
            # Handle quoted and unquoted placeholders
            template = template.replace(f'"{placeholder}"', f'"{value}"')
            template = template.replace(placeholder, value)

        # 4. Add default values for placeholders without questions (BUG-001 Fix)
        defaults = {
            '{{WORKFLOW_OBJETIVO}}': 'Workflow baseado em objetivo.yaml v2.0 com SpecKit',
            '{{WORKFLOW_SPECIFY}}': 'Geração automática de spec.md, plan.md e tasks.md',
            # BUG-001 Fix #2: NÃO incluir default para OUT_SCOPE (será removido se vazio)
            '{{FOLDER_STRUCTURE_CUSTOM}}': '',  # Empty for default structure
            '{{DOCSTYLE}}': DEFAULT_DOCSTYLE,  # BUG-001 Fix #1: Default quando não fornecido
            '{{ARCHITECTURE}}': DEFAULT_ARCHITECTURE,
            '{{NAMING_CONVENTIONS}}': naming_conventions(answers.project_language),
        }

        for placeholder, default_value in defaults.items():
            # Só aplicar default se placeholder ainda existe (não foi substituído por resposta)
            if placeholder in template:
                template = template.replace(f'"{placeholder}"', f'"{default_value}"')
                template = template.replace(placeholder, default_value)

        # 5. Clean up remaining empty placeholders (remove or set to empty string)
        import re

        # BUG-001 Fix #2: Remover linhas com out-scope vazio
        # Detecta: "      - out-scope: """" ou "      - out-scope: "{{OUT_SCOPE}}""
        template = re.sub(r'^\s*-?\s*out-scope:\s*("{{OUT_SCOPE}}"|"")?\s*$', '', template, flags=re.MULTILINE)

        # Remove lines with unreplaced placeholders that look like "{{PLACEHOLDER_N}}"
        template = re.sub(r'^\s*-?\s*"?\{\{[A-Z_0-9]+\}\}"?\s*$', '', template, flags=re.MULTILINE)

        # Clean up remaining single placeholders
        template = re.sub(r'"?\{\{[A-Z_0-9]+\}\}"?', '""', template)

        return template

    def run(self, output_path: Optional[Path] = None) -> int:
        """Run the wizard in interactive mode.

        Args:
            output_path: Where to write the generated objetivo-init.yaml
                        If None, uses CWD/objetivo-init.yaml

        Returns:
            Exit code: 0 if success, 1 if cancelled/error

        Implementation in T030.
        """
        # Use CWD if no path provided (fix for ~./local/bin/scaffold issue)
        if output_path is None:
            output_path = Path.cwd() / "objetivo-init.yaml"

        try:
            # Print banner
            self._print("\n")
            if HAS_RICH and console:
                console.print(Panel(
                    "[bold cyan]🧙 Wizard objetivo-init.yaml v1.0[/bold cyan]\n\n"
                    "Crie seu arquivo objetivo-init.yaml respondendo perguntas.\n"
                    "[dim]Ctrl+C: salvar draft | Ctrl+Z: voltar[/dim]",
                    border_style="cyan",
                    padding=(1, 2),
                ))
            else:
                self._print("\n🧙 Wizard objetivo-init.yaml v1.0\n")
                self._print("Crie seu arquivo objetivo.yaml respondendo algumas perguntas.")
                self._print("(Ctrl+C: salvar draft | Ctrl+Z: voltar)\n")

            # Ask project metadata
            self._print("\n[bold]Metadados do Projeto[/bold]\n")

            self.answers.project_name = self._ask_simple("Nome do projeto (kebab-case)", "user-management-api", required=True)
            self.answers.project_title = self._ask_simple("Título legível", "API de Gerenciamento de Usuários", required=True)
            self.answers.project_type = self._ask_choice(
                "Tipo do projeto",
                ["backend-api", "frontend-spa", "cli-tool", "library", "deployment-chart", "infrastructure-code"],
                default="backend-api"
            )
            self.answers.project_domain = self._ask_choice(
                "Domínio",
                ["programming", "infrastructure", "data-engineering", "security", "qa", "design"],
                default="programming"
            )
            self.answers.project_language = self._ask_simple("Linguagem principal", "python", required=True)
            self.answers.created_by = self._ask_simple("Criado por (seu nome ou username)", "devops-team", required=True)

            # Ask project context (new vs update)
            project_context = self._ask_choice(
                "Este é um projeto novo ou atualização/melhoria?",
                ["novo", "update"],
                default="novo"
            )

            # Ask P0 questions (required)
            self._print("\n[bold]Seções P0 (Essenciais - Obrigatório)[/bold]\n")

            p0_questions = [q for q in self.questions if q.priority == "P0"]
            for question in p0_questions:
                # Skip "problem" question for new projects
                if question.id == "q2_problem" and project_context == "novo":
                    # Add default text for new projects
                    self.answers.answers[question.placeholder] = "Projeto greenfield — não há sistema anterior a ser substituído."
                    continue
                try:
                    answer = self._ask_question(question)
                    if answer:
                        self.answers.answers[question.placeholder] = answer
                        self.answer_stack.append((question, answer))
                except EOFError:
                    # Ctrl+Z - go back
                    if self.answer_stack:
                        prev_q, _ = self.answer_stack.pop()
                        self._print(f"[dim]Voltando para: {prev_q.prompt}[/dim]")
                        # Re-ask previous question
                        # (simplified - in full implementation would properly handle stack)
                        continue

            # Ask if want to add optional sections
            self._print("\n[bold]Seções Opcionais[/bold]\n")
            add_optional = self._ask_simple("Adicionar seções opcionais (P1)? [y/N]", "n", required=False)

            if add_optional and add_optional.lower() in ['y', 'yes', 's', 'sim']:
                self._print("\n[bold]Seções P1 (Contextuais - Recomendado)[/bold]\n")
                p1_questions = [q for q in self.questions if q.priority == "P1"]

                for question in p1_questions:
                    try:
                        answer = self._ask_question(question)
                        if answer:
                            self.answers.answers[question.placeholder] = answer
                            self.answer_stack.append((question, answer))
                    except EOFError:
                        continue

            # Render template
            content = self._render_template(self.answers)

            # Write to file
            output_path.write_text(content, encoding='utf-8')

            # Success message
            self._print("\n[bold green]✅ Pronto![/bold green]\n")
            self._print(f"Arquivo criado: [cyan]{output_path}[/cyan]\n")
            self._print("[bold]Próximos passos:[/bold]")
            self._print("  1. Revise e complete o arquivo objetivo-init.yaml")
            self._print("  2. Valide: [cyan]scaffold objetivo-validate --file objetivo-init.yaml[/cyan]")
            self._print("  3. Gere spec: [cyan]scaffold objetivo-generate --input objetivo-init.yaml[/cyan]\n")

            return 0

        except KeyboardInterrupt:
            # Ctrl+C - save draft
            self._print("\n\n[yellow]⚠️  Wizard cancelado.[/yellow]")
            self.save_draft()
            return 1
        except Exception as e:
            self._print(f"\n[bold red]❌ Erro:[/bold red] {e}\n")
            return 1

    def run_non_interactive(
        self,
        answers: WizardAnswers,
        output_path: Optional[Path] = None
    ) -> int:
        """Run the wizard in non-interactive mode (from JSON file).

        Args:
            answers: Pre-filled WizardAnswers
            output_path: Where to write the generated objetivo-init.yaml
                        If None, uses CWD/objetivo-init.yaml

        Returns:
            Exit code: 0 if success, 1 if error

        Implementation in T035.
        """
        # Use CWD if no path provided
        if output_path is None:
            output_path = Path.cwd() / "objetivo-init.yaml"

        try:
            self._print("\n🤖 Modo não-interativo\n")
            self._print(f"Gerando objetivo-init.yaml de: {answers.project_name}\n")

            # Use provided answers
            self.answers = answers

            # Render template
            content = self._render_template(self.answers)

            # Write to file
            output_path.write_text(content, encoding='utf-8')

            # Success message
            self._print(f"\n[green]✅ Gerado:[/green] {output_path}\n")

            return 0

        except Exception as e:
            self._print(f"\n[bold red]❌ Erro:[/bold red] {e}\n")
            return 1

    def save_draft(self, draft_path: Path = Path("objetivo-draft.yaml")) -> None:
        """Save current answers as draft (called on Ctrl+C).

        Args:
            draft_path: Where to save draft
        """
        try:
            content = self._render_template(self.answers)
            draft_path.write_text(content, encoding='utf-8')
            self._print(f"\n  [yellow]📝 Draft salvo:[/yellow] {draft_path}")
        except Exception as e:
            self._print(f"\n  [red]❌ Erro ao salvar draft:[/red] {e}")

    def _print(self, message: str, **kwargs) -> None:
        """Print message with Rich if available, otherwise plain print().

        Args:
            message: Message to print (supports Rich markup)
            **kwargs: Additional arguments for console.print()
        """
        if HAS_RICH and console:
            # Remove Rich markup tags for plain print
            console.print(message, **kwargs)
        else:
            # Strip Rich markup tags like [bold], [red], etc.
            import re
            clean_message = re.sub(r'\[/?[a-z\s]+\]', '', message)
            print(clean_message, **kwargs)

    def _ask_simple(self, prompt: str, example: str, required: bool = True) -> str:
        """Ask a simple single-line question.

        Args:
            prompt: Question prompt
            example: Example answer
            required: Whether answer is required

        Returns:
            Answer string
        """
        self._print(f"\n[cyan]{prompt}[/cyan]")
        if example:
            self._print(f"[dim]Exemplo: {example}[/dim]")

        if HAS_RICH and console:
            answer = Prompt.ask("  Resposta").strip()
        else:
            answer = input("  Resposta: ").strip()

        if required and not answer:
            self._print("[yellow]⚠️  Esta pergunta é obrigatória.[/yellow]")
            return self._ask_simple(prompt, example, required)

        return answer

    def _ask_choice(self, prompt: str, choices: list[str], default: str) -> str:
        """Ask a multiple choice question.

        Args:
            prompt: Question prompt
            choices: List of valid choices
            default: Default choice

        Returns:
            Selected choice
        """
        self._print(f"\n[cyan]{prompt}[/cyan]")
        self._print(f"[dim]Opções: {', '.join(choices)}[/dim]")

        if HAS_RICH and console:
            answer = Prompt.ask("  Escolha", default=default).strip()
        else:
            answer = input(f"  Escolha [{default}]: ").strip() or default

        if answer not in choices:
            self._print(f"[yellow]⚠️  Escolha inválida. Escolha entre: {', '.join(choices)}[/yellow]")
            return self._ask_choice(prompt, choices, default)

        return answer
