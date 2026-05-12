from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import models
import re
from auth import check_rights
from reports import reports_bp

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
app.config['PER_PAGE'] = 20

# Регистрация Blueprint для отчётов
app.register_blueprint(reports_bp)

# Инициализация базы данных
models.init_db()

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.login = user_data['login']
        self.role_id = user_data['role_id']
        # Безопасное получение role_name
        self.role_name = user_data['role_name'] if 'role_name' in user_data else None

@login_manager.user_loader
def load_user(user_id):
    user_data = models.get_user_by_id(user_id)
    if user_data:
        return User(user_data)
    return None

# Декоратор для логирования посещений
@app.before_request
def log_visit():
    """Логирование всех посещений страниц"""
    # Исключаем статические файлы и перенаправления
    if request.endpoint and not request.endpoint.startswith('static'):
        path = request.path
        user_id = current_user.id if current_user.is_authenticated else None
        models.add_visit_log(path, user_id)

def validate_login(login):
    if not login or len(login) < 5:
        return False, 'Логин должен содержать не менее 5 символов'
    if not re.match(r'^[a-zA-Z0-9]+$', login):
        return False, 'Логин должен содержать только латинские буквы и цифры'
    return True, None

def validate_password(password):
    if not password or len(password) < 8:
        return False, 'Пароль должен содержать не менее 8 символов'
    if len(password) > 128:
        return False, 'Пароль должен содержать не более 128 символов'
    if not re.search(r'[A-ZА-Я]', password):
        return False, 'Пароль должен содержать хотя бы одну заглавную букву'
    if not re.search(r'[a-zа-я]', password):
        return False, 'Пароль должен содержать хотя бы одну строчную букву'
    if not re.search(r'[0-9]', password):
        return False, 'Пароль должен содержать хотя бы одну цифру'
    if re.search(r'\s', password):
        return False, 'Пароль не должен содержать пробелов'
    allowed = r'^[a-zA-Zа-яА-Я0-9~!?@#$%^&*_\-+()\[\]{}><\/\\|"\',.:;]+$'
    if not re.match(allowed, password):
        return False, 'Пароль содержит недопустимые символы'
    return True, None

def validate_name_field(value, field_name):
    if not value or not value.strip():
        return False, f'Поле "{field_name}" не может быть пустым'
    return True, None

@app.context_processor
def utility_processor():
    user_data = None
    user_role = None
    if current_user.is_authenticated:
        user_data = models.get_user_by_id(current_user.id)
        user_role = user_data['role_name'] if user_data else None
    return {
        'is_authenticated': current_user.is_authenticated,
        'user_role': user_role,
        'current_user_id': current_user.id if current_user.is_authenticated else None
    }

@app.route('/')
def index():
    users = models.get_all_users()
    return render_template('index.html', users=users)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user_data = models.get_user_by_login(login)
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data)
            login_user(user, remember=remember)
            flash('Вы успешно вошли в систему!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверный логин или пароль.', 'danger')
    return render_template('login.html')

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

@app.route('/user/<int:user_id>/')
def user_view(user_id):
    user = models.get_user_by_id(user_id)
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('index'))
    return render_template('user_view.html', user=user)

@app.route('/user/create/', methods=['GET', 'POST'])
@login_required
@check_rights(required_role='admin')
def user_create():
    roles = models.get_all_roles()
    errors = {}
    
    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        last_name = request.form.get('last_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        role_id = request.form.get('role_id')
        
        is_valid = True
        
        login_valid, login_error = validate_login(login)
        if not login_valid:
            errors['login'] = login_error
            is_valid = False
        
        password_valid, password_error = validate_password(password)
        if not password_valid:
            errors['password'] = password_error
            is_valid = False
        
        name_valid, name_error = validate_name_field(first_name, 'Имя')
        if not name_valid:
            errors['first_name'] = name_error
            is_valid = False
        
        if not role_id:
            errors['role_id'] = 'Выберите роль'
            is_valid = False
        
        if is_valid:
            success, error = models.create_user(
                login, password, last_name, first_name, middle_name, role_id
            )
            if success:
                flash('Пользователь успешно создан!', 'success')
                return redirect(url_for('index'))
            else:
                flash(f'Ошибка при создании: {error}', 'danger')
    
    return render_template('user_form.html', 
                         user=None, 
                         roles=roles, 
                         form_data=request.form if request.method == 'POST' else {},
                         errors=errors)

@app.route('/user/<int:user_id>/edit/', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    user = models.get_user_by_id(user_id)
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('index'))
    
    # Проверка прав
    user_data = models.get_user_by_id(current_user.id)
    user_role = user_data['role_name'] if user_data else None
    
    if user_role != 'admin' and user_id != current_user.id:
        flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
        return redirect(url_for('index'))
    
    roles = models.get_all_roles()
    errors = {}
    is_admin = (user_role == 'admin')
    
    if request.method == 'POST':
        last_name = request.form.get('last_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        
        is_valid = True
        
        name_valid, name_error = validate_name_field(first_name, 'Имя')
        if not name_valid:
            errors['first_name'] = name_error
            is_valid = False
        
        if is_admin:
            role_id = request.form.get('role_id')
            if not role_id:
                errors['role_id'] = 'Выберите роль'
                is_valid = False
            if is_valid:
                success, error = models.update_user(user_id, last_name, first_name, middle_name, role_id)
        else:
            # Обычный пользователь не может менять роль
            if is_valid:
                success, error = models.update_user_without_role(user_id, last_name, first_name, middle_name)
        
        if is_valid and success:
            flash('Пользователь успешно обновлён!', 'success')
            return redirect(url_for('index'))
        elif is_valid:
            flash(f'Ошибка при обновлении: {error}', 'danger')
    
    form_data = {
        'last_name': user['last_name'] or '',
        'first_name': user['first_name'],
        'middle_name': user['middle_name'] or '',
        'role_id': str(user['role_id']) if user['role_id'] and is_admin else ''
    }
    
    return render_template('user_form.html', 
                         user=user, 
                         roles=roles, 
                         form_data=form_data,
                         errors=errors,
                         is_admin=is_admin)

@app.route('/user/<int:user_id>/delete/', methods=['POST'])
@login_required
@check_rights(required_role='admin')
def user_delete(user_id):
    if user_id == current_user.id:
        flash('Нельзя удалить самого себя!', 'danger')
        return redirect(url_for('index'))
    
    success, error = models.delete_user(user_id)
    if success:
        flash('Пользователь успешно удалён!', 'success')
    else:
        flash(f'Ошибка при удалении: {error}', 'danger')
    return redirect(url_for('index'))

@app.route('/change-password/', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        user_data = models.get_user_by_id(current_user.id)
        
        if not check_password_hash(user_data['password_hash'], old_password):
            flash('Неверный старый пароль.', 'danger')
        elif new_password != confirm_password:
            flash('Новый пароль и подтверждение не совпадают.', 'danger')
        else:
            password_valid, password_error = validate_password(new_password)
            if not password_valid:
                flash(password_error, 'danger')
            else:
                success, error = models.change_password(current_user.id, new_password)
                if success:
                    flash('Пароль успешно изменён!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash(f'Ошибка при смене пароля: {error}', 'danger')
    
    return render_template('change_password.html')

if __name__ == '__main__':
    app.run(debug=True,port=5005)