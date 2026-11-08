"""BackgroundTasks: do work after the response has been sent."""
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status

from ..deps import get_audit_log
from ..schemas import Notification, Queued

router = APIRouter(prefix="/background", tags=["background"])

AuditLog = Annotated[list[str], Depends(get_audit_log)]


def record_notification(log: list[str], email: str, message: str) -> None:
    """Stand-in for slow work such as sending an email."""
    log.append(f"to={email} message={message}")


@router.post("/notify", response_model=Queued, status_code=status.HTTP_202_ACCEPTED)
def notify(body: Notification, tasks: BackgroundTasks, log: AuditLog):
    tasks.add_task(record_notification, log, body.email, body.message)
    return Queued()


@router.get("/log", response_model=list[str])
def read_log(log: AuditLog):
    return log
