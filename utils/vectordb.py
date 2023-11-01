import pinecone
from configs.config_settings import pinecone as pinecone_config
import time
import AI
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

env = os.getenv('us-east1-gcp')
key = os.getenv('15fde1c3-19ab-4996-a783-f82ff8aee87c')

pinecone.init(api_key=key,
            environment=key)

async def save_data(index_name, embedded):
    
    list = pinecone.list_indexes()
    # if len(list) > 0:
    #     pinecone.delete_index(list[0])

    if index_name not in pinecone.list_indexes():
        print("-------------Embedded Query Start----------")
        print(index_name)
        print("-------------Embedded Query End----------")
        pinecone.create_index(index_name, dimension=1536, metric="cosine")
        pinecone.describe_index(index_name)
        time.sleep(1)
    index = pinecone.Index(index_name)
    index.upsert(embedded)
    print(index.describe_index_stats())
    return "success"

def get_context_with_id(index_name, query):
    # index_name='wafi-37'
    print(pinecone.list_indexes())
    async def get_converted_data(query):
        embedded_query =  await AI.convert_vector_data(query)
        return embedded_query
    embedded_query = asyncio.run(get_converted_data(query))
    embedded = embedded_query["values"]
    index = pinecone.Index(index_name)
    describe = index.describe_index_stats()
    print(describe)
    matched_sections = index.query(
        vector=embedded,
        top_k=5,
        # include_values=True
        includeMetadata=True
    )
    # print("-------------Embedded Query Start----------")
    # print(matched_sections)
    # print("-------------Embedded Query End----------")
    text = ""
    for section in matched_sections["matches"]:
        text = text +section['metadata']['text']
    print(text)
    return text