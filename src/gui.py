import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QComboBox, QSpinBox, QDateEdit,
    QTableWidget, QTableWidgetItem, QTextEdit, QFileDialog,
    QCheckBox, QGridLayout
)
from PyQt5.QtCore import QDate
from corpus_manager import CorpusManager


class CorpusGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Корпусный менеджер — Транспорт")
        self.setMinimumSize(900, 700)

        self.manager = CorpusManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Параметры фильтрации
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

        layout.addLayout(filter_layout)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.search_btn = QPushButton("Частотный анализ")
        self.search_btn.clicked.connect(self.run_frequency)
        self.concord_btn = QPushButton("Показать конкордансы")
        self.concord_btn.clicked.connect(self.run_concordance)
        self.export_btn = QPushButton("Экспорт в CSV")
        self.export_btn.clicked.connect(self.export_csv)
        btn_layout.addWidget(self.search_btn)
        btn_layout.addWidget(self.concord_btn)
        btn_layout.addWidget(self.export_btn)
        layout.addLayout(btn_layout)

        # Результаты
        layout.addWidget(QLabel("Результаты частотного анализа:"))
        self.results_area = QTableWidget()
        self.results_area.setColumnCount(2)
        self.results_area.setHorizontalHeaderLabels(["Элемент", "Частота"])
        layout.addWidget(self.results_area)

        layout.addWidget(QLabel("Конкордансы:"))
        self.concord_area = QTextEdit()
        self.concord_area.setReadOnly(True)
        layout.addWidget(self.concord_area)

        # Справка
        self.help_area = QTextEdit()
        self.help_area.setReadOnly(True)
        self.help_area.setHtml(
            "<h3>Инструкция</h3>"
            "<ul>"
            "<li>Введите токен или лемму в поле и выберите тип поиска.</li>"
            "<li>При необходимости отметьте фильтрацию по POS или дате и задайте параметры.</li>"
            "<li>Нажмите 'Частотный анализ' для отображения частот или 'Показать конкордансы' для контекстов.</li>"
            "<li>Для экспорта результатов частот нажмите 'Экспорт в CSV'.</li>"
            "</ul>"
        )
        layout.addWidget(QLabel("Справка:"))
        layout.addWidget(self.help_area)

        self.setLayout(layout)

    def get_filters(self):
        f = {}
        if self.include_pos.isChecked():
            f['pos'] = self.pos_filter.text().strip()
        if self.include_date.isChecked():
            f['date_from'] = self.date_from.date().toString('yyyy-MM-dd')
            f['date_to'] = self.date_to.date().toString('yyyy-MM-dd')
        return f or None

    def run_frequency(self):
        self.results_area.clearContents()
        self.results_area.setRowCount(0)

        query = self.query_input.text().strip()
        by = self.by_combo.currentText()
        filters = self.get_filters()
        if not query:
            return

        result = self.manager.get_frequency(query=query, by=by, filters=filters)
        self.results_area.setRowCount(len(result))
        for row, (elem, freq) in enumerate(result.items()):
            self.results_area.setItem(row, 0, QTableWidgetItem(elem))
            self.results_area.setItem(row, 1, QTableWidgetItem(str(freq)))

    def run_concordance(self):
        self.concord_area.clear()
        query = self.query_input.text().strip()
        filters = self.get_filters()
        if not query:
            return

        concordances = self.manager.get_concordance(query=query, window=5, filters=filters)
        for left, match, right, doc_id, sent_id in concordances:
            line = f"... {' '.join(left)} >> {match} << {' '.join(right)} ... (doc {doc_id}, sent {sent_id})"
            self.concord_area.append(line)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        rows = []
        for row in range(self.results_area.rowCount()):
            elem = self.results_area.item(row, 0).text()
            freq = self.results_area.item(row, 1).text()
            rows.append(f"{elem},{freq}\n")
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(rows)

    def closeEvent(self, event):
        self.manager.close()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CorpusGUI()
    window.show()
    sys.exit(app.exec_())
