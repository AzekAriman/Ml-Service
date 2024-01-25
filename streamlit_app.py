import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"


def show_user_profile():
    # Здесь предполагается, что токен уже сохранен в st.session_state['token']
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    response = requests.get(f"{BASE_URL}/users/me/", headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        st.write(
            f"Привет, {user_data['username']}! Ваш баланс токенов: {user_data['tokens']}"
        )
    else:
        st.error("Ошибка при загрузке профиля пользователя.")


def predict_page():
    st.subheader("Получите предсказание")

    # Функция для получения и отображения баланса токенов пользователя
    def show_user_tokens():
        user_info_response = requests.get(f"{BASE_URL}/users/me/", headers=headers)
        if user_info_response.status_code == 200:
            user_info = user_info_response.json()
            st.write(f"Ваш баланс токенов: {user_info['tokens']}")
        else:
            st.error("Не удалось загрузить информацию о пользователе.")

    if "token" in st.session_state:
        headers = {"Authorization": f"Bearer {st.session_state['token']}"}

        # Поле и кнопка для пополнения баланса токенов
        recharge_amount = st.number_input(
            "Введите количество токенов для пополнения",
            min_value=1,
            value=10,
            step=1,
        )
        if st.button("Пополнить баланс"):
            recharge_response = requests.post(
                f"{BASE_URL}/users/me/tokens/recharge/",
                headers=headers,
                json={"recharge_amount": recharge_amount},
            )
            if recharge_response.status_code == 200:
                st.success("Баланс успешно пополнен.")
                # Заново запросить и отобразить обновленный баланс токенов
                show_user_tokens()
            else:
                st.error("Произошла ошибка при пополнении баланса.")
        else:
            # Отображение текущего баланса токенов (вызывается только если кнопка не нажата)
            show_user_tokens()
        # Выбор модели для предсказания
        model_name = st.selectbox(
            "Выберите модель", ["logistic_regression", "xgboost", "svm"]
        )

        # Загрузка файла для предсказания
        uploaded_file = st.file_uploader("Загрузите CSV файл", type="csv")
        if uploaded_file is not None and st.button("Получить предсказание"):
            files = {"file": uploaded_file.getvalue()}
            predict_response = requests.post(
                f"{BASE_URL}/predict/{model_name}", files=files, headers=headers
            )
            if predict_response.status_code == 200:
                predictions = predict_response.json()["predictions"]
                st.write("Предсказания модели:")
                st.write(predictions)
            else:
                st.error("Произошла ошибка при получении предсказаний.")
    else:
        st.error(
            "Пожалуйста, войдите в систему, чтобы получить доступ к предсказаниям."
        )


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
