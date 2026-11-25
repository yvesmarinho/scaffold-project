"""
PreCommit Config Merger - Intelligent merge for .pre-commit-config.yaml

Merger especializado para arquivos de configuração pre-commit com suporte a:
- Parse YAML (repos com hooks)
- Merge aditivo de hooks
- Atualização de versões de repos
- Preservação de hooks customizados
- Merge de args e configurações

Sprint 4 (P2 MEDIUM): Expansão do merge system para 90% coverage
Feature: Pre-commit hooks não propagados em upgrades
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
class PreCommitHook:
    """Representa um hook dentro de um repo."""

    id: str
    name: str | None
    args: list[str]
    exclude: str | None
    files: str | None
    other: dict[str, Any]  # Outros campos customizados


@dataclass
class PreCommitRepo:
    """Representa um repo com seus hooks."""

    repo: str
    rev: str
    hooks: list[PreCommitHook]


# =============================================================================
# PreCommitMerger
# =============================================================================


class PreCommitMerger:
    """
    Merger inteligente para .pre-commit-config.yaml

    Estratégia de merge:
    1. **Repos**:
       - Adicionar novos repos ausentes
       - Atualizar versão (rev) se mais recente
       - Preservar repos customizados

    2. **Hooks**:
       - Adicionar novos hooks ausentes dentro de repos existentes
       - Preservar hooks customizados
       - Merge de args (união de listas)
       - Preservar exclude e files patterns

    3. **Preservação**:
       - Hooks customizados sempre preservados
       - Merge é sempre aditivo (nunca remove)
       - Em caso de dúvida, preserva local
    """

    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é .pre-commit-config.yaml na raiz."""
        return file_path.name == ".pre-commit-config.yaml"

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Faz merge inteligente do pre-commit config YAML.

        Algoritmo:
        1. Parse YAML (existente e template)
        2. Identificar repos novos e existentes
        3. Para repos existentes:
           - Atualizar rev se mais recente
           - Merge hooks (adicionar novos, preservar customizados)
        4. Adicionar repos novos
        5. Gerar YAML mesclado
        6. Salvar com backup do original
        """
        try:
            # 1. Parse existente
            existing_content = existing_path.read_text(encoding="utf-8")
            existing_data = yaml.safe_load(existing_content)

            # 2. Parse template
            template_data = yaml.safe_load(template_content)

            # Validar estrutura básica
            if not isinstance(existing_data, dict) or "repos" not in existing_data:
                log.warning("⚠️  %s: estrutura inválida", existing_path.name)
                return CreatedItem(
                    path=existing_path,
                    kind="file",
                    status="skipped",
                    message="Estrutura YAML inválida",
                )

            if not isinstance(template_data, dict) or "repos" not in template_data:
                log.warning("⚠️  Template: estrutura inválida")
                return CreatedItem(
                    path=existing_path,
                    kind="file",
                    status="skipped",
                    message="Template YAML inválido",
                )

            # 3. Parse repos
            existing_repos = self._parse_repos(existing_data["repos"])
            template_repos = self._parse_repos(template_data["repos"])

            # 4. Merge repos
            merged_repos = self._merge_repos(existing_repos, template_repos)

            # 5. Verificar se houve mudanças
            changes = self._detect_changes(existing_repos, merged_repos)
            if not changes:
                log.info("⏭️  Skip: %s (sem mudanças)", existing_path.name)
                return CreatedItem(
                    path=existing_path,
                    kind="file",
                    status="skipped",
                    message="Nenhuma mudança necessária",
                )

            # 6. Backup do original
            backup_path = existing_path.with_suffix(existing_path.suffix + ".backup")
            existing_path.rename(backup_path)
            log.info("📦 Backup: %s", backup_path.name)

            # 7. Gerar YAML mesclado
            merged_data = {"repos": [self._repo_to_dict(r) for r in merged_repos]}

            # Preservar outras chaves top-level se existirem
            for key in existing_data:
                if key != "repos":
                    merged_data[key] = existing_data[key]

            # 8. Escrever arquivo
            merged_yaml = yaml.dump(
                merged_data,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
            existing_path.write_text(merged_yaml, encoding="utf-8")

            log.info("🔀 Merged %s: %s", existing_path.name, ", ".join(changes))

            return CreatedItem(
                path=existing_path,
                kind="file",
                status="merged",
                message=f"Merged: {', '.join(changes)}",
            )

        except yaml.YAMLError as e:
            log.error("❌ YAML error em %s: %s", existing_path.name, e)
            return CreatedItem(
                path=existing_path,
                kind="file",
                status="error",
                message=f"YAML error: {e}",
            )
        except Exception as e:
            log.error("❌ Erro ao mergear %s: %s", existing_path.name, e)
            return CreatedItem(
                path=existing_path,
                kind="file",
                status="error",
                message=f"Merge error: {e}",
            )

    def _parse_repos(self, repos_list: list[dict[str, Any]]) -> list[PreCommitRepo]:
        """Parse lista de repos em estrutura tipada."""
        result = []
        for repo_dict in repos_list:
            hooks_data = repo_dict.get("hooks", [])
            hooks = []
            for hook_dict in hooks_data:
                hook = PreCommitHook(
                    id=hook_dict.get("id", ""),
                    name=hook_dict.get("name"),
                    args=hook_dict.get("args", []),
                    exclude=hook_dict.get("exclude"),
                    files=hook_dict.get("files"),
                    other={
                        k: v
                        for k, v in hook_dict.items()
                        if k not in ["id", "name", "args", "exclude", "files"]
                    },
                )
                hooks.append(hook)

            result.append(
                PreCommitRepo(
                    repo=repo_dict.get("repo", ""),
                    rev=repo_dict.get("rev", ""),
                    hooks=hooks,
                )
            )
        return result

    def _merge_repos(
        self, existing: list[PreCommitRepo], template: list[PreCommitRepo]
    ) -> list[PreCommitRepo]:
        """
        Merge repos: adiciona novos, atualiza existentes.

        Estratégia:
        - Repos são identificados por URL
        - Se repo existe, merge hooks
        - Se repo é novo, adiciona
        """
        {r.repo: r for r in existing}
        merged = []

        # Processar todos repos (manter ordem do existente)
        seen = set()

        # Primeiro, adicionar repos existentes (preservar ordem)
        for repo in existing:
            if repo.repo in seen:
                continue
            seen.add(repo.repo)

            # Verificar se há versão no template
            template_repo = next((t for t in template if t.repo == repo.repo), None)
            if template_repo:
                # Merge hooks
                merged_hooks = self._merge_hooks(repo.hooks, template_repo.hooks)
                # Usar rev mais recente (preferir template se diferente)
                rev = template_repo.rev if template_repo.rev != repo.rev else repo.rev
                merged.append(
                    PreCommitRepo(repo=repo.repo, rev=rev, hooks=merged_hooks)
                )
            else:
                # Repo customizado, preservar
                merged.append(repo)

        # Adicionar repos novos do template
        for template_repo in template:
            if template_repo.repo not in seen:
                seen.add(template_repo.repo)
                merged.append(template_repo)

        return merged

    def _merge_hooks(
        self, existing: list[PreCommitHook], template: list[PreCommitHook]
    ) -> list[PreCommitHook]:
        """
        Merge hooks dentro de um repo.

        Estratégia:
        - Hooks identificados por ID
        - Preservar hooks customizados
        - Adicionar hooks novos do template
        - Merge args (união)
        """
        {h.id: h for h in existing}
        merged = []
        seen = set()

        # Preservar hooks existentes (ordem preservada)
        for hook in existing:
            if hook.id in seen:
                continue
            seen.add(hook.id)

            # Verificar se há versão no template
            template_hook = next((t for t in template if t.id == hook.id), None)
            if template_hook:
                # Merge args (união, preservar ordem)
                merged_args = list(dict.fromkeys(hook.args + template_hook.args))
                # Preservar customizações do existente
                merged.append(
                    PreCommitHook(
                        id=hook.id,
                        name=hook.name or template_hook.name,
                        args=merged_args,
                        exclude=hook.exclude or template_hook.exclude,
                        files=hook.files or template_hook.files,
                        other={**template_hook.other, **hook.other},  # User wins
                    )
                )
            else:
                # Hook customizado, preservar
                merged.append(hook)

        # Adicionar hooks novos do template
        for template_hook in template:
            if template_hook.id not in seen:
                seen.add(template_hook.id)
                merged.append(template_hook)

        return merged

    def _detect_changes(
        self, original: list[PreCommitRepo], merged: list[PreCommitRepo]
    ) -> list[str]:
        """Detecta mudanças entre configurações."""
        changes = []

        original_urls = {r.repo for r in original}
        merged_urls = {r.repo for r in merged}

        new_repos = merged_urls - original_urls
        if new_repos:
            changes.append(f"+{len(new_repos)} repos")

        # Detectar hooks novos ou args atualizados
        original_hooks = sum(len(r.hooks) for r in original)
        merged_hooks = sum(len(r.hooks) for r in merged)
        if merged_hooks > original_hooks:
            changes.append(f"+{merged_hooks - original_hooks} hooks")

        # Detectar mudanças em args de hooks existentes
        for repo in merged:
            orig_repo = next((r for r in original if r.repo == repo.repo), None)
            if orig_repo:
                for hook in repo.hooks:
                    orig_hook = next(
                        (h for h in orig_repo.hooks if h.id == hook.id), None
                    )
                    if orig_hook and orig_hook.args != hook.args:
                        if "args updated" not in changes:
                            changes.append("args updated")
                        break

        # Detectar versões atualizadas
        updated_revs = 0
        for repo in merged:
            orig = next((r for r in original if r.repo == repo.repo), None)
            if orig and orig.rev != repo.rev:
                updated_revs += 1
        if updated_revs > 0:
            changes.append(f"~{updated_revs} versions")

        return changes

    def _repo_to_dict(self, repo: PreCommitRepo) -> dict[str, Any]:
        """Converte PreCommitRepo de volta para dict YAML."""
        hooks_list = []
        for hook in repo.hooks:
            hook_dict: dict[str, Any] = {"id": hook.id}
            if hook.name:
                hook_dict["name"] = hook.name
            if hook.args:
                hook_dict["args"] = hook.args
            if hook.exclude:
                hook_dict["exclude"] = hook.exclude
            if hook.files:
                hook_dict["files"] = hook.files
            # Adicionar outros campos customizados
            hook_dict.update(hook.other)
            hooks_list.append(hook_dict)

        return {"repo": repo.repo, "rev": repo.rev, "hooks": hooks_list}
