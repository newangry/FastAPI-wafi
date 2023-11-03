database_config = {
    "url": "sqlite:///./test.db"
}

auth_config = {
    "access_token_rate_limit": 100
}

login_auths_config = {
    'SECRET_KEY': "",
    'ALGORITHM': "HS256",
    'ACCESS_TOKEN_EXPIRE_MINUTES': 60*8  # Access token validity duration in minutes
}

google_auth_config = {
    'CLIENT_ID': "439027388814-q5knfou7tt7hdtlsejurcmjg6dcre7ta.apps.googleusercontent.com",
    'CLIENT_SECRET': "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",
    # 'REDIRECT_URI': "https://wafi-six.vercel.app/redirect",
    'REDIRECT_URI': "http//localhost:3000/redirect",
    'TOKEN_ENDPOINT': "https://oauth2.googleapis.com/token",
    'USERINFO_ENDPOINT': "https://www.googleapis.com/oauth2/v3/userinfo"
}

pinecone = {
    'API_KEY': '',
    'ENVIRONMENT':''
}

template = """You are a chatbot having a conversation with a human.

Given the following extracted parts of a long document and a question, create a final answer.

{context}

{chat_history}
Human: {human_input}
Chatbot:"""

SPEAKER = 'en_US/hifi-tts_low' 
EMBEDDING_MODEL = 'text-embedding-ada-002'

sample_pdf_path = "Cryptocurrencies and stablecoins.pdf"