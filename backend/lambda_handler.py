"""AWS Lambda entry point: runs the FastAPI app behind API Gateway."""

from mangum import Mangum

from flashpoll.main import create_app

handler = Mangum(create_app(), lifespan="off")
