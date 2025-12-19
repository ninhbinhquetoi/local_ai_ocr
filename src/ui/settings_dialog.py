# src/ui/settings_dialog.py
# Settings dialog for configuring Local AI OCR.

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QHBoxLayout, QPushButton, QLabel, QMessageBox)
from PySide6.QtCore import Qt

import re
import config


class SettingsDialog(QDialog):
    def __init__(self, translations, parent=None):
        super().__init__(parent)
        self.t = translations
        self.setWindowTitle(self.t["dlg_settings_title"])
        self.setFixedWidth(400)

        layout = QVBoxLayout(self)

        # Warning Label
        warning_label = QLabel(self.t["dlg_settings_warning"])
        warning_label.setTextFormat(Qt.RichText)
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)

        # Form for Settings
        form = QFormLayout()

        # Load current values from config
        cfg = config.load_user_config()

        self.input_ip = QLineEdit(cfg["ip_address"])
        self.input_port = QLineEdit(cfg["port"])
        self.input_model = QLineEdit(cfg["model"])

        # This is hardcoded for a reason
        form.addRow("IP Address:", self.input_ip)
        form.addRow("Port:", self.input_port)
        form.addRow("AI Model:", self.input_model)
        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_restore = QPushButton(self.t["dlg_settings_restore"])
        self.btn_restore.clicked.connect(self.restore_defaults)
        self.btn_restore.setAutoDefault(False) # Prevent Enter from triggering this
        btn_layout.addWidget(self.btn_restore)

        btn_layout.addStretch()

        self.btn_apply = QPushButton(self.t["dlg_settings_apply"])
        self.btn_apply.clicked.connect(self.apply_settings)
        # Make this the default button when Enter is pressed
        self.btn_apply.setDefault(True)
        btn_layout.addWidget(self.btn_apply)

        self.btn_cancel = QPushButton(self.t["dlg_settings_cancel"])
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setAutoDefault(False) # Prevent Enter from triggering this
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def restore_defaults(self):
        self.input_ip.setText(config.DEFAULT_OLLAMA_IP)
        self.input_port.setText(config.DEFAULT_OLLAMA_PORT)
        self.input_model.setText(config.DEFAULT_OLLAMA_MODEL)

    def apply_settings(self):
        ip = self.input_ip.text().strip()
        port = self.input_port.text().strip()
        model = self.input_model.text().strip()

        # Validation patterns
        ip_pattern = re.compile(r'^[a-zA-Z0-9/:\\.\\-]+$') # letters, numbers, :, /, ., -
        port_pattern = re.compile(r'^[0-9]+$') # numbers only
        model_pattern = re.compile(r'^[a-zA-Z0-9:\-_]+$') # letters, numbers, :, -, _

        # Check all validations (IP must not end with colon to prevent double-colon)
        # Port must also be in valid range 1-65535
        port_in_range = port.isdigit() and 1 <= int(port) <= 65535 if port else False

        is_valid = (
            ip and ip_pattern.match(ip) and not ip.endswith(':') and
            port_in_range and
            model and model_pattern.match(model)
        )

        if not is_valid:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle(self.t["title_error"])
            msg.setTextFormat(Qt.RichText)
            msg.setText(self.t["dlg_settings_error"])
            msg.exec()
            return

        # Save to TOML file
        config.save_user_config(ip, port, model)

        # Reload config module globals
        config.reload_config()

        self.accept()
