from dotenv import load_dotenv
load_dotenv()
import uvicorn
from fastapi import FastAPI
from polls.create import router as polls_router


app = FastAPI()
app.include_router(polls_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)