import sys
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QComboBox, QDateEdit,
    QTableWidget, QTableWidgetItem, QTextEdit, QFileDialog,
    QCheckBox, QGridLayout, QMessageBox, QDialog, QFormLayout
)
from PyQt5.QtCore import QDate
from corpus_manager import CorpusManager
from corpus_loader import import_corpus
from text_cleaner import tokenize_and_store
import logging

# Setup logging
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
        
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Например, 'Киножурнал'")
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Например, 'Иван Иванов'")
        
        layout.addRow(self.file_label)
        layout.addRow(file_layout)
        layout.addRow("Источник:", self.source_input)
        layout.addRow("Автор:", self.author_input)
        
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

        # Filter parameters
        filter_layout = QGridLayout()
        filter_layout.addWidget(QLabel("Токен/лемма:"), 0, 0)
        self.query_input = QLineEdit()
        filter_layout.addWidget(self.query_input, 0, 1, 1, 3)

        filter_layout.addWidget(QLabel("Поиск по:"), 1, 0)
        self.by_combo = QComboBox()
        self.by_combo.addItems(["token", "lemma", "pos"])
        filter_layout.addWidget(self.by_combo, 1, 1)

        filter_layout.addWidget(QLabel("POS-фильтр:"), 2, 0)
        self.pos_filter = QLineEdit()
        self.pos_filter.setPlaceholderText("например, NOUN, VERB...")
        filter_layout.addWidget(self.pos_filter, 2, 1)

        filter_layout.addWidget(QLabel("Источник:"), 3, 0)
        self.source_filter = QLineEdit()
        self.source_filter.setPlaceholderText("например, Киножурнал")
        filter_layout.addWidget(self.source_filter, 3, 1)

        filter_layout.addWidget(QLabel("Автор:"), 4, 0)
        self.author_filter = QLineEdit()
        self.author_filter.setPlaceholderText("например, Иван Иванов")
        filter_layout.addWidget(self.author_filter, 4, 1)

        filter_layout.addWidget(QLabel("Дата с:"), 2, 2)
        self.date_from = QDateEdit(calendarPopup=True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.date_from, 2, 3)

        filter_layout.addWidget(QLabel("по:"), 3, 2)
        self.date_to = QDateEdit(calendarPopup=True)
        self.date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.date_to, 3, 3)

        self.include_pos = QCheckBox("Применить POS-фильтр")
        filter_layout.addWidget(self.include_pos, 1, 2)
        self.include_date = QCheckBox("Применить фильтр по дате")
        filter_layout.addWidget(self.include_date, 1, 3)
        self.include_source = QCheckBox("Применить фильтр по источнику")
        filter_layout.addWidget(self.include_source, 4, 2)
        self.include_author = QCheckBox("Применить фильтр по автору")
        filter_layout.addWidget(self.include_author, 4, 3)

        layout.addLayout(filter_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.add_file_btn = QPushButton("Добавить файл")
        self.add_file_btn.clicked.connect(self.add_file)
        self.search_btn = QPushButton("Частотный анализ")
        self.search_btn.clicked.connect(self.run_frequency)
        self.concord_btn = QPushButton("Показать конкордансы")
        self.concord_btn.clicked.connect(self.run_concordance)
        self.export_btn = QPushButton("Экспорт в CSV")
        self.export_btn.clicked.connect(self.export_csv)
        btn_layout.addWidget(self.add_file_btn)
        btn_layout.addWidget(self.search_btn)
        btn_layout.addWidget(self.concord_btn)
        btn_layout.addWidget(self.export_btn)
        layout.addLayout(btn_layout)

        # Results
        layout.addWidget(QLabel("Результаты частотного анализа:"))
        self.results_area = QTableWidget()
        self.results_area.setColumnCount(2)
        self.results_area.setHorizontalHeaderLabels(["Элемент", "Частота"])
        layout.addWidget(self.results_area)

        layout.addWidget(QLabel("Конкордансы:"))
        self.concord_area = QTextEdit()
        self.concord_area.setReadOnly(True)
        layout.addWidget(self.concord_area)

        # Help
        self.help_area = QTextEdit()
        self.help_area.setReadOnly(True)
        self.help_area.setHtml(
            "<h3>Инструкция</h3>"
            "<ul>"
            "<li>Нажмите 'Добавить файл' для загрузки новых документов.</li>"
            "<li>Введите токен или лемму в поле и выберите тип поиска.</li>"
            "<li>При необходимости отметьте фильтрацию по POS, дате, источнику или автору.</li>"
            "<li>Нажмите 'Частотный анализ' для отображения частот или 'Показать конкордансы' для контекстов.</li>"
            "<li>Для экспорта результатов частот нажмите 'Экспорт в CSV'.</li>"
            "<li>Убедитесь, что в папке data/raw есть текстовые файлы.</li>"
            "</ul>"
        )
        layout.addWidget(QLabel("Справка:"))
        layout.addWidget(self.help_area)

        self.setLayout(layout)

    def add_file(self):
        dialog = AddFileDialog(self)
        if dialog.exec_():
            file_path = dialog.file_path.text()
            source = dialog.source_input.text().strip()
            author = dialog.author_input.text().strip()
            
            if not file_path:
                QMessageBox.warning(self, "Предупреждение", "Пожалуйста, выберите файл.")
                return
            
            # Copy file to data/raw
            try:
                fname = os.path.basename(file_path)
                dest_path = os.path.join('data', 'raw', fname)
                shutil.copy(file_path, dest_path)
                logger.info(f"Copied file to {dest_path}")
                
                # Process only the new file
                import_corpus(new_files=[(fname, source, author)])
                tokenize_and_store()
                
                # Reload CorpusManager to reflect new data
                self.manager = CorpusManager()
                QMessageBox.information(self, "Успех", "Файл успешно добавлен и обработан.")
            except Exception as e:
                logger.error(f"Error adding file: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить файл: {str(e)}")

    def get_filters(self):
        f = {}
        if self.include_pos.isChecked():
            pos = self.pos_filter.text().strip().lower()
            if pos:
                f['pos'] = pos
        if self.include_date.isChecked():
            f['date_from'] = self.date_from.date().toString('yyyy-MM-dd')
            f['date_to'] = self.date_to.date().toString('yyyy-MM-dd')
        if self.include_source.isChecked():
            source = self.source_filter.text().strip().lower()
            if source:
                f['source'] = source
        if self.include_author.isChecked():
            author = self.author_filter.text().strip().lower()
            if author:
                f['author'] = author
        logger.debug(f"Filters applied: {f}")
        return f or None

    def run_frequency(self):
        logger.info("Frequency analysis button clicked")
        self.results_area.clearContents()
        self.results_area.setRowCount(0)

        query = self.query_input.text().strip()
        by = self.by_combo.currentText()
        filters = self.get_filters()

        if not query:
            QMessageBox.warning(self, "Предупреждение", "Введите токен или лемму для поиска.")
            return

        try:
            result = self.manager.get_frequency(query=query, by=by, filters=filters)
            if not result:
                QMessageBox.warning(self, "Нет результатов", f"Не найдено совпадений для '{query}' (тип: {by}).")
                return
            self.results_area.setRowCount(len(result))
            for row, (elem, freq) in enumerate(result.items()):
                self.results_area.setItem(row, 0, QTableWidgetItem(elem))
                self.results_area.setItem(row, 1, QTableWidgetItem(str(freq)))
            logger.info(f"Displayed {len(result)} frequency results")
        except Exception as e:
            logger.error(f"Error in frequency analysis: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при выполнении частотного анализа: {str(e)}")

    def run_concordance(self):
        logger.info("Concordance button clicked")
        self.concord_area.clear()
        query = self.query_input.text().strip()
        filters = self.get_filters()

        if not query:
            QMessageBox.warning(self, "Предупреждение", "Введите токен или лемму для поиска.")
            return

        try:
            concordances = self.manager.get_concordance(query=query, window=5, filters=filters)
            if not concordances:
                QMessageBox.warning(self, "Нет результатов", f"Не найдено конкордансов для '{query}'.")
                return
            for left, match, right, doc_id, sent_id in concordances:
                line = f"... {' '.join(left)} >> {match} << {' '.join(right)} ... (doc {doc_id}, sent {sent_id})"
                self.concord_area.append(line)
            logger.info(f"Displayed {len(concordances)} concordances")
        except Exception as e:
            logger.error(f"Error in concordance analysis: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при получении конкордансов: {str(e)}")

    def export_csv(self):
        logger.info("Export CSV button clicked")
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        rows = []
        for row in range(self.results_area.rowCount()):
            elem = self.results_area.item(row, 0).text()
            freq = self.results_area.item(row, 1).text()
            rows.append(f"{elem},{freq}\n")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(rows)
            logger.info(f"Exported results to {path}")
            QMessageBox.information(self, "Успех", "Результаты успешно экспортированы в CSV.")
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при экспорте CSV: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CorpusGUI()
    window.show()
    sys.exit(app.exec_())