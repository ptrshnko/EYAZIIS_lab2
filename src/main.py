import os
import sys
import json  # Added missing import
from PyQt5.QtWidgets import QApplication, QMessageBox
from gui import CorpusGUI
from corpus_loader import import_corpus
from text_cleaner import tokenize_and_store
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist and create metadata.json if missing"""
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
    """Main entry point for the application"""
    ensure_directories()
    
    # Check and populate metadata if missing or empty
    metadata_path = os.path.join('data', 'metadata', 'metadata.json')
    raw_files = [f for f in os.listdir(os.path.join('data', 'raw')) if os.path.isfile(os.path.join('data', 'raw', f))]
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        if not metadata or not raw_files:
            if raw_files:
                logger.info("Populating metadata and tokenizing existing files...")
                import_corpus()
                tokenize_and_store()
            else:
                logger.warning("No files found in data/raw. Metadata will remain empty until files are added.")
    except Exception as e:
        logger.error(f"Error initializing corpus: {e}")
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