"""
GitHub Workflow Merger - Intelligent merge for .github/workflows/*.yml files

Merger especializado para arquivos de workflow GitHub Actions com suporte a:
- Parse YAML (name, on, permissions, jobs)
- Merge aditivo de jobs (security workflows)
- Preservação de jobs customizados
- Atualização de action versions
- Merge de triggers (on: push, schedule, etc.)

Sprint 3 (P1 HIGH): Resolve gap de 3+ workflows sem merge
Bug fix: Security workflows não propagados (CodeQL, secret scan, dependency audit)
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import CreatedItem

log = logging.getLogger(__name__)


# =============================================================================
# Types and Data Classes
# =============================================================================


@dataclass
class WorkflowContent:
    """Representa conteúdo de um workflow YAML."""

    name: str | None
    on_triggers: dict[str, Any]  # on: push, pull_request, schedule, etc.
    permissions: dict[str, str]  # permissions: contents: read, etc.
    jobs: dict[str, Any]  # jobs: job_name: {...}
    env: dict[str, Any]  # env global
    raw_yaml: dict[str, Any]  # YAML completo


@dataclass
class WorkflowMergeDecision:
    """Decisão de merge para um workflow."""

    should_merge: bool
    reason: str
    changes: list[str]


# =============================================================================
# GitHubWorkflowMerger
# =============================================================================


class GitHubWorkflowMerger:
    """
    Merger inteligente para arquivos .github/workflows/*.yml

    Estratégia de merge:
    1. **Triggers (on)**:
       - Adicionar novos triggers ausentes (schedule, workflow_dispatch)
       - Preservar triggers customizados
       - Merge de branches arrays

    2. **Permissions**:
       - Adicionar novas permissions ausentes
       - Atualizar se mais restritivas (security best practice)

    3. **Jobs**:
       - Adicionar novos jobs ausentes (security scans)
       - Preservar jobs customizados
       - Atualizar action versions (uses: action@vX)
       - Nunca remover jobs existentes

    4. **Preservação**:
       - Jobs customizados sempre preservados
       - Merge é sempre aditivo (nunca remove)
       - Em caso de dúvida, preserva local
    """

    # Jobs considerados "security critical" que devem ser sempre atualizados
    SECURITY_JOBS = {
        "secret-scan",
        "sast",
        "dependency-audit",
        "codeql",
        "gitleaks",
        "trufflehog",
        "bandit",
    }

    # Triggers recomendados para security workflows
    SECURITY_TRIGGERS = {
        "push",
        "pull_request",
        "schedule",
        "workflow_dispatch",
    }

    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é um workflow YAML em .github/workflows/."""
        return (
            file_path.suffix in [".yml", ".yaml"]
            and len(file_path.parts) >= 3
            and ".github" in file_path.parts
            and "workflows" in file_path.parts
        )

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Faz merge inteligente do workflow YAML

        Algoritmo:
        1. Parse YAML (existente e template)
        2. Decidir se deve fazer merge (novos jobs, triggers, etc.)
        3. Merge triggers (on)
        4. Merge permissions
        5. Merge jobs (aditivo, preservando custom)
        6. Gerar YAML mesclado
        7. Salvar com backup do original
        """
        try:
            # 1. Parse existente
            existing_content = existing_path.read_text(encoding="utf-8")
            existing_wf = self._parse_workflow(existing_content)

            # 2. Parse template
            template_wf = self._parse_workflow(template_content)

            # 3. Decisão de merge
            decision = self._should_merge(existing_wf, template_wf, existing_path.name)

            if not decision.should_merge:
                log.info("⏭️  Skip: %s (%s)", existing_path.name, decision.reason)
                return CreatedItem(
                    path=existing_path,
                    kind="file",
                    status="skipped",
                    message=decision.reason,
                )

            # 4. Merge triggers
            merged_triggers = self._merge_triggers(
                existing_wf.on_triggers, template_wf.on_triggers
            )

            # 5. Merge permissions
            merged_permissions = self._merge_permissions(
                existing_wf.permissions, template_wf.permissions
            )

            # 6. Merge jobs
            merged_jobs = self._merge_jobs(existing_wf.jobs, template_wf.jobs)

            # 7. Merge env (se houver)
            merged_env = {**existing_wf.env, **template_wf.env}

            # 8. Gerar YAML final
            merged_yaml = {
                "name": template_wf.name or existing_wf.name,
                "on": merged_triggers,
            }

            if merged_permissions:
                merged_yaml["permissions"] = merged_permissions

            if merged_env:
                merged_yaml["env"] = merged_env

            merged_yaml["jobs"] = merged_jobs

            merged_content = yaml.dump(
                merged_yaml,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                width=120,
            )

            # 9. Backup e save
            backup_path = existing_path.with_suffix(".yml.backup")
            backup_path.write_text(existing_content, encoding="utf-8")
            existing_path.write_text(merged_content, encoding="utf-8")

            changes_msg = "\n".join(f"  - {change}" for change in decision.changes)
            log.info(
                "✅ Merged: %s\n%s\n  Backup: %s",
                existing_path.name,
                changes_msg,
                backup_path.name,
            )

            return CreatedItem(
                path=existing_path,
                kind="file",
                status="merged",
                message=f"Merged with {len(decision.changes)} changes (backup created)",
            )

        except Exception as e:
            log.error("❌ Merge failed for %s: %s", existing_path.name, e)
            return CreatedItem(
                path=existing_path,
                kind="file",
                status="error",
                message=f"Merge error: {str(e)}",
            )

    # =========================================================================
    # Parsing Methods
    # =========================================================================

    def _parse_workflow(self, content: str) -> WorkflowContent:
        """
        Parse workflow YAML em estrutura WorkflowContent.

        Extrai: name, on, permissions, jobs, env

        Bug fix: YAML interpreta "on" como boolean True keyword
        """
        try:
            yaml_data = yaml.safe_load(content)
            if not isinstance(yaml_data, dict):
                yaml_data = {}
        except yaml.YAMLError as e:
            log.warning("YAML parse error: %s, using empty workflow", e)
            yaml_data = {}

        # Bug fix: YAML converte "on" para True (boolean keyword)
        # Precisamos verificar ambos "on" (string) e True (boolean)
        on_triggers = yaml_data.get("on", yaml_data.get(True, {}))

        return WorkflowContent(
            name=yaml_data.get("name"),
            on_triggers=on_triggers,
            permissions=yaml_data.get("permissions", {}),
            jobs=yaml_data.get("jobs", {}),
            env=yaml_data.get("env", {}),
            raw_yaml=yaml_data,
        )

    # =========================================================================
    # Decision Logic
    # =========================================================================

    def _should_merge(
        self, existing_wf: WorkflowContent, template_wf: WorkflowContent, filename: str
    ) -> WorkflowMergeDecision:
        """
        Decide se deve fazer merge baseado em novos jobs/triggers.

        Critérios:
        1. Se template tem novos security jobs → merge
        2. Se template tem novos triggers (schedule, workflow_dispatch) → merge
        3. Se template tem permissions mais seguras → merge
        4. Caso contrário → skip
        """
        changes = []

        # 1. Detectar novos security jobs
        existing_jobs = set(existing_wf.jobs.keys())
        template_jobs = set(template_wf.jobs.keys())
        new_security_jobs = []

        for job_name in template_jobs - existing_jobs:
            # Verificar se é security job
            job_name_lower = job_name.lower()
            if any(sec in job_name_lower for sec in self.SECURITY_JOBS):
                new_security_jobs.append(job_name)

        if new_security_jobs:
            changes.append(f"Add {len(new_security_jobs)} security jobs")

        # 2. Detectar novos triggers
        existing_triggers = set(existing_wf.on_triggers.keys())
        template_triggers = set(template_wf.on_triggers.keys())
        new_triggers = template_triggers - existing_triggers

        new_security_triggers = [t for t in new_triggers if t in self.SECURITY_TRIGGERS]

        if new_security_triggers:
            changes.append(
                f"Add {len(new_security_triggers)} triggers ({', '.join(new_security_triggers)})"
            )

        # 3. Detectar novas permissions
        existing_perms = set(existing_wf.permissions.keys())
        template_perms = set(template_wf.permissions.keys())
        new_perms = template_perms - existing_perms

        if new_perms:
            changes.append(f"Add {len(new_perms)} permissions")

        # Decisão final
        if not changes:
            return WorkflowMergeDecision(
                should_merge=False, reason="Workflow already up-to-date", changes=[]
            )

        return WorkflowMergeDecision(
            should_merge=True,
            reason=f"Template has updates ({len(changes)} changes)",
            changes=changes,
        )

    # =========================================================================
    # Merge Methods
    # =========================================================================

    def _merge_triggers(
        self, existing: dict[str, Any], template: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge triggers (on) com estratégia aditiva.

        Regras:
        - Adicionar novos triggers ausentes
        - Preservar triggers existentes
        - Merge de arrays (branches, paths)
        """
        merged = dict(existing)

        for trigger, config in template.items():
            if trigger not in merged:
                # Novo trigger - adicionar
                merged[trigger] = config
            elif isinstance(config, dict) and isinstance(merged[trigger], dict):
                # Merge configs (branches, paths, etc.)
                merged[trigger] = {**merged[trigger], **config}
            elif isinstance(config, list) and isinstance(merged[trigger], list):
                # Merge arrays (branches)
                merged[trigger] = list(set(merged[trigger] + config))

        return merged

    def _merge_permissions(
        self, existing: dict[str, str], template: dict[str, str]
    ) -> dict[str, str]:
        """
        Merge permissions com estratégia de adicionar ausentes.

        Regras:
        - Adicionar novas permissions ausentes
        - Preservar existing (podem ser mais restritivas)
        """
        merged = dict(existing)

        for perm, level in template.items():
            if perm not in merged:
                # Nova permission - adicionar
                merged[perm] = level

        return merged

    def _merge_jobs(
        self, existing: dict[str, Any], template: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge jobs com estratégia aditiva preservando customizações.

        Regras:
        - Adicionar novos security jobs ausentes
        - Preservar jobs customizados
        - Atualizar action versions em security jobs
        - Nunca remover jobs existentes
        """
        merged = dict(existing)

        for job_name, job_config in template.items():
            if job_name not in merged:
                # Novo job - adicionar
                merged[job_name] = job_config
            else:
                # Job existe - verificar se é security job
                job_name_lower = job_name.lower()
                is_security = any(sec in job_name_lower for sec in self.SECURITY_JOBS)

                if is_security:
                    # Security job - atualizar steps (action versions)
                    merged[job_name] = self._merge_job_steps(
                        merged[job_name], job_config
                    )
                # Else: preserve existing custom job

        return merged

    def _merge_job_steps(
        self, existing_job: dict[str, Any], template_job: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge steps de um job (principalmente action versions).

        Atualiza 'uses' para versões mais recentes de actions.
        """
        merged = dict(existing_job)

        # Preservar configuração básica do template
        if "runs-on" in template_job:
            merged["runs-on"] = template_job["runs-on"]
        if "timeout-minutes" in template_job:
            merged["timeout-minutes"] = template_job["timeout-minutes"]

        # Merge steps: adicionar novos, atualizar action versions
        existing_steps = merged.get("steps", [])
        template_steps = template_job.get("steps", [])

        # Criar map de steps por name
        existing_map = {
            step.get("name"): step for step in existing_steps if "name" in step
        }

        merged_steps = []
        for template_step in template_steps:
            step_name = template_step.get("name")

            if step_name and step_name in existing_map:
                # Step existe - atualizar 'uses' se for action
                existing_step = existing_map[step_name]
                if "uses" in template_step:
                    # Atualizar action version
                    existing_step["uses"] = template_step["uses"]
                merged_steps.append(existing_step)
                del existing_map[step_name]
            else:
                # Novo step - adicionar
                merged_steps.append(template_step)

        # Adicionar steps customizados que não foram mesclados
        merged_steps.extend(existing_map.values())

        merged["steps"] = merged_steps
        return merged
