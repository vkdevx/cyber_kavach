from typing import Optional, List
from sqlalchemy.orm import Session
from storage.models_orm import UserORM


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(
        self,
        user_id: str,
        username: str,
        email: str,
        hashed_password: str,
        role: str = "analyst",
        created_ts: float = 0.0
    ) -> UserORM:
        user = UserORM(
            user_id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role,
            is_active=True,
            created_ts=created_ts
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_username(self, username: str) -> Optional[UserORM]:
        return self.db.query(UserORM).filter(UserORM.username == username).first()

    def get_by_email(self, email: str) -> Optional[UserORM]:
        return self.db.query(UserORM).filter(UserORM.email == email).first()

    def get_by_id(self, user_id: str) -> Optional[UserORM]:
        return self.db.query(UserORM).filter(UserORM.user_id == user_id).first()

    def list_users(self) -> List[UserORM]:
        return self.db.query(UserORM).all()
