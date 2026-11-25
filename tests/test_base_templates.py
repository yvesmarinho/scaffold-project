"""
Testes — ADR-003 fatia 3: strings de ``project.py`` extraídas para
``scaffold/templates/base/*.tmpl`` e placeholder único ``{{NOME}}``.

Contrato:
- ``load_base_template(nome)`` devolve os bytes do arquivo **sem alteração**
  (sem tradução de quebra de linha, preservando ausência de newline final);
- nome vazio, absoluto, com ``..`` ou fora do padrão → ``InvalidTemplateNameError``;
- template ausente → ``TemplateNotFoundError`` (subclasse de ``FileNotFoundError``);
- ``render(texto, valores)`` substitui só ``{{CHAVE}}`` conhecidas; ``${{ x }}``
  (GitHub Actions) e chaves desconhecidas ficam intactas; valor não-str → erro.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib import base_templates
from scripts.lib.base_templates import (
    BASE_TEMPLATES_DIR,
    InvalidTemplateNameError,
    TemplateNotFoundError,
    load_base_template,
    render,
)

_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# load_base_template — falhas
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    ["", "   ", "/etc/passwd", "../README.md", "docs/../../x.tmpl", "a\\b.tmpl", "x"],
)
def test_nome_invalido_levanta_excecao_semantica(name):
    with pytest.raises(InvalidTemplateNameError):
        load_base_template(name)


def test_nome_nao_str_levanta_excecao_semantica():
    with pytest.raises(InvalidTemplateNameError):
        load_base_template(None)  # type: ignore[arg-type]


def test_template_ausente_levanta_not_found():
    with pytest.raises(TemplateNotFoundError) as exc:
        load_base_template("nao-existe.md.tmpl")
    assert isinstance(exc.value, FileNotFoundError)
    assert "nao-existe.md.tmpl" in str(exc.value)


def test_diretorio_indisponivel_levanta_not_found(monkeypatch, tmp_path):
    monkeypatch.setattr(base_templates, "BASE_TEMPLATES_DIR", tmp_path / "sumiu")
    base_templates.load_base_template.cache_clear()
    try:
        with pytest.raises(TemplateNotFoundError):
            load_base_template("README.md.tmpl")
    finally:
        base_templates.load_base_template.cache_clear()


# ---------------------------------------------------------------------------
# load_base_template — bytes preservados
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        b"sem newline final",
        b"linha\n\n",
        b"crlf\r\nfica\r\n",
        "acentuação ✅\n".encode(),
    ],
)
def test_conteudo_preservado_byte_a_byte(monkeypatch, tmp_path, raw):
    (tmp_path / "x.md.tmpl").write_bytes(raw)
    monkeypatch.setattr(base_templates, "BASE_TEMPLATES_DIR", tmp_path)
    base_templates.load_base_template.cache_clear()
    try:
        assert load_base_template("x.md.tmpl").encode("utf-8") == raw
    finally:
        base_templates.load_base_template.cache_clear()


def test_todos_os_templates_mapeados_existem():
    missing = [
        name
        for name in base_templates.TEMPLATE_FILES.values()
        if not (BASE_TEMPLATES_DIR / name).is_file()
    ]
    assert missing == []


def test_nenhum_template_orfao_no_diretorio():
    mapped = set(base_templates.TEMPLATE_FILES.values())
    on_disk = {
        p.relative_to(BASE_TEMPLATES_DIR).as_posix()
        for p in BASE_TEMPLATES_DIR.rglob("*.tmpl")
    }
    assert on_disk == mapped


def test_templates_nao_ficam_em_pastas_com_ponto():
    """Pastas com ponto (.secrets/, .memory/) podem ser ignoradas pelo git."""
    offenders = [n for n in base_templates.TEMPLATE_FILES.values() if "/." in f"/{n}"]
    assert offenders == []


# ---------------------------------------------------------------------------
# render — placeholder único
# ---------------------------------------------------------------------------


def test_render_substitui_chaves_conhecidas():
    assert render("Olá {{NOME}}, {{NOME}}!", {"NOME": "Ana"}) == "Olá Ana, Ana!"


def test_render_preserva_github_actions_e_chaves_desconhecidas():
    text = "a: ${{ github.sha }} b: {{OUTRA}} c: {{NOME}}"
    assert render(text, {"NOME": "x"}) == "a: ${{ github.sha }} b: {{OUTRA}} c: x"


def test_render_valor_vazio_e_valido():
    assert render("[{{SECAO}}]", {"SECAO": ""}) == "[]"


@pytest.mark.parametrize("bad", [{"NOME": None}, {"NOME": 1}, {"": "x"}, {"nome": "x"}])
def test_render_rejeita_valores_ou_chaves_invalidas(bad):
    with pytest.raises(ValueError):
        render("{{NOME}}", bad)


def test_render_nao_reprocessa_valor_substituido():
    """Valor contendo outro placeholder não é expandido de novo (determinismo)."""
    out = render("{{A}} {{B}}", {"A": "{{B}}", "B": "b"})
    assert out == "{{B}} b"


# ---------------------------------------------------------------------------
# project.py usa os templates
# ---------------------------------------------------------------------------


def test_project_nao_tem_mais_strings_longas_de_template():
    src = (_ROOT / "scripts" / "lib" / "project.py").read_text(encoding="utf-8")
    assert '_README_MD = """' not in src
    assert '_PRE_COMMIT_SECRETS_HOOK = r"""' not in src
    assert "@OWNER" not in src
    assert "{profiles_section}" not in src


def test_constantes_publicas_continuam_disponiveis():
    from scripts.lib import project

    for const, name in base_templates.TEMPLATE_FILES.items():
        assert getattr(project, const) == load_base_template(name), const


def test_nenhum_template_ignorado_pelo_git():
    """.gitignore do repo (secrets/, logs/) não pode esconder templates do publish."""
    import shutil
    import subprocess

    git = shutil.which("git")
    if git is None:
        pytest.skip("git indisponível")
    files = [
        str((BASE_TEMPLATES_DIR / n).relative_to(_ROOT))
        for n in base_templates.TEMPLATE_FILES.values()
    ]
    result = subprocess.run(
        [git, "check-ignore", "--no-index", *files],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.split() == []
