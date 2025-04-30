# src/corpus_loader.py

import os
import sqlite3
import logging
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from striprtf.striprtf import rtf_to_text

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
CLEANED_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
DB_PATH = os.path.join(BASE_DIR, 'db', 'corpus.db')

def init_db():
    """Инициализация базы данных"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            doc_id     INTEGER PRIMARY KEY,
            filename   TEXT,
            path_raw   TEXT,
            path_txt   TEXT,
            title      TEXT,
            source     TEXT,
            date       DATE
        )
        ''')
        conn.commit()
        conn.close()
        logger.info("База данных успешно инициализирована")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise

def convert_file(filepath):
    """Конвертация файла в текст"""
    try:
        ext = filepath.lower().rsplit('.', 1)[-1]
        if ext == 'txt':
            with open(filepath, encoding='utf-8') as f:
                return f.read()
        elif ext == 'pdf':
            text = []
            reader = PdfReader(filepath)
            for page in reader.pages:
                text.append(page.extract_text() or '')
            return '\n'.join(text)
        elif ext == 'docx':
            doc = DocxDocument(filepath)
            return '\n'.join(p.text for p in doc.paragraphs)
        elif ext == 'rtf':
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return rtf_to_text(f.read())
        else:
            logger.warning(f"Неподдерживаемый формат файла: {filepath}")
            return ''
    except Exception as e:
        logger.error(f"Ошибка при конвертации файла {filepath}: {e}")
        return ''

def import_corpus():
    """Импорт корпуса в базу данных"""
    try:
        # Проверяем существование директорий
        os.makedirs(RAW_DIR, exist_ok=True)
        os.makedirs(CLEANED_DIR, exist_ok=True)
        
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for fname in os.listdir(RAW_DIR):
            path_raw = os.path.join(RAW_DIR, fname)
            if not os.path.isfile(path_raw):
                continue
                
            text = convert_file(path_raw)
            if not text.strip():
                logger.warning(f"Пустой текст в файле: {fname}")
                continue
                
            # Сохраняем текст
            base, _ = os.path.splitext(fname)
            txt_name = base + '.txt'
            path_txt = os.path.join(CLEANED_DIR, txt_name)
            
            try:
                with open(path_txt, 'w', encoding='utf-8') as f:
                    f.write(text)
            except Exception as e:
                logger.error(f"Ошибка при сохранении текста {path_txt}: {e}")
                continue
                
            # Запись в БД
            try:
                cursor.execute('''
                    INSERT INTO documents (filename, path_raw, path_txt, title)
                    VALUES (?, ?, ?, ?)
                ''', (fname, path_raw, path_txt, text.splitlines()[0][:200]))
            except sqlite3.Error as e:
                logger.error(f"Ошибка при записи в БД для файла {fname}: {e}")
                continue
                
        conn.commit()
        conn.close()
        logger.info("Импорт корпуса успешно завершен")
    except Exception as e:
        logger.error(f"Критическая ошибка при импорте корпуса: {e}")
        raise

if __name__ == '__main__':
    import_corpus()
