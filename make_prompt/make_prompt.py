#!/usr/bin/env python3
"""
Скрипт для создания единого markdown файла с кодовой базой для LLM промпта.
Рекурсивно сканирует директорию и объединяет файлы указанных типов.
"""

import os
import sys
from pathlib import Path
from typing import Set, List, Optional

# Настройки по умолчанию
DEFAULT_EXTENSIONS = {'.md', '.py', '.js', '.css', '.html', '.json'}
DEFAULT_IGNORE_DIRS = {
    '.git', '__pycache__', 'node_modules', 'venv', '.venv',
    'env', '.env', 'dist', 'build', '.idea', '.vscode', 'make_prompt', 'make_pormpt', 'doc','backups','datasets','json','minio-data','models','runs','temp_video','tests','utils'
}
MAX_FILE_SIZE = 200 * 1024  # 200KB

# Соответствие расширений языкам для подсветки синтаксиса
EXTENSION_TO_LANG = {
    '.py': 'python',
    '.js': 'javascript',
    '.md': 'markdown',
    '.css': 'css',
    '.html': 'html',
    '.json': 'json',
}


def find_files(root_dir: Path, extensions: Set[str], ignore_dirs: Set[str]) -> List[Path]:
    """
    Рекурсивно находит файлы с указанными расширениями.
    
    Args:
        root_dir: Корневая директория для поиска
        extensions: Множество расширений файлов
        ignore_dirs: Множество игнорируемых директорий
    
    Returns:
        Отсортированный список найденных файлов
    """
    found_files = []
    
    for item in root_dir.rglob('*'):
        if not item.is_file():
            continue
            
        if item.suffix.lower() not in extensions:
            continue
        
        # Проверяем, не находится ли файл в игнорируемой директории
        try:
            rel_path = item.relative_to(root_dir)
            if any(part in ignore_dirs for part in rel_path.parts[:-1]):
                continue
        except ValueError:
            continue
        
        found_files.append(item)
    
    return sorted(found_files)


def read_file_safely(file_path: Path, max_size: int) -> Optional[str]:
    """
    Безопасно читает файл с обработкой ошибок и проверкой размера.
    
    Args:
        file_path: Путь к файлу
        max_size: Максимальный размер файла в байтах
    
    Returns:
        Содержимое файла или сообщение об ошибке
    """
    try:
        file_size = file_path.stat().st_size
        if file_size > max_size:
            return f"⚠️ Файл пропущен: размер {file_size:,} байт превышает лимит {max_size:,} байт"
        
        # Пробуем разные кодировки
        for encoding in ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1']:
            try:
                return file_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        
        return "⚠️ Не удалось прочитать файл: ошибка кодировки"
    except PermissionError:
        return "⚠️ Нет доступа к файлу: permission denied"
    except Exception as e:
        return f"⚠️ Ошибка чтения файла: {e}"


def create_prompt_file(
    root_dir: Path,
    output_file: Path,
    extensions: Set[str] = None,
    ignore_dirs: Set[str] = None,
    max_size: int = MAX_FILE_SIZE
) -> None:
    """
    Создает единый markdown файл с содержимым всех найденных файлов.
    
    Args:
        root_dir: Корневая директория проекта
        output_file: Путь к выходному markdown файлу
        extensions: Расширения файлов для включения
        ignore_dirs: Директории для игнорирования
        max_size: Максимальный размер файла в байтах
    """
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS
    if ignore_dirs is None:
        ignore_dirs = DEFAULT_IGNORE_DIRS
    
    print(f"🔍 Сканирую директорию: {root_dir}")
    print(f"🎯 Ищу файлы с расширениями: {', '.join(sorted(extensions))}")
    print(f"🚫 Игнорирую папки: {', '.join(sorted(ignore_dirs))}")
    print(f"📏 Лимит размера файла: {max_size:,} байт")
    
    files_to_process = find_files(root_dir, extensions, ignore_dirs)
    
    if not files_to_process:
        print("\n❌ Файлы не найдены.")
        return
    
    print(f"\n✅ Найдено файлов: {len(files_to_process)}")
    print(f"💾 Создаю промпт-файл: {output_file}")
    
    success_count = 0
    error_count = 0
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Заголовок
        f.write("# Промпт с кодовой базой\n\n")
        f.write(f"**Сгенерировано:** {Path().cwd().name}\n\n")
        f.write(f"**Источник:** `{root_dir}`\n\n")
        f.write(f"**Файлов найдено:** {len(files_to_process)}\n\n")
        
        # Оглавление
        f.write("## Оглавление\n\n")
        for file_path in files_to_process:
            rel_path = file_path.relative_to(root_dir)
            anchor = str(rel_path).replace(' ', '-').replace('.', '')
            f.write(f"- [{rel_path}](#{anchor})\n")
        f.write("\n---\n\n")
        
        # Содержимое файлов
        for idx, file_path in enumerate(files_to_process, 1):
            rel_path = file_path.relative_to(root_dir)
            
            # Заголовок файла
            anchor = str(rel_path).replace(' ', '-').replace('.', '')
            f.write(f"<a id='{anchor}'></a>\n\n")
            f.write(f"* {rel_path}\n\n")
            
            # Содержимое
            content = read_file_safely(file_path, max_size)
            lang = EXTENSION_TO_LANG.get(file_path.suffix.lower(), '')
            
            f.write(f"```{lang}\n")
            f.write(content)
            f.write("\n```\n\n")
            f.write("---\n\n")
            
            # Статус в консоль
            if content.startswith('⚠️'):
                error_count += 1
                print(f"❌ [{idx}/{len(files_to_process)}] {rel_path} - ОШИБКА")
            else:
                success_count += 1
                print(f"✅ [{idx}/{len(files_to_process)}] {rel_path}")
    
    print(f"\n🎉 Готово!")
    print(f"   ✅ Успешно обработано: {success_count}")
    print(f"   ❌ Ошибок: {error_count}")
    print(f"   📄 Результат: {output_file}")
    
    # Показываем примерный размер
    if output_file.exists():
        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"   📊 Размер файла: {size_mb:.2f} MB")


def parse_arguments():
    """Парсинг аргументов командной строки."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Создает единый markdown файл с кодовой базой для LLM промпта',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Примеры использования:
  # Стандартный запуск в текущей директории
  python {sys.argv[0]}
  
  # Указать конкретную директорию
  python {sys.argv[0]} -d /path/to/project
  
  # Указать выходной файл
  python {sys.argv[0]} -o my_prompt.md
  
  # Добавить дополнительные расширения
  python {sys.argv[0]} -e .txt .yaml .sh
  
  # Исключить дополнительные папки
  python {sys.argv[0]} -i logs temp cache
  
  # Увеличить лимит размера файла
  python {sys.argv[0]} --max-size 500000
        """
    )
    
    parser.add_argument(
        '-d', '--directory',
        type=str,
        default='.',
        help='Корневая директория для сканирования (по умолчанию: текущая)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='prompt.md',
        help='Имя выходного markdown файла (по умолчанию: prompt.md)'
    )
    
    parser.add_argument(
        '-e', '--extensions',
        nargs='*',
        type=str,
        default=[],
        help='Дополнительные расширения файлов для включения (например: .txt .yaml)'
    )
    
    parser.add_argument(
        '-i', '--ignore',
        nargs='*',
        type=str,
        default=[],
        help='Дополнительные папки для игнорирования (например: logs temp)'
    )
    
    parser.add_argument(
        '--max-size',
        type=int,
        default=MAX_FILE_SIZE,
        help=f'Максимальный размер файла в байтах (по умолчанию: {MAX_FILE_SIZE:,})'
    )
    
    return parser.parse_args()


def main():
    """Точка входа в приложение."""
    args = parse_arguments()
    
    # Подготовка путей
    root_dir = Path(args.directory).resolve()
    output_file = Path(args.output)
    
    # Проверки
    if not root_dir.exists():
        print(f"❌ Директория не существует: {root_dir}")
        sys.exit(1)
    
    if not root_dir.is_dir():
        print(f"❌ Указанный путь не является директорией: {root_dir}")
        sys.exit(1)
    
    # Объединяем настройки
    extensions = DEFAULT_EXTENSIONS | set(args.extensions)
    ignore_dirs = DEFAULT_IGNORE_DIRS | set(args.ignore)
    
    # Запуск
    try:
        create_prompt_file(root_dir, output_file, extensions, ignore_dirs, args.max_size)
    except KeyboardInterrupt:
        print("\n\n⛔ Прервано пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()