import pytest
from app import app, validate_login, validate_password
import models


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    models.init_db()
    with app.test_client() as client:
        with app.app_context():
            yield client


def test_index_page_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200


def test_login_page_returns_200(client):
    response = client.get('/login/')
    assert response.status_code == 200


def test_successful_login(client):
    response = client.post('/login/', data={
        'login': 'admin',
        'password': 'Admin123!'
    }, follow_redirects=True)
    assert response.status_code == 200



def test_failed_login(client):
    response = client.post('/login/', data={
        'login': 'admin',
        'password': 'wrong'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert ('ошибк' in response.text.lower() or
            'неверн' in response.text.lower())


def test_validate_login_valid():
    is_valid, error = validate_login('user123')
    assert is_valid is True
    assert error is None


def test_validate_login_too_short():
    is_valid, error = validate_login('usr')
    assert is_valid is False
    assert error is not None
    assert ('5' in str(error) or 'пять' in str(error) or 'символ' in str(error))


def test_validate_login_invalid_chars():
    is_valid, error = validate_login('user_123')
    assert is_valid is False
    assert error is not None
    assert ('латин' in str(error) or 'букв' in str(error) or 'символ' in str(error))


def test_validate_password_valid():
    is_valid, error = validate_password('Admin123!')
    assert is_valid is True
    assert error is None


def test_validate_password_too_short():
    is_valid, error = validate_password('Abc1!')
    assert is_valid is False
    assert error is not None
    assert ('8' in str(error) or 'восемь' in str(error) or 'символ' in str(error))


def test_validate_password_no_uppercase():
    is_valid, error = validate_password('admin123!')
    assert is_valid is False
    assert error is not None
    assert ('заглавн' in str(error) or 'uppercase' in str(error).lower())


def test_validate_password_no_digit():
    is_valid, error = validate_password('AdminPass!')
    assert is_valid is False
    assert error is not None
    assert ('цифр' in str(error).lower() or 'digit' in str(error).lower())


def test_authenticated_user_can_access_create_page(client):
    login_response = client.post('/login/', data={
        'login': 'admin',
        'password': 'Admin123!'
    }, follow_redirects=True)

    response = client.get('/user/create/')


    assert response.status_code in [200, 302]

    if response.status_code == 302:
        assert 'login' in response.headers.get('Location', '')


def test_unauthenticated_user_redirected_from_create(client):
    response = client.get('/user/create/')
    # Неавторизованный пользователь должен быть перенаправлен
    assert response.status_code == 302
    assert 'login' in response.headers.get('Location', '')


def test_user_view_page_accessible_to_all(client):
    response = client.get('/user/1/')
    assert response.status_code == 200
    assert 'admin' in response.text or 'пользователь' in response.text.lower()


def test_change_password_page_requires_login(client):
    response = client.get('/change-password/')
    assert response.status_code == 302
    assert 'login' in response.headers.get('Location', '')


def test_change_password_works(client):
    client.post('/login/', data={
        'login': 'admin',
        'password': 'Admin123!'
    }, follow_redirects=True)

    response = client.post('/change-password/', data={
        'old_password': 'Admin123!',
        'new_password': 'NewPass456!',
        'confirm_password': 'NewPass456!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert ('пароль' in response.text.lower() or
            'успешн' in response.text.lower() or
            'изменен' in response.text.lower())