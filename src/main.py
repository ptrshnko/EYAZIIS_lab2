import os
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from gui import CorpusGUI
from corpus_loader import import_corpus
from text_cleaner import tokenize_and_store
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        os.path.join('data', 'raw'),
        os.path.join('data', 'cleaned'),
        os.path.join('data', 'tokens'),
        os.path.join('data', 'metadata')
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def main():
    """Main entry point for the application"""
    ensure_directories()
    
    # Import corpus and tokenize if metadata is empty
    metadata_path = os.path.join('data', 'metadata', 'metadata.json')
    try:
        if not os.path.exists(metadata_path) or os.path.getsize(metadata_path) == 0:
            print("Импорт корпуса...")
            import_corpus()
            print("Токенизация...")
            tokenize_and_store()
    except Exception as e:
        logger.error(f"Error during corpus initialization: {e}")
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "Ошибка", f"Не удалось инициализировать корпус: {str(e)}")
        sys.exit(1)
    
    # Start GUI
    app = QApplication(sys.argv)
    window = CorpusGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()