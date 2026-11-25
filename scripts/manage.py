#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "textual>=0.80",
#   "rich>=13.7",
#   "pyyaml>=6.0",
# ]
# ///
"""
Enterprise Ansible Manager — TUI
Gerenciador interativo para operações de infraestrutura VPS / SSH SPA / ZTA.

Uso:
    uv run manage.py          # recomendado
    python manage.py          # com venv ativado
    make manage               # via Makefile
"""

from __future__ import annotations

import argparse
import json
import logging
import logging.handlers
import os
import shlex
import shutil
import subprocess
import sys
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Any

import yaml
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Select,
    Static,
    Tree,
)

# Caminho absoluto do git (S607/B607); "git" como fallback fora do PATH.
_GIT = shutil.which("git") or "git"

# ─────────────────────────────────────────────────────────────────────────────
# Project root (directory where this script lives)
# ─────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.resolve()

# ─────────────────────────────────────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────────────────────────────────────
LOG_FILE = ROOT / "logs" / "manage.log"


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configure file logging. Always writes errors; --debug writes everything."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if debug else logging.WARNING

    handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Capture unhandled exceptions
    def _excepthook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        root_logger.critical(
            "Unhandled exception:\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )

    sys.excepthook = _excepthook
    return logging.getLogger("manage")


logger = logging.getLogger("manage")
VAULT_PASS = ROOT / ".secrets" / ".vault_pass"
INVENTORY = "inventories/hosts.yml"
ANSIBLE_PLAYBOOK = "ansible-playbook"

ALL_SPA_HOSTS = [
    ("wf001", "31.220.103.208"),
    ("wf002", "154.53.49.110"),
    ("wf008", "151.242.149.22"),
    ("wfdb01", "86.48.31.149"),
    ("wfdb02", "82.197.64.145"),
    ("wfdb03", "154.53.36.3"),
]

# ─────────────────────────────────────────────────────────────────────────────
# Menu data model
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class MenuInput:
    name: str
    hint: str
    optional: bool = True
    default: str = ""


@dataclass
class MenuItem:
    id: str
    title: str
    description: str
    command: str = ""
    inputs: list[MenuInput] = field(default_factory=list)
    requires_file: str = ""
    generator_id: str = ""  # key into FILE_GENERATORS
    dangerous: bool = False
    dry_run_flag: str = "--check --diff"
    tags: list[str] = field(default_factory=list)


@dataclass
class Category:
    id: str
    icon: str
    title: str
    items: list[MenuItem] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# MENU DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────


def _ap(playbook: str, extra: str = "") -> str:
    """Build ansible-playbook command with vault."""
    base = f"{ANSIBLE_PLAYBOOK} -i {INVENTORY} {playbook} --vault-password-file .secrets/.vault_pass"
    if extra:
        base += f" {extra}"
    return base


MENU: list[Category] = [
    Category(
        id="setup",
        icon="📦",
        title="Setup & Instalação",
        items=[
            MenuItem(
                id="venv",
                title="Criar ambiente virtual",
                description=(
                    "Cria o ambiente virtual Python com UV.\n\n"
                    "Cria o diretório .venv/ no projeto com Python 3.12+.\n"
                    "Necessário antes de instalar dependências."
                ),
                command="uv venv",
            ),
            MenuItem(
                id="install",
                title="Instalar dependências",
                description=(
                    "Instala as dependências Python do projeto via UV\n"
                    "e as collections Ansible necessárias:\n"
                    "  • community.general\n"
                    "  • ansible.posix\n\n"
                    "Arquivo: requirements.txt"
                ),
                command=(
                    "uv pip install -r requirements.txt && "
                    "ansible-galaxy collection install community.general ansible.posix"
                ),
            ),
            MenuItem(
                id="setup-full",
                title="Setup completo",
                description=(
                    "Executa venv + install em sequência.\n"
                    "Use na primeira vez ou após um clone do repositório."
                ),
                command="uv venv && uv pip install -r requirements.txt && "
                "ansible-galaxy collection install community.general ansible.posix",
            ),
            MenuItem(
                id="lint",
                title="Lint (YAML + Ansible)",
                description=(
                    "Valida todos os arquivos YAML e playbooks Ansible:\n"
                    "  • yamllint — regras de formatação YAML\n"
                    "  • ansible-lint — boas práticas Ansible\n\n"
                    "Configuração: .yamllint.yml / .ansible-lint"
                ),
                command="yamllint . && ansible-lint",
            ),
            MenuItem(
                id="syntax-check",
                title="Syntax check playbooks",
                description="Verifica sintaxe de todos os playbooks em playbooks/*.yml.",
                command=(
                    "for p in playbooks/*.yml; do "
                    'echo "  ✓ $p" && '
                    f'{ANSIBLE_PLAYBOOK} "$p" --syntax-check || exit 1; '
                    "done && echo 'Todos OK'"
                ),
            ),
        ],
    ),
    Category(
        id="inventory",
        icon="🖥️",
        title="Inventário & Hosts",
        items=[
            MenuItem(
                id="hosts-graph",
                title="Ver grafo do inventário",
                description=(
                    "Exibe a estrutura hierárquica completa do inventário.\n\n"
                    "Mostra grupos, subgrupos e hosts com suas relações.\n"
                    "Arquivo: inventories/hosts.yml\n\n"
                    "Comando: ansible-inventory --graph"
                ),
                command=f"ansible-inventory -i {INVENTORY} --graph",
            ),
            MenuItem(
                id="hosts-list-all",
                title="Listar todos os hosts",
                description=(
                    "Lista todos os hosts do inventário (um por linha).\n\n"
                    "Arquivo: inventories/hosts.yml\n\n"
                    "Comando: ansible-inventory --list-hosts all"
                ),
                command=f"ansible-inventory -i {INVENTORY} --list-hosts all",
            ),
            MenuItem(
                id="hosts-vars",
                title="Ver variáveis dos hosts (JSON)",
                description=(
                    "Exibe todas as variáveis de todos os hosts em formato JSON.\n"
                    "Útil para verificar se as vars de grupo estão corretas.\n\n"
                    "Arquivo: inventories/hosts.yml\n\n"
                    "Comando: ansible-inventory --list"
                ),
                command=f"ansible-inventory -i {INVENTORY} --list",
            ),
            MenuItem(
                id="hosts-ping-all",
                title="Ping todos os hosts",
                description=(
                    "Executa o módulo ping Ansible em todos os hosts.\n\n"
                    "⚠️  Servidores com SPA ativo precisam de knock antes.\n"
                    "Requer SSH configurado e porta 5010 acessível.\n\n"
                    "Comando: ansible all -m ping"
                ),
                command=(
                    f"ansible all -i {INVENTORY} -m ping "
                    "--vault-password-file .secrets/.vault_pass"
                ),
            ),
            MenuItem(
                id="gen-hosts-add",
                title="✏️  Adicionar host ao inventário",
                description=(
                    "Abre formulário para adicionar um novo servidor a\n"
                    "inventories/hosts.yml.\n\n"
                    "Campos:\n"
                    "  • Nome do host  (ex: wf010)\n"
                    "  • IP / ansible_host\n"
                    "  • Grupo alvo   (all_spa, vps_new, etc.)\n"
                    "  • Hostname FQDN\n"
                    "  • Node name\n\n"
                    "Nota: comentários inline do arquivo original são\n"
                    "preservados no cabeçalho; o restante é re-gerado."
                ),
                command="",
                generator_id="hosts-yml-add",
            ),
            MenuItem(
                id="gen-hosts-remove",
                title="🗑️  Remover host do inventário",
                description=(
                    "Abre seletor para remover um host existente de\n"
                    "inventories/hosts.yml.\n\n"
                    "⚠️  A remoção é permanente.\n"
                    "Os dados do host serão apagados do grupo\n"
                    "no qual ele está cadastrado."
                ),
                command="",
                generator_id="hosts-yml-remove",
                dangerous=True,
            ),
        ],
    ),
    Category(
        id="vps",
        icon="🚀",
        title="VPS Deploy",
        items=[
            MenuItem(
                id="vps-setup-check",
                title="VPS Setup — Dry-run",
                description=(
                    "Verifica o que o playbook de setup inicial faria\n"
                    "sem aplicar nenhuma mudança (--check --diff).\n\n"
                    "Grupo alvo: production\n"
                    "Playbook: playbooks/vps-initial-setup.yml"
                ),
                command=_ap(
                    "playbooks/vps-initial-setup.yml",
                    "--limit production --check --diff",
                ),
            ),
            MenuItem(
                id="vps-setup",
                title="VPS Setup — Aplicar",
                description=(
                    "Executa a configuração inicial completa dos servidores:\n"
                    "  • Usuários e sudo\n"
                    "  • Hardening SSH (porta 5010)\n"
                    "  • UFW firewall\n"
                    "  • Logging\n\n"
                    "Grupo alvo: production"
                ),
                command=_ap("playbooks/vps-initial-setup.yml", "--limit production"),
                dangerous=True,
            ),
            MenuItem(
                id="vps-setup-prod",
                title="VPS Setup — PRODUÇÃO",
                description=(
                    "⚠️  ATENÇÃO: Executa em servidores de produção.\n\n"
                    "Solicita confirmação antes de prosseguir.\n"
                    "Grupo alvo: production"
                ),
                command=_ap("playbooks/vps-initial-setup.yml", "--limit production"),
                dangerous=True,
            ),
            MenuItem(
                id="site-deploy",
                title="Site First Deploy",
                description=(
                    "Primeiro deploy completo do site.\n"
                    "Playbook: playbooks/site-first-deploy.yml"
                ),
                command=_ap("playbooks/site-first-deploy.yml", "--limit production"),
                dangerous=True,
            ),
            MenuItem(
                id="vps-security",
                title="VPS Security Hardening",
                description=(
                    "Aplica apenas o hardening de segurança:\n"
                    "  • Configuração SSH\n"
                    "  • UFW rules\n"
                    "  • Fail2ban (se habilitado)\n\n"
                    "Playbook: playbooks/vps-security.yml"
                ),
                command=_ap("playbooks/vps-security.yml"),
            ),
        ],
    ),
    Category(
        id="ssh-spa",
        icon="🔐",
        title="SSH SPA (fwknop)",
        items=[
            MenuItem(
                id="ssh-spa-deploy-check",
                title="Deploy SPA — Dry-run",
                description=(
                    "Simula o deploy do fwknop SPA em todos os 6 servidores.\n\n"
                    "Servidores: wf001, wf002, wf008, wfdb01, wfdb02, wfdb03\n"
                    "Grupo: all_spa\n"
                    "Playbook: playbooks/ssh-spa-deploy.yml\n\n"
                    "Não aplica nenhuma mudança (--check --diff)."
                ),
                command=_ap("playbooks/ssh-spa-deploy.yml", "--check --diff"),
            ),
            MenuItem(
                id="ssh-spa-deploy",
                title="Deploy SPA — Aplicar",
                description=(
                    "Deploy completo do fwknop SPA em todos os 6 servidores:\n"
                    "  • Instala fwknop-server\n"
                    "  • Configura /etc/fwknop/access.conf (ENC_KEY + HMAC_KEY)\n"
                    "  • Fecha porta 5010/tcp (UFW deny)\n"
                    "  • Habilita knock na porta 62201/udp\n\n"
                    "Requer: group_vars/all_spa/vault.yml (Ansible Vault)"
                ),
                command=_ap("playbooks/ssh-spa-deploy.yml"),
                inputs=[
                    MenuInput(
                        "HOST", "Limitar a um servidor (ex: wf001)", optional=True
                    )
                ],
            ),
            MenuItem(
                id="ssh-spa-fix-ufw",
                title="Fix UFW — Remover allow residual",
                description=(
                    "Remove a regra 'allow 5010/tcp' residual criada pelo\n"
                    "job de rollback do at (bug corrigido).\n\n"
                    "Aplique se a porta 5010 estiver acessível sem knock.\n"
                    "Playbook: playbooks/fix-ufw-spa-allow-rule.yml\n\n"
                    "✅ Executado com sucesso em: wf008, wfdb01"
                ),
                command=_ap("playbooks/fix-ufw-spa-allow-rule.yml"),
            ),
            MenuItem(
                id="spa-check-security",
                title="Verificar segurança (sem knock)",
                description=(
                    "Testa que a porta 5010/tcp está FECHADA em todos os\n"
                    "servidores sem knock SPA.\n\n"
                    "12 testes esperados: PASS\n"
                    "Script: scripts/test_ports.py\n"
                    "Cenário: tests/port-checks/ssh-spa-no-knock.json\n\n"
                    "Resultado esperado: 5010/tcp = CLOSED em todos"
                ),
                command="python scripts/test_ports.py tests/port-checks/ssh-spa-no-knock.json --parallel --timeout 5",
            ),
            MenuItem(
                id="spa-check-access",
                title="Verificar acesso (após knock)",
                description=(
                    "Testa que a porta 5010/tcp está ABERTA após knock SPA.\n"
                    "⚠️  Execute APÓS 'Enviar Knock' (janela de 30s).\n\n"
                    "Script: scripts/test_ports.py\n"
                    "Cenário: tests/port-checks/ssh-spa-after-knock.json"
                ),
                command="python scripts/test_ports.py tests/port-checks/ssh-spa-after-knock.json --parallel --timeout 5",
            ),
            MenuItem(
                id="spa-client-linux",
                title="Gerar pacote cliente Linux",
                description=(
                    "Gera client-packages/dist/spa-client-linux-YYYYMMDD.tar.gz\n\n"
                    "Conteúdo:\n"
                    "  • install.sh  — instala fwknop, configura ~/.fwknoprc\n"
                    "  • spa-ssh     — knock + wait + ssh em um comando\n"
                    "  • docs/MANUAL.md\n"
                    "  • fwknoprc.template"
                ),
                command=(
                    "chmod +x client-packages/spa-client/linux/install.sh "
                    "client-packages/spa-client/linux/spa-ssh && "
                    "mkdir -p client-packages/dist && "
                    "tar -czf client-packages/dist/spa-client-linux-$(date +%Y%m%d).tar.gz "
                    "-C client-packages spa-client/README.md spa-client/keys.secret.example "
                    "spa-client/docs spa-client/linux && "
                    "echo '✅ Pacote gerado em client-packages/dist/'"
                ),
            ),
            MenuItem(
                id="spa-client-windows",
                title="Gerar pacote cliente Windows",
                description=(
                    "Gera client-packages/dist/spa-client-windows-YYYYMMDD.zip\n\n"
                    "Conteúdo:\n"
                    "  • Install-SPA.ps1  — instala fwknop, configura .fwknoprc\n"
                    "  • spa-ssh.ps1      — knock + TCP wait + ssh (PowerShell)\n"
                    "  • docs/MANUAL.md\n"
                    "  • fwknoprc.template"
                ),
                command=(
                    "mkdir -p client-packages/dist && "
                    "cd client-packages && "
                    "zip -r dist/spa-client-windows-$(date +%Y%m%d).zip "
                    "spa-client/README.md spa-client/keys.secret.example "
                    "spa-client/docs spa-client/windows && "
                    "echo '✅ Pacote gerado em client-packages/dist/'"
                ),
            ),
        ],
    ),
    Category(
        id="ssh-keys",
        icon="🔑",
        title="SSH Keys",
        items=[
            MenuItem(
                id="ssh-keys-deploy-check",
                title="Publicar Chaves — Dry-run",
                description=(
                    "Simula a publicação de chaves SSH sem aplicar mudanças.\n\n"
                    "Lê usuários de: data/ssh-users.json\n"
                    "Playbook: playbooks/ssh-keys-deploy.yml\n"
                    "Grupo alvo: all_spa\n\n"
                    "Valida:\n"
                    "  • Chaves não são placeholder\n"
                    "  • AllowUsers correto\n"
                    "  • Blocos Match User"
                ),
                command=_ap("playbooks/ssh-keys-deploy.yml", "--check --diff"),
                requires_file="data/ssh-users.json",
                generator_id="ssh-users-json",
            ),
            MenuItem(
                id="ssh-keys-deploy",
                title="Publicar Chaves — Aplicar",
                description=(
                    "Publica chaves SSH e configura sshd_config:\n"
                    "  1. Pre-knock SPA (se fwknop disponível)\n"
                    "  2. Valida chaves (recusa placeholders)\n"
                    "  3. Cria usuários conforme JSON\n"
                    "  4. Deploy authorized_keys (0600)\n"
                    "  5. Configura sshd: PubkeyAuth yes, PasswordAuth no\n"
                    "  6. Atualiza AllowUsers (preserva existentes)\n"
                    "  7. Adiciona blocos Match User\n"
                    "  8. Valida sshd -t + reinicia sshd\n\n"
                    "Fonte: data/ssh-users.json"
                ),
                command=_ap("playbooks/ssh-keys-deploy.yml"),
                inputs=[
                    MenuInput(
                        "HOST", "Limitar a um servidor (ex: wf008)", optional=True
                    )
                ],
                requires_file="data/ssh-users.json",
                generator_id="ssh-users-json",
            ),
            MenuItem(
                id="gen-ssh-users",
                title="✏️  Gerar data/ssh-users.json",
                description=(
                    "Abre formulário para criar/editar data/ssh-users.json.\n\n"
                    "O arquivo define:\n"
                    "  • Usuários SSH (nome, shell, grupos)\n"
                    "  • Chaves públicas autorizadas\n"
                    "  • Política de autenticação por usuário\n"
                    "  • Servidores alvo\n\n"
                    "⚠️  Substitua os placeholders pelas chaves reais!"
                ),
                command="",  # handled by generator_id
                generator_id="ssh-users-json",
                requires_file="",
            ),
        ],
    ),
    Category(
        id="zta",
        icon="☁️",
        title="Cloudflare ZTA",
        items=[
            MenuItem(
                id="zta-status",
                title="Status do deploy ZTA",
                description=(
                    "Exibe o status atual do deploy Cloudflare Zero Trust Access.\n"
                    "Script: scripts/zta-deploy-facilitator.sh status"
                ),
                command="./scripts/zta-deploy-facilitator.sh status",
            ),
            MenuItem(
                id="zta-check-cert",
                title="Verificar cert.pem",
                description="Verifica se cert.pem está disponível no servidor.",
                command="./scripts/zta-deploy-facilitator.sh check-cert",
            ),
            MenuItem(
                id="zta-cert-download",
                title="Download cert.pem (API)",
                description=(
                    "Baixa cert.pem da Cloudflare API via Python.\n"
                    "Credenciais via Ansible Vault (seguro).\n"
                    "Script: scripts/download-zta-cert.py"
                ),
                command="python scripts/download-zta-cert.py",
            ),
            MenuItem(
                id="zta-cert-deploy",
                title="Deploy cert.pem",
                description=(
                    "Faz deploy do cert.pem nos servidores ZTA.\n"
                    "Playbook: cloudflare/zero-trust/playbooks/zta-cert-pem-deploy.yml\n"
                    "Inventário: inventories/cloudflare-zta-hosts.yml"
                ),
                command=(
                    f"{ANSIBLE_PLAYBOOK} cloudflare/zero-trust/playbooks/zta-cert-pem-deploy.yml "
                    "-i inventories/cloudflare-zta-hosts.yml --vault-password-file .secrets/.vault_pass"
                ),
            ),
            MenuItem(
                id="zta-phase6",
                title="Fase 6 — DNS",
                description=(
                    "Executa Fase 6: Configuração DNS (CNAME records).\n"
                    "Script: scripts/zta-deploy-facilitator.sh phase6"
                ),
                command="./scripts/zta-deploy-facilitator.sh phase6",
            ),
            MenuItem(
                id="zta-phase7",
                title="Fase 7 — Validação",
                description=(
                    "Executa Fase 7: Validação e testes do ZTA.\n"
                    "Script: scripts/zta-deploy-facilitator.sh phase7"
                ),
                command="./scripts/zta-deploy-facilitator.sh phase7",
            ),
            MenuItem(
                id="zta-deploy",
                title="Deploy completo (fases 6+7)",
                description=(
                    "Executa Fases 6 e 7 em sequência.\n"
                    "Script: scripts/zta-deploy-facilitator.sh full"
                ),
                command="./scripts/zta-deploy-facilitator.sh full",
                dangerous=True,
            ),
        ],
    ),
    Category(
        id="vpn",
        icon="🌐",
        title="Cloudflare VPN",
        items=[
            MenuItem(
                id="vpn-server-check",
                title="Deploy WARP Connector — Dry-run",
                description=(
                    "Simula o deploy do Cloudflare WARP Connector no wfdb03.\n"
                    "Playbook: playbooks/cloudflare-vpn-server-deploy.yml"
                ),
                command=_ap(
                    "playbooks/cloudflare-vpn-server-deploy.yml", "--check --diff"
                ),
            ),
            MenuItem(
                id="vpn-server-deploy",
                title="Deploy WARP Connector",
                description=(
                    "Instala cloudflared no wfdb03 como WARP Connector\n"
                    "(modo private network — não roteamento full).\n\n"
                    "Host alvo: wfdb03 (154.53.36.3)\n"
                    "Playbook: playbooks/cloudflare-vpn-server-deploy.yml"
                ),
                command=_ap("playbooks/cloudflare-vpn-server-deploy.yml"),
                dangerous=True,
            ),
            MenuItem(
                id="vpn-configure",
                title="Configurar Access Group",
                description=(
                    "Atualiza emails autorizados no Cloudflare Access Group.\n"
                    "Playbook: playbooks/cloudflare-vpn-configure.yml"
                ),
                command=_ap("playbooks/cloudflare-vpn-configure.yml"),
            ),
            MenuItem(
                id="vpn-validate",
                title="Validar conectividade VPN",
                description=(
                    "Testa conectividade e regressão no servidor VPN.\n"
                    "Playbook: playbooks/cloudflare-vpn-validate.yml"
                ),
                command=_ap("playbooks/cloudflare-vpn-validate.yml"),
            ),
            MenuItem(
                id="vpn-client-deploy",
                title="Instalar WARP client (local)",
                description=(
                    "Instala o Cloudflare WARP client nesta máquina.\n"
                    "Playbook: playbooks/cloudflare-vpn-client-deploy.yml\n"
                    "Alvo: localhost"
                ),
                command=_ap("playbooks/cloudflare-vpn-client-deploy.yml"),
            ),
            MenuItem(
                id="vpn-rollback",
                title="⚠️  Rollback WARP Connector",
                description=(
                    "DESTRUTIVO: Remove cloudflared do wfdb03 e\n"
                    "limpa recursos na Cloudflare API.\n\n"
                    "Playbook: playbooks/cloudflare-vpn-rollback.yml"
                ),
                command=_ap("playbooks/cloudflare-vpn-rollback.yml"),
                dangerous=True,
            ),
        ],
    ),
    Category(
        id="messaging",
        icon="📨",
        title="Messaging Stack",
        items=[
            MenuItem(
                id="messaging-deploy",
                title="Deploy RabbitMQ + Redis",
                description=(
                    "Deploy completo do stack de mensageria via Helm:\n"
                    "  • RabbitMQ 3.12+ (quorum queues)\n"
                    "  • Redis 7.2+ (Sentinel HA, RDB+AOF)\n\n"
                    "Playbook: playbooks/messaging-deploy.yml\n"
                    "Grupo: production"
                ),
                command=_ap("playbooks/messaging-deploy.yml", "--limit production"),
                dangerous=True,
            ),
            MenuItem(
                id="messaging-rabbitmq",
                title="Deploy só RabbitMQ",
                description=(
                    "Deploy isolado do RabbitMQ cluster.\n"
                    "Playbook: playbooks/messaging-rabbitmq-deploy.yml"
                ),
                command=_ap(
                    "playbooks/messaging-rabbitmq-deploy.yml", "--limit production"
                ),
            ),
            MenuItem(
                id="messaging-redis",
                title="Deploy só Redis + Sentinel",
                description=(
                    "Deploy isolado do Redis com Sentinel HA.\n"
                    "Persistência híbrida (RDB + AOF).\n"
                    "Playbook: playbooks/messaging-redis-deploy.yml"
                ),
                command=_ap(
                    "playbooks/messaging-redis-deploy.yml", "--limit production"
                ),
            ),
            MenuItem(
                id="messaging-validate",
                title="Validar stack de mensageria",
                description="Testa conectividade e saúde do RabbitMQ e Redis.",
                command=_ap("playbooks/messaging-validate.yml", "--limit production"),
            ),
            MenuItem(
                id="messaging-destroy",
                title="⚠️  Remover stack mensageria",
                description=(
                    "DESTRUTIVO: Remove RabbitMQ e Redis.\n"
                    "Playbook: playbooks/messaging-destroy.yml"
                ),
                command=_ap("playbooks/messaging-destroy.yml", "--limit production"),
                dangerous=True,
            ),
        ],
    ),
    Category(
        id="firewall",
        icon="🔥",
        title="Firewall",
        items=[
            MenuItem(
                id="firewall-fix",
                title="Correção emergencial UFW",
                description=(
                    "Aplica correção emergencial no firewall UFW.\n"
                    "Playbook: playbooks/emergency-fix-firewall.yml"
                ),
                command=_ap("playbooks/emergency-fix-firewall.yml"),
            ),
            MenuItem(
                id="firewall-whitelist",
                title="Atualizar whitelist de IPs",
                description=(
                    "Atualiza a whitelist de IPs permitidos no UFW.\n"
                    "Playbook: playbooks/update-firewall-whitelist.yml"
                ),
                command=_ap("playbooks/update-firewall-whitelist.yml"),
            ),
            MenuItem(
                id="firewall-fix-vpn",
                title="Corrigir whitelist VPN",
                description=(
                    "Corrige a whitelist para IPs da VPN Cloudflare.\n"
                    "Playbook: playbooks/fix-vpn-ip-whitelist.yml"
                ),
                command=_ap("playbooks/fix-vpn-ip-whitelist.yml"),
            ),
        ],
    ),
    Category(
        id="testing",
        icon="🧪",
        title="Testes & Validação",
        items=[
            MenuItem(
                id="test-connectivity",
                title="Testar conectividade SSH",
                description=(
                    "Testa conectividade SSH (porta 5010) em todos os servidores.\n"
                    "Playbook: playbooks/test-connectivity.yml"
                ),
                command=_ap("playbooks/test-connectivity.yml"),
            ),
            MenuItem(
                id="test-ssh",
                title="Testar SSH porta 5010",
                description=(
                    "Teste específico de SSH na porta 5010.\n"
                    "Playbook: playbooks/test-ssh-5010.yml"
                ),
                command=_ap("playbooks/test-ssh-5010.yml"),
            ),
            MenuItem(
                id="validate-deployment",
                title="Validar deployment completo",
                description=(
                    "Validação completa do deployment:\n"
                    "  • SSH\n  • Firewall\n  • Serviços\n  • Segurança\n\n"
                    "Playbook: playbooks/validate-deployment.yml"
                ),
                command=_ap("playbooks/validate-deployment.yml"),
            ),
            MenuItem(
                id="validate-hostname",
                title="Validar hostnames",
                description="Verifica configuração de hostname nos servidores.",
                command=_ap("playbooks/validate-hostname.yml"),
            ),
        ],
    ),
    Category(
        id="vault",
        icon="🗝️",
        title="Ansible Vault",
        items=[
            MenuItem(
                id="vault-encrypt",
                title="Encriptar arquivo",
                description=(
                    "Encripta um arquivo com Ansible Vault.\n\n"
                    "Uso: especifique o caminho do arquivo no campo abaixo.\n"
                    "Ex: group_vars/all_spa/vault.yml"
                ),
                command="ansible-vault encrypt {FILE}",
                inputs=[
                    MenuInput("FILE", "Caminho do arquivo a encriptar", optional=False)
                ],
            ),
            MenuItem(
                id="vault-decrypt",
                title="Desencriptar arquivo",
                description="Desencripta um arquivo Ansible Vault.",
                command="ansible-vault decrypt {FILE}",
                inputs=[
                    MenuInput(
                        "FILE", "Caminho do arquivo a desencriptar", optional=False
                    )
                ],
            ),
            MenuItem(
                id="vault-edit",
                title="Editar arquivo vault",
                description=(
                    "Abre o editor configurado em $EDITOR para editar\n"
                    "um arquivo Ansible Vault.\n\n"
                    "Arquivos vault do projeto:\n"
                    "  • group_vars/all_spa/vault.yml   (SPA keys)\n"
                    "  • group_vars/cf_vpn_servers/vault.yml  (VPN keys)"
                ),
                command="ansible-vault edit {FILE}",
                inputs=[MenuInput("FILE", "Caminho do arquivo vault", optional=False)],
            ),
            MenuItem(
                id="vault-view",
                title="Visualizar arquivo vault",
                description="Exibe o conteúdo desencriptado de um arquivo Vault.",
                command="ansible-vault view {FILE} --vault-password-file .secrets/.vault_pass",
                inputs=[MenuInput("FILE", "Caminho do arquivo vault", optional=False)],
            ),
            MenuItem(
                id="gen-vault-pass",
                title="✏️  Criar .secrets/.vault_pass",
                description=(
                    "Cria o arquivo .secrets/.vault_pass com a senha\n"
                    "do Ansible Vault.\n\n"
                    "⚠️  Nunca comite este arquivo no git!\n"
                    "O .gitignore já o exclui."
                ),
                command="",
                generator_id="vault-pass",
            ),
        ],
    ),
    Category(
        id="utils",
        icon="🛠️",
        title="Utilitários",
        items=[
            MenuItem(
                id="git-status",
                title="Git status",
                description="Exibe status do repositório e últimos 5 commits.",
                command="git status -sb && echo '' && git log --oneline -5",
            ),
            MenuItem(
                id="list-playbooks",
                title="Listar playbooks",
                description="Lista todos os playbooks disponíveis em playbooks/*.yml.",
                command="ls -1 playbooks/*.yml | sed 's|playbooks/||' | sort",
            ),
            MenuItem(
                id="clean",
                title="Limpar cache",
                description=(
                    "Remove arquivos temporários e cache:\n"
                    "  • __pycache__\n  • *.pyc\n  • *.retry\n  • .pytest_cache"
                ),
                command=(
                    "find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true; "
                    "find . -type f -name '*.pyc' -delete; "
                    "find . -type f -name '*.retry' -delete; "
                    "echo '✅ Cache limpo'"
                ),
            ),
            MenuItem(
                id="fix-keyboard",
                title="Corrigir layout teclado",
                description=(
                    "Corrige o layout de teclado nos servidores.\n"
                    "Playbook: playbooks/fix-keyboard-layout.yml"
                ),
                command=_ap("playbooks/fix-keyboard-layout.yml"),
            ),
            MenuItem(
                id="hostname-fix",
                title="Configurar hostname pós-hardening",
                description=(
                    "Configura o hostname correto após o hardening.\n"
                    "Playbook: playbooks/configure-hostname-post-hardening.yml"
                ),
                command=_ap("playbooks/configure-hostname-post-hardening.yml"),
            ),
        ],
    ),
]

# Build a flat index for quick lookup
MENU_INDEX: dict[str, MenuItem] = {item.id: item for cat in MENU for item in cat.items}

# ─────────────────────────────────────────────────────────────────────────────
# File Generators
# ─────────────────────────────────────────────────────────────────────────────


def generate_ssh_users_json(data: dict[str, Any]) -> str:
    """Build data/ssh-users.json from form data."""
    users = []
    n = int(data.get("user_count", 1))
    for i in range(1, n + 1):
        name = data.get(f"user{i}_name", "").strip()
        if not name:
            continue
        keys_raw = data.get(f"user{i}_keys", "").strip()
        ssh_keys = [k.strip() for k in keys_raw.splitlines() if k.strip()]
        users.append(
            {
                "name": name,
                "comment": data.get(f"user{i}_comment", name),
                "state": data.get(f"user{i}_state", "present"),
                "shell": data.get(f"user{i}_shell", "/bin/bash"),
                "groups": [
                    g.strip()
                    for g in data.get(f"user{i}_groups", "sudo").split(",")
                    if g.strip()
                ],
                "password_auth": data.get(f"user{i}_password_auth", "false").lower()
                == "true",
                "pubkey_auth": True,
                "ssh_keys": (
                    ssh_keys
                    if ssh_keys
                    else [f"ssh-ed25519 AAAA_SUBSTITUA_CHAVE_{name.upper()}"]
                ),
                "servers": "all",
            }
        )
    manifest = {
        "_comment": "Manifesto de usuários SSH gerenciado por enterprise-ansible/manage.py",
        "_instructions": [
            "1. Substitua ssh_keys pelos valores reais de chave pública.",
            "2. Execute: make ssh-keys-deploy",
        ],
        "users": users,
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False)


def generate_vault_pass(data: dict[str, Any]) -> str:
    """Just the password string."""
    password: str = data.get("password", "")
    return password


FILE_GENERATORS: dict[str, Callable[[dict], str]] = {
    "ssh-users-json": generate_ssh_users_json,
    "vault-pass": generate_vault_pass,
}

FILE_GENERATOR_PATHS: dict[str, str] = {
    "ssh-users-json": "data/ssh-users.json",
    "vault-pass": ".secrets/.vault_pass",
}

# ─────────────────────────────────────────────────────────────────────────────
# Modal Screens
# ─────────────────────────────────────────────────────────────────────────────


class ConfirmModal(ModalScreen[bool]):
    """Simple yes/no confirmation."""

    CSS = """
    ConfirmModal {
        align: center middle;
    }
    #dialog {
        background: $surface;
        border: thick $warning;
        padding: 2 4;
        width: 60;
        height: auto;
    }
    #dialog Label {
        margin-bottom: 1;
        text-align: center;
        width: 100%;
    }
    #buttons {
        height: 3;
        align: center middle;
        margin-top: 1;
    }
    #btn-yes { margin-right: 2; background: $error; }
    #btn-no  { background: $success; }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("⚠️  AÇÃO DESTRUTIVA / PRODUÇÃO", id="title")
            yield Static(self.message)
            with Horizontal(id="buttons"):
                yield Button("✅ Confirmar", id="btn-yes", variant="error")
                yield Button("❌ Cancelar", id="btn-no", variant="success")

    @on(Button.Pressed, "#btn-yes")
    def confirm(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#btn-no")
    def cancel(self) -> None:
        self.dismiss(False)


class InputModal(ModalScreen[dict[str, str]]):
    """Collect runtime inputs (HOST=, FILE=, etc.)."""

    CSS = """
    InputModal {
        align: center middle;
    }
    #dialog {
        background: $surface;
        border: thick $accent;
        padding: 2 4;
        width: 70;
        height: auto;
        max-height: 30;
    }
    #dialog Label { margin-top: 1; }
    .hint { color: $text-muted; font-size: 85%; }
    #buttons { height: 3; align: center middle; margin-top: 1; }
    """

    def __init__(self, inputs: list[MenuInput]) -> None:
        super().__init__()
        self.inputs = inputs
        self._widgets: dict[str, Input] = {}

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("📝 Parâmetros adicionais")
            for inp in self.inputs:
                label = f"{inp.name}" + (
                    "  (opcional)" if inp.optional else "  *obrigatório*"
                )
                yield Label(label)
                widget = Input(
                    placeholder=inp.hint, value=inp.default, id=f"inp_{inp.name}"
                )
                self._widgets[inp.name] = widget
                yield widget
                yield Static(f"  {inp.hint}", classes="hint")
            with Horizontal(id="buttons"):
                yield Button("▶ Executar", id="btn-ok", variant="primary")
                yield Button("✖ Cancelar", id="btn-cancel")

    @on(Button.Pressed, "#btn-ok")
    def submit(self) -> None:
        result = {}
        for inp in self.inputs:
            widget = self.query_one(f"#inp_{inp.name}", Input)
            result[inp.name] = widget.value.strip()
        self.dismiss(result)

    @on(Button.Pressed, "#btn-cancel")
    def cancel(self) -> None:
        self.dismiss({})


class SSHUsersGeneratorModal(ModalScreen[dict[str, str] | None]):
    """Form to generate data/ssh-users.json."""

    CSS = """
    SSHUsersGeneratorModal {
        align: center middle;
    }
    #dialog {
        background: $surface;
        border: thick $success;
        padding: 2 3;
        width: 80;
        height: 38;
    }
    #title { text-align: center; color: $success; margin-bottom: 1; }
    #scroll { height: 28; border: solid $panel; padding: 0 1; }
    Label { margin-top: 1; color: $text-muted; }
    Input { margin-bottom: 0; }
    #buttons { height: 3; align: center middle; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("✏️  Gerador — data/ssh-users.json", id="title")
            with ScrollableContainer(id="scroll"):
                yield Label("─── Usuário 1 ───────────────────────────────")
                yield Label("Nome do usuário *")
                yield Input(placeholder="archaris", id="user1_name")
                yield Label("Comentário")
                yield Input(placeholder="Operador principal", id="user1_comment")
                yield Label("Shell")
                yield Input(
                    placeholder="/bin/bash", value="/bin/bash", id="user1_shell"
                )
                yield Label("Grupos (vírgula)")
                yield Input(placeholder="sudo", value="sudo", id="user1_groups")
                yield Label("Estado")
                yield Input(placeholder="present", value="present", id="user1_state")
                yield Label("Permitir senha? (true/false)")
                yield Input(
                    placeholder="false", value="false", id="user1_password_auth"
                )
                yield Label("Chaves SSH públicas (uma por linha) *")
                yield Input(
                    placeholder="ssh-ed25519 AAAA... usuario@host",
                    id="user1_keys",
                )
                yield Label("")
                yield Label("─── Usuário 2 (opcional) ───────────────────")
                yield Label("Nome do usuário")
                yield Input(
                    placeholder="archyros (deixe vazio para ignorar)", id="user2_name"
                )
                yield Label("Comentário")
                yield Input(placeholder="Administrador secundário", id="user2_comment")
                yield Label("Shell")
                yield Input(
                    placeholder="/bin/bash", value="/bin/bash", id="user2_shell"
                )
                yield Label("Grupos (vírgula)")
                yield Input(placeholder="sudo", value="sudo", id="user2_groups")
                yield Label("Estado")
                yield Input(placeholder="present", value="present", id="user2_state")
                yield Label("Permitir senha? (true/false)")
                yield Input(placeholder="true", value="true", id="user2_password_auth")
                yield Label("Chaves SSH públicas (uma por linha)")
                yield Input(placeholder="ssh-ed25519 AAAA...", id="user2_keys")
            with Horizontal(id="buttons"):
                yield Button("💾 Gerar arquivo", id="btn-save", variant="success")
                yield Button("✖ Cancelar", id="btn-cancel")

    def _collect(self) -> dict[str, str]:
        fields = [
            "user1_name",
            "user1_comment",
            "user1_shell",
            "user1_groups",
            "user1_state",
            "user1_password_auth",
            "user1_keys",
            "user2_name",
            "user2_comment",
            "user2_shell",
            "user2_groups",
            "user2_state",
            "user2_password_auth",
            "user2_keys",
        ]
        data: dict[str, str] = {"user_count": "2"}
        for f in fields:
            try:
                data[f] = self.query_one(f"#{f}", Input).value
            except Exception:
                data[f] = ""
        return data

    @on(Button.Pressed, "#btn-save")
    def save(self) -> None:
        self.dismiss(self._collect())

    @on(Button.Pressed, "#btn-cancel")
    def cancel(self) -> None:
        self.dismiss(None)


class VaultPassGeneratorModal(ModalScreen[str | None]):
    """Form to create .secrets/.vault_pass."""

    CSS = """
    VaultPassGeneratorModal {
        align: center middle;
    }
    #dialog {
        background: $surface;
        border: thick $warning;
        padding: 2 4;
        width: 60;
        height: auto;
    }
    #title { text-align: center; color: $warning; margin-bottom: 1; }
    Label { margin-top: 1; }
    #buttons { height: 3; align: center middle; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("✏️  Criar .secrets/.vault_pass", id="title")
            yield Static(
                "Este arquivo contém a senha usada para encriptar/desencriptar\n"
                "arquivos Ansible Vault do projeto.\n\n"
                "⚠️  Nunca comite este arquivo no git!"
            )
            yield Label("Senha do Vault *")
            yield Input(placeholder="senha-do-vault", password=True, id="password")
            yield Label("Confirmar senha *")
            yield Input(placeholder="repita a senha", password=True, id="password2")
            with Horizontal(id="buttons"):
                yield Button("💾 Criar arquivo", id="btn-save", variant="warning")
                yield Button("✖ Cancelar", id="btn-cancel")

    @on(Button.Pressed, "#btn-save")
    def save(self) -> None:
        pw1 = self.query_one("#password", Input).value
        pw2 = self.query_one("#password2", Input).value
        if pw1 != pw2:
            self.notify("❌ Senhas não conferem!", severity="error")
            return
        if not pw1:
            self.notify("❌ Senha não pode ser vazia!", severity="error")
            return
        self.dismiss(pw1)

    @on(Button.Pressed, "#btn-cancel")
    def cancel(self) -> None:
        self.dismiss(None)


class HostsGeneratorModal(ModalScreen[dict[str, str] | None]):
    """Form to add a new host to inventories/hosts.yml."""

    GROUPS = [
        ("all_spa", "all_spa — SSH SPA (fwknop, porta 5010)"),
        ("vps_new", "vps_new — Novo servidor (porta 22, root)"),
        ("vps_fresh_setup", "vps_fresh_setup — Setup inicial (porta 22)"),
        ("vps_hardened", "vps_hardened — Servidor endurecido (porta 5010)"),
        ("cf_vpn_servers", "cf_vpn_servers — WARP Connector (Cloudflare VPN)"),
    ]

    CSS = """
    HostsGeneratorModal {
        align: center middle;
    }
    #dialog {
        background: $surface;
        border: thick $success;
        padding: 2 4;
        width: 72;
        height: auto;
        max-height: 38;
    }
    #title { text-align: center; color: $success; margin-bottom: 1; }
    #hint  { color: $text-muted; margin-bottom: 1; }
    Label  { margin-top: 1; color: $text-muted; }
    Select { margin-bottom: 0; }
    #buttons { height: 3; align: center middle; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("🖥️  Adicionar Host ao Inventário", id="title")
            yield Static(
                "Preencha os campos abaixo. O host será inserido em\n"
                "inventories/hosts.yml no grupo selecionado.",
                id="hint",
            )
            yield Label("Nome do host  *  (id Ansible, ex: wf010)")
            yield Input(placeholder="wf010", id="host_name")
            yield Label("IP (ansible_host)  *")
            yield Input(placeholder="1.2.3.4", id="host_ip")
            yield Label("Grupo alvo  *")
            yield Select(
                options=[(label, value) for value, label in self.GROUPS],
                id="host_group",
                prompt="Selecione o grupo...",
            )
            yield Label("Hostname FQDN  (deixe vazio para auto: <nome>.vya.digital)")
            yield Input(placeholder="wf010.vya.digital", id="host_fqdn")
            yield Label("Node name  (deixe vazio para auto: igual ao nome do host)")
            yield Input(placeholder="wf010", id="host_node")
            with Horizontal(id="buttons"):
                yield Button(
                    "💾 Adicionar ao hosts.yml", id="btn-save", variant="success"
                )
                yield Button("✖ Cancelar", id="btn-cancel")

    @on(Button.Pressed, "#btn-save")
    def save(self) -> None:
        name = self.query_one("#host_name", Input).value.strip()
        ip = self.query_one("#host_ip", Input).value.strip()
        group_sel = self.query_one("#host_group", Select)
        group = group_sel.value

        if not name:
            self.notify("❌ Nome do host é obrigatório!", severity="error")
            return
        if not ip:
            self.notify("❌ IP (ansible_host) é obrigatório!", severity="error")
            return
        if group is Select.BLANK:
            self.notify("❌ Selecione um grupo!", severity="error")
            return

        fqdn = (
            self.query_one("#host_fqdn", Input).value.strip() or f"{name}.vya.digital"
        )
        node = self.query_one("#host_node", Input).value.strip() or name
        self.dismiss(
            {
                "name": name,
                "ip": ip,
                "group": str(group),
                "fqdn": fqdn,
                "node": node,
            }
        )

    @on(Button.Pressed, "#btn-cancel")
    def cancel(self) -> None:
        self.dismiss(None)


class HostsRemoveModal(ModalScreen[dict[str, str] | None]):
    """Form to remove a host from inventories/hosts.yml."""

    CSS = """
    HostsRemoveModal {
        align: center middle;
    }
    #dialog {
        background: $surface;
        border: thick $error;
        padding: 2 4;
        width: 72;
        height: auto;
        max-height: 28;
    }
    #title { text-align: center; color: $error; margin-bottom: 1; }
    Label  { margin-top: 1; color: $text-muted; }
    Select { margin-bottom: 0; }
    #buttons { height: 3; align: center middle; margin-top: 1; }
    """

    def __init__(self) -> None:
        super().__init__()
        # Load hosts from yaml at construction time (sync, fast)
        self._hosts_by_group: dict[str, list[str]] = {}
        try:
            hosts_file = ROOT / "inventories" / "hosts.yml"
            data = yaml.safe_load(hosts_file.read_text())
            children = data.get("all", {}).get("children", {})
            for grp, grp_data in children.items():
                hosts = (grp_data or {}).get("hosts") or {}
                if hosts:
                    self._hosts_by_group[grp] = list(hosts.keys())
        except Exception as exc:
            # inventário ausente/ilegível: TUI segue sem lista de hosts (como antes)
            logger.debug("hosts.yml não carregado: %s", exc)

    def compose(self) -> ComposeResult:
        # Build flat SelectOption list: "hostname  (grupo)"
        options: list[tuple[str, str]] = []
        for grp, names in self._hosts_by_group.items():
            for h in names:
                options.append((f"{h}  ({grp})", f"{h}|{grp}"))

        with Vertical(id="dialog"):
            yield Label("🗑️  Remover Host do Inventário", id="title")
            yield Static(
                "⚠️  O host será removido permanentemente de inventories/hosts.yml.\n"
                "Confirme o host que deseja excluir:"
            )
            yield Label("Host a remover  *")
            if options:
                yield Select(
                    options=options, id="host_select", prompt="Selecione o host..."
                )
            else:
                yield Static("[yellow]Nenhum host encontrado no inventário.[/yellow]")
            with Horizontal(id="buttons"):
                yield Button("🗑️  Remover", id="btn-save", variant="error")
                yield Button("✖ Cancelar", id="btn-cancel")

    @on(Button.Pressed, "#btn-save")
    def save(self) -> None:
        try:
            sel = self.query_one("#host_select", Select)
        except Exception:
            self.notify("❌ Nenhum host disponível para remover.", severity="error")
            return
        value = sel.value
        if value is Select.BLANK:
            self.notify("❌ Selecione um host!", severity="error")
            return
        name, group = str(value).split("|", 1)
        self.dismiss({"name": name, "group": group})

    @on(Button.Pressed, "#btn-cancel")
    def cancel(self) -> None:
        self.dismiss(None)


# ─────────────────────────────────────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────────────────────────────────────

APP_CSS = """
Screen {
    background: #0d1117;
}

Header {
    background: #1a1a2e;
    color: #58a6ff;
    height: 1;
}

Footer {
    background: #161b22;
    color: #8b949e;
}

#main-layout {
    height: 1fr;
}

/* ── Nav panel ─────────────────────────────────────────────── */
#nav-panel {
    width: 32;
    background: #161b22;
    border-right: solid #30363d;
    padding: 0 1;
}

#nav-title {
    background: #1f2937;
    color: #58a6ff;
    text-align: center;
    padding: 0 1;
    height: 2;
    content-align: center middle;
}

Tree {
    background: #161b22;
    padding: 0;
    scrollbar-gutter: stable;
}

Tree > .tree--cursor {
    background: #1f6feb;
    color: white;
}

Tree > .tree--highlight {
    background: #21262d;
}

/* ── Content panel ─────────────────────────────────────────── */
#content-panel {
    width: 1fr;
    padding: 0;
}

#info-panel {
    height: 1fr;
    border-bottom: solid #30363d;
    padding: 1 2;
    overflow-y: auto;
}

#item-title {
    color: #58a6ff;
    text-style: bold;
    margin-bottom: 1;
    border-bottom: solid #21262d;
    padding-bottom: 1;
}

#item-description {
    color: #c9d1d9;
    margin-bottom: 1;
}

#item-meta {
    color: #8b949e;
    margin-bottom: 1;
}

#file-status {
    margin-bottom: 1;
}

#actions-bar {
    height: 3;
    background: #161b22;
    border-top: solid #30363d;
    padding: 0 2;
    align: left middle;
}

#actions-bar Button {
    margin-right: 1;
    min-width: 16;
}

Button.-primary  { background: #1f6feb; }
Button.-warning  { background: #9e6a03; }
Button.-success  { background: #276749; }
Button.-error    { background: #b91c1c; }
Button.-disabled { opacity: 50%; }

/* ── Output panel ───────────────────────────────────────────── */
#output-panel {
    height: 14;
    background: #0d1117;
    border-top: solid #21262d;
}

#output-title {
    height: 1;
    background: #21262d;
    color: #8b949e;
    padding: 0 2;
}

RichLog {
    background: #0d1117;
    padding: 0 2;
    scrollbar-gutter: stable;
}

/* ── Welcome ────────────────────────────────────────────────── */
#welcome {
    padding: 2 4;
    color: #8b949e;
    text-align: center;
    height: 1fr;
}
"""


class EnterpriseAnsibleApp(App[None]):
    """Enterprise Ansible TUI Manager."""

    TITLE = "Enterprise Ansible Manager"
    CSS = APP_CSS
    BINDINGS = [
        Binding("q", "quit", "Sair"),
        Binding("r", "run_item", "Executar", show=True),
        Binding("d", "dry_run", "Dry-run", show=True),
        Binding("g", "generate_file", "Gerar arquivo", show=True),
        Binding("c", "clear_output", "Limpar output"),
        Binding("ctrl+l", "clear_output", "Limpar", show=False),
    ]

    def handle_exception(self, error: Exception) -> None:
        """Capture all Textual-internal exceptions and write to log file."""
        logger.exception("Textual unhandled exception: %s", error)
        super().handle_exception(error)

    def __init__(self) -> None:
        super().__init__()
        self._current_item: MenuItem | None = None
        self._running = False

    # ── Composition ──────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            # Left: navigation tree
            with Vertical(id="nav-panel"):
                yield Static("  ⚙  Navigation", id="nav-title")
                yield self._build_tree()
            # Right: content + output
            with Vertical(id="content-panel"):
                with ScrollableContainer(id="info-panel"):
                    yield Static(self._welcome_text(), id="welcome")
                with Horizontal(id="actions-bar"):
                    yield Button("▶ Executar [r]", id="btn-run", variant="primary")
                    yield Button("🔍 Dry-run [d]", id="btn-dry", variant="warning")
                    yield Button(
                        "✏️  Gerar arquivo [g]", id="btn-gen", variant="success"
                    )
                with Vertical(id="output-panel"):
                    yield Static(" 📋 Output", id="output-title")
                    yield RichLog(highlight=True, markup=True, id="output-log")
        yield Footer()

    def _build_tree(self) -> Tree:
        tree: Tree = Tree("📁 Projeto", id="nav-tree")
        tree.root.expand()
        for cat in MENU:
            branch = tree.root.add(f"{cat.icon} {cat.title}", data={"type": "category"})
            for item in cat.items:
                branch.add_leaf(item.title, data={"type": "item", "id": item.id})
        return tree

    def _welcome_text(self) -> str:
        branch = self._git_branch()
        hosts = "  ".join(
            f"[cyan]{h}[/cyan] [dim]{ip}[/dim]" for h, ip in ALL_SPA_HOSTS
        )
        return (
            f"\n\n"
            f"[bold #58a6ff]Enterprise Ansible Manager[/bold #58a6ff]\n\n"
            f"[dim]Branch:[/dim] [yellow]{branch}[/yellow]\n"
            f"[dim]Root:[/dim]   [dim]{ROOT}[/dim]\n"
            f"[dim]Vault:[/dim]  {'[green]✓ .secrets/.vault_pass[/green]' if VAULT_PASS.exists() else '[red]✗ .secrets/.vault_pass (ausente)[/red]'}\n\n"
            f"[dim]Servidores all_spa:[/dim]\n{hosts}\n\n"
            f"[dim]Navegue pela árvore à esquerda para selecionar uma operação.\n"
            f"Use as teclas [bold]r[/bold] / [bold]d[/bold] / [bold]g[/bold] ou os botões abaixo.[/dim]"
        )

    @staticmethod
    def _git_branch() -> str:
        try:
            result = subprocess.run(
                [_GIT, "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=ROOT,
                timeout=3,
            )
            return result.stdout.strip() or "desconhecida"
        except Exception:
            return "desconhecida"

    # ── Tree selection ────────────────────────────────────────────────────────

    @on(Tree.NodeSelected)
    async def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        node_data = event.node.data
        if not node_data or node_data.get("type") != "item":
            return
        item_id = node_data["id"]
        item = MENU_INDEX.get(item_id)
        if item:
            self._current_item = item
            await self._refresh_info(item)

    async def _refresh_info(self, item: MenuItem) -> None:
        panel = self.query_one("#info-panel", ScrollableContainer)
        await panel.remove_children()

        # Title
        danger_badge = " [bold red]⚠ DESTRUTIVO[/bold red]" if item.dangerous else ""
        await panel.mount(
            Static(
                f"[bold #58a6ff]{item.title}[/bold #58a6ff]{danger_badge}",
                id="item-title",
            )
        )

        # Description
        await panel.mount(Static(item.description, id="item-description"))

        # Command preview
        if item.command:
            cmd_display = item.command.replace(
                "--vault-password-file .secrets/.vault_pass", "[dim]--vault-pass[/dim]"
            )
            await panel.mount(
                Static(
                    f"[dim]🔧 Comando:[/dim]\n[green]{cmd_display}[/green]",
                    id="item-meta",
                )
            )

        # File status
        if item.requires_file:
            fpath = ROOT / item.requires_file
            if fpath.exists():
                status = f"[green]✅ {item.requires_file} — existe[/green]"
            else:
                status = f"[red]⚠️  {item.requires_file} — NÃO EXISTE (use 'Gerar arquivo')[/red]"
            await panel.mount(Static(status, id="file-status"))

        # Inputs hint
        if item.inputs:
            hints = "\n".join(
                f"  [yellow]{i.name}[/yellow] — {i.hint}{'  [dim](opcional)[/dim]' if i.optional else '  [red]*obrigatório[/red]'}"
                for i in item.inputs
            )
            await panel.mount(Static(f"[dim]📝 Parâmetros:[/dim]\n{hints}"))

        # Button visibility
        self.query_one("#btn-run", Button).disabled = (
            not item.command and not item.generator_id
        )
        self.query_one("#btn-dry", Button).disabled = (
            not item.command or not item.dry_run_flag
        )
        self.query_one("#btn-gen", Button).disabled = not item.generator_id
        self.query_one("#btn-gen", Button).display = bool(item.generator_id)

    # ── Actions ───────────────────────────────────────────────────────────────

    @on(Button.Pressed, "#btn-run")
    def handle_run(self) -> None:
        self.action_run_item()

    @on(Button.Pressed, "#btn-dry")
    def handle_dry(self) -> None:
        self.action_dry_run()

    @on(Button.Pressed, "#btn-gen")
    def handle_gen(self) -> None:
        self.action_generate_file()

    @work(exclusive=True)
    async def action_run_item(self) -> None:
        item = self._current_item
        if not item:
            return
        if item.generator_id and not item.command:
            self.action_generate_file()
            return
        if not item.command:
            return
        if item.requires_file and not (ROOT / item.requires_file).exists():
            self.notify(
                f"⚠️  Arquivo obrigatório não encontrado: {item.requires_file}\n"
                "Use 'Gerar arquivo' primeiro.",
                severity="warning",
                timeout=5,
            )
            return
        await self._run_with_inputs(item, dry_run=False)

    @work(exclusive=True)
    async def action_dry_run(self) -> None:
        item = self._current_item
        if not item or not item.command:
            return
        await self._run_with_inputs(item, dry_run=True)

    @work(exclusive=True)
    async def action_generate_file(self) -> None:
        item = self._current_item
        if not item or not item.generator_id:
            return
        gen_id = item.generator_id
        if gen_id == "ssh-users-json":
            data = await self.push_screen_wait(SSHUsersGeneratorModal())
            if data is None:
                return
            content = generate_ssh_users_json(data)
            await self._save_generated_file("data/ssh-users.json", content)
        elif gen_id == "vault-pass":
            password = await self.push_screen_wait(VaultPassGeneratorModal())
            if password is None:
                return
            await self._save_generated_file(".secrets/.vault_pass", password)
        elif gen_id == "hosts-yml-add":
            data = await self.push_screen_wait(HostsGeneratorModal())
            if data is None:
                return
            await self._add_host_to_inventory(data)
        elif gen_id == "hosts-yml-remove":
            if self._current_item and self._current_item.dangerous:
                confirmed = await self.push_screen_wait(
                    ConfirmModal("Remover host permanentemente do inventário?")
                )
                if not confirmed:
                    return
            data = await self.push_screen_wait(HostsRemoveModal())
            if data is None:
                return
            await self._remove_host_from_inventory(data)

    def action_clear_output(self) -> None:
        self.query_one("#output-log", RichLog).clear()

    # ── Run pipeline ─────────────────────────────────────────────────────────

    async def _run_with_inputs(self, item: MenuItem, dry_run: bool) -> None:
        """Collect optional inputs, confirm if dangerous, then run."""
        input_values: dict[str, str] = {}
        required_inputs = item.inputs
        if required_inputs:
            result = await self.push_screen_wait(InputModal(required_inputs))
            if not result:
                return
            # Check required fields
            for inp in required_inputs:
                if not inp.optional and not result.get(inp.name, "").strip():
                    self.notify(f"Campo obrigatório: {inp.name}", severity="error")
                    return
            input_values = result

        if item.dangerous and not dry_run:
            confirmed = await self.push_screen_wait(
                ConfirmModal(f"Confirmar execução de:\n[bold]{item.title}[/bold]")
            )
            if not confirmed:
                self.notify("Execução cancelada.", severity="warning")
                return

        cmd = item.command
        # Substitute input placeholders {FOO}
        for k, v in input_values.items():
            cmd = cmd.replace(f"{{{k}}}", v)
        # Append Ansible --limit if HOST provided
        if "HOST" in input_values and input_values["HOST"]:
            if "--limit" not in cmd:
                cmd += f" --limit {shlex.quote(input_values['HOST'])}"
        if dry_run and item.dry_run_flag:
            cmd += f" {item.dry_run_flag}"

        mode = "DRY-RUN" if dry_run else "EXECUTAR"
        self._run_command(cmd, label=f"[{mode}] {item.title}")

    @work(exclusive=True, thread=True)
    def _run_command(self, cmd: str, label: str = "") -> None:
        """Run shell command with live output in RichLog."""
        log = self.query_one("#output-log", RichLog)
        self.call_from_thread(log.write, f"\n[bold cyan]{'─'*60}[/bold cyan]")
        self.call_from_thread(log.write, f"[bold yellow]▶  {label}[/bold yellow]")
        self.call_from_thread(log.write, f"[dim]$ {cmd}[/dim]")
        self.call_from_thread(log.write, f"[bold cyan]{'─'*60}[/bold cyan]")

        try:
            # shell=True intencional: comandos do menu podem usar sintaxe de shell;
            # valores digitados (ex.: HOST) entram escapados via shlex.quote.
            proc = subprocess.Popen(  # noqa: S602  # nosec B602
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=ROOT,
                bufsize=1,
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                self.call_from_thread(log.write, line.rstrip())
            proc.wait()
            rc = proc.returncode
            if rc == 0:
                self.call_from_thread(
                    log.write,
                    "\n[bold green]✅ Concluído com sucesso (rc=0)[/bold green]",
                )
                self.call_from_thread(
                    self.notify,
                    "✅ Comando concluído com sucesso!",
                    severity="information",
                )
            else:
                self.call_from_thread(
                    log.write, f"\n[bold red]❌ Falhou com código {rc}[/bold red]"
                )
                self.call_from_thread(
                    self.notify, f"❌ Falhou (rc={rc})", severity="error"
                )
        except Exception as exc:
            self.call_from_thread(log.write, f"[red]Erro ao executar: {exc}[/red]")
            self.call_from_thread(self.notify, f"Erro: {exc}", severity="error")

    # ── File saver ────────────────────────────────────────────────────────────

    async def _save_generated_file(self, rel_path: str, content: str) -> None:
        dest = ROOT / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
        if rel_path.endswith(".vault_pass"):
            dest.chmod(0o600)

        log = self.query_one("#output-log", RichLog)
        log.write(f"\n[bold green]💾 Arquivo gerado: {dest}[/bold green]")
        if rel_path.endswith(".json"):
            log.write(content)
        self.notify(f"✅ {rel_path} criado!", severity="information")

        # Refresh info panel if current item references this file
        if self._current_item and self._current_item.requires_file == rel_path:
            self._refresh_info(self._current_item)

    # ── Inventory helpers ─────────────────────────────────────────────────────

    async def _add_host_to_inventory(self, host_data: dict[str, str]) -> None:
        """Insert a new host entry into inventories/hosts.yml."""
        hosts_file = ROOT / "inventories" / "hosts.yml"
        log = self.query_one("#output-log", RichLog)
        try:
            raw = yaml.safe_load(hosts_file.read_text())
        except Exception as exc:
            self.notify(f"❌ Erro ao ler hosts.yml: {exc}", severity="error")
            return

        group = host_data["group"]
        name = host_data["name"]
        ip = host_data["ip"]

        children = (raw.get("all") or {}).get("children") or {}
        if group not in children:
            self.notify(
                f"❌ Grupo '{group}' não encontrado em hosts.yml", severity="error"
            )
            return
        if children[group] is None:
            children[group] = {}
        if children[group].get("hosts") is None:
            children[group]["hosts"] = {}

        group_hosts = children[group]["hosts"]
        if name in group_hosts:
            self.notify(
                f"⚠️  Host '{name}' já existe no grupo '{group}'!", severity="warning"
            )
            return

        group_hosts[name] = {
            "ansible_host": ip,
            "hostname": host_data.get("fqdn") or f"{name}.vya.digital",
            "node_name": host_data.get("node") or name,
        }

        try:
            header = (
                "---\n"
                "# =========================================================================\n"
                "# VPS Inventory — gerenciado por Enterprise Ansible Manager\n"
                "# =========================================================================\n"
            )
            yaml_body = yaml.dump(
                raw,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2,
            )
            hosts_file.write_text(header + yaml_body)
            log.write(
                f"\n[bold green]✅ Host '{name}' adicionado ao grupo '{group}'[/bold green]"
            )
            log.write(f"[dim]  ansible_host : {ip}[/dim]")
            log.write(f"[dim]  hostname     : {group_hosts[name]['hostname']}[/dim]")
            log.write(f"[dim]  Arquivo      : {hosts_file}[/dim]")
            self.notify(f"✅ {name} adicionado ao inventário!", severity="information")
        except Exception as exc:
            self.notify(f"❌ Erro ao salvar hosts.yml: {exc}", severity="error")
            log.write(f"[red]Erro ao salvar: {exc}[/red]")

    async def _remove_host_from_inventory(self, host_data: dict[str, str]) -> None:
        """Delete a host entry from inventories/hosts.yml."""
        hosts_file = ROOT / "inventories" / "hosts.yml"
        log = self.query_one("#output-log", RichLog)
        try:
            raw = yaml.safe_load(hosts_file.read_text())
        except Exception as exc:
            self.notify(f"❌ Erro ao ler hosts.yml: {exc}", severity="error")
            return

        group = host_data["group"]
        name = host_data["name"]

        children = (raw.get("all") or {}).get("children") or {}
        group_hosts = (children.get(group) or {}).get("hosts") or {}
        if name not in group_hosts:
            self.notify(
                f"❌ Host '{name}' não encontrado no grupo '{group}'!", severity="error"
            )
            return

        del group_hosts[name]

        try:
            header = (
                "---\n"
                "# =========================================================================\n"
                "# VPS Inventory — gerenciado por Enterprise Ansible Manager\n"
                "# =========================================================================\n"
            )
            yaml_body = yaml.dump(
                raw,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2,
            )
            hosts_file.write_text(header + yaml_body)
            log.write(
                f"\n[bold red]🗑️  Host '{name}' removido do grupo '{group}'[/bold red]"
            )
            log.write(f"[dim]  Arquivo: {hosts_file}[/dim]")
            self.notify(f"🗑️  {name} removido do inventário.", severity="warning")
        except Exception as exc:
            self.notify(f"❌ Erro ao salvar hosts.yml: {exc}", severity="error")
            log.write(f"[red]Erro ao salvar: {exc}[/red]")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Enterprise Ansible Manager TUI")
    parser.add_argument(
        "--debug",
        action="store_true",
        help=f"Ativa log detalhado em {LOG_FILE}",
    )
    args = parser.parse_args()

    setup_logging(debug=args.debug)

    if args.debug:
        # Textual's own internal log written to logs/textual.log
        os.environ.setdefault("TEXTUAL_LOG", str(ROOT / "logs" / "textual.log"))
        logger.debug("Debug mode enabled — log: %s", LOG_FILE)
        print(f"[debug] Logs em: {LOG_FILE}")

    os.chdir(ROOT)
    app = EnterpriseAnsibleApp()
    app.run()


if __name__ == "__main__":
    main()
