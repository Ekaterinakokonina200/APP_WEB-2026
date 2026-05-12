import pytest
from app import app, validate_login, validate_password
import models
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    models.init_db()

    # Убеждаемся, что пользователь admin существует с правильным паролем
    conn = models.get_db()
    cursor = conn.cursor()

    # Обновляем пароль admin, если нужно
    password_hash = generate_password_hash('Admin123!')
    cursor.execute('''
        UPDATE users SET password_hash = ? WHERE login = 'admin'
    ''', (password_hash,))

    # Создаём admin, если его нет
    cursor.execute('''
        INSERT OR IGNORE INTO users (id, login, password_hash, last_name, first_name, role_id)
        VALUES (1, 'admin', ?, 'Admin', 'Admin', 1)
    ''', (password_hash,))

    conn.commit()
    conn.close()

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
    assert 'Вы успешно вошли'.encode() in response.data

def test_failed_login(client):
    response = client.post('/login/', data={
        'login': 'admin',
        'password': 'wrong'
    }, follow_redirects=True)
    assert 'Неверный логин или пароль'.encode() in response.data

def test_validate_login_valid():
    is_valid, error = validate_login('user123')
    assert is_valid is True

def test_validate_login_too_short():
    is_valid, error = validate_login('usr')
    assert is_valid is False
    assert 'не менее 5 символов' in error

def test_validate_login_invalid_chars():
    is_valid, error = validate_login('user_123')
    assert is_valid is False
    assert 'только латинские буквы и цифры' in error

def test_validate_password_valid():
    is_valid, error = validate_password('Admin123!')
    assert is_valid is True

def test_validate_password_too_short():
    is_valid, error = validate_password('Abc1!')
    assert is_valid is False
    assert 'не менее 8 символов' in error

def test_validate_password_no_uppercase():
    is_valid, error = validate_password('admin123!')
    assert is_valid is False
    assert 'заглавную букву' in error

def test_validate_password_no_digit():
    is_valid, error = validate_password('AdminPass!')
    assert is_valid is False
    assert 'цифру' in error

def test_authenticated_user_can_access_create_page(client):
    client.post('/login/', data={'login': 'admin', 'password': 'Admin123!'})
    response = client.get('/user/create/')
    assert response.status_code == 200

def test_unauthenticated_user_redirected_from_create(client):
    response = client.get('/user/create/')
    assert response.status_code == 302

def test_user_view_page_accessible_to_all(client):
    response = client.get('/user/1/')
    assert response.status_code == 200
    assert b'admin' in response.data

def test_change_password_page_requires_login(client):
    response = client.get('/change-password/')
    assert response.status_code == 302

def test_change_password_works(client):
    client.post('/login/', data={'login': 'admin', 'password': 'Admin123!'})
    response = client.post('/change-password/', data={
        'old_password': 'Admin123!',
        'new_password': 'NewPass456!',
        'confirm_password': 'NewPass456!'
    }, follow_redirects=True)
    assert 'Пароль успешно изменён'.encode() in response.data