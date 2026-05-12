from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def check_rights(required_role=None, allow_self=False):
    """
    Декоратор для проверки прав доступа
    
    required_role: имя роли, которая имеет доступ ('admin' или 'user')
    allow_self: разрешить доступ к своему профилю (для обычных пользователей)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Если пользователь не аутентифицирован
            if not current_user.is_authenticated:
                flash('Пожалуйста, войдите для доступа к этой странице.', 'warning')
                return redirect(url_for('login'))
            
            # Получаем роль пользователя из базы
            from models import get_user_by_id
            user_data = get_user_by_id(current_user.id)
            user_role = user_data['role_name'] if user_data else None
            
            # Проверка для обычного пользователя (доступ к своему профилю)
            if allow_self and 'user_id' in kwargs:
                if kwargs['user_id'] == current_user.id:
                    return f(*args, **kwargs)
            
            # Проверка роли
            if required_role == 'admin' and user_role == 'admin':
                return f(*args, **kwargs)
            elif required_role == 'user' and user_role == 'user':
                return f(*args, **kwargs)
            elif required_role == 'admin' and user_role != 'admin':
                flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
                return redirect(url_for('index'))
            elif required_role == 'user' and user_role != 'user':
                flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
                return redirect(url_for('index'))
            
            # Если роль не указана (любой аутентифицированный пользователь)
            return f(*args, **kwargs)
        return decorated_function
    return decorator