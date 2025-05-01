import sys
import os
import shutil
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QFileDialog, QMessageBox, QMenuBar,
    QFormLayout, QDialog, QMenu, QAction, QDialogButtonBox, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt
from corpus_manager import CorpusManager
from corpus_loader import import_corpus
from text_cleaner import tokenize_and_store
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AddFileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить файл")
        layout = QFormLayout()
        
        self.file_label = QLabel("Выберите файл:")
        self.file_path = QLineEdit()
        self.file_btn = QPushButton("Обзор...")
        self.file_btn.clicked.connect(self.browse_file)
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(self.file_btn)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Например, 'Обзор фильма'")
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Например, 'Киножурнал'")
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Например, 'Иван Иванов'")
        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("Например, '2023'")
        self.genre_input = QLineEdit()
        self.genre_input.setPlaceholderText("Например, 'Обзор'")
        self.language_input = QLineEdit()
        self.language_input.setPlaceholderText("Например, 'Русский'")
        
        layout.addRow(self.file_label)
        layout.addRow(file_layout)
        layout.addRow("Название:", self.title_input)
        layout.addRow("Источник:", self.source_input)
        layout.addRow("Автор:", self.author_input)
        layout.addRow("Год:", self.year_input)
        layout.addRow("Жанр:", self.genre_input)
        layout.addRow("Язык:", self.language_input)
        
        self.buttons = QHBoxLayout()
        self.ok_btn = QPushButton("Добавить")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        self.buttons.addWidget(self.ok_btn)
        self.buttons.addWidget(self.cancel_btn)
        
        layout.addRow(self.buttons)
        self.setLayout(layout)
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Text Files (*.txt *.pdf *.doc *.docx *.rtf)")
        if file_path:
            self.file_path.setText(file_path)

class EditFileDialog(QDialog):
    def __init__(self, text, metadata, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать файл")
        self.resize(600, 400)
        layout = QVBoxLayout()
        
        self.text_edit = QTextEdit()
        self.text_edit.setText(text)
        layout.addWidget(self.text_edit)
        
        self.metadata_form = QFormLayout()
        self.title_input = QLineEdit(metadata.get('title', ''))
        self.source_input = QLineEdit(metadata.get('source', ''))
        self.author_input = QLineEdit(metadata.get('author', ''))
        self.year_input = QLineEdit(metadata.get('year', ''))
        self.genre_input = QLineEdit(metadata.get('genre', ''))
        self.language_input = QLineEdit(metadata.get('language', ''))
        
        self.metadata_form.addRow("Название:", self.title_input)
        self.metadata_form.addRow("Источник:", self.source_input)
        self.metadata_form.addRow("Автор:", self.author_input)
        self.metadata_form.addRow("Год:", self.year_input)
        self.metadata_form.addRow("Жанр:", self.genre_input)
        self.metadata_form.addRow("Язык:", self.language_input)
        layout.addLayout(self.metadata_form)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
        self.setLayout(layout)

class DeleteFileDialog(QDialog):
    def __init__(self, filenames, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Удалить файл")
        layout = QVBoxLayout()
        
        self.file_list = QComboBox()
        self.file_list.addItems(filenames)
        layout.addWidget(self.file_list)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
        self.setLayout(layout)

class CorpusGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Корпусный менеджер — Кинематограф")
        self.setMinimumSize(900, 700)
        try:
            self.manager = CorpusManager()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось инициализировать корпус: {str(e)}")
            sys.exit(1)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Menu bar
        self.menu_bar = QMenuBar()
        file_menu = QMenu("Файлы", self)
        self.add_file_action = QAction("Добавить файл", self)
        self.add_file_action.triggered.connect(self.add_file)
        file_menu.addAction(self.add_file_action)
        self.create_file_action = QAction("Создать новый", self)
        self.create_file_action.triggered.connect(self.create_new_file)
        file_menu.addAction(self.create_file_action)
        self.edit_file_action = QAction("Редактировать файл", self)
        self.edit_file_action.triggered.connect(self.edit_file)
        file_menu.addAction(self.edit_file_action)
        self.delete_file_action = QAction("Удалить файл", self)
        self.delete_file_action.triggered.connect(self.delete_file)
        file_menu.addAction(self.delete_file_action)
        self.save_results_action = QAction("Сохранить результаты", self)
        self.save_results_action.triggered.connect(self.save_results)
        file_menu.addAction(self.save_results_action)
        self.menu_bar.addMenu(file_menu)
        
        help_menu = QMenu("Справка", self)
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        self.menu_bar.addMenu(help_menu)
        
        layout.setMenuBar(self.menu_bar)

        # Filter parameters
        filter_layout = QGridLayout()
        filter_layout.addWidget(QLabel("Запрос:"), 0, 0)
        self.query_input = QLineEdit()
        filter_layout.addWidget(self.query_input, 0, 1, 1, 3)

        filter_layout.addWidget(QLabel("Тип поиска:"), 1, 0)
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Словоформа", "Часть речи"])
        filter_layout.addWidget(self.search_type_combo, 1, 1)

        filter_layout.addWidget(QLabel("Фильтр по источнику:"), 2, 0)
        self.source_filter = QLineEdit()
        self.source_filter.setPlaceholderText("Например, 'Киножурнал'")
        filter_layout.addWidget(self.source_filter, 2, 1)

        filter_layout.addWidget(QLabel("Фильтр по автору:"), 3, 0)
        self.author_filter = QLineEdit()
        self.author_filter.setPlaceholderText("Например, 'Иван Иванов'")
        filter_layout.addWidget(self.author_filter, 3, 1)

        layout.addLayout(filter_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.search_btn = QPushButton("Частотный анализ")
        self.search_btn.clicked.connect(self.run_frequency)
        self.morph_btn = QPushButton("Морфологический анализ")
        self.morph_btn.clicked.connect(self.run_morphological_analysis)
        self.concord_btn = QPushButton("Показать конкордансы")
        self.concord_btn.clicked.connect(self.run_concordance)
        self.save_btn = QPushButton("Сохранить результаты")
        self.save_btn.clicked.connect(self.save_results)
        btn_layout.addWidget(self.search_btn)
        btn_layout.addWidget(self.morph_btn)
        btn_layout.addWidget(self.concord_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        # Results area
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(2)
        self.results_table.setHorizontalHeaderLabels(["Элемент", "Значение"])
        layout.addWidget(self.results_table)

        self.setLayout(layout)

    def add_file(self):
        dialog = AddFileDialog(self)
        if dialog.exec_():
            file_path = dialog.file_path.text()
            title = dialog.title_input.text()
            source = dialog.source_input.text()
            author = dialog.author_input.text()
            year = dialog.year_input.text()
            genre = dialog.genre_input.text()
            language = dialog.language_input.text()
            if not file_path:
                QMessageBox.warning(self, "Предупреждение", "Выберите файл.")
                return
            try:
                fname = os.path.basename(file_path)
                dest_path = os.path.join('data', 'raw', fname)
                shutil.copy(file_path, dest_path)
                import_corpus(new_files=[(fname, source, author, year, genre, language, title)])
                tokenize_and_store()
                self.manager = CorpusManager()
                QMessageBox.information(self, "Успех", "Файл добавлен.")
            except Exception as e:
                logger.error(f"Error adding file: {e}")
                QMessageBox.critical(self, "Ошибка", str(e))

    def create_new_file(self):
        dialog = EditFileDialog("", {"title": "", "source": "", "author": "", "year": "", "genre": "", "language": ""}, self)
        if dialog.exec_():
            text = dialog.text_edit.toPlainText()
            title = dialog.title_input.text()
            source = dialog.source_input.text()
            author = dialog.author_input.text()
            year = dialog.year_input.text()
            genre = dialog.genre_input.text()
            language = dialog.language_input.text()
            if not text or not title:
                QMessageBox.warning(self, "Предупреждение", "Введите текст и название.")
                return
            fname, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Text Files (*.txt)")
            if fname:
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(text)
                shutil.copy(fname, os.path.join('data', 'raw', os.path.basename(fname)))
                import_corpus(new_files=[(os.path.basename(fname), source, author, year, genre, language, title)])
                tokenize_and_store()
                self.manager = CorpusManager()
                QMessageBox.information(self, "Успех", "Файл создан.")

    def edit_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Выберите файл для редактирования", "data/raw", "Text Files (*.txt)")
        if fname:
            with open(fname, 'r', encoding='utf-8') as f:
                text = f.read()
            metadata = next((meta for meta in self.manager.metadata.values() if meta['path_raw'] == fname), {})
            dialog = EditFileDialog(text, metadata, self)
            if dialog.exec_():
                new_text = dialog.text_edit.toPlainText()
                title = dialog.title_input.text()
                source = dialog.source_input.text()
                author = dialog.author_input.text()
                year = dialog.year_input.text()
                genre = dialog.genre_input.text()
                language = dialog.language_input.text()
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(new_text)
                import_corpus()
                tokenize_and_store()
                self.manager = CorpusManager()
                if title or source or author or year or genre or language:
                    self.update_metadata(os.path.basename(fname), title, source, author, year, genre, language)
                QMessageBox.information(self, "Успех", "Файл обновлен.")

    def delete_file(self):
        filenames = [meta['filename'] for meta in self.manager.metadata.values()]
        if not filenames:
            QMessageBox.warning(self, "Предупреждение", "Нет файлов для удаления.")
            return
        dialog = DeleteFileDialog(filenames, self)
        if dialog.exec_():
            filename = dialog.file_list.currentText()
            self.manager.remove_document(filename)
            import_corpus()
            tokenize_and_store()
            self.manager = CorpusManager()
            QMessageBox.information(self, "Успех", "Файл удален.")

    def save_results(self):
        if not self.results_table.rowCount():
            QMessageBox.warning(self, "Предупреждение", "Нет результатов для сохранения.")
            return
        fname, _ = QFileDialog.getSaveFileName(self, "Сохранить результаты", "", "JSON Files (*.json)")
        if fname:
            results = {}
            for row in range(self.results_table.rowCount()):
                key = self.results_table.item(row, 0).text()
                value = self.results_table.item(row, 1).text()
                results[key] = value
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Успех", "Результаты сохранены.")

    def show_about(self):
        QMessageBox.information(self, "О программе", "Корпусный менеджер для текстов о кинематографии.\nВерсия 1.0")

    def run_frequency(self):
        query = self.query_input.text().strip()
        search_type = self.search_type_combo.currentText()
        filters = {}
        if self.source_filter.text():
            filters['source'] = self.source_filter.text()
        if self.author_filter.text():
            filters['author'] = self.author_filter.text()
        try:
            if search_type == "Словоформа":
                results = self.manager.get_wordform_frequency(query, filters)
                self.display_results({k: str(v) for k, v in results.items()})
            elif search_type == "Часть речи":
                pos_results = self.manager.get_pos_analysis(query)
                self.display_results({word: pos for word, pos in pos_results})
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def run_morphological_analysis(self):
        query = self.query_input.text().strip()
        try:
            results = self.manager.get_morphological_analysis(query)
            self.display_results({f"{r['token']}": f"Лемма: {r['lemma']}, POS: {r['pos']}, Граммемы: {r['grammems']}" for r in results})
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def run_concordance(self):
        query = self.query_input.text().strip()
        filters = {}
        if self.source_filter.text():
            filters['source'] = self.source_filter.text()
        if self.author_filter.text():
            filters['author'] = self.author_filter.text()
        try:
            concordances = self.manager.get_concordance(query, window=5, filters=filters)
            self.display_results({f"Конкорданс {i+1}": f"... {' '.join(left)} >> {match} << {' '.join(right)} ... (doc {doc_id}, sent {sent_id})" for i, (left, match, right, doc_id, sent_id) in enumerate(concordances)})
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def display_results(self, results):
        self.results_table.setRowCount(0)
        for key, value in results.items():
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(key))
            self.results_table.setItem(row, 1, QTableWidgetItem(value))

    def update_metadata(self, filename, title, source, author, year, genre, language):
        for doc_id, meta in self.manager.metadata.items():
            if meta['filename'] == filename:
                meta.update({
                    'title': title or meta.get('title', ''),
                    'source': source or meta.get('source', ''),
                    'author': author or meta.get('author', ''),
                    'year': year or meta.get('year', ''),
                    'genre': genre or meta.get('genre', ''),
                    'language': language or meta.get('language', '')
                })
                with open(os.path.join('data', 'metadata', 'metadata.json'), 'w', encoding='utf-8') as f:
                    json.dump(self.manager.metadata, f, ensure_ascii=False, indent=2)
                break

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CorpusGUI()
    window.show()
    sys.exit(app.exec_())