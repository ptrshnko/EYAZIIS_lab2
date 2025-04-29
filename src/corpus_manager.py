import sqlite3
from collections import Counter

DB_PATH = "../db/corpus.db"

class CorpusManager:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def get_frequency(self, query, by='token', filters=None):
        """
        Подсчет частот по токенам, леммам или POS.
        :param query: строка поиска (токен или лемма)
        :param by: 'token', 'lemma' или 'pos'
        :param filters: dict с ключами 'pos', 'date_from', 'date_to', 'doc_ids'
        :return: Counter
        """
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

    def get_global_frequency(self, by='token', filters=None):
        """
        Подсчет общей частоты всех элементов указанного типа.
        :param by: 'token', 'lemma' или 'pos'
        :param filters: аналогично get_frequency
        :return: Counter
        """
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

    def get_concordance(self, query, window=5, filters=None):
        """
        KWIC: контексты вокруг query.
        :param query: строка поиска (токен или лемма)
        :param window: число токенов до и после
        :param filters: dict как выше
        :return: list of (left_context, match, right_context, doc_id, sent_id)
        """
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
            # получить контекст токенов в пределах предложения
            self.cursor.execute(
                "SELECT token FROM tokens WHERE doc_id = ? AND sent_id = ? ORDER BY token_id", 
                (doc_id, sent_id)
            )
            sentence = [r['token'] for r in self.cursor.fetchall()]
            # найти позицию токена
            # NOTE: token_id may not align index; fetch all token_ids
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

        return concordances

    def close(self):
        self.conn.close()


if __name__ == '__main__':
    cm = CorpusManager()
    print(cm.get_global_frequency(by='lemma').most_common(10))
    print(cm.get_concordance('автомобиль', window=3)[:5])
    cm.close()
