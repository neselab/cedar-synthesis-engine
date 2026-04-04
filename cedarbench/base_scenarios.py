"""Registry of base scenarios and their file paths."""

from pathlib import Path
from dataclasses import dataclass


@dataclass
class BaseScenario:
    id: str
    domain: str
    schema_path: Path  # relative to repo root
    policy_path: Path  # .cedar ground truth (for understanding, not copied)
    description: str

    def load_schema(self, repo_root: Path) -> str:
        return (repo_root / self.schema_path).read_text()

    def load_policy(self, repo_root: Path) -> str:
        return (repo_root / self.policy_path).read_text()


BASE_SCENARIOS = {
    "github": BaseScenario(
        id="github",
        domain="github",
        schema_path=Path("experiments/github/schema.cedarschema"),
        policy_path=Path("dataset/github_example/policies.cedar"),
        description="GitHub repository permissions with 5 role tiers, dual-path issue edit/delete, and archive blocking",
    ),
    "doccloud": BaseScenario(
        id="doccloud",
        domain="doccloud",
        schema_path=Path("dataset/document_cloud/policies.cedarschema"),
        policy_path=Path("dataset/document_cloud/policies.cedar"),
        description="Cloud document sharing with ACLs, public access, and mutual blocking",
    ),
    "hotel": BaseScenario(
        id="hotel",
        domain="hotel",
        schema_path=Path("dataset/hotel_chains/static/policies.cedarschema"),
        policy_path=Path("dataset/hotel_chains/static/policies.cedar"),
        description="Hotel chain hierarchical permissions with viewer/member/admin roles",
    ),
    "sales": BaseScenario(
        id="sales",
        domain="sales",
        schema_path=Path("dataset/sales_orgs/static/policies.cedarschema"),
        policy_path=Path("dataset/sales_orgs/static/policies.cedar"),
        description="Sales organization with job-based segmentation and market grouping",
    ),
    "streaming": BaseScenario(
        id="streaming",
        domain="streaming",
        schema_path=Path("dataset/streaming_service/policies.cedarschema"),
        policy_path=Path("dataset/streaming_service/policies.cedar"),
        description="Streaming service with subscription tiers and datetime-based rules",
    ),
    "tags": BaseScenario(
        id="tags",
        domain="tags",
        schema_path=Path("dataset/tags_n_roles/policies.cedarschema"),
        policy_path=Path("dataset/tags_n_roles/policies.cedar"),
        description="Tag-based access control with role-scoped tag namespaces",
    ),
    "tax": BaseScenario(
        id="tax",
        domain="tax",
        schema_path=Path("dataset/tax_preparer/policies.cedarschema"),
        policy_path=Path("dataset/tax_preparer/policies.cedar"),
        description="Tax preparer org-matching with consent and ad-hoc template access",
    ),
    "clinical": BaseScenario(
        id="clinical",
        domain="clinical",
        schema_path=Path("workspace/schema.cedarschema"),
        policy_path=Path("workspace/candidate.cedar"),
        description="Clinical trial platform with multi-role, numeric constraints, and auditor loophole",
    ),
}


def get_repo_root() -> Path:
    """Walk up from this file to find the repo root (contains pyproject.toml)."""
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "pyproject.toml").exists():
            return p
        p = p.parent
    raise RuntimeError("Could not find repo root (no pyproject.toml found)")
