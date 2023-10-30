import os
from fastapi import FastAPI
from routers import authentication, user, bot, chat
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# app.add_middleware(HTTPSRedirectMiddleware)
origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # or you can specify methods like ["GET", "POST"]
    allow_headers=["*"],
)

app.include_router(authentication.router)
app.include_router(user.router)
app.include_router(bot.router)
app.include_router(chat.router)

if __name__ == "__main__":
    import uvicorn
    
    if os.path.isfile('configs/key.pem') and os.path.isfile('configs/key.pem'):
        uvicorn.run(app, host="0.0.0.0", port=8001, ssl_keyfile="configs/key.pem", ssl_certfile="configs/cert.pem")
    else:
        uvicorn.run(app, host="0.0.0.0", port=8001)
