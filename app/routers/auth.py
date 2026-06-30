from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.models.schemas import UserRegisterRequest, TokenResponse
from app.models.user import get_user, create_user
from app.auth.security import hash_password, verify_password, create_access_token

router = APIRouter()


@router.post("/auth/register", response_model=TokenResponse)
def register(request: UserRegisterRequest):
    if get_user(request.email):
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    hashed = hash_password(request.password)
    user = create_user(request.email, hashed)
    token = create_access_token(user_id=user.user_id, email=user.email)
    return TokenResponse(access_token=token)


@router.post("/auth/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user_id=user.user_id, email=user.email)
    return TokenResponse(access_token=token)
