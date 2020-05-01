import sqlalchemy
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class ConfirmUser(SqlAlchemyBase, UserMixin):
    __tablename__ = 'confirm_users'
    name = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=True, index=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=True, index=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    registration_date = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    token = sqlalchemy.Column(sqlalchemy.String, nullable=True, index=True, primary_key=True)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)