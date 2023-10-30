from entities.user import Users
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.automap import automap_base
import requests

from configs import config_settings


lac = config_settings.login_auths_config
cfg = config_settings.database_config

gac = config_settings.google_auth_config


DATABASE_URL = cfg['url']
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = automap_base()
Base.prepare(autoload_with=engine)
UsersDB = Base.classes.Users
db = SessionLocal()

router = APIRouter(prefix="/users",)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class login_info(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user_by_email(email: str):
    print(email)
    return db.query(UsersDB).filter_by(Email=email).first()
    
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, lac['SECRET_KEY'], algorithm=lac['ALGORITHM'])
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, lac['SECRET_KEY'], algorithms=[lac['ALGORITHM']])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_admin(user: dict = Depends(get_current_user)):
    if user.IsSuperUser==False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You're not an admin",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post("/login")
def login_for_access_token(form_data: login_info = Depends(),):
    user = get_user_by_email(form_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    verified = verify_password(form_data.password, user.Password)
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=lac['ACCESS_TOKEN_EXPIRE_MINUTES'])
    access_token = create_access_token(
        data={"sub": user.Email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/google")
def login_for_access_token_with_google(code: str):
    # Step 1: Exchange authorization code for access token
    data = {
        'code': code,
        'client_id': gac['CLIENT_ID'],
        'client_secret': gac['CLIENT_SECRET'],
        'redirect_uri': gac['REDIRECT_URI'],
        'grant_type': 'authorization_code'
    }
    response = requests.post(gac['TOKEN_ENDPOINT'], data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve access token.")
    
    token_data = response.json()
    access_token = token_data['access_token']

    # Step 2: Fetch user's profile data
    headers = {
        'Authorization': f"Bearer {access_token}"
    }
    response = requests.get(gac['USERINFO_ENDPOINT'], headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve user information.")

    user_data = response.json()
    user_email = user_data['email']

    user = db.query(UsersDB).filter_by(Email=user_email).first()
    if not user:
        new_user = UsersDB(Email=user_email)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user
    
    access_token_expires = timedelta(minutes=lac['ACCESS_TOKEN_EXPIRE_MINUTES'])
    access_token = create_access_token(
        data={"sub": user.Email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

@router.get("/me/super")
def read_users_me(current_user: dict = Depends(get_current_admin)):
    return current_user

@router.post("/logout")
def logout():
    return {"message": "Successfully logged out"}