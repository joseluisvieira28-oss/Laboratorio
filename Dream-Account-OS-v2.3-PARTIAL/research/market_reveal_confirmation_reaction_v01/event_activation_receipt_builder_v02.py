"""Build tamper-evident MRCR H02 event activation receipts V0.2.

This builder consumes normalized official T0 evidence. It cannot authorize
TARGET_OBSERVATION_OPEN or outcomes.
"""

from __future__ import annotations

from typing import Any, Mapping

from h02_calendar_binding_v02 import event_activation_sha256
from official_event_t0_extractor_v02 import OfficialT0Evidence


def build_event_activation_receipt_v02(
    *,
    event_id: str,
    evidence: OfficialT0Evidence,
    confirmed_at_utc: str,
    primary_official_source_url: str,
    supporting_official_sources: list[Mapping[str, Any]],
) -> dict[str, Any]:
    authority = (
        "FEDERAL_RESERVE"
        if evidence.event_family == "FOMC_STATEMENT"
        else "BLS"
    )
    receipt: dict[str, Any] = {
        "document_type": "MRCR_H02_EVENT_ACTIVATION_RECEIPT_V02",
        "lab_id": "MARKET-REVEAL-CONFIRMATION-REACTION-001",
        "h02_id": "MRCR-H02-ACCEPTANCE-REJECTION-V01",
        "event_id": event_id,
        "event_family": evidence.event_family,
        "scheduled_time_utc": evidence.scheduled_time_utc,
        "scheduled_date": evidence.scheduled_date,
        "confirmed_at_utc": confirmed_at_utc,
        "official_authority": authority,
        "official_source_url": primary_official_source_url,
        "official_status": "OFFICIAL_CONFIRMED_FOR_CAPTURE",
        "confirmation_mode": evidence.confirmation_mode,
        "evidence_roles": list(evidence.evidence_roles),
        "supporting_official_sources": [
            dict(row) for row in supporting_official_sources
        ],
        "target_observation_authorized": False,
        "outcomes_authorized": False,
        "promotion_credit": "NONE",
        "activation_receipt_sha256": None,
    }
    receipt["activation_receipt_sha256"] = event_activation_sha256(receipt)
    return receipt
