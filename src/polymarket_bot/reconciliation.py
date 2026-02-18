from dataclasses import dataclass

from .models import BookSnapshot


@dataclass(frozen=True)
class ReconciliationResult:
    ok: bool
    used_snapshot_recovery: bool
    reason: str


def reconcile_order_book(
    current_sequence: int,
    incoming_sequence: int,
    snapshot: BookSnapshot | None,
) -> ReconciliationResult:
    """Reconcile incremental sequence with optional snapshot fallback."""

    if incoming_sequence == current_sequence + 1:
        return ReconciliationResult(ok=True, used_snapshot_recovery=False, reason="incremental")

    if incoming_sequence <= current_sequence:
        return ReconciliationResult(ok=False, used_snapshot_recovery=False, reason="stale event")

    if snapshot is None:
        return ReconciliationResult(
            ok=False,
            used_snapshot_recovery=False,
            reason="sequence gap without snapshot",
        )

    if snapshot.sequence >= incoming_sequence - 1:
        return ReconciliationResult(
            ok=True,
            used_snapshot_recovery=True,
            reason="gap recovered by snapshot",
        )

    return ReconciliationResult(
        ok=False,
        used_snapshot_recovery=True,
        reason="snapshot too old",
    )
