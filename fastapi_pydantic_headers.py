from typing import Annotated
from fastapi import FastAPI, Header, Depends
from pydantic import BaseModel, Field

app = FastAPI()

# 1. Define your Pydantic model for the Headers
# This allows you to use Pydantic's powerful validation (e.g., min_length)
class CustomHeaders(BaseModel):
    username: str = Field(..., min_length=3, description="The user's username")
    realm: str

# 2. Define the Pydantic model for the Body
class RequestData(BaseModel):
    message: str
    count: int

# 3. Create a Dependency function to map HTTP headers to the Pydantic model
def get_custom_headers(
    username: Annotated[str, Header()],
    realm: Annotated[str, Header()]
) -> CustomHeaders:
    # Initialize and return the Pydantic model
    return CustomHeaders(username=username, realm=realm)

@app.post("/submit")
async def submit_data(
    data: RequestData,
    # 4. Inject the dependency into your route
    headers: Annotated[CustomHeaders, Depends(get_custom_headers)]
):
    """
    Reads a grouped Pydantic model for headers and a Pydantic model for the body.
    """
    return {
        "status": "success",
        # You can now use standard Pydantic methods like .model_dump()
        "extracted_headers": headers.model_dump(), 
        "extracted_data": data.model_dump()
    }
