# src/text_cleaner.py

import os
import sqlite3
import logging
from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    Doc
)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEANED_DIR = os.path.join(BASE_DIR, 'data', 'cleaned')
DB_PATH = os.path.join(BASE_DIR, 'db', 'corpus.db')

# Инициализируем инструменты Natasha
segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)

def tokenize_and_store():
    """Пройти по всем документам, сегментировать и токенизировать текст, 
    сохранить токены в БД (таблица tokens)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Создаём таблицу tokens, если она не существует
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            token_id   INTEGER PRIMARY KEY,
            doc_id     INTEGER,
            sent_id    INTEGER,
            token      TEXT,
            lemma      TEXT,
            pos        TEXT,
            grammems   TEXT,
            FOREIGN KEY(doc_id) REFERENCES documents(doc_id)
        )
        ''')

        # Получаем все документы
        cursor.execute('SELECT doc_id, path_txt FROM documents')
        docs = cursor.fetchall()

        if not docs:
            logger.warning("Нет документов для обработки")
            return

        for doc_id, path_txt in docs:
            if not os.path.exists(path_txt):
                logger.error(f"Файл не найден: {path_txt}")
                continue

            try:
                with open(path_txt, encoding='utf-8') as f:
                    text = f.read()
            except Exception as e:
                logger.error(f"Ошибка при чтении файла {path_txt}: {e}")
                continue

            # Обрабатываем документ Natasha
            try:
                nat_doc = Doc(text)
                nat_doc.segment(segmenter)
                nat_doc.tag_morph(morph_tagger)
            except Exception as e:
                logger.error(f"Ошибка при обработке документа {doc_id}: {e}")
                continue
            
            token_count = 0
            for sent_id, sent in enumerate(nat_doc.sents, start=1):
                for token in sent.tokens:
                    try:
                        token.lemmatize(morph_vocab)
                        cursor.execute('''
                            INSERT INTO tokens (doc_id, sent_id, token, lemma, pos, grammems)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            doc_id,
                            sent_id,
                            token.text,
                            token.lemma,
                            token.pos,
                            ','.join(f'{k}={v}' for k,v in token.feats.items())
                        ))
                        token_count += 1
                    except sqlite3.Error as e:
                        logger.error(f"Ошибка при сохранении токена: {e}")
                        continue

            logger.info(f'Документ {doc_id} обработан: {token_count} токенов.')

        conn.commit()
        conn.close()
        logger.info("Токенизация успешно завершена")
    except Exception as e:
        logger.error(f"Критическая ошибка при токенизации: {e}")
        raise

if __name__ == '__main__':
    tokenize_and_store()
