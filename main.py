from fastapi import FastAPI, UploadFile, File, HTTPException
from sklearn.preprocessing import StandardScaler
import pandas as pd
import joblib
from io import StringIO
from enum import Enum
import uvicorn
from fastapi import FastAPI
from dependencies import get_db
import models, schemas, crud
from database import engine
from models import Base
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from models import User  # Импортируем модель пользователя
from schemas import UserCreate  # Импортируем схему создания пользователя
from datetime import datetime, timedelta
from jose import jwt
from fastapi.security import OAuth2PasswordBearer



# Определение доступных моделей как перечисления
class ModelName(str, Enum):
    logistic_regression = "logistic_regression"
    xgboost = "xgboost"
    svm = "svm"


Base.metadata.create_all(bind=engine)

# Инициализация приложения FastAPI
app = FastAPI()

# Загрузка моделей
ml_models = {
    ModelName.logistic_regression: joblib.load("models/log_reg.pkl"),
    ModelName.xgboost: joblib.load("models/svm.pkl"),
    ModelName.svm: joblib.load("models/xgb_classifier.pkl"),
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token/")

async def get_current_active_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# Настройка для работы с JWT
SECRET_KEY = "ваш_секретный_ключ"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # время жизни токена

# Экземпляр CryptContext для хэширования пароля
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Эндпоинт для загрузки файла и получения предсказаний

# Утилита для получения пользователя по имени
def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

# Утилита для проверки пароля
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Утилита для аутентификации пользователя
def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Функция для создания JWT токена
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/predict/{model_name}")
async def create_upload_file(
    model_name: ModelName,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),  # Добавлена проверка авторизации
    db: Session = Depends(get_db)
):
    # Проверяем, достаточно ли у пользователя токенов
    if current_user.tokens <= 0:
        raise HTTPException(status_code=400, detail="Insufficient tokens")

    # Проверяем, доступна ли модель
    if model_name not in ml_models:
        raise HTTPException(status_code=400, detail="Model name is not valid")

    # Проверяем, доступна ли модель
    if model_name not in ml_models:
        raise HTTPException(status_code=400, detail="Model name is not valid")

    model = ml_models[model_name]

    # Прочитать файл в формате csv
    contents = await file.read()
    df = pd.read_csv(StringIO(str(contents, "utf-8")))

    # Нормализация данных
    std_scaler = StandardScaler()
    X = std_scaler.fit_transform(df)

    # Получение предсказаний от модели
    predictions = model.predict(X)

    # Списываем один токен за использование модели
    current_user.tokens -= 1
    db.add(current_user)
    db.commit()

    # Возврат предсказаний
    return {"predictions": predictions.tolist()}

# Эндпоинт для регистрации пользователя
@app.post("/register/", response_model=schemas.UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Проверяем, существует ли уже пользователь с таким именем
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Хэшируем пароль пользователя
    hashed_password = pwd_context.hash(user.password)

    # Создаем нового пользователя
    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Возвращаем данные нового пользователя
    return new_user

@app.post("/token/", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=schemas.UserOut)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user


@app.get("/test_db")
def test_db(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
