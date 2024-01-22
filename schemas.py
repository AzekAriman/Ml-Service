from pydantic import BaseModel

# Схема для регистрации пользователя
class UserCreate(BaseModel):
    username: str
    password: str

# Схема для ответа, не включающая пароль
class UserOut(BaseModel):
    username: str
    tokens: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None