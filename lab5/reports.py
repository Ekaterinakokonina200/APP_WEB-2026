from flask import Blueprint, render_template, request, Response, flash, redirect, url_for
from flask_login import current_user
import csv
import io
from models import get_page_stats, get_user_stats, get_visit_logs, get_user_by_id

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.before_request
def check_access():
    """Проверка прав доступа к отчётам"""
    if not current_user.is_authenticated:
        flash('Пожалуйста, войдите для доступа к отчётам.', 'warning')
        return redirect(url_for('login'))
    
    user_data = get_user_by_id(current_user.id)
    if user_data['role_name'] != 'admin':
        flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
        return redirect(url_for('index'))

@reports_bp.route('/visit-logs/')
def visit_logs():
    """Страница журнала посещений"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    user_data = get_user_by_id(current_user.id)
    
    if user_data['role_name'] == 'admin':
        logs, total = get_visit_logs(page, per_page)
    else:
        logs, total = get_visit_logs(page, per_page, current_user.id)
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('visit_logs.html', 
                         logs=logs, 
                         page=page, 
                         total_pages=total_pages,
                         total=total)

@reports_bp.route('/pages/')
def report_pages():
    """Отчёт по страницам"""
    stats = get_page_stats()
    return render_template('report_pages.html', stats=stats)

@reports_bp.route('/pages/export/')
def export_pages_csv():
    """Экспорт отчёта по страницам в CSV"""
    stats = get_page_stats()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['№', 'Страница', 'Количество посещений'])
    
    for idx, stat in enumerate(stats, 1):
        writer.writerow([idx, stat['path'], stat['visits']])
    
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=pages_report.csv'
    return response

@reports_bp.route('/users/')
def report_users():
    """Отчёт по пользователям"""
    stats = get_user_stats()
    return render_template('report_users.html', stats=stats)

@reports_bp.route('/users/export/')
def export_users_csv():
    """Экспорт отчёта по пользователям в CSV"""
    stats = get_user_stats()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['№', 'Пользователь', 'Количество посещений'])
    
    for idx, stat in enumerate(stats, 1):
        if stat['user_id']:
            name = f"{stat['last_name'] or ''} {stat['first_name'] or ''} {stat['middle_name'] or ''}".strip()
            if not name:
                name = f"Пользователь {stat['user_id']}"
        else:
            name = "Неаутентифицированный пользователь"
        writer.writerow([idx, name, stat['visits']])
    
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=users_report.csv'
    return response