from github import Github
import os

def upload_to_github(token, repo_name, file_paths):
    """
    Загружает файлы на GitHub
    
    Args:
        token (str): Персональный токен доступа GitHub
        repo_name (str): Имя репозитория (формат: 'username/repository')
        file_paths (list): Список путей к файлам для загрузки
    """
    try:
        # Инициализация GitHub с токеном
        g = Github(token)
        
        # Получение репозитория
        repo = g.get_repo(repo_name)
        
        for file_path in file_paths:
            # Читаем содержимое файла
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Получаем имя файла из пути
            file_name = os.path.basename(file_path)
            
            try:
                # Проверяем существует ли файл
                contents = repo.get_contents(file_name)
                # Обновляем существующий файл
                repo.update_file(
                    contents.path,
                    f"Update {file_name}",
                    content,
                    contents.sha
                )
                print(f"Updated {file_name}")
            except:
                # Создаем новый файл
                repo.create_file(
                    file_name,
                    f"Add {file_name}",
                    content
                )
                print(f"Created {file_name}")
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

# Пример использования:
if __name__ == "__main__":
    # Получаем токен из переменной окружения
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable is not set")
        print("Please set it using: export GITHUB_TOKEN='your_token'")
        exit(1)
    
    repository = "oleg121203/vscode-remote-try-python"  # Обновите на ваш репозиторий
    files_to_upload = ["requirements.txt", "github_upload.py"]
    
    print(f"Attempting to upload files to GitHub repository: {repository}")
    success = upload_to_github(github_token, repository, files_to_upload)
    if success:
        print("Files uploaded successfully")
    else:
        print("Failed to upload files")