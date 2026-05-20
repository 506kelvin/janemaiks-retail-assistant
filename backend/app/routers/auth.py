from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..auth import create_access_token, get_current_user
from ..config import DEFAULT_USERNAME, DEFAULT_PASSWORD

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    name: str
    role: str


class UserInfo(BaseModel):
    username: str
    name: str
    role: str


@router.post("/api/auth/login", response_model=LoginResponse)
def login(req: LoginRequest):
    if req.username != DEFAULT_USERNAME or req.password != DEFAULT_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": DEFAULT_USERNAME, "name": "JaneMaiks Staff", "role": "admin"})
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        name="JaneMaiks Staff",
        role="admin",
    )


@router.get("/api/auth/me", response_model=UserInfo)
def me(current_user: dict = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return UserInfo(
        username=current_user.get("sub", ""),
        name=current_user.get("name", ""),
        role=current_user.get("role", ""),
    )
