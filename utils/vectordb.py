import pinecone
from configs.config_settings import pinecone as pinecone_config
import time
import AI
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

env = os.getenv('PINECONE_ENVIRONMENT')
key = os.getenv('PINECONE_KEY')

pinecone.init(api_key=key,
            environment=key)

async def save_data(chat_id, embedded):

    list = pinecone.list_indexes()
    if "wafi" not in pinecone.list_indexes():
        pinecone.create_index("wafi", dimension=1536, metric="cosine")
        time.sleep(1)
    index = pinecone.Index("wafi")
    index.upsert(embedded)
    return "success"


def get_context_with_id(chat_id, query):
    # index_name='wafi-37'
    print(pinecone.list_indexes())

    async def get_converted_data(query):
        embedded_query = await AI.convert_vector_data(query, chat_id)
        return embedded_query
    embedded_query = asyncio.run(get_converted_data(query))
    embedded = embedded_query["values"]
    index = pinecone.Index("wafi")
    describe = index.describe_index_stats()
    matched_sections = index.query(
        vector=embedded,
        top_k=5,
        filter={
            "chat_id":chat_id
        },
        includeMetadata=True
    )
    # print("-------------Embedded Query Start----------")
    # print(matched_sections)
    # print("-------------Embedded Query End----------")
    text = ""
    for section in matched_sections["matches"]:
        text = text + section['metadata']['text']
    print(text)
    return text
