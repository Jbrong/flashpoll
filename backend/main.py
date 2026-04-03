from dotenv import load_dotenv
load_dotenv()
import uvicorn
from fastapi import FastAPI
from polls.create import router as polls_create_router
from polls.retrieve import router as polls_retrieve_router
from polls.vote import router as polls_vote_router


app = FastAPI()
app.include_router(polls_create_router)
app.include_router(polls_retrieve_router)
app.include_router(polls_vote_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)