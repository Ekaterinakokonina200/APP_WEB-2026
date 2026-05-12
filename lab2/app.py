from flask import Flask, request, render_template, make_response, redirect, url_for
import re

app = Flask(__name__)


# Главная страница
@app.route('/')
def index():
    return render_template('index.html')


# Страница 1: Параметры URL
@app.route('/url-params/')
def url_params():
    params = request.args
    return render_template('url_params.html', params=params)


# Страница 2: Заголовки запроса
@app.route('/headers/')
def headers():
    headers = dict(request.headers)
    return render_template('headers.html', headers=headers)


# Страница 3: Cookie
@app.route('/cookies/')
def cookies():
    all_cookies = dict(request.cookies)
    cookie_value = request.cookies.get('lab_cookie')
    return render_template('cookies.html', cookies=all_cookies, cookie_value=cookie_value)


# Установка cookie
@app.route('/set-cookie/')
def set_cookie():
    response = make_response(redirect(url_for('cookies')))
    response.set_cookie('lab_cookie', 'Hello from Lab2!', max_age=3600)
    return response


# Удаление cookie
@app.route('/delete-cookie/')
def delete_cookie():
    response = make_response(redirect(url_for('cookies')))
    response.delete_cookie('lab_cookie')
    return response


# Страница 4: Параметры формы
@app.route('/form-params/', methods=['GET', 'POST'])
def form_params():
    form_data = {}
    submitted = False

    if request.method == 'POST':
        form_data = dict(request.form)
        submitted = True

    return render_template('form_params.html', form_data=form_data, submitted=submitted)


# Страница 5: Валидация номера телефона
@app.route('/phone/', methods=['GET', 'POST'])
def phone():
    error = None
    error_type = None
    formatted_phone = None
    phone_input = ''

    if request.method == 'POST':
        phone_input = request.form.get('phone', '')
        is_valid, error_type, formatted = validate_phone(phone_input)

        if is_valid:
            formatted_phone = formatted
        else:
            if error_type == 'digit_count':
                error = 'Недопустимый ввод. Неверное количество цифр.'
            elif error_type == 'invalid_chars':
                error = 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.'

    return render_template('phone.html', error=error, formatted_phone=formatted_phone, phone_input=phone_input)


def validate_phone(phone):
    """
    Проверяет и форматирует номер телефона
    Возвращает: (is_valid, error_type, formatted_phone)
    """
    original = phone

    # Удаляем все разрешённые символы (пробелы, скобки, дефисы, точки, +)
    temp = re.sub(r'[\s\(\)\-\.\+]', '', phone)

    # Проверка 1: только цифры должны остаться
    if not temp.isdigit():
        return False, 'invalid_chars', None

    # Подсчёт количества цифр
    digit_count = len(temp)

    # Определяем ожидаемое количество цифр
    expected_digits = None
    is_plus7_or_8 = False

    # Проверяем, начинается ли с +7 или 8
    cleaned_original = re.sub(r'[\s\(\)\-\.]', '', original)
    if cleaned_original.startswith('+7'):
        is_plus7_or_8 = True
        expected_digits = 11
    elif cleaned_original.startswith('8'):
        is_plus7_or_8 = True
        expected_digits = 11
    else:
        expected_digits = 10

    # Проверка количества цифр
    if digit_count != expected_digits:
        return False, 'digit_count', None

    # Форматирование номера
    if is_plus7_or_8:
        if len(temp) == 11:
            formatted = f"8-{temp[1:4]}-{temp[4:7]}-{temp[7:9]}-{temp[9:11]}"
        else:
            formatted = phone
    else:
        formatted = f"{temp[0:3]}-{temp[3:6]}-{temp[6:8]}-{temp[8:10]}"

    return True, None, formatted


if __name__ == '__main__':
    app.run(debug=True, port=5002)