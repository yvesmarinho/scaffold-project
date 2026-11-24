"""
Testes para scripts/lib/git_validators.py

Valida:
- Validação de nomes de branch (convenção feature/NNN-descricao)
- Validação de mensagens de commit (Conventional Commits)
- Detecção de breaking changes
- Sugestões de nomes de branch
"""

# Import do módulo a testar
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.git_validators import (
    BranchType,
    CommitType,
    format_validation_errors,
    is_protected_branch,
    suggest_branch_name,
    validate_branch_name,
    validate_commit_message,
)

# =============================================================================
# Testes de Validação de Branch
# =============================================================================


class TestBranchNameValidation:
    """Testes para validate_branch_name()"""

    def test_valid_feature_branch_with_issue(self):
        """Feature branch com issue number deve ser válida"""
        result = validate_branch_name("feature/042-user-authentication")

        assert result.is_valid
        assert result.branch_type == BranchType.FEATURE
        assert result.issue_number == 42
        assert result.description == "user-authentication"
        assert len(result.errors) == 0

    def test_valid_fix_branch_without_issue(self):
        """Fix branch sem issue number deve ser válida"""
        result = validate_branch_name("fix/memory-leak")

        assert result.is_valid
        assert result.branch_type == BranchType.FIX
        assert result.issue_number is None
        assert result.description == "memory-leak"
        assert len(result.errors) == 0

    def test_valid_hotfix_branch(self):
        """Hotfix branch deve ser válida"""
        result = validate_branch_name("hotfix/critical-security-patch")

        assert result.is_valid
        assert result.branch_type == BranchType.HOTFIX
        assert len(result.errors) == 0

    def test_valid_chore_branch(self):
        """Chore branch deve ser válida"""
        result = validate_branch_name("chore/update-dependencies")

        assert result.is_valid
        assert result.branch_type == BranchType.CHORE
        assert len(result.errors) == 0

    def test_protected_branch_main(self):
        """Branch 'main' deve ser aceita como protegida"""
        result = validate_branch_name("main")

        assert result.is_valid
        assert result.branch_type is None
        assert len(result.errors) == 0

    def test_protected_branch_develop(self):
        """Branch 'develop' deve ser aceita como protegida"""
        result = validate_branch_name("develop")

        assert result.is_valid
        assert len(result.errors) == 0

    def test_invalid_uppercase(self):
        """Branch com uppercase deve ser inválida"""
        result = validate_branch_name("FEATURE/bad-case")

        assert not result.is_valid
        assert "lowercase" in " ".join(result.errors).lower()

    def test_invalid_pattern(self):
        """Branch sem padrão correto deve ser inválida"""
        result = validate_branch_name("invalid-branch-name")

        assert not result.is_valid
        assert "padrão" in " ".join(result.errors).lower()

    def test_invalid_special_characters(self):
        """Branch com caracteres especiais deve ser inválida"""
        result = validate_branch_name("feature/user@authentication")

        assert not result.is_valid
        assert (
            "caracteres" in " ".join(result.errors).lower()
            or "apenas" in " ".join(result.errors).lower()
        )

    def test_warning_feature_without_issue(self):
        """Feature sem issue deve gerar warning"""
        result = validate_branch_name("feature/no-issue-number")

        assert result.is_valid  # válida mas com warning
        assert len(result.warnings) > 0
        assert "issue" in " ".join(result.warnings).lower()

    def test_warning_long_description(self):
        """Descrição muito longa deve gerar warning"""
        long_desc = "a" * 60
        result = validate_branch_name(f"fix/{long_desc}")

        assert len(result.warnings) > 0
        assert "longa" in " ".join(result.warnings).lower()

    def test_error_short_description(self):
        """Descrição muito curta deve gerar erro"""
        result = validate_branch_name("fix/ab")

        assert not result.is_valid
        assert "curta" in " ".join(result.errors).lower()

    def test_warning_underscores(self):
        """Underscores devem gerar erro (caracteres não permitidos)"""
        result = validate_branch_name("fix/use_hyphens_not_underscores")

        # Underscores não são permitidos, então gera erro (não warning)
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any(
            "caracteres" in e.lower() or "apenas" in e.lower() for e in result.errors
        )


# =============================================================================
# Testes de Validação de Commit
# =============================================================================


class TestCommitMessageValidation:
    """Testes para validate_commit_message()"""

    def test_valid_feat_with_scope(self):
        """Commit feat com scope deve ser válido"""
        result = validate_commit_message("feat(api): add user endpoint")

        assert result.is_valid
        assert result.commit_type == CommitType.FEAT
        assert result.scope == "api"
        assert result.subject == "add user endpoint"
        assert not result.is_breaking
        assert len(result.errors) == 0

    def test_valid_fix_without_scope(self):
        """Commit fix sem scope deve ser válido"""
        result = validate_commit_message("fix: memory leak in parser")

        assert result.is_valid
        assert result.commit_type == CommitType.FIX
        assert result.scope is None
        assert result.subject == "memory leak in parser"
        assert not result.is_breaking
        assert len(result.errors) == 0

    def test_valid_breaking_change_with_exclamation(self):
        """Breaking change com ! deve ser detectado"""
        result = validate_commit_message("feat(api)!: change response format")

        assert result.is_valid
        assert result.commit_type == CommitType.FEAT
        assert result.scope == "api"
        assert result.is_breaking
        assert len(result.errors) == 0

    def test_valid_breaking_change_with_footer(self):
        """Breaking change no footer/body deve ser detectado"""
        message = """feat(api): change response format

BREAKING CHANGE: campo 'userId' renomeado para 'user_id'
"""
        result = validate_commit_message(message)

        assert result.is_valid
        assert result.is_breaking
        # BREAKING CHANGE pode estar no body ou footer
        assert (result.body and "BREAKING CHANGE" in result.body) or (
            result.footer and "BREAKING CHANGE" in result.footer
        )

    def test_valid_commit_types(self):
        """Todos os tipos válidos devem ser aceitos"""
        valid_types = [
            "feat",
            "fix",
            "docs",
            "style",
            "refactor",
            "perf",
            "test",
            "chore",
            "ci",
            "build",
        ]

        for commit_type in valid_types:
            result = validate_commit_message(f"{commit_type}: test message")
            assert result.is_valid, f"Tipo '{commit_type}' deveria ser válido"
            assert result.commit_type == CommitType(commit_type)

    def test_invalid_commit_format(self):
        """Commit sem formato correto deve ser inválido"""
        result = validate_commit_message("invalid commit message")

        assert not result.is_valid
        assert "Conventional Commits" in " ".join(result.errors)

    def test_invalid_commit_type(self):
        """Commit com tipo inválido deve ser inválido"""
        result = validate_commit_message("invalid: message")

        assert not result.is_valid

    def test_warning_long_subject(self):
        """Subject muito longo deve gerar warning"""
        long_subject = "a" * 80
        result = validate_commit_message(f"feat: {long_subject}")

        assert len(result.warnings) > 0
        assert "longo" in " ".join(result.warnings).lower()

    def test_warning_short_subject(self):
        """Subject muito curto deve gerar erro"""
        result = validate_commit_message("feat: abc")

        assert not result.is_valid
        assert "curto" in " ".join(result.errors).lower()

    def test_warning_subject_period(self):
        """Subject terminando com ponto deve gerar warning"""
        result = validate_commit_message("feat: add feature.")

        assert len(result.warnings) > 0
        assert "ponto" in " ".join(result.warnings).lower()

    def test_warning_subject_uppercase(self):
        """Subject começando com maiúscula deve gerar warning"""
        result = validate_commit_message("feat: Add New Feature")

        assert len(result.warnings) > 0
        assert "minúscula" in " ".join(result.warnings).lower()

    def test_warning_vague_message(self):
        """Mensagens vagas devem gerar warning"""
        result = validate_commit_message("fix: update")

        assert result.is_valid, "mensagem vaga gera aviso, não erro"
        assert any("vagas" in w for w in result.warnings), result.warnings

    def test_commit_with_body_and_footer(self):
        """Commit com body e footer deve ser parseado corretamente"""
        message = """feat(api): add user endpoint

This endpoint allows creating new users.
Includes validation and error handling.

Closes #123
Refs #456
"""
        result = validate_commit_message(message)

        assert result.is_valid
        assert result.body is not None
        assert "validation" in result.body
        assert result.footer is not None
        assert "#123" in result.footer


# =============================================================================
# Testes de Funções Auxiliares
# =============================================================================


class TestHelperFunctions:
    """Testes para funções auxiliares"""

    def test_is_protected_branch_main(self):
        """'main' deve ser reconhecida como protegida"""
        assert is_protected_branch("main")

    def test_is_protected_branch_master(self):
        """'master' deve ser reconhecida como protegida"""
        assert is_protected_branch("master")

    def test_is_protected_branch_develop(self):
        """'develop' deve ser reconhecida como protegida"""
        assert is_protected_branch("develop")

    def test_is_not_protected_branch(self):
        """Feature branch não deve ser protegida"""
        assert not is_protected_branch("feature/123-test")

    def test_suggest_branch_name_feature_with_issue(self):
        """Sugestão de feature branch com issue"""
        result = suggest_branch_name("Add User Authentication", 42)

        assert result.startswith("feature/042-")
        assert "user" in result
        assert "authentication" in result

    def test_suggest_branch_name_fix(self):
        """Sugestão de fix branch sem issue"""
        result = suggest_branch_name("Fix Memory Leak")

        assert result.startswith("fix/")
        assert "memory" in result
        assert "leak" in result

    def test_suggest_branch_name_normalize(self):
        """Sugestão deve normalizar caracteres especiais"""
        result = suggest_branch_name("Fix: Weird@Characters!")

        # Deve remover caracteres especiais
        assert "@" not in result
        assert "!" not in result
        assert ":" not in result

    def test_suggest_branch_name_max_length(self):
        """Sugestão deve respeitar limite de 50 chars"""
        long_desc = "A" * 100
        result = suggest_branch_name(long_desc)

        # Remove prefixo tipo "feature/" para contar apenas descrição
        desc_part = result.split("/", 1)[1]
        assert len(desc_part) <= 50

    def test_format_validation_errors_with_errors(self):
        """Formatação de erros deve incluir ❌"""
        result = validate_branch_name("INVALID")
        formatted = format_validation_errors(result)

        assert "❌" in formatted
        assert "Erros:" in formatted

    def test_format_validation_errors_with_warnings(self):
        """Formatação de warnings deve incluir ⚠️"""
        result = validate_branch_name("feature/no-issue")
        formatted = format_validation_errors(result)

        # Pode ter warnings
        if result.warnings:
            assert "⚠️" in formatted

    def test_format_validation_errors_success(self):
        """Formatação de sucesso deve incluir ✅"""
        result = validate_branch_name("feature/042-valid-branch")
        formatted = format_validation_errors(result)

        if not result.errors and not result.warnings:
            assert "✅" in formatted


# =============================================================================
# Testes de Edge Cases
# =============================================================================


class TestEdgeCases:
    """Testes para casos extremos"""

    def test_empty_branch_name(self):
        """Branch vazia deve ser inválida"""
        result = validate_branch_name("")
        assert not result.is_valid

    def test_empty_commit_message(self):
        """Commit vazio deve ser inválido"""
        result = validate_commit_message("")
        assert not result.is_valid

    def test_branch_name_only_slashes(self):
        """Branch com apenas barras deve ser inválida"""
        result = validate_branch_name("///")
        assert not result.is_valid

    def test_commit_message_only_whitespace(self):
        """Commit com apenas espaços deve ser inválido"""
        result = validate_commit_message("   \n   ")
        assert not result.is_valid

    def test_branch_name_with_numbers_only(self):
        """Branch apenas com números deve funcionar se seguir padrão"""
        result = validate_branch_name("feature/123-456")
        # Deve ser válida se passar validação de tamanho
        assert result.branch_type == BranchType.FEATURE
        assert result.issue_number == 123


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
