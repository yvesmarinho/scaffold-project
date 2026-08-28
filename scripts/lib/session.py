"""
lib/session.py — Módulo de auto-documentação incremental de sessões.

Parte do scripts/scaffold.py — Enterprise Scaffold Project Template.

Este módulo fornece funções para documentar atividades durante uma sessão de
desenvolvimento de forma incremental, estruturada e segura.

Componentes principais:
- ActivityBlock: dataclass para blocos de atividade estruturados
- generate_activity_block(): factory para criar blocos padronizados
- sanitize_block(): aplica redact patterns para remover dados sensíveis
- append_to_daily_activities(): adiciona bloco ao DAILY_ACTIVITIES de forma idempotente
- validate_daily_activities_format(): valida schema de documento de sessão
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums e Tipos
# ---------------------------------------------------------------------------


class ActivityStatus(Enum):
    """Status de uma atividade de sessão."""
    COMPLETE = "✅ Completo"
    IN_PROGRESS = "🔵 Em progresso"
    BLOCKED = "❌ Bloqueado"
    ON_HOLD = "⏸️ On hold"


# ---------------------------------------------------------------------------
# Redact Patterns — Sanitização de dados sensíveis
# ---------------------------------------------------------------------------

# Padrões de detecção de dados sensíveis (credenciais, IPs, tokens, etc.)
# Divididos em dois grupos: case-sensitive e case-insensitive

# Padrões case-sensitive (aplicados primeiro, prioridade para tokens específicos)
REDACT_PATTERNS_CASE_SENSITIVE = [
    # Tokens GitHub com contexto (GITHUB_TOKEN=, export, etc.)
    # IMPORTANTE: estes padrões DEVEM vir ANTES dos padrões standalone
    (r"GITHUB_TOKEN[\s]*=[\s]*['\"]?ghp_[a-zA-Z0-9]{36}['\"]?", "GITHUB_TOKEN=[GITHUB_TOKEN_REDACTED]"),
    (r"token[\s]*=[\s]*['\"]?github_pat_[a-zA-Z0-9_]{82}['\"]?", "token=[GITHUB_PAT_REDACTED]"),
    
    # Tokens GitHub standalone (para casos sem contexto de assignment)
    (r"ghp_[a-zA-Z0-9]{36}", "[GITHUB_TOKEN_REDACTED]"),
    (r"github_pat_[a-zA-Z0-9_]{82}", "[GITHUB_PAT_REDACTED]"),
    (r"gho_[a-zA-Z0-9]{36}", "[GITHUB_OAUTH_REDACTED]"),
    
    # OpenAI
    (r"sk-[a-zA-Z0-9]{48}", "[OPENAI_KEY_REDACTED]"),
    
    # Slack
    (r"xoxb-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24}", "[SLACK_BOT_TOKEN_REDACTED]"),
    (r"xoxp-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24}", "[SLACK_USER_TOKEN_REDACTED]"),
    
    # AWS
    (r"AKIA[0-9A-Z]{16}", "[AWS_ACCESS_KEY_REDACTED]"),
    
    # JWT Tokens
    (r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}", "[JWT_TOKEN_REDACTED]"),
]

# Padrões case-insensitive (aplicados depois)
REDACT_PATTERNS_CASE_INSENSITIVE = [
    # AWS Secret
    (r"aws_secret_access_key[\s]*=[\s]*[A-Za-z0-9/+=]{40}", "[AWS_SECRET_KEY_REDACTED]"),
    
    # Azure
    (r"DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[^;]+", "[AZURE_CONNECTION_STRING_REDACTED]"),
    
    # Google Cloud
    (r'"private_key":\s*"-----BEGIN PRIVATE KEY-----[^"]+-----END PRIVATE KEY-----"', '"private_key": "[GCP_PRIVATE_KEY_REDACTED]"'),
    
    # Senhas em URLs (esquema://user:password@host)
    (r"((?:https?|ftp|postgres|mysql|mongodb)://[^:@\s]+):([^@\s]+)@", r"\1:[PASSWORD_REDACTED]@"),
    
    # IPs privados (opcionalmente redactar)
    (r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[PRIVATE_IP_REDACTED]"),
    (r"\b172\.(1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3}\b", "[PRIVATE_IP_REDACTED]"),
    (r"\b192\.168\.\d{1,3}\.\d{1,3}\b", "[PRIVATE_IP_REDACTED]"),
    
    # Emails (opcionalmente preservar domínio)
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_REDACTED]"),
    
    # Padrões genéricos de senha/token/api_key/secret
    # Nota: aplicados por último para não interferir com padrões específicos
    # Usa negative lookbehind para evitar capturar tokens conhecidos (GITHUB_, github_pat_, etc.)
    # Usa negative lookahead (?!\[) para não capturar valores já redacted (ex: [GITHUB_TOKEN_REDACTED])
    (r"(?<!GITHUB_)(?<!github_pat_)password[\s]*=[\s]*['\"]?(?!\[)[^\s'\"]+", "password=[PASSWORD_REDACTED]"),
    (r"(?<!GITHUB_)(?<!github_pat_)token[\s]*=[\s]*['\"]?(?!\[)[^\s'\"]+", "token=[TOKEN_REDACTED]"),
    (r"api_key[\s]*=[\s]*['\"]?(?!\[)[^\s'\"]+", "api_key=[API_KEY_REDACTED]"),
    (r"secret[\s]*=[\s]*['\"]?(?!\[)[^\s'\"]+", "secret=[SECRET_REDACTED]"),
]


def sanitize_text(text: str) -> str:
    """
    Aplica todos os redact patterns no texto fornecido.
    
    Args:
        text: Texto a ser sanitizado
        
    Returns:
        Texto com dados sensíveis removidos/substituídos
    """
    sanitized = text
    
    # Aplicar patterns case-sensitive primeiro (prioridade)
    for pattern, replacement in REDACT_PATTERNS_CASE_SENSITIVE:
        sanitized = re.sub(pattern, replacement, sanitized)
    
    # Aplicar patterns case-insensitive depois
    for pattern, replacement in REDACT_PATTERNS_CASE_INSENSITIVE:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    return sanitized


# ---------------------------------------------------------------------------
# ActivityBlock — Dataclass
# ---------------------------------------------------------------------------


@dataclass
class ActivityBlock:
    """
    Representa um bloco de atividade estruturado para DAILY_ACTIVITIES.
    
    Attributes:
        title: Título conciso da atividade (ex: "IMP-47 Bug Fix")
        todo_id: ID do TODO relacionado (ex: "IMP-47", opcional)
        timestamp: Timestamp da atividade (formato HH:MM)
        objective: Descrição do objetivo da atividade
        context: Contexto/motivação da atividade
        steps: Lista de passos executados
        result: Resultado/outcome da atividade
        decisions: Decisões técnicas tomadas (opcional)
        files_modified: Lista de arquivos modificados/criados
        commits: Lista de commits (formato: "hash — mensagem")
        status: Status da atividade (ActivityStatus enum)
    """
    title: str
    timestamp: str
    objective: str
    context: str
    steps: list[str]
    result: str
    status: ActivityStatus
    todo_id: Optional[str] = None
    decisions: Optional[str] = None
    files_modified: list[str] = field(default_factory=list)
    commits: list[str] = field(default_factory=list)
    
    def to_markdown(self, sanitize: bool = True) -> str:
        """
        Converte o ActivityBlock para formato Markdown padronizado.
        
        Args:
            sanitize: Se True, aplica redact patterns no conteúdo
            
        Returns:
            String em Markdown formatada segundo o template padrão
        """
        # Construir cabeçalho
        header = f"### {self.title}"
        if self.todo_id:
            header = f"### {self.title} ({self.todo_id})"
        
        # Construir corpo
        lines = [
            "---",
            "",
            header,
            "",
            f"**{self.timestamp} — {self.status.value}**",
            "",
            f"**Objetivo**: {self.objective}",
            "",
            f"**Contexto**: {self.context}",
            "",
        ]
        
        # Adicionar passos executados
        if self.steps:
            lines.append("**Passos executados**:")
            for i, step in enumerate(self.steps, start=1):
                lines.append(f"{i}. {step}")
            lines.append("")
        
        # Adicionar resultado
        lines.append(f"**Resultado**: {self.result}")
        lines.append("")
        
        # Adicionar decisões (se houver)
        if self.decisions:
            lines.append(f"**Decisões técnicas**: {self.decisions}")
            lines.append("")
        
        # Adicionar arquivos modificados (se houver)
        if self.files_modified:
            lines.append("**Arquivos modificados/criados**:")
            for file_info in self.files_modified:
                lines.append(f"- {file_info}")
            lines.append("")
        
        # Adicionar commits (se houver)
        if self.commits:
            lines.append("**Commits**:")
            for commit in self.commits:
                lines.append(f"- `{commit}`")
            lines.append("")
        
        # Adicionar status final
        lines.append(f"**Status**: {self.status.value}")
        lines.append("")
        
        # Juntar todas as linhas
        markdown = "\n".join(lines)
        
        # Aplicar sanitização se solicitado
        if sanitize:
            markdown = sanitize_text(markdown)
        
        return markdown


# ---------------------------------------------------------------------------
# Factory Functions — Geração de blocos
# ---------------------------------------------------------------------------


def generate_activity_block(
    title: str,
    objective: str,
    context: str,
    steps: list[str],
    result: str,
    status: ActivityStatus = ActivityStatus.COMPLETE,
    todo_id: Optional[str] = None,
    decisions: Optional[str] = None,
    files_modified: Optional[list[str]] = None,
    commits: Optional[list[str]] = None,
    timestamp: Optional[str] = None,
) -> ActivityBlock:
    """
    Factory para criar um ActivityBlock com validações básicas.
    
    Args:
        title: Título da atividade
        objective: Objetivo da atividade
        context: Contexto da atividade
        steps: Lista de passos executados
        result: Resultado obtido
        status: Status da atividade (default: COMPLETE)
        todo_id: ID do TODO relacionado (opcional)
        decisions: Decisões técnicas (opcional)
        files_modified: Lista de arquivos modificados (opcional)
        commits: Lista de commits (opcional)
        timestamp: Timestamp HH:MM (default: agora)
        
    Returns:
        ActivityBlock configurado
        
    Raises:
        ValueError: Se campos obrigatórios estão vazios
    """
    # Validações
    if not title.strip():
        raise ValueError("'title' não pode estar vazio")
    if not objective.strip():
        raise ValueError("'objective' não pode estar vazio")
    if not context.strip():
        raise ValueError("'context' não pode estar vazio")
    if not steps:
        raise ValueError("'steps' não pode estar vazio")
    if not result.strip():
        raise ValueError("'result' não pode estar vazio")
    
    # Timestamp padrão: HH:MM atual
    if timestamp is None:
        timestamp = datetime.now().strftime("%H:%M")
    
    # Criar ActivityBlock
    return ActivityBlock(
        title=title,
        timestamp=timestamp,
        objective=objective,
        context=context,
        steps=steps,
        result=result,
        status=status,
        todo_id=todo_id,
        decisions=decisions,
        files_modified=files_modified or [],
        commits=commits or [],
    )


# ---------------------------------------------------------------------------
# Append Functions — Adicionar blocos a DAILY_ACTIVITIES
# ---------------------------------------------------------------------------


def append_to_daily_activities(
    block: ActivityBlock,
    session_dir: Path,
    sanitize: bool = True,
    dry_run: bool = False,
) -> bool:
    """
    Adiciona um ActivityBlock ao arquivo DAILY_ACTIVITIES da sessão.
    
    Esta função é idempotente: se o bloco já existe (detectado por título e
    timestamp), não será adicionado novamente.
    
    Args:
        block: ActivityBlock a ser adicionado
        session_dir: Diretório da sessão (ex: docs/SESSIONS/2026-03-29/)
        sanitize: Se True, aplica redact patterns antes de persistir
        dry_run: Se True, apenas simula sem escrever no arquivo
        
    Returns:
        True se o bloco foi adicionado, False se já existia ou erro
        
    Raises:
        FileNotFoundError: Se o diretório da sessão não existe
    """
    # Validar que session_dir existe
    if not session_dir.exists():
        raise FileNotFoundError(f"Diretório de sessão não encontrado: {session_dir}")
    
    # Encontrar arquivo DAILY_ACTIVITIES
    daily_activities_files = list(session_dir.glob("DAILY_ACTIVITIES_*.md"))
    
    if not daily_activities_files:
        log.error(f"Nenhum arquivo DAILY_ACTIVITIES encontrado em {session_dir}")
        return False
    
    if len(daily_activities_files) > 1:
        log.warning(f"Múltiplos arquivos DAILY_ACTIVITIES encontrados, usando o primeiro: {daily_activities_files[0].name}")
    
    daily_activities_file = daily_activities_files[0]
    
    # Ler conteúdo atual
    current_content = daily_activities_file.read_text(encoding="utf-8")
    
    # Verificar se bloco já existe (idempotência)
    block_signature = f"### {block.title}"
    if block.todo_id:
        block_signature = f"### {block.title} ({block.todo_id})"
    
    if block_signature in current_content:
        log.info(f"Bloco já existe em {daily_activities_file.name}: {block_signature}")
        return False
    
    # Gerar markdown do bloco
    block_markdown = block.to_markdown(sanitize=sanitize)
    
    # Dry run: apenas mostrar o que seria adicionado
    if dry_run:
        log.info(f"[DRY RUN] Bloco que seria adicionado a {daily_activities_file.name}:")
        log.info(block_markdown)
        return True
    
    # Adicionar bloco no final do arquivo
    with daily_activities_file.open("a", encoding="utf-8") as f:
        f.write("\n")
        f.write(block_markdown)
    
    log.info(f"✅ Bloco adicionado a {daily_activities_file.name}: {block_signature}")
    return True


# ---------------------------------------------------------------------------
# Validation Functions — Validação de formato
# ---------------------------------------------------------------------------


def validate_daily_activities_format(file_path: Path) -> tuple[bool, list[str]]:
    """
    Valida se um arquivo DAILY_ACTIVITIES segue o formato estruturado.
    
    Verifica:
    - Presença de cabeçalhos obrigatórios (# 📅 Daily Activities)
    - Formato de blocos de atividade (### [título], **Objetivo**, etc.)
    - Separadores (---) entre blocos
    
    Args:
        file_path: Caminho para o arquivo DAILY_ACTIVITIES
        
    Returns:
        Tupla (is_valid, errors) onde:
        - is_valid: True se o arquivo é válido
        - errors: Lista de mensagens de erro (vazia se válido)
    """
    if not file_path.exists():
        return False, [f"Arquivo não encontrado: {file_path}"]
    
    content = file_path.read_text(encoding="utf-8")
    errors = []
    
    # Verificar cabeçalho principal
    if not re.search(r"^# 📅 Daily Activities", content, re.MULTILINE):
        errors.append("Cabeçalho principal ausente: '# 📅 Daily Activities'")
    
    # Verificar estrutura de blocos
    # Cada bloco deve ter: ### [título], **Objetivo**, **Contexto**, **Resultado**, **Status**
    block_pattern = r"---\s+### .+?\s+\*\*\d{2}:\d{2}.+?\*\*Objetivo\*\*:.+?\*\*Contexto\*\*:.+?\*\*Resultado\*\*:.+?\*\*Status\*\*:"
    blocks_found = re.findall(block_pattern, content, re.DOTALL)
    
    # Se não encontrou nenhum bloco estruturado, mas há conteúdo após o cabeçalho
    # pode ser formato freeform (ainda aceito, mas deprecado)
    if len(blocks_found) == 0 and len(content) > 500:
        errors.append("Nenhum bloco estruturado encontrado (possível formato freeform deprecado)")
    
    # Verificar separadores
    separator_count = content.count("---")
    if separator_count < 2:  # Pelo menos um separador inicial + um por bloco
        errors.append(f"Poucos separadores encontrados ({separator_count}). Esperado pelo menos 2.")
    
    # Validação de Status
    valid_statuses = ["✅ Completo", "🔵 Em progresso", "❌ Bloqueado", "⏸️ On hold"]
    status_pattern = r"\*\*Status\*\*:\s*(.+?)(?:\n|$)"
    statuses = re.findall(status_pattern, content)
    
    for status in statuses:
        status_clean = status.strip()
        if status_clean not in valid_statuses:
            errors.append(f"Status inválido encontrado: '{status_clean}'")
    
    is_valid = len(errors) == 0
    return is_valid, errors


# ---------------------------------------------------------------------------
# Utility Functions — Funções auxiliares
# ---------------------------------------------------------------------------


def sanitize_block(block: ActivityBlock) -> ActivityBlock:
    """
    Aplica sanitização em todos os campos de um ActivityBlock.
    
    Args:
        block: ActivityBlock a ser sanitizado
        
    Returns:
        Novo ActivityBlock com dados sensíveis removidos
    """
    return ActivityBlock(
        title=sanitize_text(block.title),
        timestamp=block.timestamp,  # timestamp não precisa sanitizar
        objective=sanitize_text(block.objective),
        context=sanitize_text(block.context),
        steps=[sanitize_text(step) for step in block.steps],
        result=sanitize_text(block.result),
        status=block.status,
        todo_id=block.todo_id,  # todo_id não precisa sanitizar
        decisions=sanitize_text(block.decisions) if block.decisions else None,
        files_modified=[sanitize_text(f) for f in block.files_modified],
        commits=[sanitize_text(c) for c in block.commits],
    )


def get_session_dir_for_date(base_dir: Path, date: Optional[datetime] = None) -> Path:
    """
    Retorna o diretório de sessão para uma data específica.
    
    Args:
        base_dir: Diretório base (ex: docs/SESSIONS/)
        date: Data da sessão (default: hoje)
        
    Returns:
        Path para o diretório da sessão (ex: docs/SESSIONS/2026-03-29/)
    """
    if date is None:
        date = datetime.now()
    
    session_date = date.strftime("%Y-%m-%d")
    return base_dir / session_date
