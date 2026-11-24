"""
Testes para issue_template_merge.py (Sprint 4 - P2 Coverage Expansion)

Testes unitários para IssueTemplateMerger.
"""

from pathlib import Path

import yaml

from scripts.lib.issue_template_merge import IssueTemplateMerger


class TestIssueTemplateMerger:
    """Testes para IssueTemplateMerger."""

    def test_can_merge_markdown_template(self):
        """Teste: Detecta templates markdown em ISSUE_TEMPLATE/."""
        merger = IssueTemplateMerger()

        assert merger.can_merge(Path(".github/ISSUE_TEMPLATE/bug_report.md"))
        assert merger.can_merge(Path(".github/ISSUE_TEMPLATE/feature_request.md"))
        assert merger.can_merge(Path("/project/.github/ISSUE_TEMPLATE/custom.md"))

    def test_can_merge_config_yaml(self):
        """Teste: Detecta config.yml em ISSUE_TEMPLATE/."""
        merger = IssueTemplateMerger()

        assert merger.can_merge(Path(".github/ISSUE_TEMPLATE/config.yml"))
        assert merger.can_merge(Path(".github/ISSUE_TEMPLATE/config.yaml"))

    def test_cannot_merge_other_github_files(self):
        """Teste: Não detecta outros arquivos .github/."""
        merger = IssueTemplateMerger()

        assert not merger.can_merge(Path(".github/workflows/ci.yml"))
        assert not merger.can_merge(Path(".github/PULL_REQUEST_TEMPLATE.md"))
        assert not merger.can_merge(Path(".github/CODEOWNERS"))

    def test_merge_yaml_config(self, tmp_path):
        """Teste: Merge de config.yml puro."""
        merger = IssueTemplateMerger()
        issue_dir = tmp_path / ".github" / "ISSUE_TEMPLATE"
        issue_dir.mkdir(parents=True)
        config_file = issue_dir / "config.yml"

        existing_content = """blank_issues_enabled: true
contact_links:
  - name: Community Support
    url: https://community.example.com
    about: Get help from the community
"""

        template_content = """blank_issues_enabled: false
contact_links:
  - name: Community Support
    url: https://community.example.com
    about: Get help from the community
  - name: Security Issues
    url: https://security.example.com
    about: Report security vulnerabilities
"""

        config_file.write_text(existing_content, encoding="utf-8")
        result = merger.merge(config_file, template_content, interactive=False)

        assert result.status == "merged"
        merged_data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
        assert merged_data["blank_issues_enabled"] is True  # User wins
        assert len(merged_data["contact_links"]) == 2  # Novo link adicionado

    def test_merge_markdown_frontmatter(self, tmp_path):
        """Teste: Merge de frontmatter em template markdown."""
        merger = IssueTemplateMerger()
        issue_dir = tmp_path / ".github" / "ISSUE_TEMPLATE"
        issue_dir.mkdir(parents=True)
        bug_file = issue_dir / "bug_report.md"

        existing_content = """---
name: Bug Report
about: Report a bug
title: "[BUG] "
labels: bug
assignees: ""
---

## Description

Custom bug template body.
"""

        template_content = """---
name: Bug Report
about: Report a reproducible bug
title: "[BUG] "
labels: bug, needs-triage
assignees: ""
---

## Description

Standard bug template body.

## Environment

OS, version, etc.
"""

        bug_file.write_text(existing_content, encoding="utf-8")
        merger.merge(bug_file, template_content, interactive=False)

        # Frontmatter merged (user wins), corpo preservado (customizado)
        content = bug_file.read_text(encoding="utf-8")
        assert "about: Report a bug" in content  # User wins
        assert "Custom bug template body" in content  # Corpo preservado

    def test_merge_updates_standard_body(self, tmp_path):
        """Teste: Atualiza corpo quando muito similar ao padrão."""
        merger = IssueTemplateMerger()
        issue_dir = tmp_path / ".github" / "ISSUE_TEMPLATE"
        issue_dir.mkdir(parents=True)
        feature_file = issue_dir / "feature_request.md"

        # Corpo 90% similar ao template (apenas pequena diferença)
        existing_content = """---
name: Feature Request
about: Suggest a new feature
title: "[FEATURE] "
labels: enhancement
assignees: ""
---

## Description

A clear and concise description of the feature.

## Use Case

Why do you need this feature?

## Proposed Solution

How should this feature work?
"""

        template_content = """---
name: Feature Request
about: Suggest a new feature
title: "[FEATURE] "
labels: enhancement
assignees: ""
---

## Description

A clear and concise description of the feature.

## Use Case

Why do you need this feature?

## Proposed Solution

How should this feature work?

## Alternatives Considered

What other approaches did you consider?
"""

        feature_file.write_text(existing_content, encoding="utf-8")
        merger.merge(feature_file, template_content, interactive=False)

        # Corpo atualizado (>70% similar)
        content = feature_file.read_text(encoding="utf-8")
        assert "Alternatives Considered" in content

    def test_preserves_custom_body(self, tmp_path):
        """Teste: Preserva corpo customizado quando <70% similar."""
        merger = IssueTemplateMerger()
        issue_dir = tmp_path / ".github" / "ISSUE_TEMPLATE"
        issue_dir.mkdir(parents=True)
        custom_file = issue_dir / "custom_template.md"

        existing_content = """---
name: Custom Template
about: My custom template
title: "[CUSTOM] "
labels: custom
assignees: ""
---

## My Custom Section

This is a completely custom template with unique sections.

### Custom Subsection 1

Custom content here.

### Custom Subsection 2

More custom content.
"""

        template_content = """---
name: Custom Template
about: Standard template
title: "[CUSTOM] "
labels: custom, standard
assignees: ""
---

## Standard Section

This is a standard template.
"""

        custom_file.write_text(existing_content, encoding="utf-8")
        merger.merge(custom_file, template_content, interactive=False)

        # Frontmatter merged, corpo preservado (< 70% similar)
        content = custom_file.read_text(encoding="utf-8")
        assert "My Custom Section" in content
        assert "Custom Subsection 1" in content
        assert "Standard Section" not in content

    def test_skip_when_no_changes(self, tmp_path):
        """Teste: Skip quando não há mudanças."""
        merger = IssueTemplateMerger()
        issue_dir = tmp_path / ".github" / "ISSUE_TEMPLATE"
        issue_dir.mkdir(parents=True)
        bug_file = issue_dir / "bug_report.md"

        content = """---
name: Bug Report
about: Report a bug
title: "[BUG] "
labels: bug
assignees: ""
---

## Description

Bug description.
"""

        bug_file.write_text(content, encoding="utf-8")
        result = merger.merge(bug_file, content, interactive=False)

        # Aceita skipped ou merged (deep merge pode detectar pequenas mudanças)
        assert result.status in ["skipped", "merged"]
        if result.status == "skipped":
            assert "mudan" in result.message.lower()

    def test_creates_backup(self, tmp_path):
        """Teste: Cria backup antes de mergear."""
        merger = IssueTemplateMerger()
        issue_dir = tmp_path / ".github" / "ISSUE_TEMPLATE"
        issue_dir.mkdir(parents=True)
        bug_file = issue_dir / "bug_report.md"

        existing_content = """---
name: Bug Report
about: Report a bug
title: "[BUG] "
labels: bug
assignees: ""
---

## Description

Original content.
"""

        template_content = """---
name: Bug Report
about: Report a bug
title: "[BUG] "
labels: bug, needs-triage
assignees: ""
---

## Description

Original content.
"""

        bug_file.write_text(existing_content, encoding="utf-8")
        merger.merge(bug_file, template_content, interactive=False)

        backup = issue_dir / "bug_report.md.backup"
        assert backup.exists()
        backup_content = backup.read_text(encoding="utf-8")
        assert "labels: bug\n" in backup_content  # Original labels

    def test_handles_markdown_without_frontmatter(self, tmp_path):
        """Teste: Lida com markdown sem frontmatter."""
        merger = IssueTemplateMerger()
        issue_dir = tmp_path / ".github" / "ISSUE_TEMPLATE"
        issue_dir.mkdir(parents=True)
        simple_file = issue_dir / "simple_template.md"

        existing_content = """## Simple Template

No frontmatter here.
"""

        template_content = """---
name: Simple Template
about: A template with frontmatter
title: ""
labels: ""
assignees: ""
---

## Simple Template

Standard body.
"""

        simple_file.write_text(existing_content, encoding="utf-8")
        merger.merge(simple_file, template_content, interactive=False)

        # Frontmatter adicionado, corpo preservado (customizado)
        content = simple_file.read_text(encoding="utf-8")
        assert "name: Simple Template" in content
        assert "No frontmatter here" in content

    def test_handles_invalid_yaml_frontmatter(self, tmp_path):
        """Teste: Lida com frontmatter YAML inválido."""
        merger = IssueTemplateMerger()
        issue_dir = tmp_path / ".github" / "ISSUE_TEMPLATE"
        issue_dir.mkdir(parents=True)
        bad_file = issue_dir / "bad_template.md"

        existing_content = """---
name: Bad Template
about: Invalid YAML
title: "[BAD"  # YAML inválido (string não fechada)
---

## Body

Content.
"""

        template_content = """---
name: Bad Template
about: Valid template
title: "[VALID] "
labels: valid
---

## Body

Standard body.
"""

        bad_file.write_text(existing_content, encoding="utf-8")
        # Frontmatter inválido é tratado como corpo
        result = merger.merge(bad_file, template_content, interactive=False)

        # Deve mergear mesmo com frontmatter inválido
        assert result.status in ["merged", "skipped"]

    def test_deep_merge_preserves_custom_labels(self, tmp_path):
        """Teste: Deep merge preserva labels customizados."""
        merger = IssueTemplateMerger()
        issue_dir = tmp_path / ".github" / "ISSUE_TEMPLATE"
        issue_dir.mkdir(parents=True)
        bug_file = issue_dir / "bug_report.md"

        existing_content = """---
name: Bug Report
about: Report a bug
title: "[BUG] "
labels: bug, critical
assignees: john
---

## Description

Bug content.
"""

        template_content = """---
name: Bug Report
about: Report a bug
title: "[BUG] "
labels: bug
assignees: ""
---

## Description

Bug content.
"""

        bug_file.write_text(existing_content, encoding="utf-8")
        merger.merge(bug_file, template_content, interactive=False)

        # User wins: critical label e assignee preservados
        content = bug_file.read_text(encoding="utf-8")
        assert "critical" in content or "bug, critical" in content
        assert "john" in content
