"""Base class for CedarBench mutations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MutationResult:
    schema: str
    policy_spec: str


@dataclass
class MutationMeta:
    id: str
    base_scenario: str  # key into BASE_SCENARIOS
    difficulty: str  # "easy", "medium", "hard"
    description: str
    operators: list[str]  # e.g. ["S1", "P1"]
    features_tested: list[str]  # e.g. ["boolean_guard", "forbid_rule"]


class Mutation(ABC):
    """A mutation that transforms a base scenario into a variant."""

    @abstractmethod
    def meta(self) -> MutationMeta:
        """Return metadata about this mutation."""

    @abstractmethod
    def apply(self, base_schema: str) -> MutationResult:
        """Apply this mutation to a base schema, returning new schema + NL spec."""


# Registry of all mutations, populated by each domain module
_REGISTRY: dict[str, Mutation] = {}


def register(mutation: Mutation) -> Mutation:
    """Register a mutation in the global registry."""
    m = mutation.meta()
    _REGISTRY[m.id] = mutation
    return mutation


def get_all_mutations() -> dict[str, Mutation]:
    return dict(_REGISTRY)


def get_mutations_for_domain(domain: str) -> dict[str, Mutation]:
    return {k: v for k, v in _REGISTRY.items() if v.meta().base_scenario == domain}
