from fastapi import FastAPI
from middleware import setup_middlewares

app = FastAPI()

# Attach CORS and Header Context logic in one line
setup_middlewares(app)

@app.get("/")
async def root():
    return {"message": "Middlewares are fully wired!"}
