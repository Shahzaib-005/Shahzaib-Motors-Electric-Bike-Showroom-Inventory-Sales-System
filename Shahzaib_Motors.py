"""
Shahzaib Motors - Electric Bike Showroom Inventory & Sales System
A complete PyQt6 desktop application with SQLite, ReportLab, Pandas/OpenPyXL.
"""

import sys
import os
import sqlite3
from datetime import datetime, date, timedelta
from io import BytesIO

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QDialog, QFormLayout, QMessageBox,
    QHeaderView, QFrame, QGridLayout, QDateEdit, QSpinBox,
    QDoubleSpinBox, QTextEdit, QScrollArea, QSizePolicy, QSplitter,
    QFileDialog, QAbstractItemView
)
from PyQt6.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon, QPalette

# ─────────────────────────────────────────────────────────────────
# DATABASE LAYER
# ─────────────────────────────────────────────────────────────────

if getattr(sys, 'frozen', False):
    # Running as compiled exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as normal python script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "shahzaib_motors.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS bikes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            brand       TEXT    NOT NULL,
            model       TEXT    NOT NULL,
            color       TEXT    NOT NULL,
            sale_price  REAL    NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 0,
            date_added  TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS customers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            phone       TEXT NOT NULL,
            cnic        TEXT NOT NULL,
            address     TEXT NOT NULL,
            date_added  TEXT NOT NULL
        );

      CREATE TABLE IF NOT EXISTS sales (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id    INTEGER NOT NULL,
            bike_id        INTEGER NOT NULL,
            sale_price     REAL    NOT NULL,
            amount_paid    REAL    NOT NULL,
            pending_amount REAL    NOT NULL,
            sale_date      TEXT    NOT NULL,
            vin_number     TEXT    DEFAULT '',
            battery_serial TEXT    DEFAULT '',
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (bike_id)     REFERENCES bikes(id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    # Insert defaults if not present
    defaults = [
        ("shop_name",    "Shahzaib Motors"),
        ("shop_tagline", "Electric Bike Showroom & Service"),
        ("shop_address", "Multan, Punjab, Pakistan"),
        ("shop_phone",   "0300-0000000"),
        ("shop_email",   "shahzaibmotors@gmail.com"),
        ("shop_website", "ShahzaibMotors.com"),
        ("logo_path",    ""),
    ]
    for key, val in defaults:
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
    conn.commit()
    # Migrate existing database — safe to run every time
    try:
        conn.execute("ALTER TABLE sales ADD COLUMN vin_number TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE sales ADD COLUMN battery_serial TEXT DEFAULT ''")
    except Exception:
        pass
    conn.commit()
    conn.close()



def get_setting(key, default=""):
    try:
        conn = get_connection()
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        conn.close()
        return row["value"] if row else default
    except Exception:
        return default


def set_setting(key, value):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()



# ─────────────────────────────────────────────────────────────────
# STYLESHEET
# ─────────────────────────────────────────────────────────────────

APP_STYLE = """
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

/* ── Sidebar ── */
#sidebar {
    background-color: #010409;
    border-right: 1px solid #21262d;
    min-width: 210px;
    max-width: 210px;
}
#logo_label {
    color: #58a6ff;
    font-size: 16px;
    font-weight: bold;
    padding: 20px 16px 8px 16px;
    letter-spacing: 1px;
}
#logo_sub {
    color: #8b949e;
    font-size: 10px;
    padding: 0px 16px 20px 16px;
    letter-spacing: 2px;
}
QPushButton#nav_btn {
    background-color: transparent;
    color: #8b949e;
    border: none;
    text-align: left;
    padding: 12px 20px;
    font-size: 13px;
    border-radius: 0px;
}
QPushButton#nav_btn:hover {
    background-color: #161b22;
    color: #e6edf3;
}
QPushButton#nav_btn:checked {
    background-color: #1f2937;
    color: #58a6ff;
    border-left: 3px solid #58a6ff;
    font-weight: bold;
}

/* ── Content area ── */
#content_area {
    background-color: #0d1117;
}

/* ── Page title ── */
#page_title {
    color: #e6edf3;
    font-size: 22px;
    font-weight: bold;
    padding: 24px 28px 4px 28px;
}
#page_subtitle {
    color: #8b949e;
    font-size: 12px;
    padding: 0px 28px 20px 28px;
}

/* ── KPI Cards ── */
#kpi_card {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 20px;
    min-width: 160px;
}
#kpi_value {
    color: #58a6ff;
    font-size: 28px;
    font-weight: bold;
}
#kpi_label {
    color: #8b949e;
    font-size: 11px;
    letter-spacing: 1px;
}
#kpi_icon {
    font-size: 22px;
}

/* ── Tables ── */
QTableWidget {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    gridline-color: #21262d;
    color: #e6edf3;
    selection-background-color: #1f3a5f;
    alternate-background-color: #0d1117;
}
QTableWidget::item {
    padding: 8px 10px;
    border: none;
}
QTableWidget::item:selected {
    background-color: #1f3a5f;
    color: #e6edf3;
}
QHeaderView::section {
    background-color: #21262d;
    color: #8b949e;
    padding: 10px;
    border: none;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
QHeaderView::section:first {
    border-top-left-radius: 8px;
}
QHeaderView::section:last {
    border-top-right-radius: 8px;
}
QScrollBar:vertical {
    background: #161b22;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal {
    background: #161b22;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 4px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

/* ── Buttons ── */
QPushButton#primary_btn {
    background-color: #1f6feb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton#primary_btn:hover { background-color: #388bfd; }
QPushButton#primary_btn:pressed { background-color: #1158c7; }

QPushButton#danger_btn {
    background-color: #da3633;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton#danger_btn:hover { background-color: #f85149; }

QPushButton#success_btn {
    background-color: #238636;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton#success_btn:hover { background-color: #2ea043; }

QPushButton#secondary_btn {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
}
QPushButton#secondary_btn:hover { background-color: #30363d; }

QPushButton#export_btn {
    background-color: #6e40c9;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton#export_btn:hover { background-color: #8957e5; }

/* ── Inputs ── */
QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QDateEdit, QTextEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #e6edf3;
    padding: 8px 10px;
    font-size: 13px;
    selection-background-color: #1f3a5f;
}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus,
QSpinBox:focus, QDateEdit:focus, QTextEdit:focus {
    border-color: #58a6ff;
    outline: none;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}
QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    color: #e6edf3;
    selection-background-color: #1f3a5f;
}
QDateEdit::drop-down { border: none; width: 24px; }
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #21262d;
    border: none;
    border-radius: 3px;
    width: 18px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #30363d;
}

/* ── Dialogs ── */
QDialog {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
}
QDialog QLabel { color: #e6edf3; font-size: 13px; }

/* ── Section headers ── */
#section_header {
    color: #e6edf3;
    font-size: 14px;
    font-weight: bold;
    padding: 12px 0px 8px 0px;
    border-bottom: 1px solid #21262d;
    margin-bottom: 8px;
}

/* ── Divider ── */
QFrame#divider {
    color: #21262d;
    background-color: #21262d;
    max-height: 1px;
}

/* ── Status badge ── */
#badge_green { color: #3fb950; font-weight: bold; }
#badge_red   { color: #f85149; font-weight: bold; }
#badge_yellow{ color: #e3b341; font-weight: bold; }

/* ── Receipt preview ── */
#receipt_box {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 20px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    color: #e6edf3;
}
"""

# ─────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────

def today_str():
    return date.today().strftime("%Y-%m-%d")


def fmt_currency(value):
    return f"PKR {value:,.0f}"


def make_table_widget(headers):
    tbl = QTableWidget()
    tbl.setColumnCount(len(headers))
    tbl.setHorizontalHeaderLabels(headers)
    tbl.horizontalHeader().setStretchLastSection(True)
    tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    tbl.verticalHeader().setVisible(False)
    tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tbl.setAlternatingRowColors(True)
    tbl.setShowGrid(True)
    tbl.setSortingEnabled(True)
    return tbl


def set_item(tbl, row, col, text, align=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft):
    item = QTableWidgetItem(str(text))
    item.setTextAlignment(align)
    tbl.setItem(row, col, item)


def page_header(title, subtitle=""):
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(28, 20, 28, 0)
    lay.setSpacing(2)
    t = QLabel(title)
    t.setObjectName("page_title")
    t.setContentsMargins(0, 0, 0, 0)
    lay.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setObjectName("page_subtitle")
        lay.addWidget(s)
    return w


# ─────────────────────────────────────────────────────────────────
# DIALOGS
# ─────────────────────────────────────────────────────────────────

class BikeDialog(QDialog):
    def __init__(self, parent=None, bike=None):
        super().__init__(parent)
        self.bike = bike
        self.setWindowTitle("Add Bike" if bike is None else "Edit Bike")
        self.setMinimumWidth(420)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Add New Bike" if self.bike is None else "Edit Bike")
        title.setObjectName("section_header")
        lay.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.brand = QLineEdit()
        self.model = QLineEdit()
        self.color = QLineEdit()
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 10_000_000)
        self.price.setPrefix("PKR ")
        self.price.setSingleStep(1000)
        self.qty   = QSpinBox()
        self.qty.setRange(0, 9999)

        form.addRow("Brand:",    self.brand)
        form.addRow("Model:",    self.model)
        form.addRow("Color:",    self.color)
        form.addRow("Price:",    self.price)
        form.addRow("Quantity:", self.qty)
        lay.addLayout(form)

        if self.bike:
            self.brand.setText(self.bike["brand"])
            self.model.setText(self.bike["model"])
            self.color.setText(self.bike["color"])
            self.price.setValue(self.bike["sale_price"])
            self.qty.setValue(self.bike["quantity"])

        btns = QHBoxLayout()
        btns.setSpacing(8)
        save = QPushButton("Save" if self.bike else "Add Bike")
        save.setObjectName("primary_btn")
        cancel = QPushButton("Cancel")
        cancel.setObjectName("secondary_btn")
        save.clicked.connect(self._save)
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        lay.addLayout(btns)

    def _save(self):
        if not self.brand.text().strip() or not self.model.text().strip():
            QMessageBox.warning(self, "Validation", "Brand and Model are required.")
            return
        self.accept()

    def get_data(self):
        return {
            "brand":      self.brand.text().strip(),
            "model":      self.model.text().strip(),
            "color":      self.color.text().strip(),
            "sale_price": self.price.value(),
            "quantity":   self.qty.value(),
            "date_added": today_str(),
        }


class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("Add Customer" if customer is None else "Edit Customer")
        self.setMinimumWidth(420)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Add New Customer" if self.customer is None else "Edit Customer")
        title.setObjectName("section_header")
        lay.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name    = QLineEdit()
        self.phone   = QLineEdit()
        self.cnic    = QLineEdit()
        self.address = QTextEdit()
        self.address.setMaximumHeight(80)

        form.addRow("Full Name:", self.name)
        form.addRow("Phone:",     self.phone)
        form.addRow("CNIC:",      self.cnic)
        form.addRow("Address:",   self.address)
        lay.addLayout(form)

        if self.customer:
            self.name.setText(self.customer["name"])
            self.phone.setText(self.customer["phone"])
            self.cnic.setText(self.customer["cnic"])
            self.address.setPlainText(self.customer["address"])

        btns = QHBoxLayout()
        btns.setSpacing(8)
        save = QPushButton("Save" if self.customer else "Add Customer")
        save.setObjectName("primary_btn")
        cancel = QPushButton("Cancel")
        cancel.setObjectName("secondary_btn")
        save.clicked.connect(self._save)
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        lay.addLayout(btns)

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Validation", "Customer name is required.")
            return
        self.accept()

    def get_data(self):
        return {
            "name":       self.name.text().strip(),
            "phone":      self.phone.text().strip(),
            "cnic":       self.cnic.text().strip(),
            "address":    self.address.toPlainText().strip(),
            "date_added": today_str(),
        }


# ─────────────────────────────────────────────────────────────────
# DASHBOARD PAGE
# ─────────────────────────────────────────────────────────────────

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(page_header("Dashboard", "Showroom overview and recent activity"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(28, 12, 28, 28)
        inner_lay.setSpacing(20)

        # KPI Row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)
        self.kpi_available = self._kpi_card("🔋", "0", "AVAILABLE BIKES")
        self.kpi_sold      = self._kpi_card("✅", "0", "TOTAL SOLD")
        self.kpi_revenue   = self._kpi_card("💰", "PKR 0", "TOTAL REVENUE")
        self.kpi_pending   = self._kpi_card("⏳", "PKR 0", "PENDING AMOUNT")
        kpi_row.addWidget(self.kpi_available)
        kpi_row.addWidget(self.kpi_sold)
        kpi_row.addWidget(self.kpi_revenue)
        kpi_row.addWidget(self.kpi_pending)
        inner_lay.addLayout(kpi_row)

        # Recent Transactions
        lbl = QLabel("Recent Transactions")
        lbl.setObjectName("section_header")
        inner_lay.addWidget(lbl)

        self.recent_table = make_table_widget(
            ["Sale ID", "CNIC", "Customer", "Bike", "Sale Price", "Amount Paid", "Pending", "Date"]
        )
        self.recent_table.setMinimumHeight(300)
        inner_lay.addWidget(self.recent_table)

        scroll.setWidget(inner)
        lay.addWidget(scroll)

    def _kpi_card(self, icon, value, label):
        card = QFrame()
        card.setObjectName("kpi_card")
        card_lay = QVBoxLayout(card)
        card_lay.setSpacing(6)
        ico = QLabel(icon)
        ico.setObjectName("kpi_icon")
        val = QLabel(value)
        val.setObjectName("kpi_value")
        lbl = QLabel(label)
        lbl.setObjectName("kpi_label")
        card_lay.addWidget(ico)
        card_lay.addWidget(val)
        card_lay.addWidget(lbl)
        card._val_label = val
        return card

    def refresh(self):
        conn = get_connection()
        cur = conn.cursor()

        avail = cur.execute("SELECT COALESCE(SUM(quantity),0) FROM bikes").fetchone()[0]
        sold  = cur.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        rev   = cur.execute("SELECT COALESCE(SUM(amount_paid),0) FROM sales").fetchone()[0]
        pend  = cur.execute("SELECT COALESCE(SUM(pending_amount),0) FROM sales").fetchone()[0]

        self.kpi_available._val_label.setText(str(avail))
        self.kpi_sold._val_label.setText(str(sold))
        self.kpi_revenue._val_label.setText(fmt_currency(rev))
        self.kpi_pending._val_label.setText(fmt_currency(pend))

        rows = cur.execute("""
            SELECT s.id, c.cnic, c.name, b.brand||' '||b.model,
                   s.sale_price, s.amount_paid, s.pending_amount, s.sale_date
            FROM sales s
            JOIN customers c ON c.id = s.customer_id
            JOIN bikes     b ON b.id = s.bike_id
            ORDER BY s.id DESC LIMIT 20
        """).fetchall()
        conn.close()

        self.recent_table.setSortingEnabled(False)
        self.recent_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            set_item(self.recent_table, r, 0, row[0], Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            set_item(self.recent_table, r, 1, row[1])
            set_item(self.recent_table, r, 2, row[2])
            set_item(self.recent_table, r, 3, row[3])
            set_item(self.recent_table, r, 4, fmt_currency(row[4]))
            set_item(self.recent_table, r, 5, fmt_currency(row[5]))
            pend_item = QTableWidgetItem(fmt_currency(row[6]))
            pend_item.setForeground(QColor("#f85149") if row[6] > 0 else QColor("#3fb950"))
            self.recent_table.setItem(r, 6, pend_item)
            set_item(self.recent_table, r, 7, row[7])
        self.recent_table.setSortingEnabled(True)


# ─────────────────────────────────────────────────────────────────
# INVENTORY PAGE
# ─────────────────────────────────────────────────────────────────

class InventoryPage(QWidget):
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(page_header("Inventory", "Manage your electric bike stock"))

        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(28, 12, 28, 28)
        content_lay.setSpacing(14)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search by brand, model or color...")
        self.search.textChanged.connect(self._filter)
        self.search.setMinimumWidth(280)

        add_btn = QPushButton("＋  Add Bike")
        add_btn.setObjectName("primary_btn")
        add_btn.clicked.connect(self._add)

        edit_btn = QPushButton("✏  Edit")
        edit_btn.setObjectName("secondary_btn")
        edit_btn.clicked.connect(self._edit)

        del_btn = QPushButton("🗑  Delete")
        del_btn.setObjectName("danger_btn")
        del_btn.clicked.connect(self._delete)

        toolbar.addWidget(self.search)
        toolbar.addStretch()
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(del_btn)
        toolbar.addWidget(add_btn)
        content_lay.addLayout(toolbar)

        self.table = make_table_widget(
            ["ID", "Brand", "Model", "Color", "Sale Price", "Quantity", "Date Added"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        content_lay.addWidget(self.table)

        lay.addWidget(content)

    def refresh(self):
        conn = get_connection()
        rows = conn.execute("SELECT * FROM bikes ORDER BY id DESC").fetchall()
        conn.close()
        self._populate(rows)

    def _populate(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            set_item(self.table, r, 0, row["id"], Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            set_item(self.table, r, 1, row["brand"])
            set_item(self.table, r, 2, row["model"])
            set_item(self.table, r, 3, row["color"])
            set_item(self.table, r, 4, fmt_currency(row["sale_price"]))
            qty_item = QTableWidgetItem(str(row["quantity"]))
            qty_item.setForeground(QColor("#3fb950") if row["quantity"] > 0 else QColor("#f85149"))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, 5, qty_item)
            set_item(self.table, r, 6, row["date_added"])
        self.table.setSortingEnabled(True)

    def _filter(self, text):
        text = text.lower()
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM bikes WHERE lower(brand) LIKE ? OR lower(model) LIKE ? OR lower(color) LIKE ?",
            (f"%{text}%", f"%{text}%", f"%{text}%")
        ).fetchall()
        conn.close()
        self._populate(rows)

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select a row first.")
            return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _add(self):
        dlg = BikeDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            conn = get_connection()
            conn.execute(
                "INSERT INTO bikes (brand,model,color,sale_price,quantity,date_added) VALUES (?,?,?,?,?,?)",
                (d["brand"], d["model"], d["color"], d["sale_price"], d["quantity"], d["date_added"])
            )
            conn.commit(); conn.close()
            self.refresh()
            self.changed.emit()

    def _edit(self):
        bid = self._selected_id()
        if bid is None: return
        conn = get_connection()
        bike = conn.execute("SELECT * FROM bikes WHERE id=?", (bid,)).fetchone()
        conn.close()
        dlg = BikeDialog(self, bike)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            conn = get_connection()
            conn.execute(
                "UPDATE bikes SET brand=?,model=?,color=?,sale_price=?,quantity=? WHERE id=?",
                (d["brand"], d["model"], d["color"], d["sale_price"], d["quantity"], bid)
            )
            conn.commit(); conn.close()
            self.refresh()
            self.changed.emit()

    def _delete(self):
        bid = self._selected_id()
        if bid is None: return
        if QMessageBox.question(self, "Confirm", "Delete this bike?") == QMessageBox.StandardButton.Yes:
            conn = get_connection()
            conn.execute("DELETE FROM bikes WHERE id=?", (bid,))
            conn.commit(); conn.close()
            self.refresh()
            self.changed.emit()


# ─────────────────────────────────────────────────────────────────
# CUSTOMERS PAGE
# ─────────────────────────────────────────────────────────────────
class CustomersPage(QWidget):
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._bike_data = []
        self._customer_ids = []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(page_header("Customers", "Manage customer records and their purchases"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(28, 12, 28, 28)
        inner_lay.setSpacing(20)

        # ── Customer Info Form ──
        cust_frame = QFrame()
        cust_frame.setObjectName("kpi_card")
        cust_outer = QVBoxLayout(cust_frame)
        cust_outer.setSpacing(12)

        hdr = QLabel("Customer Details")
        hdr.setObjectName("section_header")
        cust_outer.addWidget(hdr)

        cust_form = QGridLayout()
        cust_form.setSpacing(10)
        cust_form.setColumnStretch(1, 1)
        cust_form.setColumnStretch(3, 1)

        cust_form.addWidget(QLabel("Name:"), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Full name")
        cust_form.addWidget(self.name_edit, 0, 1)

        cust_form.addWidget(QLabel("Phone:"), 0, 2)
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("03xx-xxxxxxx")
        cust_form.addWidget(self.phone_edit, 0, 3)

        cust_form.addWidget(QLabel("CNIC:"), 1, 0)
        self.cnic_edit = QLineEdit()
        self.cnic_edit.setPlaceholderText("xxxxx-xxxxxxx-x")
        cust_form.addWidget(self.cnic_edit, 1, 1)

        cust_form.addWidget(QLabel("Address:"), 1, 2)
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Full address")
        cust_form.addWidget(self.address_edit, 1, 3)

        cust_outer.addLayout(cust_form)
        inner_lay.addWidget(cust_frame)

        # ── Purchase / Sale Form ──
        sale_frame = QFrame()
        sale_frame.setObjectName("kpi_card")
        sale_outer = QVBoxLayout(sale_frame)
        sale_outer.setSpacing(12)

        sale_hdr = QLabel("Bike Purchase")
        sale_hdr.setObjectName("section_header")
        sale_outer.addWidget(sale_hdr)

        sale_form = QGridLayout()
        sale_form.setSpacing(10)
        sale_form.setColumnStretch(1, 1)
        sale_form.setColumnStretch(3, 1)

        sale_form.addWidget(QLabel("Bike:"), 0, 0)
        self.bike_cb = QComboBox()
        self.bike_cb.setMinimumWidth(240)
        self.bike_cb.currentIndexChanged.connect(self._on_bike_changed)
        sale_form.addWidget(self.bike_cb, 0, 1)

        sale_form.addWidget(QLabel("Sale Price:"), 0, 2)
        self.sale_price_spin = QDoubleSpinBox()
        self.sale_price_spin.setRange(0, 10_000_000)
        self.sale_price_spin.setPrefix("PKR ")
        self.sale_price_spin.setSingleStep(1000)
        self.sale_price_spin.valueChanged.connect(self._recalc)
        sale_form.addWidget(self.sale_price_spin, 0, 3)

        sale_form.addWidget(QLabel("Amount Paid:"), 1, 0)
        self.amount_paid_spin = QDoubleSpinBox()
        self.amount_paid_spin.setRange(0, 10_000_000)
        self.amount_paid_spin.setPrefix("PKR ")
        self.amount_paid_spin.setSingleStep(1000)
        self.amount_paid_spin.valueChanged.connect(self._recalc)
        sale_form.addWidget(self.amount_paid_spin, 1, 1)

        sale_form.addWidget(QLabel("Pending Amount:"), 1, 2)
        self.pending_label = QLabel("PKR 0")
        self.pending_label.setObjectName("kpi_value")
        self.pending_label.setStyleSheet("color: #e3b341; font-size: 16px;")
        sale_form.addWidget(self.pending_label, 1, 3)

        sale_form.addWidget(QLabel("Sale Date:"), 2, 0)
        self.sale_date = QDateEdit()
        self.sale_date.setDate(QDate.currentDate())
        self.sale_date.setCalendarPopup(True)
        sale_form.addWidget(self.sale_date, 2, 1)

        sale_form.addWidget(QLabel("VIN / Chassis No:"), 3, 0)
        self.vin_edit = QLineEdit()
        self.vin_edit.setPlaceholderText("e.g. EVEE2025XYZ001234")
        sale_form.addWidget(self.vin_edit, 3, 1)

        sale_form.addWidget(QLabel("Battery Serial No:"), 3, 2)
        self.battery_edit = QLineEdit()
        self.battery_edit.setPlaceholderText("e.g. BAT-2025-987654")
        sale_form.addWidget(self.battery_edit, 3, 3)

        sale_outer.addLayout(sale_form)

        save_btn = QPushButton("💾  Save Customer & Sale")
        save_btn.setObjectName("success_btn")
        save_btn.setMinimumHeight(42)
        save_btn.clicked.connect(self._save)
        sale_outer.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

        inner_lay.addWidget(sale_frame)

        # ── Customer Records Table ──
        lbl = QLabel("Customer Records")
        lbl.setObjectName("section_header")
        inner_lay.addWidget(lbl)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search by name, phone or CNIC...")
        self.search.textChanged.connect(self._filter)
        self.search.setMinimumWidth(280)

        edit_btn = QPushButton("✏  Edit Customer")
        edit_btn.setObjectName("secondary_btn")
        edit_btn.clicked.connect(self._edit_customer)

        del_btn = QPushButton("🗑  Delete")
        del_btn.setObjectName("danger_btn")
        del_btn.clicked.connect(self._delete_customer)

        pay_btn = QPushButton("💳  Update Payment")
        pay_btn.setObjectName("success_btn")
        pay_btn.clicked.connect(self._update_payment)

        toolbar.addWidget(self.search)
        toolbar.addStretch()
        toolbar.addWidget(pay_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(del_btn)
        inner_lay.addLayout(toolbar)

        self.table = make_table_widget([
            "Sale ID", "Name", "Phone", "CNIC", "Address",
            "Bike", "Sale Price", "Paid", "Pending", "Date Added"
        ])
        self.table.setMinimumHeight(280)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        inner_lay.addWidget(self.table)

        scroll.setWidget(inner)
        lay.addWidget(scroll)

    def refresh(self):
        self._load_bikes()
        self._load_table()
        self.sale_date.setDate(QDate.currentDate())

    def _load_bikes(self):
        conn = get_connection()
        bikes = conn.execute(
            "SELECT id, brand, model, sale_price, quantity FROM bikes WHERE quantity>0 ORDER BY brand"
        ).fetchall()
        conn.close()
        self.bike_cb.clear()
        self._bike_data = []
        for b in bikes:
            self.bike_cb.addItem(f"{b['brand']} {b['model']} — {fmt_currency(b['sale_price'])}")
            self._bike_data.append({"id": b["id"], "price": b["sale_price"]})
        self._on_bike_changed()

    def _on_bike_changed(self):
        idx = self.bike_cb.currentIndex()
        if 0 <= idx < len(self._bike_data):
            self.sale_price_spin.setValue(self._bike_data[idx]["price"])

    def _recalc(self):
        pending = max(0.0, self.sale_price_spin.value() - self.amount_paid_spin.value())
        self.pending_label.setText(fmt_currency(pending))
        if pending == 0:
            color = "#3fb950"
        elif pending < self.sale_price_spin.value():
            color = "#e3b341"
        else:
            color = "#f85149"
        self.pending_label.setStyleSheet(f"color: {color}; font-size: 16px;")

    def _save(self):
        name    = self.name_edit.text().strip()
        phone   = self.phone_edit.text().strip()
        cnic    = self.cnic_edit.text().strip()
        address = self.address_edit.text().strip()

        if not name or not phone:
            QMessageBox.warning(self, "Validation", "Name and Phone are required.")
            return
        if not self._bike_data:
            QMessageBox.warning(self, "Error", "No bikes available.")
            return

        b_idx = self.bike_cb.currentIndex()
        if b_idx < 0:
            QMessageBox.warning(self, "Error", "Please select a bike.")
            return

        bid = self._bike_data[b_idx]["id"]
        sale_price = self.sale_price_spin.value()
        paid = self.amount_paid_spin.value()
        pending = max(0.0, sale_price - paid)
        sdate = self.sale_date.date().toString("yyyy-MM-dd")
        vin = self.vin_edit.text().strip()
        battery = self.battery_edit.text().strip()

        if paid > sale_price:
            QMessageBox.warning(self, "Error", "Amount paid cannot exceed sale price.")
            return

        conn = get_connection()
        cursor = conn.execute(
            "INSERT INTO customers (name, phone, cnic, address, date_added) VALUES (?,?,?,?,?)",
            (name, phone, cnic, address, sdate)
        )
        cid = cursor.lastrowid
        conn.execute(
            "INSERT INTO sales (customer_id, bike_id, sale_price, amount_paid, pending_amount, sale_date, vin_number, battery_serial) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (cid, bid, sale_price, paid, pending, sdate, vin, battery)
        )
        conn.execute("UPDATE bikes SET quantity = quantity - 1 WHERE id=? AND quantity>0", (bid,))
        conn.commit()
        conn.close()

        # Clear form
        self.name_edit.clear()
        self.phone_edit.clear()
        self.cnic_edit.clear()
        self.address_edit.clear()
        self.amount_paid_spin.setValue(0)
        self.sale_date.setDate(QDate.currentDate())
        self.vin_edit.clear()
        self.battery_edit.clear()

        self.refresh()
        self.changed.emit()
        QMessageBox.information(self, "Success", "Customer and sale saved successfully!")

    def _load_table(self):
        conn = get_connection()
        rows = conn.execute("""
            SELECT s.id, c.name, c.phone, c.cnic, c.address,
                   b.brand||' '||b.model,
                   s.sale_price, s.amount_paid, s.pending_amount, c.date_added
            FROM customers c
            JOIN sales s ON s.customer_id = c.id
            JOIN bikes  b ON b.id = s.bike_id
            ORDER BY s.id DESC
        """).fetchall()
        conn.close()

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            set_item(self.table, r, 0, row[0], Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            set_item(self.table, r, 1, row[1])
            set_item(self.table, r, 2, row[2])
            set_item(self.table, r, 3, row[3])
            set_item(self.table, r, 4, row[4])
            set_item(self.table, r, 5, row[5])
            set_item(self.table, r, 6, fmt_currency(row[6]))
            set_item(self.table, r, 7, fmt_currency(row[7]))
            pend_item = QTableWidgetItem(fmt_currency(row[8]))
            pend_item.setForeground(QColor("#f85149") if row[8] > 0 else QColor("#3fb950"))
            self.table.setItem(r, 8, pend_item)
            set_item(self.table, r, 9, row[9])
        self.table.setSortingEnabled(True)

    def _filter(self, text):
        text = text.lower()
        conn = get_connection()
        rows = conn.execute("""
            SELECT s.id, c.name, c.phone, c.cnic, c.address,
                   b.brand||' '||b.model,
                   s.sale_price, s.amount_paid, s.pending_amount, c.date_added
            FROM customers c
            JOIN sales s ON s.customer_id = c.id
            JOIN bikes  b ON b.id = s.bike_id
            WHERE lower(c.name) LIKE ? OR lower(c.phone) LIKE ? OR lower(c.cnic) LIKE ?
            ORDER BY s.id DESC
        """, (f"%{text}%", f"%{text}%", f"%{text}%")).fetchall()
        conn.close()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            set_item(self.table, r, 0, row[0], Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            set_item(self.table, r, 1, row[1])
            set_item(self.table, r, 2, row[2])
            set_item(self.table, r, 3, row[3])
            set_item(self.table, r, 4, row[4])
            set_item(self.table, r, 5, row[5])
            set_item(self.table, r, 6, fmt_currency(row[6]))
            set_item(self.table, r, 7, fmt_currency(row[7]))
            pend_item = QTableWidgetItem(fmt_currency(row[8]))
            pend_item.setForeground(QColor("#f85149") if row[8] > 0 else QColor("#3fb950"))
            self.table.setItem(r, 8, pend_item)
            set_item(self.table, r, 9, row[9])
        self.table.setSortingEnabled(True)

    def _selected_sale_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select a row first.")
            return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _edit_customer(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select a row first.")
            return
        sale_id = int(self.table.item(row, 0).text())

        conn = get_connection()
        sale = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
        cust = conn.execute("SELECT * FROM customers WHERE id=?", (sale["customer_id"],)).fetchone()
        conn.close()

        dlg = QDialog(self)
        dlg.setWindowTitle("Edit Customer")
        dlg.setMinimumWidth(420)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)

        title = QLabel("Edit Customer Details")
        title.setObjectName("section_header")
        lay.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        name_e    = QLineEdit(cust["name"])
        phone_e   = QLineEdit(cust["phone"])
        cnic_e    = QLineEdit(cust["cnic"])
        address_e = QLineEdit(cust["address"])

        form.addRow("Name:",    name_e)
        form.addRow("Phone:",   phone_e)
        form.addRow("CNIC:",    cnic_e)
        form.addRow("Address:", address_e)
        lay.addLayout(form)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        save_btn   = QPushButton("Save")
        save_btn.setObjectName("primary_btn")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary_btn")
        save_btn.clicked.connect(dlg.accept)
        cancel_btn.clicked.connect(dlg.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        lay.addLayout(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            conn = get_connection()
            conn.execute(
                "UPDATE customers SET name=?, phone=?, cnic=?, address=? WHERE id=?",
                (name_e.text().strip(), phone_e.text().strip(),
                 cnic_e.text().strip(), address_e.text().strip(), cust["id"])
            )
            conn.commit()
            conn.close()
            self.refresh()
            self.changed.emit()

    def _delete_customer(self):
        sid = self._selected_sale_id()
        if sid is None:
            return
        conn = get_connection()
        sale = conn.execute("SELECT customer_id FROM sales WHERE id=?", (sid,)).fetchone()
        conn.close()
        if sale is None:
            return
        if QMessageBox.question(
            self, "Confirm Delete",
            "Delete this customer and all their sales? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            conn = get_connection()
            conn.execute("DELETE FROM sales WHERE customer_id=?", (sale["customer_id"],))
            conn.execute("DELETE FROM customers WHERE id=?", (sale["customer_id"],))
            conn.commit()
            conn.close()
            self.refresh()
            self.changed.emit()

    def _update_payment(self):
        sid = self._selected_sale_id()
        if sid is None:
            return
        conn = get_connection()
        sale = conn.execute("SELECT * FROM sales WHERE id=?", (sid,)).fetchone()
        conn.close()
        if sale is None:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Update Payment")
        dlg.setMinimumWidth(380)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)

        title = QLabel("Update Customer Payment")
        title.setObjectName("section_header")
        lay.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        sale_price_lbl = QLabel(fmt_currency(sale["sale_price"]))
        sale_price_lbl.setStyleSheet("color: #58a6ff; font-weight: bold;")
        form.addRow("Sale Price:", sale_price_lbl)

        paid_lbl = QLabel(fmt_currency(sale["amount_paid"]))
        paid_lbl.setStyleSheet("color: #3fb950; font-weight: bold;")
        form.addRow("Already Paid:", paid_lbl)

        pend_lbl = QLabel(fmt_currency(sale["pending_amount"]))
        pend_lbl.setStyleSheet("color: #f85149; font-weight: bold;")
        form.addRow("Current Pending:", pend_lbl)

        new_pay = QDoubleSpinBox()
        new_pay.setRange(0, sale["pending_amount"])
        new_pay.setPrefix("PKR ")
        new_pay.setSingleStep(1000)
        new_pay.setValue(sale["pending_amount"])
        form.addRow("New Payment:", new_pay)
        lay.addLayout(form)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        ok_btn     = QPushButton("Update")
        ok_btn.setObjectName("success_btn")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary_btn")
        ok_btn.clicked.connect(dlg.accept)
        cancel_btn.clicked.connect(dlg.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(ok_btn)
        lay.addLayout(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            payment     = new_pay.value()
            new_paid    = sale["amount_paid"] + payment
            new_pending = max(0.0, sale["sale_price"] - new_paid)
            conn = get_connection()
            conn.execute(
                "UPDATE sales SET amount_paid=?, pending_amount=? WHERE id=?",
                (new_paid, new_pending, sid)
            )
            conn.commit()
            conn.close()
            self.refresh()
            self.changed.emit()
            msg = "Payment fully cleared! ✅" if new_pending == 0 else \
                  f"Payment updated. Remaining: {fmt_currency(new_pending)}"
            QMessageBox.information(self, "Updated", msg)

# ─────────────────────────────────────────────────────────────────
# REPORTS PAGE
# ─────────────────────────────────────────────────────────────────

class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(page_header("Reports", "Daily sales summary and export"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(28, 12, 28, 28)
        inner_lay.setSpacing(20)

        # Filter bar
        filter_frame = QFrame()
        filter_frame.setObjectName("kpi_card")
        filter_lay = QHBoxLayout(filter_frame)
        filter_lay.setSpacing(10)

        filter_lay.addWidget(QLabel("Date Filter:"))

        today_btn = QPushButton("Today")
        today_btn.setObjectName("secondary_btn")
        today_btn.clicked.connect(self._filter_today)

        yest_btn = QPushButton("Yesterday")
        yest_btn.setObjectName("secondary_btn")
        yest_btn.clicked.connect(self._filter_yesterday)

        filter_lay.addWidget(today_btn)
        filter_lay.addWidget(yest_btn)

        filter_lay.addWidget(QLabel("  From:"))
        self.from_date = QDateEdit(QDate.currentDate())
        self.from_date.setCalendarPopup(True)
        filter_lay.addWidget(self.from_date)

        filter_lay.addWidget(QLabel("To:"))
        self.to_date = QDateEdit(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        filter_lay.addWidget(self.to_date)

        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("primary_btn")
        apply_btn.clicked.connect(self._apply_filter)
        filter_lay.addWidget(apply_btn)
        filter_lay.addStretch()

        inner_lay.addWidget(filter_frame)

        # Summary KPIs
        self.sum_row = QHBoxLayout()
        self.sum_row.setSpacing(14)
        self.sum_sales  = self._mini_kpi("Total Sales",   "0")
        self.sum_rev    = self._mini_kpi("Revenue",       "PKR 0")
        self.sum_paid   = self._mini_kpi("Collected",     "PKR 0")
        self.sum_pend   = self._mini_kpi("Pending",       "PKR 0")
        self.sum_row.addWidget(self.sum_sales)
        self.sum_row.addWidget(self.sum_rev)
        self.sum_row.addWidget(self.sum_paid)
        self.sum_row.addWidget(self.sum_pend)
        inner_lay.addLayout(self.sum_row)

        # Export buttons
        exp_row = QHBoxLayout()
        exp_row.setSpacing(10)
        pdf_btn = QPushButton("📄  Export PDF")
        pdf_btn.setObjectName("export_btn")
        pdf_btn.clicked.connect(self._export_pdf)
        xl_btn = QPushButton("📊  Export Excel")
        xl_btn.setObjectName("success_btn")
        xl_btn.clicked.connect(self._export_excel)
        exp_row.addStretch()
        exp_row.addWidget(pdf_btn)
        exp_row.addWidget(xl_btn)
        inner_lay.addLayout(exp_row)

        # Table
        lbl = QLabel("Sales Details")
        lbl.setObjectName("section_header")
        inner_lay.addWidget(lbl)

        self.table = make_table_widget(
            ["Sale ID", "Customer", "Phone", "CNIC", "Bike", "Sale Price", "Paid", "Pending", "Date"]
        )
        self.table.setMinimumHeight(280)
        inner_lay.addWidget(self.table)

        scroll.setWidget(inner)
        lay.addWidget(scroll)

        self._apply_filter()

    def _mini_kpi(self, label, value):
        card = QFrame()
        card.setObjectName("kpi_card")
        card_lay = QVBoxLayout(card)
        card_lay.setSpacing(4)
        lbl = QLabel(label.upper())
        lbl.setObjectName("kpi_label")
        val = QLabel(value)
        val.setObjectName("kpi_value")
        val.setStyleSheet("font-size: 20px;")
        card_lay.addWidget(lbl)
        card_lay.addWidget(val)
        card._val = val
        return card

    def _filter_today(self):
        t = QDate.currentDate()
        self.from_date.setDate(t)
        self.to_date.setDate(t)
        self._apply_filter()

    def _filter_yesterday(self):
        y = QDate.currentDate().addDays(-1)
        self.from_date.setDate(y)
        self.to_date.setDate(y)
        self._apply_filter()

    def _apply_filter(self):
        fd = self.from_date.date().toString("yyyy-MM-dd")
        td = self.to_date.date().toString("yyyy-MM-dd")
        conn = get_connection()
        rows = conn.execute("""
                    SELECT s.id, c.name, c.phone, c.cnic, b.brand||' '||b.model,
                           s.sale_price, s.amount_paid, s.pending_amount, s.sale_date
                    FROM sales s
                    JOIN customers c ON c.id = s.customer_id
                    JOIN bikes     b ON b.id = s.bike_id
                    WHERE s.sale_date >= ? AND s.sale_date <= ?
                    ORDER BY s.id DESC
                """, (fd, td)).fetchall()
        conn.close()

        total_rev = sum(r[5] for r in rows)
        total_paid = sum(r[6] for r in rows)
        total_pend = sum(r[7] for r in rows)

        self.sum_sales._val.setText(str(len(rows)))
        self.sum_rev._val.setText(fmt_currency(total_rev))
        self.sum_paid._val.setText(fmt_currency(total_paid))
        self.sum_pend._val.setText(fmt_currency(total_pend))

        self._current_rows = rows
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            set_item(self.table, r, 0, row[0], Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            set_item(self.table, r, 1, row[1])
            set_item(self.table, r, 2, row[2])
            set_item(self.table, r, 3, row[3])
            set_item(self.table, r, 4, row[4])
            set_item(self.table, r, 5, fmt_currency(row[5]))
            set_item(self.table, r, 6, fmt_currency(row[6]))
            pend_item = QTableWidgetItem(fmt_currency(row[7]))
            pend_item.setForeground(QColor("#f85149") if row[7] > 0 else QColor("#3fb950"))
            self.table.setItem(r, 7, pend_item)
            set_item(self.table, r, 8, row[8])
        self.table.setSortingEnabled(True)

    def refresh(self):
        self._apply_filter()

    def _export_pdf(self):
        if not hasattr(self, "_current_rows") or not self._current_rows:
            QMessageBox.information(self, "No Data", "No data to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "report.pdf", "PDF Files (*.pdf)")
        if not path: return
        try:
            _export_report_pdf(
                path,
                self._current_rows,
                self.from_date.date().toString("yyyy-MM-dd"),
                self.to_date.date().toString("yyyy-MM-dd")
            )
            QMessageBox.information(self, "Exported", f"PDF saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _export_excel(self):
        if not hasattr(self, "_current_rows") or not self._current_rows:
            QMessageBox.information(self, "No Data", "No data to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Excel", "report.xlsx", "Excel Files (*.xlsx)")
        if not path: return
        try:
            _export_report_excel(path, self._current_rows)
            QMessageBox.information(self, "Exported", f"Excel saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ─────────────────────────────────────────────────────────────────
# RECEIPTS PAGE
# ─────────────────────────────────────────────────────────────────

class ReceiptsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._sale_data = None
        self._last_pdf_path = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(page_header("Receipts", "Generate, print and share professional invoices"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(28, 12, 28, 28)
        inner_lay.setSpacing(20)

        # ── Selector bar ──
        sel_frame = QFrame()
        sel_frame.setObjectName("kpi_card")
        sel_lay = QHBoxLayout(sel_frame)
        sel_lay.setSpacing(10)
        sel_lay.addWidget(QLabel("Sale ID:"))
        self.sale_combo = QComboBox()
        self.sale_combo.setMinimumWidth(360)
        sel_lay.addWidget(self.sale_combo)
        load_btn = QPushButton("📋  Load Receipt")
        load_btn.setObjectName("primary_btn")
        load_btn.clicked.connect(self._load_receipt)
        sel_lay.addWidget(load_btn)
        sel_lay.addStretch()
        inner_lay.addWidget(sel_frame)

        # ── Receipt preview ──
        self.receipt_box = QTextEdit()
        self.receipt_box.setObjectName("receipt_box")
        self.receipt_box.setReadOnly(True)
        self.receipt_box.setMinimumHeight(420)
        self.receipt_box.setFont(QFont("Courier New", 12))
        inner_lay.addWidget(self.receipt_box)

        # ── Action buttons ──
        btn_frame = QFrame()
        btn_frame.setObjectName("kpi_card")
        btn_outer = QVBoxLayout(btn_frame)
        btn_outer.setSpacing(10)

        btn_title = QLabel("Actions")
        btn_title.setObjectName("section_header")
        btn_outer.addWidget(btn_title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        save_pdf_btn = QPushButton("📄  Save as PDF")
        save_pdf_btn.setObjectName("export_btn")
        save_pdf_btn.setMinimumHeight(40)
        save_pdf_btn.setToolTip("Save receipt as PDF file to your computer")
        save_pdf_btn.clicked.connect(self._save_pdf)

        print_btn = QPushButton("🖨  Print Receipt")
        print_btn.setObjectName("primary_btn")
        print_btn.setMinimumHeight(40)
        print_btn.setToolTip("Send receipt directly to your printer")
        print_btn.clicked.connect(self._print_receipt)

        open_btn = QPushButton("👁  Open PDF")
        open_btn.setObjectName("secondary_btn")
        open_btn.setMinimumHeight(40)
        open_btn.setToolTip("Open the saved PDF in your default viewer")
        open_btn.clicked.connect(self._open_pdf)

        share_btn = QPushButton("📤  Share PDF")
        share_btn.setObjectName("success_btn")
        share_btn.setMinimumHeight(40)
        share_btn.setToolTip("Open the PDF folder so you can attach it to WhatsApp, Email etc.")
        share_btn.clicked.connect(self._share_pdf)

        btn_row.addWidget(save_pdf_btn)
        btn_row.addWidget(print_btn)
        btn_row.addWidget(open_btn)
        btn_row.addWidget(share_btn)
        btn_outer.addLayout(btn_row)

        self.status_lbl = QLabel("💡  Load a receipt first, then use the buttons above.")
        self.status_lbl.setStyleSheet("color: #8b949e; font-size: 11px; padding: 4px 0px;")
        btn_outer.addWidget(self.status_lbl)

        inner_lay.addWidget(btn_frame)
        scroll.setWidget(inner)
        lay.addWidget(scroll)

    def refresh(self):
        conn = get_connection()
        rows = conn.execute("""
            SELECT s.id, c.name, b.brand||' '||b.model, s.sale_date
            FROM sales s
            JOIN customers c ON c.id = s.customer_id
            JOIN bikes     b ON b.id = s.bike_id
            ORDER BY s.id DESC
        """).fetchall()
        conn.close()
        self.sale_combo.clear()
        self._sale_ids = []
        for row in rows:
            self.sale_combo.addItem(
                f"#{row[0]}  |  {row[1]}  |  {row[2]}  |  {row[3]}"
            )
            self._sale_ids.append(row[0])

    def _load_receipt(self):
        idx = self.sale_combo.currentIndex()
        if idx < 0 or not self._sale_ids:
            QMessageBox.information(self, "Select", "No sale selected.")
            return
        sid = self._sale_ids[idx]
        conn = get_connection()
        row = conn.execute("""
                SELECT s.id, c.name, c.phone, c.cnic, c.address,
                       b.brand, b.model, b.color,
                       s.sale_price, s.amount_paid, s.pending_amount, s.sale_date,
                       s.vin_number, s.battery_serial
                FROM sales s
                JOIN customers c ON c.id = s.customer_id
                JOIN bikes     b ON b.id = s.bike_id
                WHERE s.id = ?
            """, (sid,)).fetchone()
        conn.close()
        if row:
            self._sale_data = dict(row)
            self._last_pdf_path = None
            self.receipt_box.setPlainText(_build_receipt_text(self._sale_data))
            self.status_lbl.setText(
                f"✅  Receipt #{sid} loaded — {self._sale_data['name']}. "
                f"Use buttons below to Save, Print or Share."
            )
            self.status_lbl.setStyleSheet(
                "color: #3fb950; font-size: 11px; padding: 4px 0px;"
            )

    def _get_default_pdf_path(self):
        folder = os.path.dirname(os.path.abspath(DB_PATH))
        name = self._sale_data["name"].replace(" ", "_")
        filename = f"Receipt_{self._sale_data['id']:05d}_{name}.pdf"
        return os.path.join(folder, filename)

    def _save_pdf(self):
        if not self._sale_data:
            QMessageBox.information(self, "No Data", "Load a receipt first.")
            return
        default = self._get_default_pdf_path()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Receipt PDF", default, "PDF Files (*.pdf)"
        )
        if not path:
            return
        try:
            _export_receipt_pdf(path, self._sale_data)
            self._last_pdf_path = path
            self.status_lbl.setText(f"✅  PDF saved: {path}")
            self.status_lbl.setStyleSheet(
                "color: #3fb950; font-size: 11px; padding: 4px 0px;"
            )
            reply = QMessageBox.question(
                self, "PDF Saved",
                f"Receipt PDF saved successfully!\n\n{path}\n\nOpen it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._open_pdf()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _print_receipt(self):
        if not self._sale_data:
            QMessageBox.information(self, "No Data", "Load a receipt first.")
            return
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt6.QtGui import QTextDocument

            import tempfile
            tmp = tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False,
                prefix=f"receipt_{self._sale_data['id']}_"
            )
            tmp_path = tmp.name
            tmp.close()
            _export_receipt_pdf(tmp_path, self._sale_data)
            self._last_pdf_path = tmp_path

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageSize(
                __import__('PyQt6.QtGui', fromlist=['QPageSize']).QPageSize(
                    __import__('PyQt6.QtGui', fromlist=['QPageSize']).QPageSize.PageSizeId.A4
                )
            )
            dlg = QPrintDialog(printer, self)
            dlg.setWindowTitle("Print Receipt")
            if dlg.exec() == QPrintDialog.DialogCode.Accepted:
                doc = QTextDocument()
                doc.setPlainText(_build_receipt_text(self._sale_data))
                doc.print(printer)
                self.status_lbl.setText(
                    f"✅  Receipt #{self._sale_data['id']} sent to printer."
                )
                self.status_lbl.setStyleSheet(
                    "color: #3fb950; font-size: 11px; padding: 4px 0px;"
                )
        except ImportError:
            self._fallback_print()
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))

    def _fallback_print(self):
        import tempfile
        tmp = tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False,
            prefix=f"receipt_{self._sale_data['id']}_"
        )
        tmp_path = tmp.name
        tmp.close()
        try:
            _export_receipt_pdf(tmp_path, self._sale_data)
            self._last_pdf_path = tmp_path
            import subprocess
            if sys.platform == "win32":
                os.startfile(tmp_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", tmp_path])
            else:
                subprocess.Popen(["xdg-open", tmp_path])
            self.status_lbl.setText(
                "🖨  PDF opened in viewer — use File → Print from there."
            )
            self.status_lbl.setStyleSheet(
                "color: #e3b341; font-size: 11px; padding: 4px 0px;"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _open_pdf(self):
        if not self._sale_data:
            QMessageBox.information(self, "No Data", "Load a receipt first.")
            return
        if not self._last_pdf_path or not os.path.exists(self._last_pdf_path):
            import tempfile
            tmp = tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False,
                prefix=f"receipt_{self._sale_data['id']}_"
            )
            self._last_pdf_path = tmp.name
            tmp.close()
            try:
                _export_receipt_pdf(self._last_pdf_path, self._sale_data)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                return
        try:
            import subprocess
            if sys.platform == "win32":
                os.startfile(self._last_pdf_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", self._last_pdf_path])
            else:
                subprocess.Popen(["xdg-open", self._last_pdf_path])
            self.status_lbl.setText(f"👁  Opened: {self._last_pdf_path}")
            self.status_lbl.setStyleSheet(
                "color: #58a6ff; font-size: 11px; padding: 4px 0px;"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open PDF:\n{e}")

    def _share_pdf(self):
        if not self._sale_data:
            QMessageBox.information(self, "No Data", "Load a receipt first.")
            return

        folder = os.path.join(os.path.dirname(os.path.abspath(DB_PATH)), "receipts")
        os.makedirs(folder, exist_ok=True)
        cust = self._sale_data["name"].replace(" ", "_")
        filename = f"Receipt_{self._sale_data['id']:05d}_{cust}_{self._sale_data['sale_date']}.pdf"
        path = os.path.join(folder, filename)

        try:
            _export_receipt_pdf(path, self._sale_data)
            self._last_pdf_path = path
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        try:
            import subprocess
            if sys.platform == "win32":
                subprocess.Popen(f'explorer /select,"{path}"')
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", path])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception:
            pass

        QMessageBox.information(
            self, "Share Receipt",
            f"✅  Receipt PDF saved to:\n{path}\n\n"
            f"The folder has been opened.\n\n"
            f"📤  To share:\n"
            f"  • WhatsApp Desktop → attach this file\n"
            f"  • Email → attach this file\n"
            f"  • USB / Drive → copy from this folder"
        )


# ─────────────────────────────────────────────────────────────────
# RECEIPT TEXT BUILDER
# ─────────────────────────────────────────────────────────────────

def _build_receipt_text(d):
    name    = get_setting("shop_name",    "Shahzaib Motors")
    address = get_setting("shop_address", "Multan, Punjab, Pakistan")
    phone   = get_setting("shop_phone",   "0300-0000000")
    email   = get_setting("shop_email",   "shahzaibmotors@gmail.com")
    line    = "─" * 60
    line2   = "─" * 28
    status  = "FULLY PAID ✓" if d["pending_amount"] == 0 else f"PENDING: {fmt_currency(d['pending_amount'])}"
    vin     = d.get("vin_number", "N/A") or "N/A"
    battery = d.get("battery_serial", "N/A") or "N/A"
    return f"""
  {name}                         ELECTRIC BIKE
  {address}                       SALE RECEIPT
  Phone : {phone}
  Email : {email}
{line}
  Receipt #: {d['id']:05d}                    Date: {d['sale_date']}
{line}
  BUYER INFORMATION              BIKE INFORMATION
  {line2}     {line2}
  Name    : {d['name']:<22} Brand : {d['brand']}
  Phone   : {d['phone']:<22} Model : {d['model']}
  CNIC    : {d['cnic']:<22} Color : {d['color']}
  Address : {d['address']}
{line}
  VIN / Chassis No : {vin}
  Battery Serial   : {battery}
{line}
  Description                                        Amount
  {line}
  Electric Bike Sale
  {d['brand']} {d['model']} ({d['color']})           {fmt_currency(d['sale_price'])}
{line}
                                        Subtotal  {fmt_currency(d['sale_price'])}
                                        Discount  PKR 0
                                        Tax/VAT   PKR 0
                                           TOTAL  {fmt_currency(d['sale_price'])}
{line}
  Amount of {fmt_currency(d['amount_paid'])} was paid by {d['name']}, the customer
  on {d['sale_date']}.

  Payment Method:
  [✓] Cash    [ ] Credit Card    [ ] Other

  Status : {status}
{line}
  _______________________________
  Signature of Buyer

                  Thank you for your business!
                       {name}
{line}
"""

# ─────────────────────────────────────────────────────────────────
# PDF EXPORT (ReportLab)
# ─────────────────────────────────────────────────────────────────

def _export_receipt_pdf(path, d):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, HRFlowable, Image)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    shop_name    = get_setting("shop_name",    "Shahzaib Motors")
    shop_tagline = get_setting("shop_tagline", "Electric Bike Showroom & Service")
    shop_address = get_setting("shop_address", "Multan, Punjab, Pakistan")
    shop_phone   = get_setting("shop_phone",   "0300-0000000")
    shop_email   = get_setting("shop_email",   "shahzaibmotors@gmail.com")
    shop_website = get_setting("shop_website", "ShahzaibMotors.com")
    logo_path    = get_setting("logo_path",    "")

    vin     = d.get("vin_number",     "") or "N/A"
    battery = d.get("battery_serial", "") or "N/A"

    ACCENT    = colors.HexColor("#C0622A")
    ACCENT_BG = colors.HexColor("#F2D9CB")
    BLACK     = colors.HexColor("#1a1a1a")
    GREY      = colors.HexColor("#555555")
    WHITE     = colors.white

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    elements = []

    co_name  = ParagraphStyle("co",  fontSize=13, fontName="Helvetica-Bold",
                               textColor=BLACK, alignment=TA_LEFT, spaceAfter=2)
    co_sub   = ParagraphStyle("cs",  fontSize=8,  fontName="Helvetica",
                               textColor=GREY,  alignment=TA_LEFT, spaceAfter=1)
    big_title= ParagraphStyle("bt",  fontSize=26, fontName="Helvetica-Bold",
                               textColor=ACCENT, alignment=TA_RIGHT, leading=30)
    sec_hdr  = ParagraphStyle("sh",  fontSize=10, fontName="Helvetica-Bold",
                               textColor=BLACK, alignment=TA_LEFT, spaceAfter=4)
    normal   = ParagraphStyle("n",   fontSize=9,  fontName="Helvetica",
                               textColor=BLACK, alignment=TA_LEFT, spaceAfter=2)
    small_g  = ParagraphStyle("sg",  fontSize=8,  fontName="Helvetica",
                               textColor=GREY,  alignment=TA_LEFT, spaceAfter=2)
    center_s = ParagraphStyle("cns", fontSize=9,  fontName="Helvetica",
                               textColor=GREY,  alignment=TA_CENTER)
    vin_style= ParagraphStyle("vs",  fontSize=9,  fontName="Helvetica-Bold",
                               textColor=BLACK, alignment=TA_LEFT, spaceAfter=2)

    # ── Header ──
    co_info_rows = []
    if logo_path and os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path, width=2*cm, height=2*cm)
            co_info_rows.append([logo_img])
        except Exception:
            pass
    co_info_rows.append([Paragraph(shop_name, co_name)])
    co_info_rows.append([Paragraph(shop_tagline, co_sub)])
    co_info_rows.append([Paragraph(shop_address, co_sub)])
    co_info_rows.append([Paragraph(f"Phone: {shop_phone}", co_sub)])
    co_info_rows.append([Paragraph(f"Email: {shop_email}", co_sub)])

    header_data = [[
        Table(co_info_rows, colWidths=[9*cm]),
        Paragraph("ELECTRIC BIKE<br/>SALE<br/>RECEIPT", big_title),
    ]]
    header_tbl = Table(header_data, colWidths=[10*cm, 7*cm])
    header_tbl.setStyle(TableStyle([
        ("VALIGN",          (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",     (0,0), (-1,-1), 0),
        ("RIGHTPADDING",    (0,0), (-1,-1), 0),
        ("TOPPADDING",      (0,0), (-1,-1), 0),
        ("BOTTOMPADDING",   (0,0), (-1,-1), 0),
    ]))
    elements.append(header_tbl)
    elements.append(Spacer(1, 0.4*cm))

    # ── Receipt # bar ──
    receipt_bar = Table([
        [Paragraph(f"<b>Receipt #</b>  {d['id']:05d}", normal),
         Paragraph(f"<b>Date:</b>  {d['sale_date']}", normal)]
    ], colWidths=[9*cm, 8*cm])
    receipt_bar.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), ACCENT_BG),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("BOX",           (0,0), (-1,-1), 0.5, ACCENT),
    ]))
    elements.append(receipt_bar)
    elements.append(Spacer(1, 0.4*cm))

    # ── Buyer | Bike side by side ──
    buyer_rows = [
        [Paragraph("<b>Buyer Information</b>", sec_hdr), "",
         Paragraph("<b>Bike Information</b>", sec_hdr), ""],
        ["", "", "", ""],
    ]
    fields_left  = [("Name",    d["name"]),  ("Phone",  d["phone"]),
                    ("CNIC",    d["cnic"]),   ("Address",d["address"])]
    fields_right = [("Brand",   d["brand"]), ("Model",  d["model"]),
                    ("Color",   d["color"]),  ("",      "")]
    for i in range(4):
        lk, lv = fields_left[i]
        rk, rv = fields_right[i]
        buyer_rows.append([Paragraph(lk, small_g), Paragraph(lv, normal),
                           Paragraph(rk, small_g), Paragraph(rv, normal)])
    info_tbl = Table(buyer_rows, colWidths=[2.2*cm, 6.3*cm, 2.2*cm, 6.3*cm])
    info_tbl.setStyle(TableStyle([
        ("SPAN",         (0,0), (1,0)),  ("SPAN",         (2,0), (3,0)),
        ("LINEBELOW",    (0,0), (1,0), 0.8, BLACK),
        ("LINEBELOW",    (2,0), (3,0), 0.8, BLACK),
        ("FONTSIZE",     (0,0), (-1,-1), 9),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("LEFTPADDING",  (0,0), (-1,-1), 2),
        ("TEXTCOLOR",    (0,2), (0,-1), GREY),
        ("TEXTCOLOR",    (2,2), (2,-1), GREY),
    ]))
    elements.append(info_tbl)
    elements.append(Spacer(1, 0.3*cm))

    # ── VIN / Battery block (NEW) ──
    vin_data = [[
        Paragraph("<b>VIN / Chassis No:</b>", small_g),
        Paragraph(vin, vin_style),
        Paragraph("<b>Battery Serial No:</b>", small_g),
        Paragraph(battery, vin_style),
    ]]
    vin_tbl = Table(vin_data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 4.5*cm])
    vin_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), ACCENT_BG),
        ("BOX",           (0,0), (-1,-1), 0.5, ACCENT),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    elements.append(vin_tbl)
    elements.append(Spacer(1, 0.4*cm))

    # ── Description table ──
    desc_data = [
        [Paragraph("<b>Description</b>", sec_hdr), Paragraph("<b>Amount</b>", sec_hdr)],
        [Paragraph(f"Electric Bike Sale — {d['brand']} {d['model']} ({d['color']})", normal),
         Paragraph(fmt_currency(d["sale_price"]), normal)],
        ["", ""], ["", ""],
    ]
    desc_tbl = Table(desc_data, colWidths=[14*cm, 3*cm], rowHeights=[None, None, 18, 18])
    desc_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), ACCENT_BG),
        ("BOX",           (0,0), (-1,-1), 0.8, ACCENT),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, colors.HexColor("#dddddd")),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("ALIGN",         (1,0), (1,-1), "RIGHT"),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    elements.append(desc_tbl)
    elements.append(Spacer(1, 0.1*cm))

    # ── Totals ──
    totals_data = [
        [Paragraph("Subtotal",  normal), Paragraph(fmt_currency(d["sale_price"]), normal)],
        [Paragraph("Discount",  normal), Paragraph("PKR 0", normal)],
        [Paragraph("Tax / VAT", normal), Paragraph("PKR 0", normal)],
        [Paragraph("<b>TOTAL</b>", ParagraphStyle("tb", fontSize=10,
                    fontName="Helvetica-Bold", textColor=BLACK, alignment=TA_LEFT)),
         Paragraph(f"<b>{fmt_currency(d['sale_price'])}</b>",
                   ParagraphStyle("tv", fontSize=10, fontName="Helvetica-Bold",
                                  textColor=BLACK, alignment=TA_RIGHT))],
    ]
    totals_tbl = Table(totals_data, colWidths=[13*cm, 4*cm])
    totals_tbl.setStyle(TableStyle([
        ("ALIGN",         (1,0), (1,-1), "RIGHT"),
        ("BACKGROUND",    (1,0), (1,-1), ACCENT_BG),
        ("BOX",           (1,0), (1,-1), 0.5, ACCENT),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (0,-1), 2),
        ("LEFTPADDING",   (1,0), (1,-1), 6),
        ("RIGHTPADDING",  (1,0), (1,-1), 6),
        ("LINEABOVE",     (0,3), (-1,3), 0.8, BLACK),
    ]))
    elements.append(totals_tbl)
    elements.append(Spacer(1, 0.4*cm))

    elements.append(Paragraph(
        f"The amount of <b>{fmt_currency(d['amount_paid'])}</b> was paid by "
        f"<b>{d['name']}</b>, the customer, on <b>{d['sale_date']}</b>.", normal
    ))
    elements.append(Spacer(1, 0.2*cm))

    pay_method = "Cash" if d["pending_amount"] == 0 else "Partial"
    elements.append(Paragraph("<b>Payment Method:</b>", normal))
    chk_data = [[
        Paragraph("☑ Cash" if pay_method == "Cash" else "☐ Cash", normal),
        Paragraph("☐ Credit Card No. ____________", normal),
    ],[
        Paragraph("☐ Check No. ____________", normal),
        Paragraph("☐ Other: ________________", normal),
    ]]
    chk_tbl = Table(chk_data, colWidths=[8*cm, 9*cm])
    chk_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
    ]))
    elements.append(chk_tbl)

    if d["pending_amount"] > 0:
        elements.append(Spacer(1, 0.2*cm))
        elements.append(Paragraph(
            f"<b>Pending Balance: {fmt_currency(d['pending_amount'])}</b>",
            ParagraphStyle("pb", fontSize=10, fontName="Helvetica-Bold",
                           textColor=ACCENT, alignment=TA_LEFT)
        ))

    elements.append(Spacer(1, 0.6*cm))

    sig_data = [[
        Table([
            [HRFlowable(width=7*cm, thickness=0.8, color=BLACK)],
            [Paragraph("<b>Signature of Buyer</b>", normal)],
        ], colWidths=[8*cm]),
        Paragraph("Thank you for your business!", center_s),
    ]]
    sig_tbl = Table(sig_data, colWidths=[9*cm, 8*cm])
    sig_tbl.setStyle(TableStyle([
        ("VALIGN",      (0,0), (-1,-1), "BOTTOM"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING",(0,0), (-1,-1), 0),
    ]))
    elements.append(sig_tbl)
    elements.append(Spacer(1, 0.3*cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GREY))
    elements.append(Spacer(1, 0.15*cm))
    elements.append(Paragraph(f"{shop_website}  •  {shop_address}", small_g))

    doc.build(elements)
def _export_report_pdf(path, rows, from_date, to_date):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    shop_name = get_setting("shop_name", "Shahzaib Motors")

    doc = SimpleDocTemplate(path, pagesize=landscape(A4),
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    elements = []

    title_style = ParagraphStyle("title", fontSize=20, alignment=TA_CENTER,
                                 textColor=colors.HexColor("#1f6feb"),
                                 fontName="Helvetica-Bold", spaceAfter=4)
    sub_style   = ParagraphStyle("sub",   fontSize=11, alignment=TA_CENTER,
                                 textColor=colors.HexColor("#555555"), spaceAfter=2)
    body_style  = ParagraphStyle("body",  fontSize=9,  alignment=TA_LEFT)

    elements.append(Paragraph(shop_name.upper(), title_style))
    elements.append(Paragraph("Electric Bike Showroom — Sales Report", sub_style))
    elements.append(Paragraph(f"Period: {from_date}  to  {to_date}", sub_style))
    elements.append(Spacer(1, 0.4*cm))

    # Summary
    total_rev = sum(r[5] for r in rows)
    total_paid = sum(r[6] for r in rows)
    total_pend = sum(r[7] for r in rows)
    summary_data = [
        ["Total Sales", "Total Revenue", "Amount Collected", "Pending Amount"],
        [str(len(rows)), fmt_currency(total_rev), fmt_currency(total_paid), fmt_currency(total_pend)],
    ]
    sum_table = Table(summary_data, colWidths=[6*cm]*4)
    sum_table.setStyle(TableStyle([
        ("BACKGROUND",      (0,0), (-1,0), colors.HexColor("#1f6feb")),
        ("TEXTCOLOR",       (0,0), (-1,0), colors.white),
        ("FONTNAME",        (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",        (0,0), (-1,-1), 10),
        ("ALIGN",           (0,0), (-1,-1), "CENTER"),
        ("BACKGROUND",      (0,1), (-1,1), colors.HexColor("#f0f4ff")),
        ("FONTNAME",        (0,1), (-1,1), "Helvetica-Bold"),
        ("BOX",             (0,0), (-1,-1), 1, colors.HexColor("#cccccc")),
        ("INNERGRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING",      (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",   (0,0), (-1,-1), 8),
    ]))
    elements.append(sum_table)
    elements.append(Spacer(1, 0.4*cm))

    # Detail table
    headers = ["#", "Customer", "Phone", "CNIC", "Bike", "Sale Price", "Paid", "Pending", "Date"]
    data = [headers]
    for row in rows:
        data.append([
            str(row[0]), row[1], row[2], row[3], row[4],
            fmt_currency(row[5]), fmt_currency(row[6]), fmt_currency(row[7]), row[8]
        ])

    col_widths = [1*cm, 3.5*cm, 3*cm, 3.5*cm, 4*cm, 3*cm, 3*cm, 3*cm, 2.5*cm]
    detail_table = Table(data, colWidths=col_widths, repeatRows=1)
    detail_table.setStyle(TableStyle([
        ("BACKGROUND",      (0,0), (-1,0), colors.HexColor("#21262d")),
        ("TEXTCOLOR",       (0,0), (-1,0), colors.white),
        ("FONTNAME",        (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",        (0,0), (-1,-1), 8),
        ("ALIGN",           (0,0), (0,-1), "CENTER"),
        ("ALIGN",           (4,0), (6,-1), "RIGHT"),
        ("ROWBACKGROUNDS",  (0,1), (-1,-1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("BOX",             (0,0), (-1,-1), 1, colors.HexColor("#cccccc")),
        ("INNERGRID",       (0,0), (-1,-1), 0.4, colors.HexColor("#dddddd")),
        ("TOPPADDING",      (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",   (0,0), (-1,-1), 6),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  {shop_name}",
        body_style
    ))

    doc.build(elements)
# ─────────────────────────────────────────────────────────────────
# EXCEL EXPORT (Pandas + OpenPyXL)
# ─────────────────────────────────────────────────────────────────

def _export_report_excel(path, rows):
    import pandas as pd
    from openpyxl import load_workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    data = []
    for row in rows:
        data.append({
            "Sale ID":      row[0],
            "Customer":     row[1],
            "Phone":        row[2],
            "Bike":         row[3],
            "Sale Price":   row[4],
            "Amount Paid":  row[5],
            "Pending":      row[6],
            "Date":         row[7],
        })
    df = pd.DataFrame(data)
    df.to_excel(path, index=False, sheet_name="Sales Report")

    wb = load_workbook(path)
    ws = wb.active

    # Title row (insert above)
    ws.insert_rows(1, amount=2)
    ws["A1"] = "SHAHZAIB MOTORS — Sales Report"
    ws["A1"].font = Font(bold=True, size=14, color="1F6FEB")
    ws["A2"] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws["A2"].font = Font(italic=True, size=9, color="555555")

    # Header row is now row 3
    hdr_fill  = PatternFill("solid", fgColor="21262D")
    hdr_font  = Font(bold=True, color="FFFFFF", size=10)
    thin = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for col in range(1, len(df.columns) + 1):
        cell = ws.cell(row=3, column=col)
        cell.fill  = hdr_fill
        cell.font  = hdr_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    # Data rows
    alt_fill = PatternFill("solid", fgColor="F5F7FA")
    for r_idx in range(4, 4 + len(df)):
        fill = alt_fill if (r_idx % 2 == 0) else PatternFill()
        for c_idx in range(1, len(df.columns) + 1):
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.fill   = fill
            cell.border = border
            cell.alignment = Alignment(vertical="center", wrap_text=True)

    # Column widths
    widths = [8, 20, 14, 22, 14, 14, 14, 12]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.row_dimensions[3].height = 22

    # Summary at bottom
    bottom = 4 + len(df) + 2
    ws.cell(row=bottom, column=1, value="TOTALS").font = Font(bold=True)
    ws.cell(row=bottom, column=5, value=sum(r[4] for r in rows)).font = Font(bold=True, color="1F6FEB")
    ws.cell(row=bottom, column=6, value=sum(r[5] for r in rows)).font = Font(bold=True, color="238636")
    ws.cell(row=bottom, column=7, value=sum(r[6] for r in rows)).font = Font(bold=True, color="DA3633")

    wb.save(path)


# ─────────────────────────────────────────────────────────────────
# MONTHLY SALES PAGE
# ─────────────────────────────────────────────────────────────────

class MonthlySalesPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(page_header("Monthly Sales", "Revenue and bikes sold by month"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(28, 12, 28, 28)
        inner_lay.setSpacing(20)

        # ── Year selector ──
        year_frame = QFrame()
        year_frame.setObjectName("kpi_card")
        year_lay = QHBoxLayout(year_frame)
        year_lay.setSpacing(12)
        year_lay.addWidget(QLabel("Select Year:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2099)
        self.year_spin.setValue(date.today().year)
        self.year_spin.setMinimumWidth(100)
        self.year_spin.valueChanged.connect(self.refresh)
        year_lay.addWidget(self.year_spin)

        year_lay.addWidget(QLabel("  Select Month:"))
        self.month_combo = QComboBox()
        self.month_combo.addItem("All Months", 0)
        for mn, mname in enumerate(["January","February","March","April","May","June",
                                    "July","August","September","October","November","December"], 1):
            self.month_combo.addItem(mname, mn)
        self.month_combo.setMinimumWidth(140)
        self.month_combo.currentIndexChanged.connect(self.refresh)
        year_lay.addWidget(self.month_combo)

        filter_btn = QPushButton("🔍  Filter")
        filter_btn.setObjectName("primary_btn")
        filter_btn.clicked.connect(self.refresh)
        year_lay.addWidget(filter_btn)

        year_lay.addStretch()
        inner_lay.addWidget(year_frame)

        # ── Annual KPI cards ──
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)
        self.kpi_annual_rev    = self._kpi("💰", "PKR 0",  "ANNUAL REVENUE")
        self.kpi_annual_sold   = self._kpi("✅", "0",      "BIKES SOLD THIS YEAR")
        self.kpi_annual_pend   = self._kpi("⏳", "PKR 0",  "ANNUAL PENDING")
        self.kpi_annual_cust   = self._kpi("👤", "0",      "CUSTOMERS THIS YEAR")
        kpi_row.addWidget(self.kpi_annual_rev)
        kpi_row.addWidget(self.kpi_annual_sold)
        kpi_row.addWidget(self.kpi_annual_pend)
        kpi_row.addWidget(self.kpi_annual_cust)
        inner_lay.addLayout(kpi_row)

        # ── Monthly breakdown table ──
        lbl = QLabel("Month-by-Month Breakdown")
        lbl.setObjectName("section_header")
        inner_lay.addWidget(lbl)

        self.month_table = make_table_widget([
            "Month", "Bikes Sold", "Total Revenue",
            "Amount Collected", "Pending Amount", "Customers"
        ])
        self.month_table.setMinimumHeight(320)
        inner_lay.addWidget(self.month_table)

        # ── Best month highlight ──
        self.best_lbl = QLabel("")
        self.best_lbl.setStyleSheet(
            "color: #3fb950; font-size: 13px; font-weight: bold; padding: 8px 0px;"
        )
        inner_lay.addWidget(self.best_lbl)

        # ── Top selling bikes this year ──
        lbl2 = QLabel("Top Selling Bikes This Year")
        lbl2.setObjectName("section_header")
        inner_lay.addWidget(lbl2)

        self.top_table = make_table_widget([
            "Rank", "Brand", "Model", "Color", "Units Sold", "Revenue"
        ])
        self.top_table.setMinimumHeight(180)
        inner_lay.addWidget(self.top_table)

        scroll.setWidget(inner)
        lay.addWidget(scroll)

    def _kpi(self, icon, value, label):
        card = QFrame()
        card.setObjectName("kpi_card")
        card_lay = QVBoxLayout(card)
        card_lay.setSpacing(6)
        ico = QLabel(icon)
        ico.setObjectName("kpi_icon")
        val = QLabel(value)
        val.setObjectName("kpi_value")
        lbl = QLabel(label)
        lbl.setObjectName("kpi_label")
        card_lay.addWidget(ico)
        card_lay.addWidget(val)
        card_lay.addWidget(lbl)
        card._val = val
        return card

    def refresh(self):
        year = self.year_spin.value()
        month = self.month_combo.currentData()  # 0 = all months, 1-12 = specific month
        conn = get_connection()

        if month == 0:
            # ── All months: annual totals + month-by-month breakdown ──
            ann = conn.execute("""
                SELECT COUNT(*) as sold,
                       COALESCE(SUM(amount_paid),0) as rev,
                       COALESCE(SUM(pending_amount),0) as pend,
                       COUNT(DISTINCT customer_id) as custs
                FROM sales
                WHERE strftime('%Y', sale_date) = ?
            """, (str(year),)).fetchone()

            self.kpi_annual_rev._val.setText(fmt_currency(ann["rev"]))
            self.kpi_annual_sold._val.setText(str(ann["sold"]))
            self.kpi_annual_pend._val.setText(fmt_currency(ann["pend"]))
            self.kpi_annual_cust._val.setText(str(ann["custs"]))

            months_data = conn.execute("""
                SELECT strftime('%m', sale_date) as month,
                       COUNT(*) as sold,
                       COALESCE(SUM(sale_price),0) as rev,
                       COALESCE(SUM(amount_paid),0) as paid,
                       COALESCE(SUM(pending_amount),0) as pend,
                       COUNT(DISTINCT customer_id) as custs
                FROM sales
                WHERE strftime('%Y', sale_date) = ?
                GROUP BY month
                ORDER BY month
            """, (str(year),)).fetchall()

            top_bikes = conn.execute("""
                SELECT b.brand, b.model, b.color,
                       COUNT(*) as units,
                       COALESCE(SUM(s.amount_paid),0) as rev
                FROM sales s
                JOIN bikes b ON b.id = s.bike_id
                WHERE strftime('%Y', s.sale_date) = ?
                GROUP BY b.id
                ORDER BY units DESC
                LIMIT 10
            """, (str(year),)).fetchall()
            conn.close()

            MONTH_NAMES = ["", "January", "February", "March", "April",
                           "May", "June", "July", "August",
                           "September", "October", "November", "December"]

            # Restore headers to month-by-month columns
            self.month_table.setColumnCount(6)
            self.month_table.setHorizontalHeaderLabels([
                "Month", "Bikes Sold", "Total Revenue",
                "Amount Collected", "Pending Amount", "Customers"
            ])

            month_dict = {row["month"]: row for row in months_data}
            self.month_table.setSortingEnabled(False)
            self.month_table.setRowCount(12)
            best_rev = 0
            best_month = ""
            for i in range(1, 13):
                key = f"{i:02d}"
                row = month_dict.get(key)
                sold = row["sold"] if row else 0
                rev  = row["rev"]  if row else 0
                paid = row["paid"] if row else 0
                pend = row["pend"] if row else 0
                custs= row["custs"]if row else 0

                set_item(self.month_table, i-1, 0, MONTH_NAMES[i])
                qty_item = QTableWidgetItem(str(sold))
                qty_item.setForeground(QColor("#3fb950") if sold > 0 else QColor("#555555"))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.month_table.setItem(i-1, 1, qty_item)
                set_item(self.month_table, i-1, 2, fmt_currency(rev))
                set_item(self.month_table, i-1, 3, fmt_currency(paid))
                pend_item = QTableWidgetItem(fmt_currency(pend))
                pend_item.setForeground(QColor("#f85149") if pend > 0 else QColor("#3fb950"))
                self.month_table.setItem(i-1, 4, pend_item)
                set_item(self.month_table, i-1, 5, str(custs),
                         Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                if rev > best_rev:
                    best_rev = rev
                    best_month = MONTH_NAMES[i]

            self.month_table.setSortingEnabled(True)

            if best_month and best_rev > 0:
                self.best_lbl.setText(
                    f"🏆  Best Month: {best_month} {year}  —  Revenue: {fmt_currency(best_rev)}"
                )
            else:
                self.best_lbl.setText(f"No sales data found for {year}.")

        else:
            # ── Single month selected: show individual sales for that month ──
            month_str = f"{month:02d}"
            MONTH_NAMES = ["", "January", "February", "March", "April",
                           "May", "June", "July", "August",
                           "September", "October", "November", "December"]
            mname = MONTH_NAMES[month]

            ann = conn.execute("""
                            SELECT COUNT(*) as sold,
                                   COALESCE(SUM(amount_paid),0) as rev,
                                   COALESCE(SUM(pending_amount),0) as pend,
                                   COUNT(DISTINCT customer_id) as custs
                            FROM sales
                            WHERE strftime('%Y', sale_date) = ?
                              AND strftime('%m', sale_date) = ?
                        """, (str(year), month_str)).fetchone()

            self.kpi_annual_rev._val.setText(fmt_currency(ann["rev"]))
            self.kpi_annual_sold._val.setText(str(ann["sold"]))
            self.kpi_annual_pend._val.setText(fmt_currency(ann["pend"]))
            self.kpi_annual_cust._val.setText(str(ann["custs"]))

            sale_rows = conn.execute("""
                SELECT s.id, c.name, c.phone, b.brand||' '||b.model||' ('||b.color||')' as bike,
                       s.sale_price, s.amount_paid, s.pending_amount, s.sale_date
                FROM sales s
                JOIN customers c ON c.id = s.customer_id
                JOIN bikes b ON b.id = s.bike_id
                WHERE strftime('%Y', s.sale_date) = ?
                  AND strftime('%m', s.sale_date) = ?
                ORDER BY s.sale_date ASC, s.id ASC
            """, (str(year), month_str)).fetchall()

            top_bikes = conn.execute("""
                            SELECT b.brand, b.model, b.color,
                                   COUNT(*) as units,
                                   COALESCE(SUM(s.amount_paid),0) as rev
                            FROM sales s
                            JOIN bikes b ON b.id = s.bike_id
                            WHERE strftime('%Y', s.sale_date) = ?
                              AND strftime('%m', s.sale_date) = ?
                            GROUP BY b.id
                            ORDER BY units DESC
                            LIMIT 10
                        """, (str(year), month_str)).fetchall()
            conn.close()

            # Switch table to per-sale columns
            self.month_table.setSortingEnabled(False)
            self.month_table.setColumnCount(8)
            self.month_table.setHorizontalHeaderLabels([
                "Sale ID", "Customer", "Phone", "Bike",
                "Sale Price", "Amount Paid", "Pending", "Date"
            ])
            self.month_table.setRowCount(len(sale_rows))
            for r, row in enumerate(sale_rows):
                set_item(self.month_table, r, 0, str(row[0]),
                         Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                set_item(self.month_table, r, 1, row[1])
                set_item(self.month_table, r, 2, row[2])
                set_item(self.month_table, r, 3, row[3])
                set_item(self.month_table, r, 4, fmt_currency(row[4]))
                set_item(self.month_table, r, 5, fmt_currency(row[5]))
                pend_item = QTableWidgetItem(fmt_currency(row[6]))
                pend_item.setForeground(QColor("#f85149") if row[6] > 0 else QColor("#3fb950"))
                self.month_table.setItem(r, 6, pend_item)
                set_item(self.month_table, r, 7, row[7])
            self.month_table.setSortingEnabled(True)

            if sale_rows:
                self.best_lbl.setText(
                    f"📅  Showing {len(sale_rows)} sale(s) for {mname} {year}  —  "
                    f"Collected: {fmt_currency(ann['rev'])}"
                )
            else:
                self.best_lbl.setText(f"No sales found for {mname} {year}.")

        # ── Top bikes table (shared for both modes) ──
        self.top_table.setSortingEnabled(False)
        self.top_table.setRowCount(len(top_bikes))
        for r, row in enumerate(top_bikes):
            set_item(self.top_table, r, 0, str(r+1),
                     Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            set_item(self.top_table, r, 1, row["brand"])
            set_item(self.top_table, r, 2, row["model"])
            set_item(self.top_table, r, 3, row["color"])
            units_item = QTableWidgetItem(str(row["units"]))
            units_item.setForeground(QColor("#58a6ff"))
            units_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.top_table.setItem(r, 4, units_item)
            set_item(self.top_table, r, 5, fmt_currency(row["rev"]))
        self.top_table.setSortingEnabled(True)


# ─────────────────────────────────────────────────────────────────
# SETTINGS PAGE
# ─────────────────────────────────────────────────────────────────

class SettingsPage(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(page_header("Settings", "Edit showroom name, logo and contact details"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(28, 12, 28, 28)
        inner_lay.setSpacing(20)

        # ── Logo section ──
        logo_frame = QFrame()
        logo_frame.setObjectName("kpi_card")
        logo_outer = QVBoxLayout(logo_frame)
        logo_outer.setSpacing(12)

        logo_hdr = QLabel("Showroom Logo")
        logo_hdr.setObjectName("section_header")
        logo_outer.addWidget(logo_hdr)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(16)

        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(120, 120)
        self.logo_preview.setStyleSheet("""
            background-color: #21262d;
            border: 2px dashed #30363d;
            border-radius: 10px;
            color: #8b949e;
            font-size: 11px;
        """)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setText("No Logo\nUploaded")
        logo_row.addWidget(self.logo_preview)

        logo_btns = QVBoxLayout()
        logo_btns.setSpacing(8)
        upload_btn = QPushButton("📁  Upload Logo")
        upload_btn.setObjectName("primary_btn")
        upload_btn.clicked.connect(self._upload_logo)
        clear_btn = QPushButton("🗑  Remove Logo")
        clear_btn.setObjectName("danger_btn")
        clear_btn.clicked.connect(self._clear_logo)
        logo_note = QLabel("Supported: PNG, JPG, BMP\nRecommended: 200×200 px")
        logo_note.setStyleSheet("color: #8b949e; font-size: 11px;")
        logo_btns.addWidget(upload_btn)
        logo_btns.addWidget(clear_btn)
        logo_btns.addWidget(logo_note)
        logo_btns.addStretch()
        logo_row.addLayout(logo_btns)
        logo_row.addStretch()
        logo_outer.addLayout(logo_row)
        inner_lay.addWidget(logo_frame)

        # ── Showroom info section ──
        info_frame = QFrame()
        info_frame.setObjectName("kpi_card")
        info_outer = QVBoxLayout(info_frame)
        info_outer.setSpacing(12)

        info_hdr = QLabel("Showroom Information")
        info_hdr.setObjectName("section_header")
        info_outer.addWidget(info_hdr)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.f_name     = QLineEdit()
        self.f_tagline  = QLineEdit()
        self.f_address  = QLineEdit()
        self.f_phone    = QLineEdit()
        self.f_email    = QLineEdit()
        self.f_website  = QLineEdit()

        self.f_name.setPlaceholderText("e.g. Shahzaib Motors")
        self.f_tagline.setPlaceholderText("e.g. Electric Bike Showroom & Service")
        self.f_address.setPlaceholderText("e.g. Multan, Punjab, Pakistan")
        self.f_phone.setPlaceholderText("e.g. 0300-0000000")
        self.f_email.setPlaceholderText("e.g. info@shahzaibmotors.com")
        self.f_website.setPlaceholderText("e.g. ShahzaibMotors.com")

        form.addRow("Showroom Name:",  self.f_name)
        form.addRow("Tagline:",        self.f_tagline)
        form.addRow("Address:",        self.f_address)
        form.addRow("Phone:",          self.f_phone)
        form.addRow("Email:",          self.f_email)
        form.addRow("Website:",        self.f_website)
        info_outer.addLayout(form)

        save_btn = QPushButton("💾  Save Settings")
        save_btn.setObjectName("success_btn")
        save_btn.setMinimumHeight(42)
        save_btn.clicked.connect(self._save)
        info_outer.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

        inner_lay.addWidget(info_frame)

        # ── Preview card ──
        prev_frame = QFrame()
        prev_frame.setObjectName("kpi_card")
        prev_outer = QVBoxLayout(prev_frame)
        prev_hdr = QLabel("Receipt Header Preview")
        prev_hdr.setObjectName("section_header")
        prev_outer.addWidget(prev_hdr)
        self.preview_lbl = QLabel()
        self.preview_lbl.setStyleSheet(
            "color: #8b949e; font-family: 'Courier New'; font-size: 12px; padding: 10px;"
        )
        self.preview_lbl.setWordWrap(True)
        prev_outer.addWidget(self.preview_lbl)
        inner_lay.addWidget(prev_frame)

        scroll.setWidget(inner)
        lay.addWidget(scroll)

        self.refresh()

    def refresh(self):
        self.f_name.setText(get_setting("shop_name"))
        self.f_tagline.setText(get_setting("shop_tagline"))
        self.f_address.setText(get_setting("shop_address"))
        self.f_phone.setText(get_setting("shop_phone"))
        self.f_email.setText(get_setting("shop_email"))
        self.f_website.setText(get_setting("shop_website"))
        self._update_logo_preview(get_setting("logo_path"))
        self._update_preview()

    def _update_preview(self):
        name    = self.f_name.text() or "Your Showroom"
        tagline = self.f_tagline.text()
        address = self.f_address.text()
        phone   = self.f_phone.text()
        email   = self.f_email.text()
        self.preview_lbl.setText(
            f"{name}\n{tagline}\n{address}\nPhone: {phone}  |  Email: {email}"
        )

    def _upload_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            import shutil
            ext = os.path.splitext(path)[1]
            dest = os.path.join(os.path.dirname(DB_PATH), f"showroom_logo{ext}")
            shutil.copy2(path, dest)
            set_setting("logo_path", dest)
            self._update_logo_preview(dest)
            QMessageBox.information(self, "Logo Saved", "Logo uploaded and saved successfully!")

    def _clear_logo(self):
        set_setting("logo_path", "")
        from PyQt6.QtGui import QPixmap
        self.logo_preview.setPixmap(QPixmap())
        self.logo_preview.setText("No Logo\nUploaded")
        QMessageBox.information(self, "Removed", "Logo removed successfully.")

    def _update_logo_preview(self, path):
        from PyQt6.QtGui import QPixmap
        if path and os.path.exists(path):
            pix = QPixmap(path).scaled(
                116, 116,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_preview.setPixmap(pix)
            self.logo_preview.setText("")
        else:
            self.logo_preview.setText("No Logo\nUploaded")

    def _save(self):
        if not self.f_name.text().strip():
            QMessageBox.warning(self, "Validation", "Showroom name cannot be empty.")
            return
        set_setting("shop_name",    self.f_name.text().strip())
        set_setting("shop_tagline", self.f_tagline.text().strip())
        set_setting("shop_address", self.f_address.text().strip())
        set_setting("shop_phone",   self.f_phone.text().strip())
        set_setting("shop_email",   self.f_email.text().strip())
        set_setting("shop_website", self.f_website.text().strip())
        self._update_preview()
        self.settings_changed.emit()
        QMessageBox.information(self, "Saved", "Settings saved! All receipts and reports will use the new information.")


# ─────────────────────────────────────────────────────────────────
# MAIN WINDOW
# ─────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._update_title()
        self.setMinimumSize(1200, 720)
        self._build()
        self._refresh_all()

    def _update_title(self):
        name = get_setting("shop_name", "Shahzaib Motors")
        self.setWindowTitle(f"{name} — Electric Bike Showroom")

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_lay = QVBoxLayout(sidebar)
        sidebar_lay.setContentsMargins(0, 0, 0, 0)
        sidebar_lay.setSpacing(0)

        self.sidebar_logo_lbl = QLabel()
        self.sidebar_logo_lbl.setFixedSize(60, 60)
        self.sidebar_logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sidebar_logo_lbl.setContentsMargins(0, 14, 0, 0)
        self._refresh_sidebar_logo()
        sidebar_lay.addWidget(self.sidebar_logo_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.logo_name_lbl = QLabel()
        self.logo_name_lbl.setObjectName("logo_label")
        self._refresh_sidebar_name()
        sub = QLabel("SHOWROOM")
        sub.setObjectName("logo_sub")
        sidebar_lay.addWidget(self.logo_name_lbl)
        sidebar_lay.addWidget(sub)

        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.Shape.HLine)
        sidebar_lay.addWidget(div)

        # ── Sales removed; Customers now handles both ──
        nav_items = [
            ("🏠  Dashboard",      0),
            ("🔋  Inventory",      1),
            ("👤  Customers",      2),
            ("📊  Reports",        3),
            ("📅  Monthly Sales",  4),
            ("🧾  Receipts",       5),
            ("⚙️  Settings",       6),
        ]
        self._nav_btns = []
        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            sidebar_lay.addWidget(btn)
            self._nav_btns.append(btn)

        sidebar_lay.addStretch()

        self.ver_lbl = QLabel()
        self._refresh_ver_label()
        self.ver_lbl.setStyleSheet("color: #444d56; font-size: 10px; padding: 12px;")
        sidebar_lay.addWidget(self.ver_lbl)

        root.addWidget(sidebar)

        # ── Stacked pages ──
        self.stack = QStackedWidget()
        self.stack.setObjectName("content_area")

        self.dash_page    = DashboardPage()
        self.inv_page     = InventoryPage()
        self.cust_page    = CustomersPage()
        self.rep_page     = ReportsPage()
        self.monthly_page = MonthlySalesPage()
        self.rec_page     = ReceiptsPage()
        self.sett_page    = SettingsPage()

        self.stack.addWidget(self.dash_page)     # index 0
        self.stack.addWidget(self.inv_page)      # index 1
        self.stack.addWidget(self.cust_page)     # index 2
        self.stack.addWidget(self.rep_page)      # index 3
        self.stack.addWidget(self.monthly_page)  # index 4
        self.stack.addWidget(self.rec_page)      # index 5
        self.stack.addWidget(self.sett_page)     # index 6

        root.addWidget(self.stack)

        # Connect signals
        self.inv_page.changed.connect(self._refresh_all)
        self.cust_page.changed.connect(self._refresh_all)
        self.sett_page.settings_changed.connect(self._on_settings_changed)

        self._switch_page(0)

    def _refresh_sidebar_logo(self):
        from PyQt6.QtGui import QPixmap
        logo_path = get_setting("logo_path", "")
        if logo_path and os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(
                56, 56,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.sidebar_logo_lbl.setPixmap(pix)
            self.sidebar_logo_lbl.setText("")
        else:
            self.sidebar_logo_lbl.setText("⚡")
            self.sidebar_logo_lbl.setStyleSheet("font-size: 28px; color: #58a6ff;")

    def _refresh_sidebar_name(self):
        name = get_setting("shop_name", "SHAHZAIB")
        self.logo_name_lbl.setText(f"⚡ {name.upper()[:10]}")

    def _refresh_ver_label(self):
        name = get_setting("shop_name", "Shahzaib Motors")
        self.ver_lbl.setText(f"v1.0.0  •  {name}")

    def _on_settings_changed(self):
        self._refresh_sidebar_logo()
        self._refresh_sidebar_name()
        self._refresh_ver_label()
        self._update_title()

    def _switch_page(self, idx):
        for i, btn in enumerate(self._nav_btns):
            btn.setChecked(i == idx)
        self.stack.setCurrentIndex(idx)
        self._refresh_current(idx)

    def _refresh_current(self, idx):
        pages = [
            self.dash_page,
            self.inv_page,
            self.cust_page,
            self.rep_page,
            self.monthly_page,
            self.rec_page,
            self.sett_page,
        ]
        if hasattr(pages[idx], "refresh"):
            pages[idx].refresh()

    def _refresh_all(self):
        self.dash_page.refresh()
        self.inv_page.refresh()
        self.cust_page.refresh()
        self.rep_page.refresh()
        self.monthly_page.refresh()
        self.rec_page.refresh()


# ─────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────

def main():
    initialize_database()
    app = QApplication(sys.argv)
    app.setApplicationName("Shahzaib Motors")
    app.setStyleSheet(APP_STYLE)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()