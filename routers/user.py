from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.automap import automap_base
import sqlalchemy

from configs.config import database_config as cfg
from entities.user import Users
from routers.authentication import get_current_admin, get_current_user, get_password_hash

DATABASE_URL = cfg['url']
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = automap_base()
Base.prepare(autoload_with=engine)
UsersDB = Base.classes.Users

router = APIRouter(prefix="/users",)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
##############################################################################################
Router for users table 
##############################################################################################
"""

# Create a new user
@router.post("/create")
def create_user(user: Users, db: Session = Depends(get_db)):
    db_user = UsersDB(**user.model_dump())
    hashed_password = get_password_hash(db_user.Password)
    db_user.Password = hashed_password
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(status_code=403, detail="Email already exists.")

# Get a user by ID
@router.get("/read/")
def read_user(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user = db.query(UsersDB).filter_by(ID=current_user.ID).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Update a user by ID
@router.put("/update/")
def update_user(updated_user: Users, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if updated_user.ID is not None:
        if updated_user.ID != current_user.ID:
            raise HTTPException(status_code=403, detail="Access forbidden")
    user = db.query(UsersDB).filter_by(ID=current_user.ID).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in updated_user.model_dump().items():
        if key=='Password' and value != user.Password:
            setattr(user, key, get_password_hash(value))
        else:
            setattr(user, key, value)
    setattr(user, 'ID', current_user.ID)
    db.commit()
    db.refresh(user)
    return user

# Delete a user by ID
@router.delete("/delete/", status_code=204)
def delete_user(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user = db.query(UsersDB).filter_by(ID=current_user.ID).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return 'Success'

# Get all users
@router.get("/")
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: dict = Depends(get_current_admin)):
    users = db.query(UsersDB).offset(skip).limit(limit).all()
    return users