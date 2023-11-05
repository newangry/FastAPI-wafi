import os
import sqlite3
from configs.config_settings import database_config
from utils.database import sql_to_pydantic

def initialize_database():
    """ Initialize SQLite database. If it doesn't exist, create it. """
    db_path = database_config['url'].split('///')[-1]
    db_dir = os.path.dirname(db_path)
    db_exists = os.path.exists(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    conn = sqlite3.connect(db_path)
    if not db_exists:
        print("Database did not exist, created new DB.")
    conn.close()

def create_tables():
    """ create tables in the SQLite database"""
    user_commands = (
        """
        CREATE TABLE Users (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Email TEXT UNIQUE,
            UserType TEXT,
            Password TEXT,
            AccessToken TEXT UNIQUE,
            AccessTokenCounter INT,
            IsSuperUser BOOLEAN
        )
        """,
    )
    bot_commands = (
        """
        CREATE TABLE Bots (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID INTEGER REFERENCES Users (ID)
        )
        """,
    )
    chat_commands = (
        """
        CREATE TABLE Chats (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Title TEXT,
            DateCreated DATETIME,
            UserID INTEGER REFERENCES Users (ID),
            ChatLocation TEXT,
            SPEECH TEXT,
            Token TEXT,
            ChatId INT
        )
        """,
    )
    command_sets = (
        (user_commands, 'user'), 
        (bot_commands, 'bot'), 
        (chat_commands, 'chat'),
    )
    print(command_sets)
    conn = None
    try:
        conn = sqlite3.connect(database_config['url'].split('///')[-1])
        cur = conn.cursor()
        for commands, name in command_sets:
            print(f'init {name}')
            pydantics = []
            for command in commands:
                try:
                    cur.execute(command)
                except Exception as e:
                    print(command)
                    print(e)   
                pydantics.append(sql_to_pydantic(command))
            pydantics_result = "from pydantic import BaseModel\nfrom typing import Optional\nfrom datetime import date, time\n\n"+"\n\n".join(pydantics)
            with open(f'entities/{name}.py', 'w') as f:
                f.write(pydantics_result)
        conn.commit()
    except Exception as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('closed')

def drop_all_tables():
    conn = sqlite3.connect(database_config['url'].split('///')[-1])
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    for table in tables:
        if table[0] != "sqlite_sequence":
            print(f"Dropping table {table[0]}")
            cur.execute(f"DROP TABLE IF EXISTS {table[0]}")
    conn.commit()
    print("All tables dropped successfully!")

def main():
    initialize_database()
    drop_all_tables()
    create_tables() 

if __name__ == '__main__':
    if not os.path.exists(database_config['url'].split('/')[-1]):
        from init_database import main
        main()
