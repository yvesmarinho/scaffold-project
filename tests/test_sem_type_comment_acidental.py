# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_sem_type_comment_acidental.py
TITULO: Nenhum comentário "# type: ..." acidental em scripts/ (quebra o mypy)
DATA: 24/11/2026 13:10
MODIFICADO: 24/11/2026 13:05
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

Bug: o comentário explicativo ``# type: subject`` em ``scripts/lib/git_validators.py``
é interpretado pelo mypy como *type comment* → "Invalid syntax", que aborta a
checagem de todo o pacote. Só ``# type: ignore[...]`` é permitido.
"""

from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
_TYPE_COMMENT = re.compile(r"^#\s*type:(?!\s*ignore\b)")


def _type_comments_acidentais(arquivo: Path) -> list[str]:
    achados: list[str] = []
    fonte = arquivo.read_text(encoding="utf-8")
    for tok in tokenize.generate_tokens(io.StringIO(fonte).readline):
        if tok.type == tokenize.COMMENT and _TYPE_COMMENT.match(tok.string):
            achados.append(
                f"{arquivo.relative_to(_SCRIPTS.parent)}:{tok.start[0]}: {tok.string}"
            )
    return achados


def test_detector_reconhece_o_padrao(tmp_path: Path) -> None:
    alvo = tmp_path / "x.py"
    alvo.write_text(
        "# type: subject\nx = 1  # type: ignore[assignment]\n", encoding="utf-8"
    )
    achados = [
        tok.string
        for tok in tokenize.generate_tokens(io.StringIO(alvo.read_text()).readline)
        if tok.type == tokenize.COMMENT and _TYPE_COMMENT.match(tok.string)
    ]
    assert achados == ["# type: subject"]


def test_scripts_sem_type_comment_acidental() -> None:
    achados = [
        a for f in sorted(_SCRIPTS.rglob("*.py")) for a in _type_comments_acidentais(f)
    ]
    assert not achados, "\n".join(achados)
