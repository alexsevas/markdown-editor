"""
Скрипт для создания релиза Markdown Editor для Windows
Использует PyInstaller для создания one-folder дистрибутива
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_dirs():
    """Очищает директории сборки"""
    print("Cleaning build directories...")
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed {dir_name}/")

def check_pyinstaller():
    """Проверяет установлен ли PyInstaller"""
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def build_executable():
    """Собирает исполняемый файл"""
    print("\nBuilding executable...")
    
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "markdown_editor.spec"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Build failed!")
        print(result.stderr)
        return False
    
    print("Build successful!")
    return True

def get_version():
    """Получает версию из main.py"""
    with open('main.py', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('# v'):
                return line.strip().replace('# v', '')
    return '0.1.4'

def create_readme():
    """Создает README для релиза"""
    version = get_version()
    readme_content = f"""# Markdown Editor v{version}

## Описание
Markdown редактор с live preview, поддержкой LaTeX формул и экспортом в PDF.

## Возможности
- Редактирование Markdown с подсветкой синтаксиса
- Live preview с рендерингом LaTeX формул (MathJax)
- Синхронизация позиции курсора между редактором и preview
- Экспорт в PDF
- Темная и светлая темы
- Поддержка различных кодировок
- Масштабирование preview (Ctrl+Plus/Minus/0)
- Подсветка HTML img тегов и Markdown изображений синим цветом

## Системные требования
- Windows 10 или выше
- 300+ MB свободного места на диске

## Запуск
Запустите файл `MarkdownEditor.exe`

## Горячие клавиши
- Ctrl+N - Новый файл
- Ctrl+O - Открыть файл
- Ctrl+S - Сохранить
- Ctrl+Shift+S - Сохранить как
- Ctrl+P - Экспорт в PDF
- Ctrl+D - Переключить темную тему
- Ctrl+Plus/Minus - Изменить масштаб preview
- Ctrl+0 - Сбросить масштаб preview
- F11 - Показать/скрыть preview

## Лицензия
См. файл LICENSE

## Автор
alexsevas (a1exsevas@yandex.ru)
"""
    
    readme_path = Path("dist/MarkdownEditor/README.txt")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"Created {readme_path}")

def copy_license():
    """Копирует LICENSE в корень дистрибутива"""
    src = Path("dist/MarkdownEditor/_internal/LICENSE")
    dst = Path("dist/MarkdownEditor/LICENSE")
    
    if src.exists():
        shutil.copy2(src, dst)
        print(f"Copied LICENSE to {dst}")
    else:
        print("Warning: LICENSE not found in _internal/")

def create_archive():
    """Создает ZIP архив с релизом"""
    print("\nCreating release archive...")
    
    version = get_version()
    dist_dir = Path("dist/MarkdownEditor")
    
    if not dist_dir.exists():
        print("Error: dist/MarkdownEditor not found!")
        return False
    
    archive_name = f"MarkdownEditor_v{version}_Windows"
    shutil.make_archive(archive_name, 'zip', 'dist', 'MarkdownEditor')
    
    archive_path = Path(f"{archive_name}.zip")
    size_mb = archive_path.stat().st_size / (1024 * 1024)
    
    print(f"Archive created: {archive_path}")
    print(f"Size: {size_mb:.2f} MB")
    
    return True

def main():
    """Основная функция сборки"""
    print("=" * 60)
    print("Markdown Editor - Windows Release Builder")
    print("=" * 60)
    
    if not check_pyinstaller():
        print("Failed to install PyInstaller")
        return 1
    
    clean_build_dirs()
    
    if not build_executable():
        return 1
    
    create_readme()
    copy_license()
    
    if not create_archive():
        return 1
    
    print("\n" + "=" * 60)
    print("Build completed successfully!")
    print("=" * 60)
    print("\nRelease package is ready in:")
    version = get_version()
    print(f"  MarkdownEditor_v{version}_Windows.zip")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
