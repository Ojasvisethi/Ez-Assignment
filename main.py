import os
from typing import Annotated, Union
from fastapi import Depends, FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from db import models
from db.database import engine

from auth import authentication
from auth.oauth2 import oauth2_scheme
from router import opuser , clientuser
from sqlalchemy.orm import Session
from db.database import get_db


app = FastAPI()
app.include_router(authentication.router)
app.include_router(opuser.router)
app.include_router(clientuser.router)


UPLOAD_DIR = "uploads"  # Specify the directory where you want to save the files

@app.post("/files/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    allowed_file_types = ['pptx', 'docx', 'xlsx']

    # Check if the file type is allowed
    if not any(file.filename.lower().endswith(ft) for ft in allowed_file_types):
        raise HTTPException(status_code=404, detail="Invalid file type. Only pptx, docx, and xlsx are allowed.")

    # Create the upload directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save the file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as local_file:
        local_file.write(await file.read())

    # Save file information to the database
    try:
        db_file = models.DbFile(filename=file.filename, content_type=file.content_type, file_path=file_path)
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
    finally:
        db.close()

    return JSONResponse(content={"message": "File saved successfully", "file_path": file_path})
    
def verify_user(db: Session, user: models.ClientUser):
    user.is_verified = True
    db.commit()

def get_user_by_verification_token(db: Session, verification_token: str):
    return db.query(models.ClientUser).filter(models.ClientUser.verification_token == verification_token).first()


@app.get("/verify-email/{verification_token}")
async def verify_email(verification_token: str, db : Session = Depends(get_db)):
        user = get_user_by_verification_token(db, verification_token)
        if user:
            verify_user(db, user)
            return {
        "message" : "Email verified. You can login now."
    }
        else:
            return {
        "message" : "Verification token not found"
    }

models.Base.metadata.create_all(engine)