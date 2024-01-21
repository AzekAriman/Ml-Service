import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from sklearn.preprocessing import StandardScaler
import pandas as pd
import joblib
from io import StringIO
from enum import Enum


# Определение доступных моделей как перечисления
class ModelName(str, Enum):
    logistic_regression = "logistic_regression"
    xgboost = "xgboost"
    svm = "svm"


# Инициализация приложения FastAPI
app = FastAPI()

# Загрузка моделей
models = {
    ModelName.logistic_regression: joblib.load('models/log_reg.pkl'),
    ModelName.xgboost: joblib.load('models/svm.pkl'),
    ModelName.svm: joblib.load('models/xgb_classifier.pkl'),
}


# Эндпоинт для загрузки файла и получения предсказаний
@app.post("/predict/{model_name}")
async def create_upload_file(model_name: ModelName, file: UploadFile = File(...)):
    # Проверяем, доступна ли модель
    if model_name not in models:
        raise HTTPException(status_code=400, detail="Model name is not valid")

    model = models[model_name]

    # Прочитать файл в формате csv
    contents = await file.read()
    df = pd.read_csv(StringIO(str(contents, 'utf-8')))

    # Нормализация данных
    std_scaler = StandardScaler()
    X = std_scaler.fit_transform(df)

    # Получение предсказаний от модели
    predictions = model.predict(X)

    # Возврат предсказаний
    return {"predictions": predictions.tolist()}

if __name__ == "__main__":
    uvicorn.run('main:app', reload=True)