import os
import sys
import json
from PyQt5.QtWidgets import QApplication, QMessageBox
from gui import CorpusGUI
from corpus_loader import import_corpus
from text_cleaner import tokenize_and_store
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories():
    """Создание необходимых директорий"""
    directories = [
        os.path.join('data', 'raw'),
        os.path.join('data', 'cleaned'),
        os.path.join('data', 'tokens'),
        os.path.join('data', 'metadata')
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    metadata_path = os.path.join('data', 'metadata', 'metadata.json')
    if not os.path.exists(metadata_path):
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        logger.info("Created new metadata.json file")

def main():
    """Основная функция запуска приложения"""
    ensure_directories()
    
    metadata_path = os.path.join('data', 'metadata', 'metadata.json')
    try:
        # Проверка целостности метаданных
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Если метаданные пусты или есть файлы в data/raw, импортируем корпус
        raw_files = [f for f in os.listdir(os.path.join('data', 'raw')) if os.path.isfile(os.path.join('data', 'raw', f))]
        if not metadata or raw_files:
            logger.info("Populating metadata and tokenizing existing files...")
            import_corpus()
            tokenize_and_store()
    except json.JSONDecodeError as e:
        logger.error(f"Metadata file is corrupted: {e}. Creating a new one.")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        import_corpus()
        tokenize_and_store()
    except Exception as e:
        logger.error(f"Error during corpus initialization: {e}")
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "Ошибка", f"Не удалось инициализировать корпус: {str(e)}")
        sys.exit(1)
    
    # Запуск GUI
    app = QApplication(sys.argv)
    try:
        window = CorpusGUI()
        window.show()
        sys.exit(app.exec_())
    except AttributeError as e:
        logger.error(f"GUI initialization error: {e}")
        QMessageBox.critical(None, "Ошибка", f"Ошибка инициализации интерфейса: {str(e)}. Проверьте файл gui.py.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during GUI launch: {e}")
        QMessageBox.critical(None, "Ошибка", f"Неожиданная ошибка: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()