import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from polls.create import router as polls_router

load_dotenv()
app = FastAPI()
app.include_router(polls_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)