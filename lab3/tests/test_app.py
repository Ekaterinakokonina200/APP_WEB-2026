import pytest
from app import app, users


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost'
    with app.test_client() as client:
        with app.app_context():
            yield client


def test_counter_increments(client):
    """Тест: Счётчик посещений увеличивается при каждом визите"""
    response1 = client.get('/counter/')
    assert b'1' in response1.data

    response2 = client.get('/counter/')
    assert b'2' in response2.data

    response3 = client.get('/counter/')
    assert b'3' in response3.data


def test_counter_session_persists_for_same_user(client):
    """Тест: Счётчик сохраняет значение для одного пользователя"""
    client.get('/counter/')
    client.get('/counter/')
    response = client.get('/counter/')
    assert b'3' in response.data


def test_successful_login_redirects_to_index(client):
    """Тест: После успешного входа перенаправляет на главную"""
    response = client.post('/login/', data={
        'username': 'user',
        'password': 'qwerty',
        'remember': False
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Вы успешно вошли в систему!'.encode() in response.data


def test_successful_login_shows_success_message(client):
    """Тест: При успешном входе показывается сообщение об успехе"""
    response = client.post('/login/', data={
        'username': 'user',
        'password': 'qwerty'
    }, follow_redirects=True)
    assert 'Вы успешно вошли'.encode() in response.data


def test_failed_login_stays_on_login_page(client):
    """Тест: При неудачном входе остаёмся на странице входа"""
    response = client.post('/login/', data={
        'username': 'user',
        'password': 'wrongpassword'
    })
    assert 'Вход в систему'.encode() in response.data


def test_failed_login_shows_error_message(client):
    """Тест: При неудачном входе показывается сообщение об ошибке"""
    response = client.post('/login/', data={
        'username': 'user',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert 'Неверное имя пользователя или пароль'.encode() in response.data


def test_authenticated_user_can_access_secret_page(client):
    """Тест: Аутентифицированный пользователь имеет доступ к секретной странице"""
    client.post('/login/', data={'username': 'user', 'password': 'qwerty'})
    response = client.get('/secret/')
    assert response.status_code == 200
    assert 'Секретная страница'.encode() in response.data


def test_unauthenticated_user_redirected_from_secret(client):
    """Тест: Неаутентифицированный пользователь перенаправляется на страницу входа"""
    response = client.get('/secret/')
    assert response.status_code == 302
    assert '/login/' in response.headers['Location']


def test_unauthenticated_user_sees_login_message_when_accessing_secret(client):
    """Тест: При попытке доступа к секретной странице показывается сообщение"""
    response = client.get('/secret/', follow_redirects=True)
    assert 'Пожалуйста, войдите для доступа к этой странице'.encode() in response.data


def test_redirect_to_requested_page_after_login(client):
    """Тест: После входа перенаправляет на запрошенную страницу"""
    client.get('/secret/')
    response = client.post('/login/', data={
        'username': 'user',
        'password': 'qwerty'
    }, follow_redirects=True)
    assert 'Секретная страница'.encode() in response.data


def test_navbar_shows_secret_link_for_authenticated_user(client):
    """Тест: В навбаре показывается ссылка на секретную страницу для аутентифицированных"""
    client.post('/login/', data={'username': 'user', 'password': 'qwerty'})
    response = client.get('/')
    assert 'Секретная страница'.encode() in response.data


def test_navbar_hides_secret_link_for_unauthenticated_user(client):
    """Тест: В навбаре скрыта ссылка на секретную страницу для неаутентифицированных"""
    response = client.get('/')
    assert 'Секретная страница'.encode() not in response.data


def test_navbar_shows_login_link_for_unauthenticated_user(client):
    """Тест: В навбаре показывается ссылка на вход для неаутентифицированных"""
    response = client.get('/')
    assert 'Войти'.encode() in response.data


def test_navbar_shows_logout_link_for_authenticated_user(client):
    """Тест: В навбаре показывается ссылка на выход для аутентифицированных"""
    client.post('/login/', data={'username': 'user', 'password': 'qwerty'})
    response = client.get('/')
    assert 'Выйти'.encode() in response.data


def test_logout_works(client):
    """Тест: Выход из системы работает корректно"""
    client.post('/login/', data={'username': 'user', 'password': 'qwerty'})
    response = client.get('/logout/', follow_redirects=True)
    assert 'Вы вышли из системы'.encode() in response.data
    assert 'Секретная страница'.encode() not in response.data


def test_remember_me_sets_cookie(client):
    """Тест: Чекбокс 'Запомнить меня' устанавливает cookie"""
    response = client.post('/login/', data={
        'username': 'user',
        'password': 'qwerty',
        'remember': True
    })
    set_cookie = response.headers.get('Set-Cookie', '')
    assert 'remember_token' in set_cookie


def test_index_page_returns_200(client):
    """Тест: Главная страница доступна"""
    response = client.get('/')
    assert response.status_code == 200


def test_counter_page_returns_200(client):
    """Тест: Страница счётчика доступна"""
    response = client.get('/counter/')
    assert response.status_code == 200


def test_login_page_returns_200(client):
    """Тест: Страница входа доступна"""
    response = client.get('/login/')
    assert response.status_code == 200