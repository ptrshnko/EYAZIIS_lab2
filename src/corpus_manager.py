import os
import sqlite3
import logging
from collections import Counter

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'db', 'corpus.db')

class CorpusManager:
    def __init__(self, db_path=DB_PATH):
        """Инициализация менеджера корпуса"""
        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            logger.info("Подключение к базе данных установлено")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при подключении к базе данных: {e}")
            raise

    def get_frequency(self, query, by='token', filters=None):
        """
        Подсчет частот по токенам, леммам или POS.
        :param query: строка поиска (токен или лемма)
        :param by: 'token', 'lemma' или 'pos'
        :param filters: dict с ключами 'pos', 'date_from', 'date_to', 'doc_ids'
        :return: Counter
        """
        try:
            field = by
            sql = f"SELECT {field} FROM tokens t JOIN documents d ON t.doc_id = d.doc_id WHERE {field} = ?"
            params = [query]
            if filters:
                if 'pos' in filters:
                    sql += " AND t.pos = ?"
                    params.append(filters['pos'])
                if 'date_from' in filters:
                    sql += " AND d.date >= ?"
                    params.append(filters['date_from'])
                if 'date_to' in filters:
                    sql += " AND d.date <= ?"
                    params.append(filters['date_to'])
                if 'doc_ids' in filters:
                    placeholders = ','.join('?' for _ in filters['doc_ids'])
                    sql += f" AND t.doc_id IN ({placeholders})"
                    params.extend(filters['doc_ids'])
            self.cursor.execute(sql, params)
            rows = self.cursor.fetchall()
            return Counter([row[field] for row in rows])
        except sqlite3.Error as e:
            logger.error(f"Ошибка при подсчете частот: {e}")
            return Counter()

    def get_global_frequency(self, by='token', filters=None):
        """
        Подсчет общей частоты всех элементов указанного типа.
        :param by: 'token', 'lemma' или 'pos'
        :param filters: аналогично get_frequency
        :return: Counter
        """
        try:
            field = by
            sql = f"SELECT {field} FROM tokens t JOIN documents d ON t.doc_id = d.doc_id"
            params = []
            if filters:
                where_clauses, where_params = [], []
                if 'pos' in filters:
                    where_clauses.append("t.pos = ?")
                    where_params.append(filters['pos'])
                if 'date_from' in filters:
                    where_clauses.append("d.date >= ?")
                    where_params.append(filters['date_from'])
                if 'date_to' in filters:
                    where_clauses.append("d.date <= ?")
                    where_params.append(filters['date_to'])
                if 'doc_ids' in filters:
                    placeholders = ','.join('?' for _ in filters['doc_ids'])
                    where_clauses.append(f"t.doc_id IN ({placeholders})")
                    where_params.extend(filters['doc_ids'])
                if where_clauses:
                    sql += " WHERE " + " AND ".join(where_clauses)
                    params = where_params
            self.cursor.execute(sql, params)
            rows = self.cursor.fetchall()
            return Counter([row[field] for row in rows])
        except sqlite3.Error as e:
            logger.error(f"Ошибка при подсчете глобальной частоты: {e}")
            return Counter()

    def get_concordance(self, query, window=5, filters=None):
        """
        KWIC: контексты вокруг query.
        :param query: строка поиска (токен или лемма)
        :param window: число токенов до и после
        :param filters: dict как выше
        :return: list of (left_context, match, right_context, doc_id, sent_id)
        """
        try:
            # Получить все токены с контекстом
            sql = ("SELECT t.doc_id, t.sent_id, t.token_id, t.token, t.lemma, t.pos "
                   "FROM tokens t JOIN documents d ON t.doc_id = d.doc_id WHERE (t.token = ? OR t.lemma = ?)")
            params = [query, query]
            if filters:
                if 'pos' in filters:
                    sql += " AND t.pos = ?"
                    params.append(filters['pos'])
                if 'date_from' in filters:
                    sql += " AND d.date >= ?"
                    params.append(filters['date_from'])
                if 'date_to' in filters:
                    sql += " AND d.date <= ?"
                    params.append(filters['date_to'])
            self.cursor.execute(sql, params)
            matches = self.cursor.fetchall()

            concordances = []
            for m in matches:
                doc_id, sent_id, token_id = m['doc_id'], m['sent_id'], m['token_id']
                try:
                    # получить контекст токенов в пределах предложения
                    self.cursor.execute(
                        "SELECT token FROM tokens WHERE doc_id = ? AND sent_id = ? ORDER BY token_id", 
                        (doc_id, sent_id)
                    )
                    sentence = [r['token'] for r in self.cursor.fetchall()]
                    # найти позицию токена
                    self.cursor.execute(
                        "SELECT token_id, token FROM tokens WHERE doc_id = ? AND sent_id = ? ORDER BY token_id", 
                        (doc_id, sent_id)
                    )
                    full = self.cursor.fetchall()
                    ids = [r['token_id'] for r in full]
                    idx = ids.index(token_id)
                    left = [r['token'] for r in full[max(0, idx-window):idx]]
                    right = [r['token'] for r in full[idx+1:idx+1+window]]
                    concordances.append((left, full[idx]['token'], right, doc_id, sent_id))
                except sqlite3.Error as e:
                    logger.error(f"Ошибка при получении контекста для токена {token_id}: {e}")
                    continue

            return concordances
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении конкордансов: {e}")
            return []

    def close(self):
        """Закрытие соединения с базой данных"""
        try:
            self.conn.close()
            logger.info("Соединение с базой данных закрыто")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при закрытии соединения: {e}")


if __name__ == '__main__':
    cm = CorpusManager()
    print(cm.get_global_frequency(by='lemma').most_common(10))
    print(cm.get_concordance('автомобиль', window=3)[:5])
    cm.close()
