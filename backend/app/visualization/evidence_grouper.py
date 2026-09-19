"""Group visualization recommendations into logical evidence groups."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.visualization.evidence_schema import (
    VisualizationEvidenceProfile,
)


def group_visualization_evidence(
    evidence_profile: VisualizationEvidenceProfile,
) -> dict[str, list[dict[str, Any]]]:
    """
    Group visualization evidence by recommendation rule.

    Each rule remains independent. Grouping only reduces repetition
    when preparing evidence for downstream reasoning.
    """

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for evidence in evidence_profile.evidence:

        grouped[evidence.rule_id].append(
            evidence.model_dump()
        )

    return dict(grouped)