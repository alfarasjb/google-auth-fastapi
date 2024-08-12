from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
import httpx
import json
from typing import Optional
from pydantic import BaseModel
from src.google import GoogleAPI

app = FastAPI()

# Load OAuth2 credentials from a local file
with open("creds3.json") as f:
    credentials = json.load(f)['web']

CLIENT_ID = credentials["client_id"]
CLIENT_SECRET = credentials["client_secret"]
REDIRECT_URI = credentials["redirect_uris"][0]

# OAuth2 configuration
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://accounts.google.com/o/oauth2/auth",
    tokenUrl="https://oauth2.googleapis.com/token"
)

class Token(BaseModel):
    access_token: str
    token_type: str

@app.get("/")
async def main():
    return {"message": "Welcome to the FastAPI OAuth2 demo"}

@app.get("/login")
def login():
    authorization_url = (
        f"https://accounts.google.com/o/oauth2/auth"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20email%20profile"
    )
    return RedirectResponse(url=authorization_url)

@app.get("/auth/callback")
async def auth_callback(code: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code"
            }
        )
        response.raise_for_status()
        token_info = response.json()
        google = GoogleAPI(token_info=token_info, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

        with open("token.json", "w") as token_file:
            json.dump(token_info, token_file)
        # google.get_events()
        google.create_meeting()
        return token_info

@app.get("/profile")
async def profile(token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        profile_info = response.json()
        return profile_info


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
