"""Celery tasks package"""

from app.tasks.claim_tasks import (
    process_claim_satellite_verification,
    process_claim_weighted_algorithm,
    process_claim_payment,
    process_claim_workflow
)

__all__ = [
    "process_claim_satellite_verification",
    "process_claim_weighted_algorithm",
    "process_claim_payment",
    "process_claim_workflow"
]
