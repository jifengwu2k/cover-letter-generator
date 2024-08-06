import json
import os
import random

from dataclasses import dataclass

from PySide6.QtCore import Slot, QMimeData
from PySide6.QtGui import QTextDocumentFragment, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLineEdit,
    QLabel,
    QVBoxLayout,
    QWidget,
    QDialog,
    QFileDialog,
    QMessageBox,
    QMenuBar,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QHBoxLayout,
    QFormLayout
)
from markdownify import markdownify as md


@dataclass
class Settings:
    api_key: str = ""
    resume: str = ""
    initial_prompt: str = ""


class SettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")

        self.settings = settings if settings is not None else Settings()

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.api_tab = QWidget()

        # API Tab Layout
        self.api_layout = QFormLayout()
        self.api_key_input = QLineEdit()
        self.api_layout.addRow("API Key:", self.api_key_input)

        self.resume_input = QTextEdit()
        self.api_layout.addRow("Resume:", self.resume_input)

        self.initial_prompt_input = QTextEdit()
        self.api_layout.addRow("Initial Prompt:", self.initial_prompt_input)

        self.api_tab.setLayout(self.api_layout)

        # Add tab to the tab widget
        self.tab_widget.addTab(self.api_tab, "API Key & Resume")

        # Dialog Layout
        self.dialog_layout = QVBoxLayout()
        self.dialog_layout.addWidget(self.tab_widget)

        # Save Button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.dialog_layout.addWidget(self.save_button)

        self.setLayout(self.dialog_layout)

        self.load_settings()

    def save_settings(self):
        self.settings.api_key = self.api_key_input.text()
        self.settings.resume = self.resume_input.toPlainText()
        self.settings.initial_prompt = self.initial_prompt_input.toPlainText()

        if not self.settings.api_key or not self.settings.resume or not self.settings.initial_prompt:
            QMessageBox.warning(self, "Incomplete Settings", "Please ensure that all settings are filled out.")
            return

        with open("settings.json", "w") as settings_file:
            json.dump(self.settings.__dict__, settings_file)
        self.accept()

    def load_settings(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as settings_file:
                self.settings.__dict__.update(json.load(settings_file))
                self.api_key_input.setText(self.settings.api_key)
                self.resume_input.setPlainText(self.settings.resume)
                self.initial_prompt_input.setPlainText(self.settings.initial_prompt)

        if not self.settings.api_key:
            self.api_key_input.setPlaceholderText("Enter your API key here")
        if not self.settings.resume:
            self.resume_input.setPlaceholderText("Enter your resume here")
        if not self.settings.initial_prompt:
            self.initial_prompt_input.setPlaceholderText("Enter the initial prompt here")


class HtmlTextEdit(QTextEdit):
    def insertFromMimeData(self, source: QMimeData):
        if source.hasHtml():
            html_string = source.html()
            # Transform the HTML as needed
            markdown_string = md(html_string).strip()
            fragment = QTextDocumentFragment.fromPlainText(markdown_string)
            self.textCursor().insertFragment(fragment)
        else:
            super().insertFromMimeData(source)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cover Letter Generator")

        self.settings = Settings()

        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main layout
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # Tabs
        self.create_tabs()

        # Menu Bar
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)

        # File Menu
        self.file_menu = self.menu_bar.addMenu("File")
        self.open_action = self.file_menu.addAction("Open")
        self.open_action.triggered.connect(self.open_file_dialog)
        self.settings_action = self.file_menu.addAction("Settings")
        self.settings_action.triggered.connect(self.show_settings_dialog)
        self.exit_action = self.file_menu.addAction("Exit")
        self.exit_action.triggered.connect(self.close)

        # Help Menu
        self.help_menu = self.menu_bar.addMenu("Help")
        self.about_action = self.help_menu.addAction("About")
        self.about_action.triggered.connect(self.show_about_dialog)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Check settings on startup
        self.check_settings()

    def create_tabs(self):
        # Tab 1 - Paste Webpage
        self.tab1 = QWidget()
        self.tab1_layout = QVBoxLayout()
        self.tab1.setLayout(self.tab1_layout)

        self.html_editor = HtmlTextEdit()
        self.tab1_layout.addWidget(self.html_editor)

        # Button to generate cover letter
        self.generate_button = QPushButton("Generate Cover Letter")
        self.generate_button.clicked.connect(self.generate_cover_letter)
        self.tab1_layout.addWidget(self.generate_button)

        self.tab_widget.addTab(self.tab1, "Paste Webpage")

        # Tab 2 - Cover Letter
        self.tab2 = QWidget()
        self.tab2_layout = QVBoxLayout()
        self.tab2.setLayout(self.tab2_layout)

        self.cover_letter_display = QTextEdit()
        self.cover_letter_display.setReadOnly(True)
        self.cover_letter_display.setPlaceholderText("Your generated cover letter will appear here.")
        self.tab2_layout.addWidget(self.cover_letter_display)

        self.copy_button = QPushButton("Copy Cover Letter")
        self.copy_button.clicked.connect(self.copy_cover_letter_to_clipboard)
        self.tab2_layout.addWidget(self.copy_button)

        # Button to repaste webpage content
        self.repaste_button = QPushButton("Repaste Web Page")
        self.repaste_button.clicked.connect(self.go_to_paste_webpage)
        self.tab2_layout.addWidget(self.repaste_button)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.tab2_layout.addWidget(self.chat_display)

        self.chat_input = QLineEdit()
        self.tab2_layout.addWidget(self.chat_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.tab2_layout.addWidget(self.send_button)

        self.tab_widget.addTab(self.tab2, "Cover Letter")

        # Disable tab switching by clicking
        self.tab_widget.tabBar().setEnabled(False)

    def send_message(self):
        user_message = self.chat_input.text()
        if user_message:
            self.chat_display.append(f"You: {user_message}")
            self.chat_input.clear()
            
            # Generate a random reply
            responses = [
                "Hello! How can I help you today?",
                "I'm here to assist you.",
                "Can you please elaborate?",
                "Thank you for your message.",
                "I'm not sure I understand. Can you clarify?"
            ]
            random_reply = random.choice(responses)
            self.chat_display.append(f"Bot: {random_reply}")

    # Check that the API key and resume are non-empty every time the app starts.
    def check_settings(self):
        settings_dialog = SettingsDialog(self, self.settings)
        if not os.path.exists("settings.json") or not self.settings.api_key or not self.settings.resume:
            QMessageBox.information(self, "Settings Required", "Please ensure both API key and resume are configured.")
            settings_dialog.exec()
        else:
            settings_dialog.load_settings()

    def show_settings_dialog(self):
        settings_dialog = SettingsDialog(self, self.settings)
        if settings_dialog.exec() == QDialog.Accepted:
            self.status_bar.showMessage("Settings saved.")

    @Slot()
    def on_button_click(self):
        user_input = self.line_edit.text()
        self.label.setText(f"You entered: {user_input}")
        self.status_bar.showMessage("Button clicked!")

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")
        if file_name:
            self.status_bar.showMessage(f"Selected file: {file_name}")

    def show_about_dialog(self):
        QMessageBox.about(self, "About", "This is a PySide6 GUI application.")

    def generate_cover_letter(self):
        if self.html_editor.toPlainText().strip() == "":
            QMessageBox.warning(self, "Incomplete Action", "Please paste the webpage content before generating a cover letter.")
        else:
            self.tab_widget.setCurrentIndex(1)

    def go_to_paste_webpage(self):
        self.tab_widget.setCurrentIndex(0)

        # Modify the go_to_next_tab() method to include a check ensuring that the HTML editor in the first tab is not empty before allowing navigation to the next tab.
        if current_index == 0 and self.html_editor.toPlainText().strip() == "":
            QMessageBox.warning(self, "Incomplete Action", "Please paste the webpage content before proceeding.")
        elif current_index < self.tab_widget.count() - 1:
            self.tab_widget.setCurrentIndex(current_index + 1)

    def copy_cover_letter_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.cover_letter_display.toPlainText())
        self.status_bar.showMessage("Cover letter copied to clipboard.")

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
