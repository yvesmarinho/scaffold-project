"""
validate.py — Validação de profile-descriptors do Enterprise Scaffold Project Template.

Verifica por descriptor:
  1. Sintaxe YAML (parsável)
  2. Campo `name` não-vazio
  3. Campo `description` não-vazio
  4. Versão (version / VERSION) presente e em formato semver X.Y.Z
  5. Data de último teste (last_tested / LAST_TESTED_DATE) presente
  6. Campo `layer` presente e com valor reconhecido
  7. `security.enforces` — se presente, cada item deve ser objeto estruturado com
     `control`, `description`, `tool`, `severity` (critical|high|medium|low), `automated`

Verifica entre descritores (cross-profile):
  8. Nomes duplicados
  9. `combines_with` → todos os nomes referenciados existem
  10. `excludes_with` → todos os nomes referenciados existem
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Valores aceitos para o campo layer
_VALID_LAYERS: frozenset[str] = frozenset(
    {"core", "1", "2", "3", "4", "layer2", "layer3", "layer4", "transversal"}
)

# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------


@dataclass
class ValidationIssue:
    field: str
    severity: str   # "error" | "warning"
    message: str


@dataclass
class ProfileResult:
    name: str
    file: str
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def status(self) -> str:
        if self.errors:
            return "error"
        if self.warnings:
            return "warning"
        return "ok"


@dataclass
class ValidationReport:
    descriptor_dir: Path
    results: list[ProfileResult] = field(default_factory=list)
    stale_days_threshold: int = 90

    @property
    def profiles_checked(self) -> int:
        return len(self.results)

    @property
    def stale_profiles(self) -> list[str]:
        """Nomes dos perfis com aviso de staleness (last_tested > stale_days_threshold dias)."""
        return [
            r.name
            for r in self.results
            for i in r.warnings
            if i.field == "last_tested" and "desatualizado" in i.message
        ]

    @property
    def total_errors(self) -> int:
        return sum(len(r.errors) for r in self.results)

    @property
    def total_warnings(self) -> int:
        return sum(len(r.warnings) for r in self.results)

    @property
    def valid(self) -> bool:
        return self.total_errors == 0


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------


def _get_field(data: dict, *keys: str) -> object | None:
    """Retorna o primeiro valor não-None encontrado entre as chaves alternativas."""
    for k in keys:
        v = data.get(k)
        if v is not None:
            return v
    return None


def _str_list(value: object) -> list[str]:
    """
    Normaliza um campo lista de referências a perfis.

    Aceita dois formatos YAML:
      - Lista de strings:  ["profile-a", "profile-b"]
      - Lista de objetos:  [{name: "profile-a", notes: "..."}, ...]
    """
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if item is None:
            continue
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            name_val = item.get("name") or item.get("profile") or item.get("id")
            if name_val:
                result.append(str(name_val))
        else:
            result.append(str(item))
    return result


# ---------------------------------------------------------------------------
# Validação individual
# ---------------------------------------------------------------------------


def _validate_descriptor(data: dict, yaml_path: Path) -> ProfileResult:
    """Valida um único descriptor carregado em `data`."""
    name_field = _get_field(data, "name")
    profile_name = str(name_field).strip() if name_field else yaml_path.stem

    result = ProfileResult(name=profile_name, file=yaml_path.name)

    # Regra 1 — name
    if not name_field or not str(name_field).strip():
        result.issues.append(ValidationIssue("name", "error", "Campo 'name' ausente ou vazio"))

    # Regra 2 — description
    description = _get_field(data, "description")
    if not description or not str(description).strip():
        result.issues.append(ValidationIssue("description", "error", "Campo 'description' ausente ou vazio"))

    # Regra 3 — version (aceita 'version' ou 'VERSION')
    version_val = _get_field(data, "version", "VERSION")
    if version_val is None:
        result.issues.append(ValidationIssue("version", "error", "Campo 'version' (ou 'VERSION') ausente"))
    else:
        version_str = str(version_val).strip().strip('"')
        if not _SEMVER_RE.match(version_str):
            result.issues.append(
                ValidationIssue(
                    "version", "error",
                    f"Versão '{version_str}' não está em formato semver X.Y.Z"
                )
            )

    # Regra 4 — last_tested (aceita 'last_tested' ou 'LAST_TESTED_DATE')
    last_tested = _get_field(data, "last_tested", "LAST_TESTED_DATE")
    if not last_tested:
        result.issues.append(
            ValidationIssue("last_tested", "warning",
                            "Campo 'last_tested' (ou 'LAST_TESTED_DATE') ausente")
        )

    # Regra 5 — layer
    layer_val = _get_field(data, "layer")
    if layer_val is None:
        result.issues.append(
            ValidationIssue("layer", "warning", "Campo 'layer' ausente")
        )
    else:
        layer_str = str(layer_val).strip().lower()
        if layer_str not in _VALID_LAYERS:
            result.issues.append(
                ValidationIssue(
                    "layer", "error",
                    f"Valor de layer '{layer_val}' não reconhecido. "
                    f"Aceitos: {', '.join(sorted(_VALID_LAYERS))}"
                )
            )

    # Regra 6 — security.enforces (se presente, deve ser lista de objetos estruturados)
    _REQUIRED_CONTROL_FIELDS = frozenset({"control", "description", "tool", "severity", "automated"})
    _VALID_SEVERITIES = frozenset({"critical", "high", "medium", "low"})
    security_data = data.get("security") or {}
    enforces = security_data.get("enforces")
    if enforces is not None:
        for i, item in enumerate(enforces):
            if not isinstance(item, dict):
                result.issues.append(
                    ValidationIssue(
                        "security.enforces",
                        "error",
                        f"enforces[{i}] deve ser objeto estruturado com campos "
                        f"{sorted(_REQUIRED_CONTROL_FIELDS)}, encontrado: {type(item).__name__}",
                    )
                )
            else:
                missing = _REQUIRED_CONTROL_FIELDS - set(item.keys())
                if missing:
                    result.issues.append(
                        ValidationIssue(
                            "security.enforces",
                            "error",
                            f"enforces[{i}]: campos obrigatórios ausentes: {sorted(missing)}",
                        )
                    )
                severity_val = item.get("severity")
                if severity_val not in _VALID_SEVERITIES:
                    result.issues.append(
                        ValidationIssue(
                            "security.enforces",
                            "error",
                            f"enforces[{i}].severity='{severity_val}' inválido. "
                            f"Aceitos: {sorted(_VALID_SEVERITIES)}",
                        )
                    )

    return result


# ---------------------------------------------------------------------------
# Validação cruzada
# ---------------------------------------------------------------------------


def _cross_validate(
    results: list[ProfileResult],
    all_data: dict[str, dict],
) -> None:
    """
    Acrescenta issues de referências cruzadas nos ProfileResults.
    Modifica `results` in-place.
    """
    known_names: set[str] = {r.name for r in results}

    # Detectar duplicatas
    seen: dict[str, str] = {}  # name → first file
    for r in results:
        if r.name in seen:
            r.issues.append(
                ValidationIssue(
                    "name", "error",
                    f"Nome duplicado — também declarado em '{seen[r.name]}'"
                )
            )
        else:
            seen[r.name] = r.file

    # Validar referências combines_with / excludes_with
    for r in results:
        data = all_data.get(r.file, {})
        for ref_field in ("combines_with", "excludes_with"):
            refs = _str_list(data.get(ref_field))
            for ref_name in refs:
                if ref_name not in known_names:
                    r.issues.append(
                        ValidationIssue(
                            ref_field, "warning",
                            f"'{ref_name}' referenciado em '{ref_field}' não existe nos descritores locais"
                        )
                    )


# ---------------------------------------------------------------------------
# Staleness check
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def _check_staleness(
    results: list[ProfileResult],
    all_data: dict[str, dict],
    threshold_days: int = 90,
    reference_date: date | None = None,
) -> None:
    """
    Acrescenta warning nos ProfileResults cujo last_tested/LAST_TESTED_DATE
    é mais antigo que `threshold_days` dias.

    Modifica `results` in-place.
    Perfis sem data ou com data inválida são ignorados (já cobertos pela Regra 4).
    """
    today = reference_date or date.today()

    for r in results:
        data = all_data.get(r.file, {})
        raw = _get_field(data, "last_tested", "LAST_TESTED_DATE")
        if not raw:
            continue  # ausência já reportada pela Regra 4
        raw_str = str(raw).strip().strip('"')
        m = _DATE_RE.match(raw_str)
        if not m:
            continue  # formato inválido — não adiciona staleness
        try:
            tested = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            continue
        delta = (today - tested).days
        if delta > threshold_days:
            r.issues.append(
                ValidationIssue(
                    "last_tested",
                    "warning",
                    f"Perfil desatualizado: last_tested '{raw_str}' é {delta} dias atrás "
                    f"(limite: {threshold_days} dias)",
                )
            )


# ---------------------------------------------------------------------------
# Entrada pública
# ---------------------------------------------------------------------------


def validate_descriptors(
    descriptors_dir: Path,
    stale_days_threshold: int = 90,
) -> ValidationReport:
    """
    Valida todos os profile-descriptors em `descriptors_dir`.

    Retorna um `ValidationReport` com todos os resultados.
    Nunca levanta exceção — erros de parse são capturados como issue.
    """
    import yaml

    report = ValidationReport(
        descriptor_dir=descriptors_dir,
        stale_days_threshold=stale_days_threshold,
    )
    all_data: dict[str, dict] = {}  # file → parsed dict

    if not descriptors_dir.exists():
        return report

    for yaml_path in sorted(descriptors_dir.glob("*.yaml")):
        try:
            with yaml_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as exc:
            err_result = ProfileResult(
                name=yaml_path.stem,
                file=yaml_path.name,
                issues=[ValidationIssue("yaml", "error", f"Erro de parse YAML: {exc}")],
            )
            report.results.append(err_result)
            continue

        all_data[yaml_path.name] = data
        result = _validate_descriptor(data, yaml_path)
        report.results.append(result)

    # Cross-profile checks (only over successfully parsed files)
    parsed_results = [r for r in report.results if r.file in all_data]
    _cross_validate(parsed_results, all_data)

    # Staleness check (warning-only, non-blocking)
    _check_staleness(parsed_results, all_data, threshold_days=stale_days_threshold)

    return report
