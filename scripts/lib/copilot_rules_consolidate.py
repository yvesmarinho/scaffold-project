"""
Copilot Rules Consolidation System

Sistema de consolidação automática de múltiplos arquivos .copilot-rules*.md
Resolve problema de duplicatas causadas por renomeação/migração de arquivos.

Bug fix: BUG-16 Fase 3 (Consolidação .copilot-rules)
Implementação: Sprint 2026-W21
"""

import logging
import re
import shutil
from pathlib import Path

log = logging.getLogger(__name__)


# =============================================================================
# Markdown Section Parser
# =============================================================================


def parse_markdown_sections(content: str) -> dict[str, str]:
    """
    Parsea documento Markdown em seções por headers (##).

    Args:
        content: Conteúdo Markdown

    Returns:
        Dict {título_seção: conteúdo_da_seção}

    Exemplos:
        >>> content = '''## Seção 1
        ... Conteúdo 1
        ... ## Seção 2
        ... Conteúdo 2'''
        >>> parse_markdown_sections(content)
        {'Seção 1': 'Conteúdo 1', 'Seção 2': 'Conteúdo 2'}
    """
    sections = {}
    current_section = None
    current_content: list[str] = []

    lines = content.split("\n")

    for line in lines:
        # Detectar header de seção (## Título)
        header_match = re.match(r"^##\s+(.+)$", line)

        if header_match:
            # Salvar seção anterior se existir
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()

            # Iniciar nova seção
            current_section = header_match.group(1).strip()
            current_content = []
        else:
            # Acumular conteúdo da seção
            if current_section:
                current_content.append(line)

    # Salvar última seção
    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def merge_markdown_sections(files: list[Path]) -> str:
    """
    Faz merge de múltiplos arquivos Markdown em um único documento.

    Estratégia:
    1. Parsear cada arquivo em seções (por headers ##)
    2. Detectar seções duplicadas (mesmo título)
    3. Para duplicatas: priorizar conteúdo do primeiro arquivo (user-wins)
    4. Preservar seções únicas de todos os arquivos
    5. Ordenar seções alfabeticamente (exceto cabeçalho)

    Args:
        files: Lista de arquivos Markdown a serem mergeados
               (primeiro arquivo tem prioridade)

    Returns:
        String com conteúdo Markdown consolidado
    """
    if not files:
        return ""

    # Coletar cabeçalhos (tudo antes do primeiro ##)
    headers = []
    all_sections: dict[str, tuple[str, int]] = (
        {}
    )  # título -> (conteúdo, prioridade_arquivo)

    for idx, file in enumerate(files):
        content = file.read_text(encoding="utf-8")

        # Extrair cabeçalho (tudo antes do primeiro ##)
        # Verificar se arquivo começa com ## (sem cabeçalho)
        if content.strip().startswith("##"):
            # Sem cabeçalho, todo conteúdo é seções
            sections_content = content
        else:
            # Procurar primeiro ## no meio do arquivo
            first_header_pos = content.find("\n##")
            if first_header_pos != -1:
                header = content[:first_header_pos].strip()
                if header:
                    headers.append((header, file.name))
                sections_content = content[first_header_pos + 1 :]
            else:
                # Arquivo sem seções, todo conteúdo é cabeçalho
                headers.append((content.strip(), file.name))
                continue

        # Parsear seções
        sections = parse_markdown_sections(sections_content)

        for title, section_content in sections.items():
            # Se seção já existe, priorizar do arquivo com menor índice (primeiro)
            if title not in all_sections:
                all_sections[title] = (section_content, idx)
                log.debug(f"  + Seção '{title}' de {file.name}")
            else:
                existing_priority = all_sections[title][1]
                if idx < existing_priority:
                    # Arquivo atual tem maior prioridade, substituir
                    all_sections[title] = (section_content, idx)
                    log.debug(f"  ↻ Seção '{title}' substituída por {file.name}")
                else:
                    log.debug(
                        f"  = Seção '{title}' preservada (de {files[existing_priority].name})"
                    )

    # Construir documento consolidado
    result_parts = []

    # 1. Cabeçalho (usar do primeiro arquivo que tem)
    if headers:
        primary_header = headers[0][0]
        result_parts.append(primary_header)
        result_parts.append("")  # Linha em branco

    # 2. Comentário de consolidação (sempre incluir quando múltiplos arquivos)
    if len(files) > 1:
        result_parts.append(
            f"<!-- Consolidado de {len(files)} arquivos: {', '.join(f.name for f in files)} -->"
        )
        result_parts.append("")

    # 3. Seções ordenadas alfabeticamente
    sorted_sections = sorted(all_sections.items(), key=lambda x: x[0].lower())

    for title, (content, _) in sorted_sections:
        result_parts.append(f"## {title}")
        result_parts.append("")
        result_parts.append(content)
        result_parts.append("")

    return "\n".join(result_parts)


# =============================================================================
# Consolidation Functions
# =============================================================================


def detect_copilot_rules_files(project_root: Path) -> list[Path]:
    """
    Detecta todos os arquivos .copilot-rules* na raiz do projeto.

    Padrões detectados:
    - .copilot-rules.md
    - .copilot-rules-*.md (específicos de projeto/domain/profile)
    - .copilot-strict-rules.md
    - .copilot-strict-enforcement.md
    - copilot-instructions.md
    - .copilot-instructions.md

    Args:
        project_root: Raiz do projeto

    Returns:
        Lista de arquivos encontrados (sorted)

    Nota: Symlinks são ignorados para preservar configurações de shared files (BUG-16).
    """
    patterns = [
        ".copilot-rules.md",
        ".copilot-rules-*.md",  # BUG-16: arquivos específicos de projeto
        ".copilot-strict-rules.md",
        ".copilot-strict-enforcement.md",
        "copilot-instructions.md",
        ".copilot-instructions.md",
    ]

    found_files = []

    for pattern in patterns:
        # Buscar apenas na raiz (não recursivo)
        matches = list(project_root.glob(pattern))
        # BUG-16 fix: filtrar symlinks para preservar .copilot-shared
        matches = [f for f in matches if not f.is_symlink()]
        found_files.extend(matches)

    # Remover duplicatas e ordenar
    unique_files = list(set(found_files))
    unique_files.sort(key=lambda f: f.name)

    return unique_files


def consolidate_copilot_rules(
    project_root: Path, backup_dir: Path | None = None
) -> Path | None:
    """
    Detecta e consolida múltiplos arquivos .copilot-rules* automaticamente.

    Processo:
    1. Detecta todos os arquivos .copilot-rules* na raiz
    2. Se 0 ou 1: retorna None/Path (não precisa consolidação)
    3. Se > 1:
       - Mergeia conteúdo (ordem: .copilot-rules.md primeiro, resto alfabético)
       - Preserva seções únicas de cada arquivo
       - Remove duplicatas de seções (priorizar primeiro arquivo)
       - Salva backup de cada arquivo original
       - Salva consolidado em .copilot-rules.md
       - Remove duplicatas

    Args:
        project_root: Raiz do projeto
        backup_dir: Diretório para backups (default: .backups/copilot-rules/)

    Returns:
        Path do arquivo consolidado (.copilot-rules.md) ou None se não havia arquivos
    """
    # Detectar arquivos
    found_files = detect_copilot_rules_files(project_root)

    if len(found_files) == 0:
        log.debug("Nenhum arquivo .copilot-rules* encontrado")
        return None

    if len(found_files) == 1:
        log.debug(f"Apenas 1 arquivo .copilot-rules* encontrado: {found_files[0].name}")
        return found_files[0]

    # Múltiplos arquivos - consolidar
    log.info(f"🔄 Consolidando {len(found_files)} arquivos de regras Copilot:")
    for f in found_files:
        log.info(f"   • {f.name}")

    # Preparar backup directory
    if backup_dir is None:
        backup_dir = project_root / ".backups" / "copilot-rules"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Priorizar .copilot-rules.md como base
    primary = project_root / ".copilot-rules.md"
    others = sorted([f for f in found_files if f != primary])

    files_to_merge = []
    if primary.exists():
        files_to_merge.append(primary)
    files_to_merge.extend(others)

    # Fazer backup de todos
    log.info("📦 Criando backups:")
    for file in found_files:
        backup_path = backup_dir / file.name
        shutil.copy2(file, backup_path)
        log.info(f"   ✓ {file.name} → {backup_path}")

    # Merge de conteúdo
    log.info("🔀 Mergeando seções...")
    consolidated_content = merge_markdown_sections(files_to_merge)

    # Salvar consolidado
    output_file = project_root / ".copilot-rules.md"
    output_file.write_text(consolidated_content, encoding="utf-8")
    log.info(f"✅ Consolidado em: {output_file.name}")

    # Remover duplicatas (manter apenas consolidado)
    removed_count = 0
    for file in found_files:
        if file != output_file:
            file.unlink()
            log.info(f"🗑️  Removido: {file.name}")
            removed_count += 1

    log.info(
        f"✨ Consolidação completa: {len(found_files)} arquivos → 1 arquivo ({removed_count} removidos)"
    )

    return output_file


def validate_consolidation_needed(project_root: Path) -> tuple[bool, list[Path]]:
    """
    Verifica se consolidação de .copilot-rules* é necessária.

    Args:
        project_root: Raiz do projeto

    Returns:
        (needs_consolidation, files_found)
    """
    files = detect_copilot_rules_files(project_root)
    needs_consolidation = len(files) > 1

    return needs_consolidation, files
