# src/text_cleaner.py

import os
import sqlite3
from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    Doc
)

# Пути
BASE_DIR = os.path.dirname(__file__)
CLEANED_DIR = os.path.join(BASE_DIR, '..', 'data', 'cleaned')
DB_PATH = os.path.join(BASE_DIR, '..', 'db', 'corpus.db')

# Инициализируем инструменты Natasha
segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)

def tokenize_and_store():
    """Пройти по всем документам, сегментировать и токенизировать текст, 
    сохранить токены в БД (таблица tokens)."""
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

    for doc_id, path_txt in docs:
        with open(path_txt, encoding='utf-8') as f:
            text = f.read()

        # Обрабатываем документ Natasha
        nat_doc = Doc(text)
        nat_doc.segment(segmenter)
        nat_doc.tag_morph(morph_tagger)
        
        for sent_id, sent in enumerate(nat_doc.sents, start=1):
            for token in sent.tokens:
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
        print(f'Документ {doc_id} обработан: {len(nat_doc.tokens)} токенов.')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    tokenize_and_store()
    print("Предобработка и токенизация завершены.")
