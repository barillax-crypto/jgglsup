from fastapi import Header, HTTPException


def get_tenant_context(
    x_org_id: str | None = Header(default=None),
    x_user_role: str | None = Header(default="viewer"),
) -> tuple[str, str]:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="Missing X-Org-Id header")
    return x_org_id, (x_user_role or "viewer")


def require_role(current_role: str, allowed_roles: set[str]) -> None:
    if current_role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Insufficient role")
