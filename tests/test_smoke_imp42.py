"""
tests/test_smoke_imp42.py — IMP-42: SBOM (Software Bill of Materials) nos perfis Layer 2.

Cobertura:
  Makefile templates:
    - sbom: target presente em python-fastapi/Makefile
    - sbom: target presente em python-flask/Makefile
    - sbom: target presente em typescript-next/Makefile
    - cyclonedx-bom referenciado no sbom target de python-fastapi
    - cyclonedx-bom referenciado no sbom target de python-flask
    - cyclonedx-npm referenciado no sbom target de typescript-next
    - sbom incluso no .PHONY de python-fastapi
    - sbom incluso no .PHONY de python-flask
    - sbom incluso no .PHONY de typescript-next
    - ci target inclui sbom em python-fastapi/Makefile
    - ci target inclui sbom em python-flask/Makefile
    - ci target inclui sbom em typescript-next/Makefile

  Profile descriptors — security.enforces CC8:
    - python-fastapi.yaml tem CC8 SBOM em security.enforces
    - python-flask.yaml tem CC8 SBOM em security.enforces
    - typescript-next.yaml tem CC8 SBOM em security.enforces
    - soc2-baseline.yaml tem CC8 SBOM em security.enforces

  Profile descriptors — ci_targets:
    - python-fastapi.yaml lista sbom em ci_targets
    - python-flask.yaml lista sbom em ci_targets
    - typescript-next.yaml lista sbom em ci_targets

  Profile descriptors — generates.files:
    - python-fastapi.yaml documenta sbom.json em generates.files
    - python-flask.yaml documenta sbom.json em generates.files
    - typescript-next.yaml documenta sbom.json em templates

  CI workflow:
    - ci-template.yml tem step de verificação de sbom target no cli-smoke job
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_PROJECT_ROOT = Path(__file__).parent.parent
_TEMPLATES = _PROJECT_ROOT / ".github" / "templates"
_DESCRIPTORS = _PROJECT_ROOT / "profile-descriptors"
_CI_TEMPLATE = _PROJECT_ROOT / ".github" / "workflows" / "ci-template.yml"


# ===========================================================================
# Helpers
# ===========================================================================


def _makefile(profile: str) -> Path:
    return _TEMPLATES / profile / "Makefile"


def _descriptor(name: str) -> dict:
    return yaml.safe_load((_DESCRIPTORS / f"{name}.yaml").read_text())


# ===========================================================================
# Makefiles — sbom: target presence
# ===========================================================================


class TestMakefileSbomTarget:
    @pytest.mark.parametrize("profile", ["python-fastapi", "python-flask"])
    def test_sbom_target_present_python(self, profile):
        content = _makefile(profile).read_text()
        assert "sbom:" in content, f"sbom: target missing in {profile}/Makefile"

    def test_sbom_target_present_typescript(self):
        content = _makefile("typescript-next").read_text()
        assert "sbom:" in content, "sbom: target missing in typescript-next/Makefile"

    @pytest.mark.parametrize("profile", ["python-fastapi", "python-flask"])
    def test_cyclonedx_bom_in_python_sbom(self, profile):
        content = _makefile(profile).read_text()
        assert (
            "cyclonedx" in content
        ), f"cyclonedx not referenced in {profile}/Makefile sbom target"

    def test_cyclonedx_npm_in_typescript_sbom(self):
        content = _makefile("typescript-next").read_text()
        assert (
            "cyclonedx-npm" in content
        ), "cyclonedx-npm not referenced in typescript-next/Makefile"

    @pytest.mark.parametrize("profile", ["python-fastapi", "python-flask"])
    def test_sbom_in_phony_python(self, profile):
        content = _makefile(profile).read_text()
        phony_line = next(linha for linha in content.splitlines() if ".PHONY:" in linha)
        assert "sbom" in phony_line, f"sbom missing from .PHONY in {profile}/Makefile"

    def test_sbom_in_phony_typescript(self):
        content = _makefile("typescript-next").read_text()
        phony_block = content[content.find(".PHONY:") : content.find(".PHONY:") + 200]
        assert (
            "sbom" in phony_block
        ), "sbom missing from .PHONY in typescript-next/Makefile"

    @pytest.mark.parametrize("profile", ["python-fastapi", "python-flask"])
    def test_ci_target_includes_sbom_python(self, profile):
        content = _makefile(profile).read_text()
        ci_line = next(
            (linha for linha in content.splitlines() if linha.startswith("ci:")), None
        )
        assert ci_line is not None, f"ci: target missing in {profile}/Makefile"
        assert "sbom" in ci_line, f"sbom not in ci: target of {profile}/Makefile"

    def test_ci_target_includes_sbom_typescript(self):
        content = _makefile("typescript-next").read_text()
        ci_line = next(
            (linha for linha in content.splitlines() if linha.startswith("ci:")), None
        )
        assert ci_line is not None, "ci: target missing in typescript-next/Makefile"
        assert "sbom" in ci_line, "sbom not in ci: target of typescript-next/Makefile"


# ===========================================================================
# Profile descriptors — security.enforces CC8
# ===========================================================================


class TestDescriptorCC8Enforces:
    def _get_enforces(self, descriptor: dict) -> list[dict]:
        sec = descriptor.get("security", {})
        return sec.get("enforces", [])

    def _has_cc8_sbom(self, enforces: list[dict]) -> bool:
        return any(
            isinstance(e, dict)
            and e.get("control") == "CC8"
            and "sbom" in e.get("description", "").lower()
            for e in enforces
        )

    @pytest.mark.parametrize(
        "name", ["python-fastapi", "python-flask", "typescript-next"]
    )
    def test_layer2_descriptor_has_cc8_sbom(self, name):
        d = _descriptor(name)
        enforces = self._get_enforces(d)
        assert self._has_cc8_sbom(
            enforces
        ), f"{name}.yaml: no CC8 SBOM entry found in security.enforces"

    def test_soc2_baseline_has_cc8_sbom(self):
        d = _descriptor("soc2-baseline")
        enforces = self._get_enforces(d)
        assert self._has_cc8_sbom(
            enforces
        ), "soc2-baseline.yaml: no CC8 SBOM entry found in security.enforces"

    @pytest.mark.parametrize(
        "name", ["python-fastapi", "python-flask", "typescript-next"]
    )
    def test_cc8_sbom_entry_is_automated(self, name):
        d = _descriptor(name)
        enforces = self._get_enforces(d)
        cc8_sbom = next(
            (
                e
                for e in enforces
                if isinstance(e, dict)
                and e.get("control") == "CC8"
                and "sbom" in e.get("description", "").lower()
            ),
            None,
        )
        assert cc8_sbom is not None, f"{name}: CC8 SBOM enforces entry not found"
        assert (
            cc8_sbom.get("automated") is True
        ), f"{name}: CC8 SBOM entry should be automated=true"


# ===========================================================================
# Profile descriptors — ci_targets
# ===========================================================================


class TestDescriptorCiTargets:
    @pytest.mark.parametrize(
        "name", ["python-fastapi", "python-flask", "typescript-next"]
    )
    def test_sbom_in_ci_targets(self, name):
        d = _descriptor(name)
        ci_targets = d.get("ci_targets", [])
        assert (
            "sbom" in ci_targets
        ), f"{name}.yaml: 'sbom' not listed in ci_targets (got: {ci_targets})"


# ===========================================================================
# Profile descriptors — generates / templates reference sbom.json
# ===========================================================================


class TestDescriptorSbomFileReference:
    @pytest.mark.parametrize("name", ["python-fastapi", "python-flask"])
    def test_sbom_json_in_generates_files(self, name):
        d = _descriptor(name)
        files = d.get("generates", {}).get("files", [])
        paths = [f.get("path", "") for f in files]
        assert (
            "sbom.json" in paths
        ), f"{name}.yaml: sbom.json not found in generates.files (got: {paths})"

    def test_sbom_json_in_typescript_templates(self):
        d = _descriptor("typescript-next")
        templates = d.get("templates", [])
        paths = [t.get("path", "") for t in templates]
        assert (
            "sbom.json" in paths
        ), f"typescript-next.yaml: sbom.json not found in templates (got: {paths})"


# ===========================================================================
# CI workflow
# ===========================================================================


class TestCiWorkflowSbom:
    def test_ci_template_has_sbom_verification_step(self):
        content = _CI_TEMPLATE.read_text()
        assert "sbom" in content.lower(), "ci-template.yml has no SBOM-related step"

    def test_ci_template_sbom_step_checks_all_layer2_profiles(self):
        content = _CI_TEMPLATE.read_text()
        assert "python-fastapi" in content
        assert "python-flask" in content
        assert "typescript-next" in content

    def test_ci_template_sbom_grep_command(self):
        content = _CI_TEMPLATE.read_text()
        assert (
            'grep -q "^sbom:"' in content
        ), "ci-template.yml should verify sbom target via grep"
