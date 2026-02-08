import os
from typing import Optional

from fastapi import Header, HTTPException, Query, status


def require_portal_token(
    token: Optional[str] = Query(default=None, description="Portal auth token (for EventSource)."),
    x_researchvault_token: Optional[str] = Header(default=None, alias="X-ResearchVault-Token"),
) -> None:
    """Default-deny auth guard.

    Note: Browser EventSource does not support custom headers, so we accept the token
    via a `?token=...` query param as well.
    """

    expected = os.getenv("RESEARCHVAULT_PORTAL_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Portal token not configured (set RESEARCHVAULT_PORTAL_TOKEN).",
        )

    provided = x_researchvault_token or token
    if not provided or provided != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
