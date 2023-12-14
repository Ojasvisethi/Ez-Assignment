import os
import uuid
from fastapi import APIRouter, Depends , HTTPException , status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from db.database import get_db
from db.hash import Hash
from db.models import ClientUser, DbFile
from schema import ClientBase, FileDisplay
from auth import oauth2
from jose import jwt , JWTError
from db import models

router = APIRouter(prefix="/clientuser", tags=["user"])


email_config = ConnectionConfig(
    MAIL_USERNAME="ojasvisethi2407@gmail.com",
    MAIL_PASSWORD="xrtc pmsr cmzr hanm",
    MAIL_FROM="ojasvisethi2407@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS = False
)

fastmail = FastMail(email_config)
def get_fastmail():
    return fastmail

# @router.post('/signup/')
# def create_user(request: UserBase, db: Session = Depends(get_db)):
    # return db_user.create_user(db, request)

@router.post("/signup/")
async def signup(client_user: ClientBase,db : Session = Depends(get_db)):
    # Hash the password before storing it in the database
    verification_token = str(uuid.uuid4())
    new_user = ClientUser(
        username=client_user.email,
        email=client_user.email,
        password=Hash.bcrypt(client_user.password),
        verification_token=verification_token,
        is_verified = False
    )

    # Generate a verification token and save it in the database
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    finally:
        db.close()

    # Send a verification email (you need to implement this)
    # send_verification_email(client_user.email, client_user.verification_token)
    message = MessageSchema(
        subject="Verifying Email",
        recipients=[client_user.email],
        body=f"Click on the following link to verify your email: {generate_verification_url(verification_token)}",
        subtype="plain"
    )

    try:
        await fastmail.send_message(message)
        return {"message": "Verification email sent on your emailid"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

def generate_verification_url(verification_token: str):
    base_url = "http://127.0.0.1:8000/verify-email"  # Replace with your actual domain
    return f"{base_url}/{verification_token}"


@router.post('/login')
def verify_client_user(req: ClientBase, db: Session = Depends(get_db)):
    user = db.query(ClientUser).filter(ClientUser.username == req.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")
    if not Hash.verify(user.password, req.password):

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect password")

    access_token = oauth2.create_access_token(data={'sub': user.username})

    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'user_id': user.id,
        'username': user.username
    }

@router.get('/uploadedFiles', response_model=list[FileDisplay])
def list_all_uploadedFiles(db: Session = Depends(get_db)):
    files = db.query(DbFile).all()
    return files



@router.get('/secure-link/{file_id}')
async def secure_link(token: str,file_id: int, db: Session = Depends(get_db)):
    # Check if the file exists
    file = db.query(DbFile).filter(DbFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Generate a secure download link
    current_user = get_current_user(token,db)
    data = {"file_id": file_id, "sub": current_user.username}
    base_url = "http://127.0.0.1:8000/clientuser"
    secure_download_url = f"{base_url}/download/{oauth2.create_access_token(data)}"

    return {"secure_download_url": secure_download_url}


SECRET_KEY = '77407c7339a6c00544e51af1101c4abb4aea2a31157ca5f7dfd87da02a628107'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_current_user(token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_client_user_by_username(username , db)

    if user is None:
        raise credentials_exception

    return user



def get_client_user_by_username(username : str , db : Session = Depends(get_db)):
    user = db.query(ClientUser).filter(ClientUser.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail=f'User with {username} not found')

    return user


UPLOAD_DIR = "uploads" 

@router.get('/download/{access_token}')
def downloadFile(access_token : str , db : Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise credentials_exception
    db_file = db.query(models.DbFile).filter(models.DbFile.id == payload.get("file_id")).first()

    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Construct the local file path
    local_file_path = os.path.join(UPLOAD_DIR, db_file.filename)

    # Check if the file exists locally
    if not os.path.exists(local_file_path):
        raise HTTPException(status_code=404, detail="File not found locally")

    # Serve the file as a response using FileResponse
    return FileResponse(local_file_path, filename=db_file.filename, media_type=db_file.content_type)



