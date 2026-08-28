"""lib/flows — UI flow wrappers (argparse.Namespace → int) para scaffold.py."""

from .adopt import flow_adopt
from .check_links import flow_check_links
from .check_templates import flow_check_templates
from .compose import flow_compose_profiles
from .diff_template import flow_diff_template
from .dry_run import flow_dry_run
from .generate_infra import flow_generate_infra
from .generate_rules import flow_generate_rules
from .list_profiles import _load_descriptor, flow_list_profiles
from .merge_template import flow_merge_template
from .new_profile import flow_new_profile
from .new_project import flow_new_project
from .objetivo_generate import flow_objetivo_generate
from .objetivo_init import flow_objetivo_init
from .objetivo_migrate import flow_objetivo_migrate
from .objetivo_validate import flow_objetivo_validate
from .publish import flow_publish
from .release import flow_release
from .upgrade import flow_upgrade
from .validate import flow_validate

__all__ = [
    "flow_new_project",
    "flow_compose_profiles",
    "flow_upgrade",
    "flow_adopt",
    "flow_dry_run",
    "flow_generate_infra",
    "flow_check_links",
    "flow_check_templates",
    "flow_diff_template",
    "flow_merge_template",
    "flow_publish",
    "flow_release",
    "flow_validate",
    "flow_generate_rules",
    "flow_list_profiles",
    "flow_new_profile",
    "flow_objetivo_validate",
    "flow_objetivo_generate",
    "flow_objetivo_migrate",
    "flow_objetivo_init",
    "_load_descriptor",
]
