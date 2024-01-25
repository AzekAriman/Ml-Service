import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"


def predict_page():
    st.subheader("Получите предсказание")
    model_name = st.selectbox(
        "Выберите модель", ["logistic_regression", "xgboost", "svm"]
    )
    uploaded_file = st.file_uploader("Загрузите CSV файл", type="csv")
    if uploaded_file is not None and st.button("Получить предсказание"):
        # После загрузки файла, отправьте его на сервер и получите предсказания
        files = {"file": uploaded_file.read()}
        headers = {"Authorization": f"Bearer {st.session_state['token']}"}
        response = requests.post(
            f"{BASE_URL}/predict/{model_name}", files=files, headers=headers
        )
        if response.status_code == 200:
            predictions = response.json()
            st.write(predictions)
        else:
            st.error("Произошла ошибка при запросе предсказаний")


def register_user():
    with st.form("Register User"):
        username = st.text_input("Имя пользователя для регистрации")
        password = st.text_input("Пароль для регистрации", type="password")
        submitted = st.form_submit_button("Зарегистрироваться")
        if submitted:
            response = requests.post(
                f"{BASE_URL}/register/",
                json={"username": username, "password": password},
            )
            if response.status_code == 200:
                st.success("Пользователь успешно зарегистрирован")
                st.session_state[
                    "message"
                ] = "Регистрация прошла успешно. Пожалуйста, войдите."
            else:
                st.error("Ошибка при регистрации пользователя")


def login_user():
    with st.form("Login User"):
        username = st.text_input("Имя пользователя")
        password = st.text_input("Пароль", type="password")
        submitted = st.form_submit_button("Войти")
        if submitted:
            response = requests.post(
                f"{BASE_URL}/token/", data={"username": username, "password": password}
            )
            if response.status_code == 200:
                token_data = response.json()
                st.session_state["token"] = token_data["access_token"]
                st.success("Вы успешно вошли в систему!")
            else:
                st.error("Ошибка при входе в систему")


def show_message():
    if "message" in st.session_state:
        st.success(st.session_state["message"])
        del st.session_state["message"]  # Удаляем сообщение после отображения


def main():
    if "token" not in st.session_state:
        show_message()  # Показываем сообщение, если оно есть
        register_user()
        login_user()
    elif "token" in st.session_state and "page" not in st.session_state:
        # Если пользователь вошел в систему, но страница не выбрана, покажем страницу предсказаний
        st.session_state["page"] = "predict"

    # В зависимости от страницы, показываем соответствующий интерфейс
    if st.session_state.get("page") == "predict":
        predict_page()


if __name__ == "__main__":
    main()
