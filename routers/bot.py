from fastapi import Depends, APIRouter, HTTPException, UploadFile, File
from routers.authentication import get_current_admin, get_current_user
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.automap import automap_base

from configs.config_settings import database_config as cfg
from entities.bot import Bots
from utils import files


DATABASE_URL = cfg['url']
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = automap_base()
Base.prepare(autoload_with=engine)
BotsDB = Base.classes.Bots

router = APIRouter(prefix="/bots",)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
##############################################################################################
Router for bots table 
##############################################################################################
"""

# Create a new bots
@router.post("/create/")
async def create_bots(pdf: UploadFile = File(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        db_bot = BotsDB(UserID=current_user.ID)
        db.add(db_bot)
        db.commit()
        db.refresh(db_bot)
        pdf_content = pdf.file.read()
        print('b')
        files.save_pdf_with_id(pdf_content, db_bot.ID)
        print('a')
        return db_bot
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Get a bots by ID
@router.get("/read/{bot_id}")
def read_bots(bot_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    bot = db.query(BotsDB).filter_by(ID=bot_id).first()

    pdf = files.load_pdf_with_id(bot.ID)

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot

# # Update a bots by ID
# @router.put("/update/")
# def update_bots(updated_bot: Bots, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
#     bot = db.query(BotsDB).filter_by(ID=updated_bot.ID).first()
#     if not bot:
#         raise HTTPException(status_code=404, detail="Bot not found")
#     for key, value in updated_bot.model_dump().items():
#         setattr(bot, key, value)
#     db.commit()
#     db.refresh(bot)
#     return bot

# Delete a bots by ID
@router.delete("/delete/{bot_id}", status_code=204)
def delete_bots(bot_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    bot = db.query(BotsDB).filter_by(ID=bot_id, UserID=current_user.ID).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    db.delete(bot)
    db.commit()
    return 'Sucsess'

# Get all bots
@router.get("/")
def read_bots(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: dict = Depends(get_current_admin)):
    bots = db.query(BotsDB).offset(skip).limit(limit).all()
    return bots

# Get a bots by ID of User
@router.get("/read_by_user_id/")
def read_bots(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    bots = db.query(BotsDB).filter_by(UserID=current_user.ID).all()
    if not bots:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bots
