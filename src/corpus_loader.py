# src/corpus_loader.py

import os
import sqlite3
from tika import parser
from docx import Document as DocxDocument

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
CLEANED_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned')
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'corpus.db')

def init_db():
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

def convert_file(filepath):
    ext = filepath.lower().split('.')[-1]
    if ext == 'txt':
        with open(filepath, encoding='utf-8') as f:
            return f.read()
    elif ext in ('pdf',):
        raw = parser.from_file(filepath)
        return raw.get('content', '')
    elif ext in ('docx',):
        doc = DocxDocument(filepath)
        return '\n'.join(p.text for p in doc.paragraphs)
    elif ext in ('rtf',):
        raw = parser.from_file(filepath)
        return raw.get('content', '')
    else:
        return ''

def import_corpus():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for fname in os.listdir(RAW_DIR):
        path_raw = os.path.join(RAW_DIR, fname)
        text = convert_file(path_raw)
        if not text.strip():
            continue
        # Сохраняем текст
        base, _ = os.path.splitext(fname)
        txt_name = base + '.txt'
        path_txt = os.path.join(CLEANED_DIR, txt_name)
        with open(path_txt, 'w', encoding='utf-8') as f:
            f.write(text)
        # Запись в БД
        cursor.execute('''
            INSERT INTO documents (filename, path_raw, path_txt, title)
            VALUES (?, ?, ?, ?)
        ''', (fname, path_raw, path_txt, text.splitlines()[0][:200]))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    import_corpus()
    print("Импорт корпуса завершён.")
