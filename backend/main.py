from dotenv import load_dotenv
load_dotenv()
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from polls.create import router as polls_create_router
from polls.retrieve import router as polls_retrieve_router
from polls.vote import router as polls_vote_router
from polls.results import router as polls_results_router


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(polls_create_router)
app.include_router(polls_retrieve_router)
app.include_router(polls_vote_router)
app.include_router(polls_results_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)