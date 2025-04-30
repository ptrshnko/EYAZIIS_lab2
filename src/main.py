import os
import sys
from PyQt5.QtWidgets import QApplication
from gui import CorpusGUI
from corpus_loader import import_corpus
from text_cleaner import tokenize_and_store

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        os.path.join('data', 'raw'),
        os.path.join('data', 'cleaned'),
        'db'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def main():
    """Main entry point for the application"""
    # Ensure required directories exist
    ensure_directories()
    
    # Import corpus if needed
    if not os.path.exists(os.path.join('db', 'corpus.db')):
        print("Импорт корпуса...")
        import_corpus()
        print("Токенизация...")
        tokenize_and_store()
    
    # Start GUI
    app = QApplication(sys.argv)
    window = CorpusGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 