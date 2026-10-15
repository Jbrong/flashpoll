"""Local development server: `pipenv run dev` (reads backend/.env)."""

from dotenv import load_dotenv

load_dotenv()

import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run("flashpoll.main:create_app", factory=True, host="127.0.0.1", port=8080, reload=True)
