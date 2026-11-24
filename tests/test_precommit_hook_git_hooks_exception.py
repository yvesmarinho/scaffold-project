"""
Testes para verificar que o hook pre-commit.secrets não bloqueia arquivos .git-hooks/

Ref: Bug encontrado 2026-04-29 — hook bloqueava .git-hooks/pre-commit.secrets (falso positivo)
     - Hook tem padrão 'secret' que fazia match com pre-commit.secrets
     - Adicionada exceção para arquivos em .git-hooks/
     - Corrigida mensagem de ajuda (git reset HEAD → git restore --staged)

Update 2026-04-29: Hook agora sempre é atualizado em projetos existentes
     - Scaffold sobrescreve .git-hooks/pre-commit.secrets sempre (não faz merge)
     - Garante que correções de segurança sejam aplicadas
"""

import re


def test_hook_ignores_git_hooks_directory():
    """Verifica que o hook pre-commit.secrets ignora arquivos em .git-hooks/"""
    from scripts.lib.project import _PRE_COMMIT_SECRETS_HOOK

    # Verificar que há exceção para .git-hooks/
    assert ".git-hooks/" in _PRE_COMMIT_SECRETS_HOOK
    assert r'if [[ "$file" =~ ^\.git-hooks/ ]]' in _PRE_COMMIT_SECRETS_HOOK
    # Não deve usar 'git reset HEAD' (falha em repos recém-inicializados)
    assert "git reset HEAD" not in _PRE_COMMIT_SECRETS_HOOK

    # Deve usar 'git restore --staged' ou 'git reset' sem HEAD
    assert (
        "git restore --staged" in _PRE_COMMIT_SECRETS_HOOK
        or "git reset " in _PRE_COMMIT_SECRETS_HOOK
    )


def test_hook_has_sensitive_patterns():
    """Verifica que hook ainda detecta padrões sensíveis"""
    from scripts.lib.project import _PRE_COMMIT_SECRETS_HOOK

    # Padrões sensíveis devem estar presentes
    sensitive_patterns = [
        "secret",
        "password",
        "token",
        r"\.env",
        r"\.key$",
        "credentials",
    ]

    for pattern in sensitive_patterns:
        # Padrão deve estar na array SENSITIVE_PATTERNS
        assert (
            pattern in _PRE_COMMIT_SECRETS_HOOK
        ), f"Padrão '{pattern}' ausente no hook"


def test_hook_validates_secrets_directory():
    """Verifica que hook bloqueia commits de .secrets/"""
    from scripts.lib.project import _PRE_COMMIT_SECRETS_HOOK

    # Deve ter verificação para .secrets/
    assert (
        r"^\\.secrets/" in _PRE_COMMIT_SECRETS_HOOK
        or r"^\.secrets/" in _PRE_COMMIT_SECRETS_HOOK
    )
    assert "BLOQUEADO: .secrets/ detectado" in _PRE_COMMIT_SECRETS_HOOK


def test_hook_checks_permissions():
    """Verifica que hook valida permissões 700 em .secrets/"""
    from scripts.lib.project import _PRE_COMMIT_SECRETS_HOOK

    # Deve verificar permissões
    assert "chmod 700" in _PRE_COMMIT_SECRETS_HOOK
    assert '[ "$PERMS" != "700" ]' in _PRE_COMMIT_SECRETS_HOOK


def test_hook_exception_pattern_syntax():
    """Verifica sintaxe correta da exceção para .git-hooks/"""
    from scripts.lib.project import _PRE_COMMIT_SECRETS_HOOK

    # Extrair trecho relevante do hook
    # Deve ter estrutura: if [[ "$file" =~ ^\.git-hooks/ ]]; then continue; fi

    # Verificar que tem condicional regex
    assert re.search(r"if \[\[.*=~.*\.git-hooks/", _PRE_COMMIT_SECRETS_HOOK)

    # Verificar que tem continue dentro do bloco
    lines = _PRE_COMMIT_SECRETS_HOOK.split("\n")
    found_pattern = False
    found_continue = False

    for i, line in enumerate(lines):
        if ".git-hooks/" in line and "=~" in line:
            found_pattern = True
            # Próximas 3 linhas devem ter 'continue'
            for j in range(i, min(i + 3, len(lines))):
                if "continue" in lines[j]:
                    found_continue = True
                    break

    assert found_pattern, "Padrão de exceção .git-hooks/ não encontrado"
    assert (
        found_continue
    ), "Comando 'continue' não encontrado após verificação .git-hooks/"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
