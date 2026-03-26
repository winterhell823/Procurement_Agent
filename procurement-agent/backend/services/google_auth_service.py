from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException
from config import settings

def verify_google_token(token: str):
    GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID

    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not set")

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise HTTPException(status_code=401, detail="Invalid token issuer")

        return {
            "email": idinfo["email"],
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture"),
            "google_id": idinfo["sub"]
        }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    
    