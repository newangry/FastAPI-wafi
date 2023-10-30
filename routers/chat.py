from fastapi import Depends, APIRouter, HTTPException, UploadFile, File
from routers.authentication import get_current_admin, get_current_user
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.automap import automap_base
from datetime import datetime

from configs.config_settings import database_config as cfg
from entities.chat import Chats
from utils import files
import AI
import tempfile
import shutil
from utils import vectordb

DATABASE_URL = cfg['url']
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = automap_base()
Base.prepare(autoload_with=engine)
ChatsDB = Base.classes.Chats

router = APIRouter(prefix="/chats",)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
##############################################################################################
New message
##############################################################################################
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date, time, datetime

class NewMessage(BaseModel):
    ChatID: Optional[int] = None
    InputType: Optional[str] = 'text'


"""
##############################################################################################
Router for chats table 
##############################################################################################
"""

# Create a new chats
@router.post("/create/")
def create_chats(title: str, pdf: UploadFile = File(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        db_chat = ChatsDB(Title=title, DateCreated=datetime.now(), UserID=current_user.ID)
        db.add(db_chat)
        db.commit()
        db.refresh(db_chat)
        pdf_content = pdf.file.read()
        files.save_pdf_with_id(pdf_content, db_chat.ID)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
    # Save the chat memory using joblib
    files.save_chat_memory_with_id(db_chat.ID)
    return db_chat

# Get a chat by ID
@router.get("/read/{chat_id}")
def read_chats(chat_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    chat = db.query(ChatsDB).filter_by(ID=chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat_history = files.load_chat_history_with_id(chat_id)
    
    return {'chat': chat, 'chat_history': chat_history}

# Get all chats
@router.get("/")
def read_chats(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: dict = Depends(get_current_admin)):
    chats = db.query(ChatsDB).filter_by(UserID=current_user.ID).order_by(desc(ChatsDB.DateCreated)).offset(skip).limit(limit).all()
    return chats

# Create a new message
@router.post("/new_message/")
def converse(chat_id: int, new_message: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = db.query(ChatsDB).filter_by(UserID=current_user.ID, ID=chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    query = new_message
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # knowledgeBase = files.load_knowledge_base_with_id(chat_id)
    context = vectordb.get_context_with_id(f"wafi-{chat_id}", query)
    memory = files.load_chat_memory_with_id(chat_id)

    print(context)

    response = AI.get_response(context, memory, query, 'text')
    history = files.update_chat_history(
        chat_id,
        query,
        date_now,
        response['response'],
        response['emotion']
    )
    # Save the chat memory using joblib
    files.save_chat_memory_with_id(chat_id=chat_id, memory=memory, history=history)
    return response

@router.post("/tts")
async def text_to_speech(text: str, current_user: dict = Depends(get_current_user)):
    return AI.mimic3_tts(text)

@router.post("/transcribe/")
async def transcribe_audio(audio_file: UploadFile, current_user: dict = Depends(get_current_user)):
    temp_dir = tempfile.TemporaryDirectory()
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True, dir=temp_dir.name) as temp_audio_file:
        shutil.copyfileobj(audio_file.file, temp_audio_file)
        return AI.transcribe(temp_audio_file.name)