"""
lib/composer.py — Motor de Composição de Perfis.

Responsabilidades:
  1. Carregar descritores YAML de profile-descriptors/
  2. Verificar conflitos via campo `excludes_with`
  3. Ordenar perfis por camada (core → layer2 → layer3 → transversal)
  4. Aplicar perfis copiando arquivos de .github/templates/{perfil}/
  5. Fazer rollback (apagar arquivos criados) em caso de erro parcial

Uso:
  from lib.composer import ProfileComposer

  composer = ProfileComposer(
      descriptors_dir=Path("scaffold/profiles"),
      project_root=Path("."),
  )
  result = composer.compose(["devops-programming", "typescript-next"], cfg)
  if not result.success:
      print(result.errors)
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .config import CreatedItem, ProjectConfig

# ---------------------------------------------------------------------------
# Ordenação de camadas: número menor = aplicado primeiro
# ---------------------------------------------------------------------------
_LAYER_ORDER: dict[str | int, int] = {
    "core": 0,
    0: 0,
    "layer2": 1,
    1: 1,
    2: 1,
    "layer3": 2,
    3: 2,
    "layer4": 3,
    4: 3,
    "transversal": 99,
}


# ---------------------------------------------------------------------------
# Resultado da composição
# ---------------------------------------------------------------------------


@dataclass
class CompositionResult:
    """Resultado completo de uma operação de composição de perfis."""

    applied: list[str] = field(default_factory=list)
    """Nomes dos perfis aplicados com sucesso (na ordem de aplicação)."""

    items: list[CreatedItem] = field(default_factory=list)
    """Todos os arquivos processados (created, skipped, error)."""

    errors: list[str] = field(default_factory=list)
    """Erros encontrados (conflitos, arquivos ausentes, rollback)."""

    rolled_back: list[Path] = field(default_factory=list)
    """Arquivos removidos durante rollback."""

    @property
    def success(self) -> bool:
        return not self.errors

    @property
    def created_count(self) -> int:
        return sum(1 for i in self.items if i.status == "created")

    @property
    def skipped_count(self) -> int:
        return sum(1 for i in self.items if i.status == "skipped")


# ---------------------------------------------------------------------------
# Loader YAML (sem dependência obrigatória de pyyaml)
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict:
    """Carrega YAML com pyyaml ou fallback para parser mínimo de campos escalares."""
    try:
        import yaml  # pyyaml

        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        data: dict = {}
        with path.open(encoding="utf-8") as f:
            for line in f:
                stripped = line.rstrip()
                if not stripped or stripped.startswith("#") or stripped.startswith(" "):
                    continue
                if ": " in stripped:
                    key, _, val = stripped.partition(": ")
                    val = val.strip().strip('"').strip("'")
                    if val not in ("|", ">", ""):
                        data[key.strip()] = val
        return data


# ---------------------------------------------------------------------------
# Funções puras (composição sem efeitos colaterais)
# ---------------------------------------------------------------------------


def load_all_descriptors(descriptors_dir: Path) -> dict[str, dict]:
    """Carrega todos os *.yaml de descriptors_dir, indexados pelo campo 'name'."""
    result: dict[str, dict] = {}
    for yaml_file in sorted(descriptors_dir.glob("*.yaml")):
        data = _load_yaml(yaml_file)
        name = data.get("name", yaml_file.stem)
        result[name] = data
    return result


def resolve_order(profile_names: list[str], descriptors: dict[str, dict]) -> list[str]:
    """Retorna profile_names ordenados por camada (core primeiro, transversal por último)."""

    def _key(name: str) -> int:
        d = descriptors.get(name, {})
        layer = d.get("layer", d.get("LAYER", "layer2"))
        # layer pode ser int (2) ou string ("core", "layer2", "2")
        order = _LAYER_ORDER.get(layer)
        if order is None:
            order = _LAYER_ORDER.get(str(layer), 1)
        return order

    return sorted(profile_names, key=_key)


def check_conflicts(
    profile_names: list[str], descriptors: dict[str, dict]
) -> list[tuple[str, str]]:
    """Retorna pares (a, b) que conflitam via excludes_with."""
    conflicts: list[tuple[str, str]] = []
    name_set = set(profile_names)
    seen: set[tuple[str, str]] = set()

    for name in profile_names:
        d = descriptors.get(name, {})
        excludes: list[str] = d.get("excludes_with") or []
        for excluded in excludes:
            if excluded in name_set:
                pair: tuple[str, str] = tuple(sorted([name, excluded]))  # type: ignore[assignment]
                if pair not in seen:
                    seen.add(pair)
                    conflicts.append(pair)

    return conflicts


def get_template_entries(descriptor: dict) -> list[dict]:
    """
    Normaliza entradas de template entre os dois schemas suportados:

    Schema A (typescript-next): templates_path + templates[{path, description}]
    Schema B (python-fastapi):  generates.files[{path, source, description}]
    """
    # ── Schema A: templates_path + templates[] ────────────────────────────────
    if "templates_path" in descriptor and "templates" in descriptor:
        if descriptor.get("templates_status") == "pendente":
            # Templates declarados mas ainda não escritos (ADR-003 fatia 2)
            return []
        tpl_base = descriptor["templates_path"].rstrip("/")
        entries = descriptor.get("templates") or []
        result = []
        for e in entries:
            if not isinstance(e, dict):
                continue
            rel = e.get("path", "")
            if not rel or e.get("generated") is True:
                # generated: saída produzida no projeto (ex.: make sbom), não template
                continue
            result.append(
                {
                    "dest": rel,
                    "src_rel": f"{tpl_base}/{rel}",
                    "description": e.get("description", ""),
                }
            )
        return result

    # ── Schema B: generates.files[] ───────────────────────────────────────────
    generates = descriptor.get("generates")
    if isinstance(generates, dict):
        files = generates.get("files") or []
        result = []
        for f in files:
            if not isinstance(f, dict):
                continue
            dest = f.get("path", "")
            src = f.get("source", "")
            if not dest:
                continue
            result.append(
                {
                    "dest": dest,
                    "src_rel": src,
                    "description": f.get("description", ""),
                }
            )
        return result

    return []


# ---------------------------------------------------------------------------
# Motor principal
# ---------------------------------------------------------------------------


# Extensões tratadas como texto (recebem substituição de placeholders)
_TEXT_EXTENSIONS = frozenset(
    {".md", ".yaml", ".yml", ".toml", ".txt", ".json", ".py", ".sh", ".env"}
)


class ProfileComposer:
    """
    Motor de composição de perfis.

    Exemplo:
        composer = ProfileComposer(
            descriptors_dir=Path("scaffold/profiles"),
            project_root=Path("."),
        )
        result = composer.compose(["typescript-next"], cfg)
    """

    def __init__(self, descriptors_dir: Path, project_root: Path) -> None:
        self.descriptors_dir = descriptors_dir
        self.project_root = project_root
        self.descriptors: dict[str, dict] = load_all_descriptors(descriptors_dir)

    # ------------------------------------------------------------------
    # Pública
    # ------------------------------------------------------------------

    def compose(
        self,
        profile_names: list[str],
        cfg: ProjectConfig,
        force: bool = False,
    ) -> CompositionResult:
        """
        Aplica perfis em ordem (core→layer2→layer3), com rollback em caso de erro.

        :param force: sobrescreve arquivos de perfil existentes que diferem do
            template (com backup ``<arquivo>.backup``); sem ``force`` eles são preservados.
        """
        result = CompositionResult()

        # 1. Todos os perfis existem?
        missing = [p for p in profile_names if p not in self.descriptors]
        if missing:
            result.errors.append(
                f"Perfis não encontrados nos descriptors: {', '.join(missing)}"
            )
            return result

        # 2. Conflitos entre perfis?
        conflicts = check_conflicts(profile_names, self.descriptors)
        if conflicts:
            pairs_str = "; ".join(f"{a} ↔ {b}" for a, b in conflicts)
            result.errors.append(f"Conflitos detectados entre perfis: {pairs_str}")
            return result

        # 3. Ordenar por camada
        ordered = resolve_order(profile_names, self.descriptors)

        # 4. Aplicar cada perfil (com rollback em falha)
        for profile_name in ordered:
            items, error = self._apply_profile(profile_name, cfg, force=force)
            result.items.extend(items)

            if error:
                result.errors.append(error)
                removed = self._rollback(result.items)
                result.rolled_back.extend(removed)
                return result

            result.applied.append(profile_name)

        return result

    def available_profiles(self) -> list[str]:
        """Lista todos os perfis carregados."""
        return list(self.descriptors.keys())

    def get_layer(self, profile_name: str) -> int:
        """Retorna a ordem numérica de camada do perfil (0=core, 1=layer2, 2=layer3, 99=transversal)."""
        d = self.descriptors.get(profile_name, {})
        layer = d.get("layer", d.get("LAYER", "layer2"))
        order = _LAYER_ORDER.get(layer)
        if order is None:
            order = _LAYER_ORDER.get(str(layer), 1)
        return order

    # ------------------------------------------------------------------
    # Privadas
    # ------------------------------------------------------------------

    def _apply_profile(
        self, profile_name: str, cfg: ProjectConfig, force: bool = False
    ) -> tuple[list[CreatedItem], str | None]:
        """Copia arquivos de template do perfil para cfg.target_dir."""
        descriptor = self.descriptors[profile_name]
        entries = get_template_entries(descriptor)
        items: list[CreatedItem] = []

        for entry in entries:
            dest_rel: str = entry["dest"]
            src_rel: str = entry["src_rel"]

            # Pula entradas inline/geradas por código (não são arquivos físicos)
            if (
                not src_rel
                or "inline" in src_rel
                or "()" in src_rel
                or "templates.py:" in src_rel
            ):
                continue

            src_path = self.project_root / src_rel
            dest_path = cfg.target_dir / dest_rel

            # Arquivo de origem ausente → aviso, não erro fatal
            if not src_path.exists():
                items.append(
                    CreatedItem(
                        path=dest_path,
                        kind="file",
                        status="skipped",
                        message=f"template não encontrado: {src_rel}",
                    )
                )
                continue

            # Conteúdo final: texto com placeholders substituídos, ou bytes do binário
            try:
                conteudo = self._render_content(src_path, dest_path, cfg)
            except OSError as exc:
                items.append(
                    CreatedItem(
                        path=dest_path, kind="file", status="error", message=str(exc)
                    )
                )
                return items, f"Erro ao copiar '{dest_rel}': {exc}"

            # Destino já existe: preserva (sem force) ou sobrescreve com backup (force)
            if dest_path.exists():
                if dest_path.read_bytes() == conteudo:
                    items.append(
                        CreatedItem(path=dest_path, kind="file", status="skipped")
                    )
                    continue
                if not force:
                    items.append(
                        CreatedItem(
                            path=dest_path,
                            kind="file",
                            status="skipped",
                            message="existe e difere do template (use --update-profile-files para atualizar com backup)",
                        )
                    )
                    continue
                backup = dest_path.with_name(dest_path.name + ".backup")
                try:
                    shutil.copy2(dest_path, backup)
                    dest_path.write_bytes(conteudo)
                except OSError as exc:
                    items.append(
                        CreatedItem(
                            path=dest_path,
                            kind="file",
                            status="error",
                            message=str(exc),
                        )
                    )
                    return items, f"Falha ao atualizar {dest_path}: {exc}"
                items.append(
                    CreatedItem(
                        path=dest_path,
                        kind="file",
                        status="updated",
                        message=f"sobrescrito com o template (backup: {backup.name})",
                    )
                )
                continue

            # Copia
            try:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_bytes(conteudo)
                if dest_path.suffix not in _TEXT_EXTENSIONS:
                    shutil.copystat(src_path, dest_path)
                items.append(CreatedItem(path=dest_path, kind="file", status="created"))
            except OSError as exc:
                items.append(
                    CreatedItem(
                        path=dest_path,
                        kind="file",
                        status="error",
                        message=str(exc),
                    )
                )
                return items, f"Erro ao copiar '{dest_rel}': {exc}"

        return items, None

    def _apply_template_placeholders(self, content: str, cfg: ProjectConfig) -> str:
        """
        Substitui placeholders em templates de perfis.

        Suporta dois formatos:
        - {xxx}: formato simples (usado em templates Layer 2/3)
        - {{XXX}}: formato double-brace (usado em templates core)
        """
        replacements = {
            # Formato simples {xxx}
            "{project_name}": cfg.project_name,
            "{description}": cfg.description,
            "{domain}": cfg.domain,
            "{language}": cfg.language,
            "{github_repo}": cfg.github_repo or "",
            # Formato double-brace {{XXX}}
            "{{PROJECT_NAME}}": cfg.project_name,
            "{{PROJECT_TITLE}}": cfg.project_title,
            "{{PROJECT_DESCRIPTION}}": cfg.description,
            "{{CREATED_AT}}": cfg.created_at,
            "{{DOMAIN}}": cfg.domain,
            "{{LANGUAGE}}": cfg.language,
            "{{GITHUB_REPO}}": cfg.github_repo or "",
        }
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        return content

    def _render_content(
        self, src_path: Path, dest_path: Path, cfg: ProjectConfig
    ) -> bytes:
        """Conteúdo que o template gera para ``dest_path`` (placeholders aplicados)."""
        if dest_path.suffix in _TEXT_EXTENSIONS or dest_path.name.startswith(".env"):
            try:
                texto = src_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                return src_path.read_bytes()  # fallback: copia binária
            return self._apply_template_placeholders(texto, cfg).encode("utf-8")
        return src_path.read_bytes()

    def divergent_files(
        self, profile_names: list[str], cfg: ProjectConfig
    ) -> list[Path]:
        """
        Arquivos de perfil que JÁ EXISTEM no projeto e diferem do template.

        São os que ``compose(..., force=True)`` sobrescreveria (com backup).
        Não escreve nada.
        """
        divergentes: list[Path] = []
        conhecidos = [p for p in profile_names if p in self.descriptors]
        for profile_name in resolve_order(conhecidos, self.descriptors):
            for entry in get_template_entries(self.descriptors[profile_name]):
                src_rel: str = entry["src_rel"]
                if (
                    not src_rel
                    or "inline" in src_rel
                    or "()" in src_rel
                    or "templates.py:" in src_rel
                ):
                    continue
                src_path = self.project_root / src_rel
                dest_path = cfg.target_dir / entry["dest"]
                if not (src_path.exists() and dest_path.exists()):
                    continue
                try:
                    gerado = self._render_content(src_path, dest_path, cfg)
                    if dest_path.read_bytes() != gerado:
                        divergentes.append(dest_path)
                except OSError:
                    continue
        return divergentes

    def _rollback(self, items: list[CreatedItem]) -> list[Path]:
        """Desfaz a composição: remove 'created' e restaura 'updated' a partir do backup."""
        removed: list[Path] = []
        for item in reversed(items):
            if item.status == "updated":
                backup = item.path.with_name(item.path.name + ".backup")
                if backup.exists():
                    try:
                        backup.replace(item.path)
                        removed.append(item.path)
                    except OSError:
                        pass
                continue
            if item.status == "created" and item.path.exists():
                try:
                    item.path.unlink()
                    removed.append(item.path)
                except OSError:
                    pass
        return removed
