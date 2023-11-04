from fastapi import Depends, APIRouter, HTTPException, UploadFile, File
from routers.authentication import get_current_admin, get_current_user
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.automap import automap_base
from datetime import datetime
from fastapi.responses import StreamingResponse
from configs.config_settings import database_config as cfg
from entities.chat import Chats
from utils import files
import AI
import tempfile
import shutil
from utils import vectordb
import asyncio

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

# Create a new chats with file
@router.post("/create/")
def create_chats(title: str, chat_id: int, user_type: str, file: UploadFile = File(...) ,db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # user_type = current_user.UserType
    db_chat = ChatsDB(Title=title, DateCreated=datetime.now(), UserID=current_user.ID, ChatId=chat_id)
    
    if user_type != "admin":
        raise HTTPException(status_code=402, detail=str("Sigin with Admin"))
    try:
        db.add(db_chat)
        db.commit()
        db.refresh(db_chat)
        file_content = file.file.read()
        file_name = file.filename
        files.save_file_with_id(file_content, file_name, db_chat.ID)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
    # Save the chat memory using joblib
    files.save_chat_memory_with_id(db_chat.ID)
    return db_chat

# Create a new chat with general user
@router.post("/new_chat/")
def create_chats(title: str = "", db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        db_chat = ChatsDB(Title=title, DateCreated=datetime.now(), UserID=current_user.ID, ChatId=-1)
        db.add(db_chat)
        db.commit()
        db.refresh(db_chat)
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
def read_chats(user_type: str, chat_id: int, skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: dict = Depends(get_current_admin)):
    user_type_ = current_user.UserType
    if user_type_ != "user" and user_type_ == "user":
        raise HTTPException(status_code=404, detail="Chat not found")
    data = []
    chats = db.query(ChatsDB).filter_by(UserID=current_user.ID, ChatId=chat_id).order_by(desc(ChatsDB.DateCreated)).offset(skip).limit(limit).all()
    if user_type == "user":
        for chat in chats:
            id = getattr(chat, 'ID', None )
            chat_history = files.load_chat_history_with_id(id)
            last_message = {"message": '',"date": ''}
            if len(chat_history) > 0:
                last_message = chat_history[len(chat_history)-1]["Human"]
            last_message["ID"] = id
            last_message['ChatId'] =  getattr(chat, 'ChatId', None )
            data.append(last_message)
    else:
        for chat in chats:
           data.append(chat)
    return data
# Create a new message
@router.post("/new_message/")
def converse(chat_id: int, new_message: str, user_type: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = db.query(ChatsDB).filter_by(UserID=current_user.ID, ID=chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    # memory = files.load_chat_memory_with_id(chat_id)
    query = new_message
    if user_type == "admin":
        
        context ="You are a hobbyist bot that provides friendly answers to the user. If you not sure the result, `Please answer only I'm not sure based on uploaded data`"
        context = context+vectordb.get_context_with_id(chat_id, query)
        print("---------Context Syart------")
        print(context)
        print("---------Context End------")
        context+=query
    else:
        context = query
    return StreamingResponse(AI.get_openai_generator(context), media_type='text/event-stream')

    # response = AI.get_response(context, memory, query, 'text')
    # history = files.update_chat_history(
    #     chat_id,
    #     query,
    #     date_now,
    #     response['response'],
    #     response['emotion']
    # )
    # # Save the chat memory using joblib
    # files.save_chat_memory_with_id(chat_id=chat_id, memory=memory, history=history)
    # return response
@router.post("/save_history")
def save_history(ai: str, message: str, chat_id: int, emotion,current_user: dict = Depends(get_current_user)):
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history = files.update_chat_history(
        chat_id,
        message,
        date_now,
        ai,
        emotion
    )
    return ''

@router.post("/tts")
async def text_to_speech(text: str, current_user: dict = Depends(get_current_user)):
    speech = AI.convert_text_to_speech(text) 
    emotion = AI.detect_emo(text)
    return {
        "speech": speech,
        "emotion": emotion
    }
    
@router.post("/transcribe/")
async def transcribe_audio(audio_file: UploadFile, current_user: dict = Depends(get_current_user)):
    temp_dir = tempfile.TemporaryDirectory()
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True, dir=temp_dir.name) as temp_audio_file:
        shutil.copyfileobj(audio_file.file, temp_audio_file)
        return AI.transcribe(temp_audio_file.name)