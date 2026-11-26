"""Security tests for mini-Engram memory system (IMP-59 Phase 3).

Tests for PII/secrets detection and sanitization in memory content.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.lib.sanitize import (
    detect_secrets,
    get_security_report,
    sanitize,
    validate_safe,
)


def test_detect_api_keys():
    """Test detection of API keys."""
    content = f"""
    # Configuration

    api_key = "sk_{"live"}_abc123defg456789"
    apikey: "prod_xyz987654321abcd"
    """

    findings = detect_secrets(content)

    # Should find 2 API keys
    assert len(findings) >= 2
    assert any(name == "api_key" for name, _ in findings)


def test_detect_passwords():
    """Test detection of password patterns."""
    content = """
    password = "mySecretPass123"
    passwd: hunter2
    pwd="admin123"
    """

    findings = detect_secrets(content)

    # Should find 3 passwords
    assert len(findings) >= 3
    assert any(name == "password" for name, _ in findings)


def test_detect_tokens():
    """Test detection of various token types."""
    content = """
    # GitHub token
    ghp_abc123defghijklmnopqrstuvwxyz12345

    # JWT
    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

    # Generic token
    bearer_token: "abc123xyz789longtoken"
    """

    findings = detect_secrets(content)

    # Should find multiple tokens
    assert len(findings) >= 2

    # Check specific types
    found_types = [name for name, _ in findings]
    assert "github_token" in found_types or "token" in found_types
    assert "jwt" in found_types or "token" in found_types


def test_sanitize_with_redaction():
    """Test sanitization with redaction."""
    content = "api_key = 'sk_" "live_secret123456789' password: admin123"

    sanitized, warnings = sanitize(content, redact=True)

    # Should have warnings
    assert len(warnings) > 0

    # Should contain redaction markers
    assert "[REDACTED" in sanitized

    # Should NOT contain original secrets
    assert "sk_" "live_secret123456789" not in sanitized
    assert "admin123" not in sanitized


def test_sanitize_without_redaction():
    """Test sanitization with removal (no redaction markers)."""
    # Use realistic secret values that match pattern requirements (key=value format)
    content = "password='secret123' and api_key: 'sk_" "live_abc1234567890123456789'"

    sanitized, warnings = sanitize(content, redact=False)

    # Should have warnings
    assert len(warnings) > 0

    # Should NOT contain redaction markers or secrets
    assert "[REDACTED" not in sanitized
    assert "secret123" not in sanitized
    assert "sk_" "live_abc1234567890123456789" not in sanitized


def test_validate_safe_with_secrets():
    """Test validation fails when secrets are present."""
    content = "api_key = 'sk_" "live_abc123456789012345'"

    is_safe, issues = validate_safe(content)

    assert is_safe is False
    assert len(issues) > 0
    assert "api_key" in issues


def test_validate_safe_clean_content():
    """Test validation passes for clean content."""
    content = """
    # Memory: Database Migration Strategy

    Use Alembic for migrations:
    1. Create migration: alembic revision -m "description"
    2. Apply: alembic upgrade head
    3. Rollback: alembic downgrade -1
    """

    is_safe, issues = validate_safe(content)

    assert is_safe is True
    assert len(issues) == 0


def test_validate_safe_allow_emails():
    """Test validation with allowed email addresses."""
    content = "Contact: support@example.com for help"

    # Should fail without allow_emails
    is_safe, issues = validate_safe(content, allow_emails=False)
    assert is_safe is False
    assert "email" in issues

    # Should pass with allow_emails
    is_safe, issues = validate_safe(content, allow_emails=True)
    assert is_safe is True
    assert len(issues) == 0


def test_validate_safe_allow_ips():
    """Test validation with allowed IP addresses."""
    content = "Server IP: 192.168.1.100"

    # Should fail without allow_ips
    is_safe, issues = validate_safe(content, allow_ips=False)
    assert is_safe is False
    assert "ip_address" in issues

    # Should pass with allow_ips
    is_safe, issues = validate_safe(content, allow_ips=True)
    assert is_safe is True
    assert len(issues) == 0


def test_security_report():
    """Test security report generation."""
    content = """
    api_key = "sk_" "live_abc123456789"
    password = "secret123"
    email: user@example.com
    """

    report = get_security_report(content)

    # Report should be non-empty
    assert len(report) > 0

    # Should mention findings
    assert "api_key" in report.lower() or "found" in report.lower()


def test_aws_keys_detection():
    """Test detection of AWS access keys."""
    content = """
    AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
    """

    findings = detect_secrets(content)

    # Should find AWS key
    assert len(findings) >= 1
    assert any(name == "aws_key" for name, _ in findings)


def test_private_key_detection():
    """Test detection of private keys."""
    # Marcador montado por concatenação: o hook detect-private-key não confunde o
    # fixture (chave falsa e truncada) com uma chave real versionada.
    marcador = "PRIVATE " + "KEY"
    content = f"""
    -----BEGIN RSA {marcador}-----
    MIIEpAIBAAKCAQEA...
    -----END RSA {marcador}-----
    """

    findings = detect_secrets(content)

    # Should find private key
    assert len(findings) >= 1
    assert any(name == "private_key" for name, _ in findings)


def test_slack_token_detection():
    """Test detection of Slack tokens."""
    # Use realistic Slack token format (xoxb" "-{10+ chars})
    content = "slack_token: xoxb" "-1234567890-1234567890123-abcdefghijklmnopqrstuvwx"

    findings = detect_secrets(content)

    # Should find Slack token
    assert len(findings) >= 1
    assert any(name == "slack_token" for name, _ in findings)


def test_no_false_positives_common_words():
    """Test that common words don't trigger false positives."""
    content = """
    # Password Policy

    All passwords must:
    - Be at least 12 characters
    - Include uppercase and lowercase
    - Include numbers and symbols

    API keys should be rotated every 90 days.
    """

    findings = detect_secrets(content)

    # Should NOT detect 'passwords' or 'API keys' in documentation
    # (these are descriptive text, not actual secrets)
    # Our patterns require '=' or ':' for assignment
    assert len(findings) == 0


# --- get_security_report não pode vazar valores (BUG-sanitize-report-vaza-secrets) ---
# Fixtures montados por concatenação para não disparar hooks de detecção de secrets.

_SENHA_CURTA = "s3nh4" + "Curta"
_TOKEN_LONGO = "tok" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
_EMAIL = "fulano" + "@example.com"
_IP = "10.20" + ".30.40"


def test_security_report_nao_exibe_senha_curta_inteira():
    """Senha com menos de 20 chars era exibida inteira no relatório."""
    report = get_security_report(f'password = "{_SENHA_CURTA}"')
    assert _SENHA_CURTA not in report


def test_security_report_nao_exibe_prefixo_de_token_longo():
    """Os 20 primeiros chars de um token longo eram exibidos."""
    report = get_security_report(f"token = {_TOKEN_LONGO}")
    for i in range(0, len(_TOKEN_LONGO) - 6):
        assert _TOKEN_LONGO[i : i + 6] not in report


def test_security_report_nao_exibe_email_nem_ip():
    """PII (email, IP) também não pode aparecer no relatório."""
    report = get_security_report(f"contato {_EMAIL} host {_IP}")
    assert _EMAIL not in report
    assert "fulano" not in report
    assert _IP not in report


def test_security_report_mantem_tipo_e_contagem():
    """Sem valores, o relatório continua informando tipo e quantidade."""
    report = get_security_report(
        f'password = "{_SENHA_CURTA}"\npassword = "{_SENHA_CURTA}x"\n{_EMAIL}'
    )
    assert "password: 2 found" in report
    assert "email: 1 found" in report


def test_security_report_texto_limpo():
    """Texto sem secrets mantém a mensagem de OK."""
    assert get_security_report("texto comum sem nada sensível").startswith("✅")
