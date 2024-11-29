from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS  # Добавляем поддержку CORS
import os
from functools import wraps
import json
from datetime import datetime

# Імпортуємо функції з нашого автоматизаційного скрипта
from github_automation import create_or_update_file, format_code_with_black, check_pep8, refactor_imports, remove_unused_code, fix_docstrings
from github_upload import upload_to_github
from ngrok_manager import start_ngrok, stop_ngrok

app = Flask(__name__)
CORS(app)  # Включаем CORS для всех маршрутов

# Обновленная конфигурация приложения
app.secret_key = 'very-secret-key'  # Фиксированный ключ для тестирования
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=1800
)
USERNAME = "oleg"
PASSWORD = "oleg"

# Декоратор для проверки авторизации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            flash('Успішний вхід!', 'success')
            return redirect(url_for('home'))
        flash('Невірні дані для входу!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Ви вийшли з системи', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    # Получаем историю операций из файла или базы данных
    history = get_operation_history()
    # Добавляем информацию о GitHub
    github_info = {
        'token': os.getenv('GITHUB_TOKEN', 'Not set'),
        'repository': os.getenv('GITHUB_REPOSITORY', 'oleg121203/vscode-remote-try-python'),
        'token_status': 'Active' if os.getenv('GITHUB_TOKEN') else 'Not configured'
    }
    ngrok_url = session.get('ngrok_url', None)
    return render_template('home.html', 
                         history=history, 
                         github_info=github_info,
                         ngrok_url=ngrok_url)

@app.route('/run_script', methods=['POST'])
@login_required
def run_script():
    try:
        action = request.form['action']
        file_path = request.form.get('file_path', 'github_automation.py')
        result = None

        if action == "create_file":
            result = create_or_update_file(
                "oleg121203", 
                "vscode-remote-try-python", 
                "web_created_file.txt", 
                "Test Commit from Flask", 
                "Це контент створений через веб-інтерфейс"
            )
        elif action == "format_code":
            result = format_code_with_black(file_path)
        elif action == "check_pep8":
            result = check_pep8(file_path)
        elif action == "refactor_imports":
            result = refactor_imports(file_path)
        elif action == "remove_unused":
            result = remove_unused_code(file_path)
        elif action == "fix_docstrings":
            result = fix_docstrings(file_path)
        
        if result:
            flash('Операція виконана успішно!', 'success')
            add_to_history(action)
            
        return redirect(url_for('home'))
    
    except Exception as e:
        flash(f'Помилка: {str(e)}', 'error')
        return redirect(url_for('home'))

# Добавляем API эндпоинты
@app.route('/api/run_script', methods=['POST'])
def run_script_api():
    # Проверка авторизации через API токен
    api_token = request.headers.get('X-API-Token')
    if api_token != 'your-api-token':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        if not data or 'action' not in data:
            return jsonify({'error': 'Invalid request'}), 400

        action = data['action']
        file_path = data.get('file_path', 'github_automation.py')
        result = None

        if action == "create_file":
            result = create_or_update_file(
                "oleg121203",
                "vscode-remote-try-python",
                "api_created_file.txt",
                "API Commit",
                "Це API-тестовий контент"
            )
        elif action == "format_code":
            result = format_code_with_black(file_path)
        elif action == "check_pep8":
            result = check_pep8(file_path)
        elif action == "refactor_imports":
            result = refactor_imports(file_path)
        elif action == "remove_unused":
            result = remove_unused_code(file_path)
        elif action == "fix_docstrings":
            result = fix_docstrings(file_path)
        
        if result:
            add_to_history(action)
            return jsonify({'message': 'Operation completed successfully'})
        return jsonify({'error': 'Operation failed'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history_api():
    api_token = request.headers.get('X-API-Token')
    if api_token != 'your-api-token':
        return jsonify({'error': 'Unauthorized'}), 401
    
    history = get_operation_history()
    return jsonify({'history': history})

# Добавляем новый эндпоинт для проверки подключения
@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok', 'message': 'Server is running'})

@app.route('/upload_to_github', methods=['POST'])
@login_required
def handle_github_upload():
    try:
        files_to_upload = request.form.getlist('files')
        github_token = request.form.get('token')
        repository = request.form.get('repository')
        
        if not files_to_upload or not github_token or not repository:
            flash('Всі поля форми повинні бути заповнені!', 'warning')
            return redirect(url_for('home'))
        
        # Сохраняем текущий токен и репозиторий
        os.environ['GITHUB_TOKEN'] = github_token
        os.environ['GITHUB_REPOSITORY'] = repository
        
        success = upload_to_github(github_token, repository, files_to_upload)
        
        if success:
            flash(f'Успішно завантажено файли: {", ".join(files_to_upload)}', 'success')
            add_to_history('github_upload')
        else:
            flash('Помилка при завантаженні файлів', 'danger')
            
        return redirect(url_for('home'))
        
    except Exception as e:
        flash(f'Помилка: {str(e)}', 'danger')
        return redirect(url_for('home'))

@app.route('/manage_ngrok', methods=['POST'])
@login_required
def manage_ngrok():
    action = request.form.get('action')
    if action == 'start':
        success, result = start_ngrok()
        if success:
            flash('Ngrok успешно запущен!', 'success')
            session['ngrok_url'] = result
        else:
            flash(f'Ошибка запуска Ngrok: {result}', 'danger')
    elif action == 'stop':
        if stop_ngrok():
            flash('Ngrok остановлен', 'success')
            session.pop('ngrok_url', None)
        else:
            flash('Ошибка при остановке Ngrok', 'danger')
    return redirect(url_for('home'))

def get_operation_history():
    try:
        with open('operation_history.json', 'r') as f:
            return json.load(f)
    except:
        return []

def add_to_history(action):
    history = get_operation_history()
    history.append({
        'action': action,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    with open('operation_history.json', 'w') as f:
        json.dump(history[-10:], f)  # Храним только последние 10 операций

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Обновляем конфигурацию для работы с ngrok
if __name__ == "__main__":
    print("Starting Flask server...")
    print("Username:", USERNAME)
    print("Password:", PASSWORD)
    print("API Token: your-api-token")
    
    # Разрешаем внешние подключения
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
