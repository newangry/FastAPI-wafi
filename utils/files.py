import joblib
import os
import AI
from langchain.memory import ConversationBufferMemory
from datetime import datetime

def save_file_with_id(file_content, file_name:str, chat_id):
    """
    Saves the pdf to a file using joblib.

    Parameters:
    - pdf: The pdf object to save.
    - chat_id: ID of the bot, to be used as the filename.
    - save_path: Directory where the pdf will be saved. Defaults to the pdfs directory.

    Returns:
    - str: Full path to the saved file.
    """
    splited_name = file_name.split(".")
    extension = splited_name[len(splited_name)-1]

    save_path="./files/"
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # Create a filename based on the bot ID and save to the desired directory

    file_path = os.path.join(save_path, f"{chat_id}.{extension}")
    with open(file_path, "wb") as f_out:
        f_out.write(file_content)
    
    knowledgeBase = AI.create_knowledge_base(file_path, chat_id)
    # file_name = f"{chat_id}_kb.joblib"
    # full_path = os.path.join(save_path, file_name)
    # joblib.dump(knowledgeBase, full_path)
    return ''
    
def load_pdf_with_id(chat_id, load_path="./files/"):
    """
    Loads the pdf from a file using joblib.

    Parameters:
    - chat_id: ID of the bot, which is also the filename.
    - load_path: Directory from which the pdf will be loaded. Defaults to the pdfs directory.

    Returns:
    - The loaded pdf object.
    """
    file_name = f"{chat_id}.pdf"
    full_path = os.path.join(load_path, file_name)

    # Check if file exists
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"PDF with ID {chat_id} not found at {full_path}")


    with open(full_path, "rb") as f:
        pdf_content = f.read()
        
    return pdf_content

def load_knowledge_base_with_id(chat_id, load_path="./pdfs/"):
    """
    Loads the KnowledgeBase from a file using joblib.

    Parameters:
    - chat_id: ID of the bot, which is also the filename.
    - load_path: Directory from which the KnowledgeBase will be loaded. Defaults to the pdfs directory.
    
    Returns:
    - The loaded KnowledgeBase object.
    """
    file_name = f"{chat_id}_kb.joblib"
    full_path = os.path.join(load_path, file_name)

    # Check if file exists
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"KnowledgeBase with ID {chat_id} not found at {full_path}")
    
    knowledgeBase = joblib.load(full_path)
    return knowledgeBase

def save_chat_memory_with_id(chat_id, save_path="./chat_memory/", memory=None, history=None):
    """
    Creates and saves the chat memory to a file using joblib.

    Parameters:
    - chat_id: ID of the chat, to be used as the filename.
    - save_path: Directory where the chat memory will be saved. Defaults to the chat_memory directory.

    Returns:
    - str: Full path to the saved file.
    """

    if not os.path.exists(save_path):
        os.makedirs(save_path)
        
    if not memory:
        memory = ConversationBufferMemory(memory_key="chat_history", input_key="human_input")
    
    if not history:
        history = []
    
    file_name = f"{chat_id}.joblib"
    full_path = os.path.join(save_path, file_name)
    joblib.dump(memory, full_path)
    
    file_name = f"{chat_id}_history.joblib"
    full_path = os.path.join(save_path, file_name)
    if not history:
        history = []
    joblib.dump(history, full_path)
    return full_path

def load_chat_memory_with_id(chat_id, load_path="./chat_memory/"):
    """
    Loads the chat memory from a file using joblib.

    Parameters:
    - chat_id: ID of the chat, which is also the filename.
    - load_path: Directory from which the chat memory will be loaded. Defaults to the chat_memory directory.

    Returns:
    - The loaded chat memory object.
    """
    file_name = f"{chat_id}.joblib"
    full_path = os.path.join(load_path, file_name)
    
    # Check if file exists
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Chat memory with ID {chat_id} not found at {full_path}")

    memory = joblib.load(full_path)
    return memory

def load_chat_history_with_id(chat_id, load_path="./chat_memory/"):
    file_name = f"{chat_id}_history.joblib"
    full_path = os.path.join(load_path, file_name)
    history=[]
    # Check if file exists
    if not os.path.exists(full_path):
        print(f"Chat history with ID {chat_id} not found at {full_path}")
        # raise FileNotFoundError(f"Chat history with ID {chat_id} not found at {full_path}")
    else:
        history = joblib.load(full_path)
    return history

def update_chat_history(chat_id, message, date_recieved, response, emo, load_path="./chat_memory/"):

    file_name = f"{chat_id}_history.joblib"
    full_path = os.path.join(load_path, file_name)

    # Check if file exists
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Chat history with ID {chat_id} not found at {full_path}")

    history = joblib.load(full_path)

    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    converse = {
        "Human": {
            "message": message,
            "date": date_recieved
        },
        "AI": {
            "message": response,
            "emotion": emo,
            "date": date_now
        }
    }

    history.append(converse)
    joblib.dump(history, full_path)

    return history