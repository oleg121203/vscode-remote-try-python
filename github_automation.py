import requests
import base64
from datetime import datetime
import subprocess
import os
import autopep8

# Використовуємо наданий токен через змінну середовища для безпеки
token = os.getenv('GITHUB_TOKEN')
if not token:
    raise EnvironmentError("GITHUB_TOKEN is not set in the environment variables")

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

repo_url = "https://github.com/oleg121203/more.git"
log_file_path = "script_log.txt"

# Функція для логування в файл
def log_to_file(message):
    with open(log_file_path, "a") as log_file:
        log_file.write(f"[{datetime.now()}] {message}\n")

# Інструменти для аналізу і виправлення коду
# Перевірка чи встановлено необхідні інструменти, якщо ні - встановлення через pip
def install_tools_if_needed():
    required_tools = ["black", "flake8", "pycodestyle"]
    for tool in required_tools:
        try:
            __import__(tool)
        except ImportError:
            print(f"[{datetime.now()}] Installing {tool}...")
            log_to_file(f"Installing {tool}...")
            try:
                subprocess.check_call(["pip", "install", tool])
            except subprocess.CalledProcessError as e:
                print(f"[{datetime.now()}] Error installing {tool}: {e}")
                log_to_file(f"Error installing {tool}: {e}")

# Використання Black для форматування коду
def format_code_with_black(file_path):
    try:
        print(f"[{datetime.now()}] Formatting code with Black...")
        log_to_file("Formatting code with Black...")
        subprocess.run(["black", file_path], check=True)
        print(f"[{datetime.now()}] Code formatted successfully.")
        log_to_file("Code formatted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now()}] Error formatting code: {e}")
        log_to_file(f"Error formatting code: {e}")
    except FileNotFoundError:
        print(f"[{datetime.now()}] Black is not installed. Please install it using 'pip install black'.")
        log_to_file("Black is not installed. Please install it using 'pip install black'.")

# Перевірка PEP8 за допомогою flake8
def check_pep8(file_path):
    try:
        print(f"[{datetime.now()}] Checking PEP8 compliance with flake8...")
        log_to_file("Checking PEP8 compliance with flake8...")
        result = subprocess.run(["flake8", file_path], capture_output=True, text=True)
        if result.stdout:
            print(f"[{datetime.now()}] PEP8 issues found: \n{result.stdout}")
            log_to_file(f"PEP8 issues found: \n{result.stdout}")
            # Автоматичне виправлення за допомогою autopep8
            fix_pep8_issues(file_path)
        else:
            print(f"[{datetime.now()}] No PEP8 issues found.")
            log_to_file("No PEP8 issues found.")
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now()}] Error checking PEP8 compliance: {e}")
        log_to_file(f"Error checking PEP8 compliance: {e}")
    except FileNotFoundError:
        print(f"[{datetime.now()}] flake8 is not installed. Please install it using 'pip install flake8'.")
        log_to_file("flake8 is not installed. Please install it using 'pip install flake8'.")

# Автоматичне виправлення PEP8 помилок за допомогою autopep8
def fix_pep8_issues(file_path):
    try:
        print(f"[{datetime.now()}] Fixing PEP8 issues with autopep8...")
        log_to_file("Fixing PEP8 issues with autopep8...")
        subprocess.run(["autopep8", "--in-place", "--aggressive", "--aggressive", file_path], check=True)
        print(f"[{datetime.now()}] PEP8 issues fixed successfully.")
        log_to_file("PEP8 issues fixed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now()}] Error fixing PEP8 issues: {e}")
        log_to_file(f"Error fixing PEP8 issues: {e}")
    except FileNotFoundError:
        print(f"[{datetime.now()}] autopep8 is not installed. Please install it using 'pip install autopep8'.")
        log_to_file("autopep8 is not installed. Please install it using 'pip install autopep8'.")

# 1. Отримання інформації про репозиторій
def get_repo_info(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"[{datetime.now()}] Error: {response.status_code} {response.json()}")
        log_to_file(f"Error: {response.status_code} {response.json()}")
        return None

# 2. Створення або оновлення файлу в репозиторії
def create_or_update_file(owner, repo, path, message, content, branch="main"):
    # Перевірка, чи файл вже існує
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sha = response.json().get("sha")
        print(f"[{datetime.now()}] File '{path}' already exists. Updating file.")
        log_to_file(f"File '{path}' already exists. Updating file.")
        update_file(owner, repo, path, message, content, sha, branch)
        return
    elif response.status_code != 404:
        print(f"Error checking if file exists: {response.status_code} {response.json()}")
        log_to_file(f"Error checking if file exists: {response.status_code} {response.json()}")
        return

    # Створення нового файлу
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch
    }
    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 201:
        print("File created successfully.")
        log_to_file("File created successfully.")
    else:
        print(f"[{datetime.now()}] Error creating file: {response.status_code} {response.json()}\n")
        log_to_file(f"Error creating file: {response.status_code} {response.json()}\n")

# 3. Оновлення файлу в репозиторії
def update_file(owner, repo, path, message, content, sha, branch="main"):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "sha": sha,
        "branch": branch
    }
    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 200:
        print("File updated successfully.")
        log_to_file("File updated successfully.")
    else:
        print(f"[{datetime.now()}] Error updating file: {response.status_code} {response.json()}")
        log_to_file(f"Error updating file: {response.status_code} {response.json()}")

# 4. Отримання SHA вихідної гілки
def get_branch_sha(owner, repo, branch):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["object"]["sha"]
    else:
        error_message = f"[{datetime.now()}] Error: Unable to get SHA for branch '{branch}': {response.status_code} {response.json()}"
        print(error_message)
        log_to_file(error_message)
        return None
