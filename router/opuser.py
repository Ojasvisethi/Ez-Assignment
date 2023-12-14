from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from db import db_user
from db.database import get_db
from schema import UserBase, UserDisplay

router = APIRouter(prefix="/opuser", tags=["user"])


@router.post('/', response_model=UserDisplay)
def create_user(request: UserBase, db: Session = Depends(get_db)):
    return db_user.create_user(db, request)



