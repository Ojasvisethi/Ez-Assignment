from sqlalchemy.orm import Session

from db.database import get_db
from db.hash import Hash
from db.models import DbUser
from schema import UserBase
from fastapi import Depends , HTTPException , status


def create_user(db: Session, req: UserBase):
    new_user = DbUser(
        username=req.username,
        email=req.email,
        password=Hash.bcrypt(req.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user(db: Session, id: int, request: UserBase):
    user = db.query(DbUser).filter(DbUser.id == id)
    user.update({
        DbUser.username: request.username,
        DbUser.email: request.email,
        DbUser.password: Hash.bcrypt(request.password)
    })
    db.commit()
    return 'ok'


def delete_user(db: Session, id: int):
    user = db.query(DbUser).filter(DbUser.id == id).first()
    db.delete(user)
    db.commit()
    return 'ok'


def get_all_users(db: Session):
    return db.query(DbUser).all()





def get_user_by_username(username : str , db : Session = Depends(get_db)):
    user = db.query(DbUser).filter(DbUser.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail=f'User with {username} not found')

    return user
