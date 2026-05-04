import json
import os
import random
import re
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid


MODE_STUDY = "study"
MODE_PAGED_TEST = "paged_test"
MODE_FULL_TEST = "full_test"
APP_DIR = Path(__file__).resolve().parent
APP_NAME = "MCQ Tester"
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
ASSETS_DIR = RESOURCE_DIR / "assets"
APP_ICON_PATH = ASSETS_DIR / "mcq_tester_icon.png"


def get_saved_tests_dir() -> Path:
    if not getattr(sys, "frozen", False):
        return APP_DIR / "saved_tests"

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_NAME / "saved_tests"
    return Path.home() / APP_NAME / "saved_tests"


SAVED_TESTS_DIR = get_saved_tests_dir()


def load_app_icon() -> QIcon:
    if APP_ICON_PATH.exists():
        return QIcon(str(APP_ICON_PATH))
    return QIcon()


@dataclass
class AnswerOption:
    key: str
    text: str
    is_correct: bool


@dataclass
class PreparedQuestion:
    question: str
    options: list[AnswerOption]
    correct_key: str
    explanation: str


SAMPLE_QUESTIONS = [
    {
        "question": "What does etiology mean?",
        "correct_answer": "The cause or origin of a disease",
        "incorrect_answers": [
            "The treatment of a disease",
            "The symptoms of a disease",
            "The prognosis of a disease",
        ],
        "explanation": "Etiology refers to the cause or origin of a disease.",
    },
    {
        "question": "Which term best describes disease of the heart muscle?",
        "correct_answer": "Cardiomyopathy",
        "incorrect_answers": [
            "Arrhythmia",
            "Pericarditis",
            "Atherosclerosis",
        ],
        "explanation": "Cardiomyopathy means disease of the heart muscle.",
    },
    {
        "question": "Which condition involves reduced blood flow to tissue?",
        "correct_answer": "Ischemia",
        "incorrect_answers": [
            "Hypertrophy",
            "Necrosis",
            "Fibrosis",
        ],
        "explanation": "Ischemia means inadequate blood supply to tissue.",
    },
]


APP_STYLESHEET = """
QMainWindow, QWidget {
    background: #f4f6f8;
    color: #17202a;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 14px;
}
QTextEdit {
    background: #ffffff;
    border: 1px solid #d6dde8;
    border-radius: 8px;
    padding: 12px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 13px;
}
QPushButton {
    min-height: 34px;
    border: 1px solid #c8d1df;
    border-radius: 7px;
    padding: 6px 14px;
    background: #ffffff;
    font-weight: 600;
}
QPushButton:hover {
    background: #eef2f7;
}
QPushButton:disabled {
    color: #9aa4b2;
    background: #eef2f7;
}
QPushButton[buttonRole="primary"] {
    border-color: #2457c5;
    background: #2457c5;
    color: #ffffff;
}
QPushButton[buttonRole="primary"]:hover {
    background: #1c4296;
}
QPushButton[buttonRole="danger"] {
    border-color: #ffd5ce;
    background: #fff0ed;
    color: #b42318;
}
QPushButton[buttonRole="flagged"] {
    border-color: #b7791f;
    background: #fff7db;
    color: #8a5a00;
}
QPushButton[buttonRole="flagged"]:hover {
    background: #ffefb0;
}
QFrame[frameRole="panel"] {
    background: #ffffff;
    border: 1px solid #d6dde8;
    border-radius: 8px;
}
QFrame[frameRole="subtle"] {
    background: #eef2f7;
    border: 1px solid #d6dde8;
    border-radius: 8px;
}
QFrame[answerCard="true"] {
    background: #ffffff;
    border: 1px solid #d6dde8;
    border-radius: 8px;
}
QFrame[answerCard="true"]:hover {
    border-color: #9db4df;
    background: #f7faff;
}
QFrame[answerCard="true"][selected="true"] {
    border: 2px solid #2457c5;
    background: #f1f6ff;
}
QFrame[answerCard="true"][result="correct"] {
    border: 2px solid #16794c;
    background: #e8f6ef;
}
QFrame[answerCard="true"][result="incorrect"] {
    border: 2px solid #b42318;
    background: #fff0ed;
}
QLabel[answerRole="letter"] {
    min-width: 30px;
    max-width: 30px;
    min-height: 30px;
    max-height: 30px;
    border-radius: 15px;
    background: #eef2f7;
    color: #17202a;
    font-weight: 800;
    qproperty-alignment: AlignCenter;
}
QLabel[answerRole="letter"][selected="true"] {
    background: #2457c5;
    color: #ffffff;
}
QLabel[answerRole="letter"][result="correct"] {
    background: #16794c;
    color: #ffffff;
}
QLabel[answerRole="letter"][result="incorrect"] {
    background: #b42318;
    color: #ffffff;
}
QLabel[answerRole="selectedText"] {
    color: #2457c5;
    font-size: 12px;
    font-weight: 800;
}
QLabel[answerRole="selectedText"][result="correct"] {
    color: #16794c;
}
QLabel[answerRole="selectedText"][result="incorrect"] {
    color: #b42318;
}
QFrame[modeCard="true"] {
    background: #ffffff;
    border: 1px solid #d6dde8;
    border-radius: 8px;
}
QFrame[modeCard="true"]:hover {
    border-color: #9db4df;
    background: #f7faff;
}
QFrame[modeCard="true"][selected="true"] {
    border: 2px solid #2457c5;
    background: #f1f6ff;
}
QLabel[modeRole="title"] {
    color: #17202a;
    font-weight: 800;
}
QLabel[modeRole="description"] {
    color: #667085;
    font-size: 12px;
}
QLabel[modeRole="badge"] {
    color: #2457c5;
    font-size: 11px;
    font-weight: 800;
}
QLabel[modeRole="selectedBadge"] {
    color: #ffffff;
    background: #2457c5;
    border-radius: 9px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 800;
}
QFrame[feedback="correct"] {
    background: #e8f6ef;
    border: 1px solid #9bd4b8;
    border-radius: 8px;
}
QFrame[feedback="incorrect"] {
    background: #fff0ed;
    border: 1px solid #ffb4a8;
    border-radius: 8px;
}
QRadioButton, QCheckBox {
    spacing: 8px;
    background: transparent;
}
QLabel {
    background: transparent;
}
QWidget[transparent="true"] {
    background: transparent;
}
QScrollArea {
    border: 0;
    background: transparent;
}
QComboBox {
    min-height: 34px;
    border: 1px solid #c8d1df;
    border-radius: 7px;
    padding: 4px 38px 4px 14px;
    background: #ffffff;
    font-weight: 500;
}
QComboBox:hover {
    border-color: #9db4df;
}
QComboBox::drop-down {
    width: 30px;
    border: 0;
}
QComboBox QAbstractItemView {
    border: 1px solid #c8d1df;
    border-radius: 7px;
    background: #ffffff;
    selection-background-color: #f1f6ff;
    selection-color: #17202a;
}
QToolTip {
    color: #17202a;
    background-color: #ffffff;
    border: 1px solid #c8d1df;
    border-radius: 6px;
    padding: 6px 8px;
    font-weight: 600;
}
"""


class MCQWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        icon = load_app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)
        self.resize(1120, 780)
        self.setMinimumSize(880, 620)

        self.raw_questions: list[dict] = []
        self.questions: list[PreparedQuestion] = []
        self.current_index = 0
        self.answers: dict[int, str] = {}
        self.submitted_questions: set[int] = set()
        self.flagged_questions: set[int] = set()
        self.mode = MODE_STUDY
        self.randomize_questions = True
        self.randomize_options = True
        self.study_submit_button: QPushButton | None = None
        self.question_status_icons: dict[str, QIcon] = {}

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.build_setup_screen()

    def set_screen(self, widget: QWidget) -> None:
        while self.stack.count():
            old_widget = self.stack.widget(0)
            self.stack.removeWidget(old_widget)
            old_widget.deleteLater()

        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)

    def build_setup_screen(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(18)

        header = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(4)
        eyebrow = QLabel("DESKTOP PRACTICE APP")
        eyebrow.setStyleSheet("color: #2457c5; font-weight: 800; font-size: 12px;")
        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size: 30px; font-weight: 800;")
        title.setWordWrap(True)
        subtitle = QLabel("Practice and grade multiple choice questions")
        subtitle.setStyleSheet("color: #52627a; font-size: 15px;")
        subtitle.setWordWrap(True)
        header_text.addWidget(eyebrow)
        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header.addLayout(header_text, stretch=1)

        sample_button = self.make_button("Insert sample")
        sample_button.clicked.connect(self.insert_sample_json)
        load_button = self.make_button("Import JSON")
        load_button.clicked.connect(self.load_json_file)
        header.addWidget(sample_button)
        header.addWidget(load_button)
        root_layout.addLayout(header)

        body = QGridLayout()
        body.setHorizontalSpacing(18)
        body.setVerticalSpacing(18)
        root_layout.addLayout(body, stretch=1)

        settings_panel = self.make_panel()
        settings_panel_layout = QVBoxLayout(settings_panel)
        settings_panel_layout.setContentsMargins(0, 0, 0, 0)
        settings_panel_layout.setSpacing(0)

        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        settings_content = QWidget()
        settings_layout = QVBoxLayout(settings_content)
        settings_layout.setContentsMargins(18, 18, 18, 18)
        settings_layout.setSpacing(14)

        setup_title = QLabel("Test setup")
        setup_title.setStyleSheet("font-size: 18px; font-weight: 800;")
        setup_note = QLabel(
            "Paste JSON from your GPT workflow, then choose how feedback should work."
        )
        setup_note.setWordWrap(True)
        setup_note.setStyleSheet("color: #667085;")
        settings_layout.addWidget(setup_title)
        settings_layout.addWidget(setup_note)

        mode_heading = QLabel("Choose feedback style")
        mode_heading.setStyleSheet("font-weight: 800; margin-top: 8px;")
        settings_layout.addWidget(mode_heading)

        self.study_mode_radio = QRadioButton()
        self.paged_mode_radio = QRadioButton()
        self.full_mode_radio = QRadioButton()
        self.study_mode_radio.setChecked(True)

        self.mode_group = QButtonGroup(settings_panel)
        self.mode_group.addButton(self.study_mode_radio)
        self.mode_group.addButton(self.paged_mode_radio)
        self.mode_group.addButton(self.full_mode_radio)

        self.mode_cards: list[QFrame] = []
        settings_layout.addWidget(
            self.build_mode_card(
                self.study_mode_radio,
                "Study mode",
                "Submit an answer, immediately see if it was right, read the explanation, then continue.",
                "Best for learning",
            )
        )
        settings_layout.addWidget(
            self.build_mode_card(
                self.paged_mode_radio,
                "Test mode",
                "Move through one question at a time. Answers are saved, but grading waits until the end.",
                "Exam-style",
            )
        )
        settings_layout.addWidget(
            self.build_mode_card(
                self.full_mode_radio,
                "Full page test",
                "Answer every question in one scrollable view, then submit once for the final score.",
                "Fast review",
            )
        )
        self.mode_group.buttonToggled.connect(self.update_mode_card_states)
        self.update_mode_card_states()

        self.randomize_questions_checkbox = QCheckBox("Randomize question order")
        self.randomize_questions_checkbox.setChecked(True)
        self.randomize_options_checkbox = QCheckBox("Randomize answer choices")
        self.randomize_options_checkbox.setChecked(True)
        settings_layout.addSpacing(8)
        settings_layout.addWidget(self.randomize_questions_checkbox)
        settings_layout.addWidget(self.randomize_options_checkbox)

        settings_layout.addStretch(1)
        start_button = self.make_button("Start", primary=True)
        start_button.clicked.connect(self.start_test)
        clear_button = self.make_button("Clear")
        clear_button.clicked.connect(self.clear_json)
        actions = QHBoxLayout()
        actions.addWidget(start_button)
        actions.addWidget(clear_button)
        settings_layout.addLayout(actions)

        self.setup_status_label = QLabel("")
        self.setup_status_label.setWordWrap(True)
        self.setup_status_label.setStyleSheet("color: #b42318; font-weight: 700;")
        settings_layout.addWidget(self.setup_status_label)

        settings_scroll.setWidget(settings_content)
        settings_panel_layout.addWidget(settings_scroll)
        body.addWidget(settings_panel, 0, 0)

        json_panel = self.make_panel()
        json_layout = QVBoxLayout(json_panel)
        json_layout.setContentsMargins(18, 18, 18, 18)
        json_layout.setSpacing(12)

        json_header = QHBoxLayout()
        json_title = QLabel("Question JSON")
        json_title.setStyleSheet("font-size: 18px; font-weight: 800;")
        self.question_count_label = QLabel("0 questions loaded")
        self.question_count_label.setStyleSheet("color: #667085;")
        json_header.addWidget(json_title)
        json_header.addStretch(1)
        json_header.addWidget(self.question_count_label)
        json_layout.addLayout(json_header)

        json_actions = QHBoxLayout()
        paste_button = self.make_button("Paste clipboard")
        paste_button.clicked.connect(self.paste_from_clipboard)
        save_button = self.make_button("Save test")
        save_button.clicked.connect(self.save_current_test)
        load_saved_button = self.make_button("Load saved")
        load_saved_button.clicked.connect(self.load_saved_test)
        json_actions.addWidget(paste_button)
        json_actions.addStretch(1)
        json_actions.addWidget(save_button)
        json_actions.addWidget(load_saved_button)
        json_layout.addLayout(json_actions)

        self.json_editor = QTextEdit()
        self.json_editor.setPlaceholderText(
            json.dumps(SAMPLE_QUESTIONS[:1], indent=2)
        )
        self.json_editor.textChanged.connect(self.update_question_count)
        json_layout.addWidget(self.json_editor, stretch=1)

        body.addWidget(json_panel, 0, 1)
        body.setColumnStretch(0, 0)
        body.setColumnStretch(1, 1)

        self.set_screen(root)

    def make_button(self, text: str, *, primary: bool = False, danger: bool = False) -> QPushButton:
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            button.setProperty("buttonRole", "primary")
        if danger:
            button.setProperty("buttonRole", "danger")
        return button

    def make_panel(self, role: str = "panel") -> QFrame:
        panel = QFrame()
        panel.setProperty("frameRole", role)
        return panel

    def question_status_icon(self, status: str) -> QIcon:
        cached_icon = self.question_status_icons.get(status)
        if cached_icon is not None:
            return cached_icon

        colors = {
            "flagged": "#b7791f",
            "answered": "#16794c",
            "unanswered": "#9aa4b2",
        }
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(colors.get(status, colors["unanswered"])))
        painter.drawEllipse(3, 3, 10, 10)
        painter.end()

        icon = QIcon(pixmap)
        self.question_status_icons[status] = icon
        return icon

    def build_mode_card(
        self,
        radio: QRadioButton,
        title: str,
        description: str,
        badge: str,
    ) -> QFrame:
        card = QFrame()
        card.setProperty("modeCard", "true")
        card.setProperty("selected", "true" if radio.isChecked() else "false")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(10)

        radio.setCursor(Qt.CursorShape.PointingHandCursor)
        radio.setParent(card)
        radio.hide()

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setProperty("modeRole", "title")
        selected_label = QLabel("Selected")
        selected_label.setObjectName("selectedLabel")
        selected_label.setProperty("modeRole", "selectedBadge")
        selected_label.setVisible(radio.isChecked())
        title_row.addWidget(title_label)
        title_row.addStretch(1)
        title_row.addWidget(selected_label)
        text_layout.addLayout(title_row)

        badge_label = QLabel(badge)
        badge_label.setProperty("modeRole", "badge")
        text_layout.addWidget(badge_label)

        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setProperty("modeRole", "description")
        description_label.setMinimumHeight(44)
        description_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.MinimumExpanding,
        )
        text_layout.addWidget(description_label)

        card_layout.addLayout(text_layout, stretch=1)

        def select_card(event, target: QRadioButton = radio) -> None:
            target.setChecked(True)

        card.mousePressEvent = select_card
        title_label.mousePressEvent = select_card
        badge_label.mousePressEvent = select_card
        selected_label.mousePressEvent = select_card
        description_label.mousePressEvent = select_card
        self.mode_cards.append(card)
        return card

    def update_mode_card_states(self, *args: object) -> None:
        for card in getattr(self, "mode_cards", []):
            radio = card.findChild(QRadioButton)
            is_selected = bool(radio and radio.isChecked())
            card.setProperty("selected", "true" if is_selected else "false")
            selected_label = card.findChild(QLabel, "selectedLabel")
            if selected_label:
                selected_label.setVisible(is_selected)
            self.refresh_widget_style(card)

    @staticmethod
    def refresh_widget_style(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def insert_sample_json(self) -> None:
        self.json_editor.setPlainText(json.dumps(SAMPLE_QUESTIONS, indent=2))
        self.setup_status_label.clear()

    def clear_json(self) -> None:
        self.json_editor.clear()
        self.setup_status_label.clear()

    def paste_from_clipboard(self) -> None:
        clipboard_text = QApplication.clipboard().text().strip()
        if not clipboard_text:
            self.setup_status_label.setText("Clipboard does not contain text.")
            return

        self.json_editor.setPlainText(clipboard_text)
        self.setup_status_label.setText("Pasted clipboard text.")

    def clean_gpt_output(self) -> None:
        raw_text = self.json_editor.toPlainText()
        if not raw_text.strip():
            self.setup_status_label.setText("Paste GPT output before cleaning.")
            return

        try:
            questions, pretty_json, changed = self.parse_question_json(raw_text)
        except (json.JSONDecodeError, ValueError) as error:
            self.setup_status_label.setText(f"Could not clean output: {error}")
            return

        self.json_editor.setPlainText(pretty_json)
        label = "question" if len(questions) == 1 else "questions"
        suffix = " Cleaned common GPT formatting." if changed else " Already clean."
        self.setup_status_label.setText(f"Ready: {len(questions)} {label}.{suffix}")

    def validate_current_json(self) -> None:
        raw_text = self.json_editor.toPlainText()
        if not raw_text.strip():
            self.setup_status_label.setText("Paste JSON or import a JSON file first.")
            return

        try:
            questions, _, changed = self.parse_question_json(raw_text)
        except json.JSONDecodeError as error:
            self.setup_status_label.setText(f"Invalid JSON: {error}")
            return
        except ValueError as error:
            self.setup_status_label.setText(str(error))
            return

        label = "question" if len(questions) == 1 else "questions"
        clean_note = " It can be cleaned before starting." if changed else ""
        self.setup_status_label.setText(f"Valid test JSON: {len(questions)} {label}.{clean_note}")

    def save_current_test(self) -> None:
        raw_text = self.json_editor.toPlainText()
        if not raw_text.strip():
            self.setup_status_label.setText("Paste or import a test before saving.")
            return

        try:
            questions, pretty_json, _ = self.parse_question_json(raw_text)
        except (json.JSONDecodeError, ValueError) as error:
            self.setup_status_label.setText(f"Fix the JSON before saving: {error}")
            return

        SAVED_TESTS_DIR.mkdir(exist_ok=True)
        default_path = SAVED_TESTS_DIR / "mcq_test.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Test JSON",
            str(default_path),
            "JSON Files (*.json);;All Files (*.*)",
        )

        if not file_path:
            return

        save_path = Path(file_path)
        if save_path.suffix.lower() != ".json":
            save_path = save_path.with_suffix(".json")

        try:
            save_path.write_text(pretty_json, encoding="utf-8")
        except OSError as error:
            QMessageBox.critical(self, "Save Error", f"Could not save test:\n\n{error}")
            return

        label = "question" if len(questions) == 1 else "questions"
        self.setup_status_label.setText(f"Saved {len(questions)} {label} to {save_path.name}.")

    def load_json_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select JSON File",
            "",
            "JSON Files (*.json);;All Files (*.*)",
        )

        if not file_path:
            return

        try:
            self.json_editor.setPlainText(Path(file_path).read_text(encoding="utf-8"))
            self.setup_status_label.clear()
        except OSError as error:
            QMessageBox.critical(self, "File Error", f"Could not load file:\n\n{error}")

    def load_saved_test(self) -> None:
        SAVED_TESTS_DIR.mkdir(exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Saved Test",
            str(SAVED_TESTS_DIR),
            "JSON Files (*.json);;All Files (*.*)",
        )

        if not file_path:
            return

        try:
            self.json_editor.setPlainText(Path(file_path).read_text(encoding="utf-8"))
            self.setup_status_label.setText(f"Loaded saved test: {Path(file_path).name}.")
        except OSError as error:
            QMessageBox.critical(self, "File Error", f"Could not load saved test:\n\n{error}")

    def update_question_count(self) -> None:
        raw_text = self.json_editor.toPlainText().strip()
        if not raw_text:
            self.question_count_label.setText("0 questions loaded")
            return

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            try:
                parsed = self.normalize_question_payload(
                    json.loads(self.clean_json_text(raw_text))
                )
            except (json.JSONDecodeError, ValueError):
                self.question_count_label.setText("Invalid JSON")
                return

            if isinstance(parsed, list):
                label = "question" if len(parsed) == 1 else "questions"
                self.question_count_label.setText(f"{len(parsed)} {label} detected")
            else:
                self.question_count_label.setText("JSON must be a list")
            return

        try:
            parsed = self.normalize_question_payload(parsed)
        except ValueError:
            self.question_count_label.setText("JSON must be a list")
            return

        if isinstance(parsed, list):
            label = "question" if len(parsed) == 1 else "questions"
            self.question_count_label.setText(f"{len(parsed)} {label} loaded")
        else:
            self.question_count_label.setText("JSON must be a list")

    def start_test(self) -> None:
        raw_text = self.json_editor.toPlainText().strip()
        if not raw_text:
            self.setup_status_label.setText("Paste JSON or import a JSON file first.")
            return

        try:
            loaded_questions, pretty_json, changed = self.parse_question_json(raw_text)
        except json.JSONDecodeError as error:
            self.setup_status_label.setText(f"Invalid JSON: {error}")
            return
        except ValueError as error:
            self.setup_status_label.setText(str(error))
            return

        if changed:
            self.json_editor.setPlainText(pretty_json)
            self.setup_status_label.setText("Cleaned GPT output before starting.")

        self.raw_questions = loaded_questions
        self.mode = self.selected_mode()
        self.randomize_questions = self.randomize_questions_checkbox.isChecked()
        self.randomize_options = self.randomize_options_checkbox.isChecked()
        self.questions = self.prepare_questions(loaded_questions)
        self.current_index = 0
        self.answers = {}
        self.submitted_questions = set()
        self.flagged_questions = set()

        if self.mode == MODE_FULL_TEST:
            self.build_full_test_screen()
        else:
            self.build_question_screen()

    def parse_question_json(self, raw_text: str) -> tuple[list[dict], str, bool]:
        original = raw_text.strip()
        cleaned_text = self.clean_json_text(original)
        loaded = json.loads(cleaned_text)
        loaded_questions = self.normalize_question_payload(loaded)
        self.validate_question_data(loaded_questions)
        pretty_json = json.dumps(loaded_questions, indent=2)
        changed = pretty_json.strip() != original
        return loaded_questions, pretty_json, changed

    @staticmethod
    def clean_json_text(raw_text: str) -> str:
        text = raw_text.strip().lstrip("\ufeff")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2018", "'").replace("\u2019", "'")

        text = re.sub(r"^\s*```(?:json|JSON)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text).strip()

        first_array = text.find("[")
        first_object = text.find("{")
        starts = [index for index in (first_array, first_object) if index != -1]
        if starts:
            start = min(starts)
            opening = text[start]
            closing = "]" if opening == "[" else "}"
            end = text.rfind(closing)
            if end != -1 and end >= start:
                text = text[start:end + 1]

        text = re.sub(r",(\s*[}\]])", r"\1", text)
        return text.strip()

    @staticmethod
    def normalize_question_payload(payload: object) -> list[dict]:
        if isinstance(payload, list):
            return payload

        if isinstance(payload, dict):
            for key in ("questions", "items", "mcqs"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value

        raise ValueError(
            "The JSON must be a list of question objects, or an object with a questions list."
        )

    def selected_mode(self) -> str:
        if self.paged_mode_radio.isChecked():
            return MODE_PAGED_TEST
        if self.full_mode_radio.isChecked():
            return MODE_FULL_TEST
        return MODE_STUDY

    def validate_question_data(self, questions: object) -> None:
        if not isinstance(questions, list):
            raise ValueError("The JSON must be a list of question objects.")

        if not questions:
            raise ValueError("The JSON list is empty. Add at least one question.")

        for index, question in enumerate(questions, start=1):
            if not isinstance(question, dict):
                raise ValueError(f"Question {index} must be a JSON object.")

            if not self.is_non_empty_string(question.get("question")):
                raise ValueError(f"Question {index} is missing a usable question field.")

            if not self.is_non_empty_string(question.get("correct_answer")):
                raise ValueError(f"Question {index} is missing a usable correct_answer field.")

            incorrect_answers = question.get("incorrect_answers")
            if not isinstance(incorrect_answers, list):
                raise ValueError(f"Question {index} incorrect_answers must be a list.")

            if len(incorrect_answers) != 3:
                raise ValueError(f"Question {index} must have exactly three incorrect_answers.")

            for answer_index, answer in enumerate(incorrect_answers, start=1):
                if not self.is_non_empty_string(answer):
                    raise ValueError(
                        f"Question {index}, incorrect answer {answer_index}, is empty or invalid."
                    )

            all_answers = [question["correct_answer"], *incorrect_answers]
            normalized_answers = [answer.strip().lower() for answer in all_answers]
            if len(set(normalized_answers)) != 4:
                raise ValueError(f"Question {index} has duplicate answer choices.")

    def prepare_questions(self, questions: list[dict]) -> list[PreparedQuestion]:
        prepared: list[PreparedQuestion] = []

        for question in deepcopy(questions):
            combined_options = [
                AnswerOption("", question["correct_answer"].strip(), True),
                *[
                    AnswerOption("", answer.strip(), False)
                    for answer in question["incorrect_answers"]
                ],
            ]

            if self.randomize_options:
                random.shuffle(combined_options)

            letters = ["A", "B", "C", "D"]
            labeled_options: list[AnswerOption] = []
            correct_key = ""
            for key, option in zip(letters, combined_options, strict=True):
                labeled_option = AnswerOption(key, option.text, option.is_correct)
                labeled_options.append(labeled_option)
                if option.is_correct:
                    correct_key = key

            prepared.append(
                PreparedQuestion(
                    question=question["question"].strip(),
                    options=labeled_options,
                    correct_key=correct_key,
                    explanation=question.get("explanation", "").strip()
                    if isinstance(question.get("explanation"), str)
                    else "",
                )
            )

        if self.randomize_questions:
            random.shuffle(prepared)

        return prepared

    @staticmethod
    def is_non_empty_string(value: object) -> bool:
        return isinstance(value, str) and bool(value.strip())

    def build_question_screen(self) -> None:
        self.study_submit_button = None
        question = self.questions[self.current_index]
        is_study_mode = self.mode == MODE_STUDY
        is_submitted = self.current_index in self.submitted_questions

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header_text = QVBoxLayout()
        flag_text = "  FLAGGED" if self.current_index in self.flagged_questions else ""
        progress_label = QLabel(
            f"Question {self.current_index + 1} of {len(self.questions)}{flag_text}"
        )
        progress_label.setStyleSheet("color: #667085; font-weight: 800;")
        title = QLabel(question.question)
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 24px; font-weight: 800;")
        header_text.addWidget(progress_label)
        header_text.addWidget(title)
        header.addLayout(header_text, stretch=1)

        back_button = self.make_button("Back to setup")
        back_button.clicked.connect(self.confirm_back_to_setup)
        header.addWidget(back_button)
        layout.addLayout(header)

        panel = self.make_panel()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(10)
        self.current_question = question
        self.current_panel_layout = panel_layout
        self.current_action_layout = None

        self.current_answer_group = QButtonGroup(panel)
        self.current_answer_group.setExclusive(True)
        selected_answer = self.answers.get(self.current_index, "")

        for option in question.options:
            result_state = ""
            status_text = None
            if is_study_mode and is_submitted:
                if option.is_correct:
                    result_state = "correct"
                    status_text = "Correct" if selected_answer == option.key else "Correct answer"
                elif selected_answer == option.key:
                    result_state = "incorrect"
                    status_text = "Your answer"

            row, radio = self.build_answer_row(
                option.key,
                option.text,
                selected_answer == option.key,
                not (is_study_mode and is_submitted),
                result_state=result_state,
                status_text=status_text,
            )
            radio.setProperty("answerKey", option.key)
            radio.toggled.connect(self.handle_current_answer_changed)
            self.current_answer_group.addButton(radio)
            panel_layout.addWidget(row)

        self.current_answer_group.buttonToggled.connect(
            lambda *_: self.update_answer_card_states(self.current_answer_group)
        )
        self.update_answer_card_states(self.current_answer_group)

        if is_study_mode and is_submitted:
            feedback = self.build_feedback_panel(question)
            panel_layout.addWidget(feedback)

        layout.addWidget(panel)

        actions = QHBoxLayout()
        self.current_action_layout = actions
        if is_study_mode:
            previous_button = self.make_button("Previous")
            previous_button.setEnabled(self.current_index > 0)
            previous_button.clicked.connect(self.go_to_previous_question)
            actions.addWidget(previous_button)

        if is_study_mode:
            if is_submitted:
                if self.current_index == len(self.questions) - 1:
                    primary_button = self.make_button("View summary", primary=True)
                    primary_button.clicked.connect(self.show_results)
                else:
                    primary_button = self.make_button("Next", primary=True)
                    primary_button.clicked.connect(self.go_to_next_question)
            else:
                primary_button = self.make_button("Submit answer", primary=True)
                primary_button.setEnabled(bool(selected_answer))
                primary_button.clicked.connect(self.submit_study_answer)
            self.study_submit_button = primary_button
            actions.addWidget(primary_button)
        else:
            actions.addStretch(1)

        if is_study_mode:
            actions.addStretch(1)
            layout.addLayout(actions)

        if self.mode == MODE_PAGED_TEST:
            nav = self.build_question_nav()
            layout.addWidget(nav)

        layout.addStretch(1)
        self.set_screen(root)

    def build_feedback_panel(self, question: PreparedQuestion) -> QFrame:
        selected_answer = self.answers.get(self.current_index, "")
        is_correct = selected_answer == question.correct_key

        feedback = QFrame()
        feedback.setProperty("feedback", "correct" if is_correct else "incorrect")
        layout = QVBoxLayout(feedback)
        layout.setContentsMargins(14, 12, 14, 12)

        result = QLabel("Correct" if is_correct else "Incorrect")
        result.setStyleSheet("font-weight: 800;")
        result.setWordWrap(True)
        layout.addWidget(result)

        if question.explanation:
            explanation = QLabel(question.explanation)
            explanation.setWordWrap(True)
            layout.addWidget(explanation)

        return feedback

    def handle_current_answer_changed(self, checked: bool) -> None:
        if not checked:
            return

        button = self.sender()
        if not isinstance(button, QRadioButton):
            return

        self.answers[self.current_index] = button.property("answerKey")
        self.update_answer_card_states(self.current_answer_group)

        if self.study_submit_button is not None and isValid(self.study_submit_button):
            self.study_submit_button.setEnabled(True)

    def submit_study_answer(self) -> None:
        if self.current_index not in self.answers:
            return

        self.submitted_questions.add(self.current_index)
        self.apply_study_submission_state()

    def apply_study_submission_state(self) -> None:
        question = self.questions[self.current_index]
        selected_answer = self.answers.get(self.current_index, "")

        for button in self.current_answer_group.buttons():
            row = button.parentWidget()
            if not isinstance(row, QFrame):
                continue

            answer_key = button.property("answerKey")
            result_state = ""
            status_text = None
            if answer_key == question.correct_key:
                result_state = "correct"
                status_text = "Correct" if answer_key == selected_answer else "Correct answer"
            elif answer_key == selected_answer:
                result_state = "incorrect"
                status_text = "Your answer"

            button.setEnabled(False)
            row.setCursor(Qt.CursorShape.ArrowCursor)
            row.mousePressEvent = lambda event: None
            row.setProperty("result", result_state)
            self.refresh_widget_style(row)

            letter_label = row.findChild(QLabel, "answerLetter")
            if letter_label:
                letter_label.mousePressEvent = lambda event: None
                letter_label.setProperty("result", result_state)
                self.refresh_widget_style(letter_label)

            selected_label = row.findChild(QLabel, "answerSelectedText")
            if selected_label:
                selected_label.mousePressEvent = lambda event: None
                selected_label.setText(status_text or "Selected")
                selected_label.setProperty("result", result_state)
                selected_label.setVisible(bool(result_state))
                self.refresh_widget_style(selected_label)

        self.update_answer_card_states(self.current_answer_group)

        if hasattr(self, "current_panel_layout") and self.current_panel_layout is not None:
            self.current_panel_layout.addWidget(self.build_feedback_panel(question))

        if self.study_submit_button is not None and isValid(self.study_submit_button):
            if self.current_action_layout is not None:
                self.current_action_layout.removeWidget(self.study_submit_button)
            self.study_submit_button.setParent(None)
            self.study_submit_button.deleteLater()
            self.study_submit_button = None

        if self.current_action_layout is not None:
            if self.current_index == len(self.questions) - 1:
                primary_button = self.make_button("View summary", primary=True)
                primary_button.clicked.connect(self.show_results)
            else:
                primary_button = self.make_button("Next", primary=True)
                primary_button.clicked.connect(self.go_to_next_question)
            self.current_action_layout.insertWidget(1, primary_button)

    def go_to_previous_question(self) -> None:
        if self.current_index > 0:
            self.current_index -= 1
            self.build_question_screen()

    def go_to_next_question(self) -> None:
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self.build_question_screen()

    def toggle_current_question_flag(self) -> None:
        if self.current_index in self.flagged_questions:
            self.flagged_questions.remove(self.current_index)
        else:
            self.flagged_questions.add(self.current_index)
        self.build_question_screen()

    def build_question_nav(self) -> QFrame:
        nav_panel = self.make_panel("subtle")
        nav_layout = QHBoxLayout(nav_panel)
        nav_layout.setContentsMargins(12, 10, 12, 10)
        nav_layout.setSpacing(10)

        previous_button = self.make_button("Previous")
        previous_button.setEnabled(self.current_index > 0)
        previous_button.clicked.connect(
            lambda: self.jump_to_question(max(0, self.current_index - 1))
        )
        nav_layout.addWidget(previous_button)

        self.question_jump_combo = QComboBox()
        digit_count = max(2, len(str(len(self.questions))))
        self.question_jump_combo.setMinimumWidth(104 + (digit_count * 12))
        self.question_jump_combo.setIconSize(QSize(10, 10))
        for index in range(len(self.questions)):
            status = self.question_dropdown_status(index)
            self.question_jump_combo.addItem(
                self.question_status_icon(status),
                str(index + 1),
                index,
            )
            self.question_jump_combo.setItemData(
                index,
                status.capitalize(),
                Qt.ItemDataRole.ToolTipRole,
            )
        self.question_jump_combo.setCurrentIndex(self.current_index)
        self.question_jump_combo.currentIndexChanged.connect(self.handle_question_jump_changed)
        nav_layout.addWidget(self.question_jump_combo)

        next_button = self.make_button("Next")
        next_button.setEnabled(self.current_index < len(self.questions) - 1)
        next_button.clicked.connect(
            lambda: self.jump_to_question(
                min(len(self.questions) - 1, self.current_index + 1)
            )
        )
        nav_layout.addWidget(next_button)

        flag_button = self.make_button(
            "Flagged" if self.current_index in self.flagged_questions else "Flag"
        )
        if self.current_index in self.flagged_questions:
            flag_button.setProperty("buttonRole", "flagged")
            self.refresh_widget_style(flag_button)
        flag_button.clicked.connect(self.toggle_current_question_flag)
        nav_layout.addWidget(flag_button)

        submit_button = self.make_button("Submit test", primary=True)
        submit_button.clicked.connect(self.submit_deferred_test)
        nav_layout.addWidget(submit_button)

        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.build_dropdown_legend())
        nav_layout.addStretch(1)

        return nav_panel

    def question_dropdown_status(self, index: int) -> str:
        if index in self.flagged_questions:
            return "flagged"
        if index in self.answers:
            return "answered"
        return "unanswered"

    def build_dropdown_legend(self) -> QWidget:
        legend = QWidget()
        legend.setProperty("transparent", "true")
        legend.setToolTip(self.build_question_status_tooltip())
        legend.setToolTipDuration(10000)
        layout = QHBoxLayout(legend)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        for label, color in (
            ("Flagged", "#b7791f"),
            ("Answered", "#16794c"),
            ("Unanswered", "#9aa4b2"),
        ):
            layout.addWidget(self.build_legend_item(label, color))

        return legend

    def build_legend_item(self, text: str, color: str) -> QWidget:
        item = QWidget()
        item.setProperty("transparent", "true")
        item.setToolTip(self.build_question_status_tooltip())
        item.setToolTipDuration(10000)
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background: {color}; border-radius: 5px;")
        dot.setToolTip(self.build_question_status_tooltip())
        dot.setToolTipDuration(10000)
        label = QLabel(text)
        label.setStyleSheet("color: #667085; font-size: 12px; font-weight: 700;")
        label.setToolTip(self.build_question_status_tooltip())
        label.setToolTipDuration(10000)
        layout.addWidget(dot)
        layout.addWidget(label)
        return item

    def build_question_status_tooltip(self) -> str:
        flagged = [index + 1 for index in sorted(self.flagged_questions)]
        unanswered = [
            index + 1
            for index in range(len(self.questions))
            if index not in self.answers
        ]
        return "\n".join(
            (
                self.question_number_tooltip("Flagged questions", flagged),
                self.question_number_tooltip("Unanswered questions", unanswered),
            )
        )

    def handle_question_jump_changed(self, combo_index: int) -> None:
        target = self.question_jump_combo.itemData(combo_index)
        if isinstance(target, int) and target != self.current_index:
            self.jump_to_question(target)

    def jump_to_question(self, index: int) -> None:
        self.current_index = index
        self.build_question_screen()

    def build_full_test_screen(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header_text = QVBoxLayout()
        progress = QLabel(f"{len(self.questions)} questions")
        progress.setStyleSheet("color: #667085; font-weight: 800;")
        title = QLabel("Full page test")
        title.setStyleSheet("font-size: 24px; font-weight: 800;")
        header_text.addWidget(progress)
        header_text.addWidget(title)
        header.addLayout(header_text, stretch=1)
        back_button = self.make_button("Back to setup")
        back_button.clicked.connect(self.confirm_back_to_setup)
        header.addWidget(back_button)
        layout.addLayout(header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(14)
        self.full_answer_groups: list[QButtonGroup] = []
        self.full_flag_buttons: dict[int, QPushButton] = {}

        for index, question in enumerate(self.questions):
            card = self.make_panel()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)
            card_layout.setSpacing(10)

            question_header = QHBoxLayout()
            question_label = QLabel(f"{index + 1}. {question.question}")
            question_label.setWordWrap(True)
            question_label.setStyleSheet("font-weight: 800; font-size: 16px;")
            question_header.addWidget(question_label, stretch=1)

            flag_button = self.make_button(
                "Flagged" if index in self.flagged_questions else "Flag"
            )
            if index in self.flagged_questions:
                flag_button.setProperty("buttonRole", "flagged")
                self.refresh_widget_style(flag_button)
            flag_button.clicked.connect(
                lambda checked=False, question_index=index, button=flag_button:
                self.toggle_full_question_flag(question_index, button)
            )
            self.full_flag_buttons[index] = flag_button
            question_header.addWidget(flag_button)
            card_layout.addLayout(question_header)

            group = QButtonGroup(card)
            group.setExclusive(True)
            self.full_answer_groups.append(group)

            for option in question.options:
                row, radio = self.build_answer_row(
                    option.key,
                    option.text,
                    self.answers.get(index) == option.key,
                    True,
                )
                radio.setProperty("answerKey", option.key)
                radio.toggled.connect(
                    lambda checked=False, question_index=index, key=option.key:
                    self.handle_full_answer_changed(checked, question_index, key)
                )
                group.addButton(radio)
                card_layout.addWidget(row)

            group.buttonToggled.connect(
                lambda *_args, answer_group=group:
                self.update_answer_card_states(answer_group)
            )
            self.update_answer_card_states(group)
            scroll_layout.addWidget(card)

        scroll_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area, stretch=1)

        actions = QHBoxLayout()
        submit_button = self.make_button("Submit test", primary=True)
        submit_button.clicked.connect(self.submit_deferred_test)
        actions.addWidget(submit_button)
        actions.addSpacing(12)

        self.full_unanswered_label = QLabel()
        self.full_unanswered_label.setStyleSheet("font-weight: 800; color: #667085;")
        self.full_unanswered_label.setToolTipDuration(10000)
        actions.addWidget(self.full_unanswered_label)

        self.full_flagged_label = QLabel()
        self.full_flagged_label.setStyleSheet("font-weight: 800; color: #8a5a00;")
        self.full_flagged_label.setToolTipDuration(10000)
        actions.addWidget(self.full_flagged_label)
        actions.addStretch(1)
        layout.addLayout(actions)
        self.update_full_test_counters()

        self.set_screen(root)

    def handle_full_answer_changed(self, checked: bool, question_index: int, key: str) -> None:
        if checked:
            self.answers[question_index] = key
            self.update_full_test_counters()

    def toggle_full_question_flag(
        self,
        question_index: int,
        button: QPushButton | None = None,
    ) -> None:
        if question_index in self.flagged_questions:
            self.flagged_questions.remove(question_index)
            if button is not None:
                button.setText("Flag")
                button.setProperty("buttonRole", "")
        else:
            self.flagged_questions.add(question_index)
            if button is not None:
                button.setText("Flagged")
                button.setProperty("buttonRole", "flagged")

        if button is not None:
            self.refresh_widget_style(button)
        self.update_full_test_counters()

    def update_full_test_counters(self) -> None:
        unanswered_questions = [
            index + 1
            for index in range(len(self.questions))
            if index not in self.answers
        ]
        flagged_questions = [index + 1 for index in sorted(self.flagged_questions)]

        if hasattr(self, "full_unanswered_label") and isValid(self.full_unanswered_label):
            count = len(unanswered_questions)
            self.full_unanswered_label.setText(f"Unanswered: {count}")
            self.full_unanswered_label.setToolTip(
                self.question_number_tooltip("Unanswered questions", unanswered_questions)
            )

        if hasattr(self, "full_flagged_label") and isValid(self.full_flagged_label):
            count = len(flagged_questions)
            self.full_flagged_label.setText(f"Flagged: {count}")
            self.full_flagged_label.setToolTip(
                self.question_number_tooltip("Flagged questions", flagged_questions)
            )

    @staticmethod
    def question_number_tooltip(title: str, question_numbers: list[int]) -> str:
        if not question_numbers:
            return f"{title}: none"
        return f"{title}: {', '.join(str(number) for number in question_numbers)}"

    def update_answer_card_states(self, group: QButtonGroup) -> None:
        for button in group.buttons():
            row = button.parentWidget()
            if not isinstance(row, QFrame):
                continue

            is_selected = button.isChecked()
            result_state = row.property("result") or ""
            row.setProperty("selected", "true" if is_selected else "false")

            letter_label = row.findChild(QLabel, "answerLetter")
            if letter_label:
                letter_label.setProperty("selected", "true" if is_selected else "false")
                self.refresh_widget_style(letter_label)

            selected_label = row.findChild(QLabel, "answerSelectedText")
            if selected_label:
                selected_label.setVisible(is_selected or bool(result_state))

            self.refresh_widget_style(row)

    def build_answer_row(
        self,
        key: str,
        text: str,
        checked: bool,
        enabled: bool,
        *,
        result_state: str = "",
        status_text: str | None = None,
    ) -> tuple[QFrame, QRadioButton]:
        row = QFrame()
        row.setProperty("answerCard", "true")
        row.setProperty("selected", "true" if checked else "false")
        row.setProperty("result", result_state)
        row.setCursor(
            Qt.CursorShape.PointingHandCursor
            if enabled
            else Qt.CursorShape.ArrowCursor
        )
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        radio = QRadioButton()
        radio.setChecked(checked)
        radio.setEnabled(enabled)
        radio.hide()

        letter_label = QLabel(key)
        letter_label.setObjectName("answerLetter")
        letter_label.setProperty("answerRole", "letter")
        letter_label.setProperty("selected", "true" if checked else "false")
        letter_label.setProperty("result", result_state)
        layout.addWidget(letter_label, alignment=Qt.AlignmentFlag.AlignTop)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(label, stretch=1)

        selected_label = QLabel(status_text or "Selected")
        selected_label.setObjectName("answerSelectedText")
        selected_label.setProperty("answerRole", "selectedText")
        selected_label.setProperty("result", result_state)
        selected_label.setVisible(checked or bool(result_state))
        layout.addWidget(selected_label, alignment=Qt.AlignmentFlag.AlignTop)

        radio.setParent(row)

        if enabled:
            def select_answer(event, target: QRadioButton = radio) -> None:
                target.setChecked(True)

            row.mousePressEvent = select_answer
            label.mousePressEvent = select_answer
            letter_label.mousePressEvent = select_answer
            selected_label.mousePressEvent = select_answer

        return row, radio

    def submit_deferred_test(self) -> None:
        unanswered = len(self.questions) - len(self.answers)
        if unanswered:
            response = QMessageBox.question(
                self,
                "Unanswered Questions",
                f"You have {unanswered} unanswered question(s).\n\nSubmit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if response != QMessageBox.StandardButton.Yes:
                return

        if self.mode in (MODE_PAGED_TEST, MODE_FULL_TEST) and self.flagged_questions:
            flagged_numbers = ", ".join(
                str(index + 1) for index in sorted(self.flagged_questions)
            )
            response = QMessageBox.question(
                self,
                "Flagged Questions",
                f"You still have flagged question(s): {flagged_numbers}.\n\nSubmit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if response != QMessageBox.StandardButton.Yes:
                return

        self.show_results()

    def show_results(self) -> None:
        score = sum(
            1
            for index, question in enumerate(self.questions)
            if self.answers.get(index) == question.correct_key
        )
        total = len(self.questions)
        percent = round((score / total) * 100, 1)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header_text = QVBoxLayout()
        summary_label = QLabel("Summary")
        summary_label.setStyleSheet("color: #667085; font-weight: 800;")
        score_label = QLabel(f"Score: {score}/{total}")
        score_label.setStyleSheet("font-size: 26px; font-weight: 800;")
        header_text.addWidget(summary_label)
        header_text.addWidget(score_label)
        header.addLayout(header_text, stretch=1)

        back_button = self.make_button("Back to setup")
        back_button.clicked.connect(self.build_setup_screen)
        header.addWidget(back_button)
        layout.addLayout(header)

        stats = QHBoxLayout()
        stats.addWidget(self.build_stat_panel("Percent", f"{percent}%"))
        stats.addWidget(self.build_stat_panel("Correct", str(score)))
        stats.addWidget(self.build_stat_panel("Incorrect", str(total - score)))
        layout.addLayout(stats)

        actions = QHBoxLayout()
        retake_button = self.make_button("Retake same order")
        retake_button.clicked.connect(self.retake_same_test)
        randomize_button = self.make_button("Randomize again")
        randomize_button.clicked.connect(self.randomize_again)
        actions.addWidget(retake_button)
        actions.addWidget(randomize_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(14)

        for index, question in enumerate(self.questions):
            scroll_layout.addWidget(self.build_review_card(index, question))

        scroll_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area, stretch=1)

        self.set_screen(root)

    def build_stat_panel(self, label: str, value: str) -> QFrame:
        panel = self.make_panel("subtle")
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        name = QLabel(label)
        name.setStyleSheet("color: #667085; font-weight: 800;")
        number = QLabel(value)
        number.setStyleSheet("font-size: 24px; font-weight: 800;")
        layout.addWidget(name)
        layout.addWidget(number)
        return panel

    def build_review_card(self, index: int, question: PreparedQuestion) -> QFrame:
        selected_key = self.answers.get(index, "")
        is_correct = selected_key == question.correct_key

        card = self.make_panel()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        result = QLabel("Correct" if is_correct else "Incorrect")
        result.setStyleSheet(
            "font-weight: 800; color: #16794c;"
            if is_correct
            else "font-weight: 800; color: #b42318;"
        )
        layout.addWidget(result)

        prompt = QLabel(f"{index + 1}. {question.question}")
        prompt.setWordWrap(True)
        prompt.setStyleSheet("font-weight: 800;")
        layout.addWidget(prompt)

        for option in question.options:
            markers = []
            if option.key == question.correct_key:
                markers.append("correct answer")
            if option.key == selected_key:
                markers.append("your answer")

            text = f"{option.key}. {option.text}"
            if markers:
                text += f" ({', '.join(markers)})"

            option_label = QLabel(text)
            option_label.setWordWrap(True)
            if option.key == question.correct_key:
                option_label.setStyleSheet(
                    "background: #e8f6ef; border-radius: 6px; padding: 6px;"
                )
            elif option.key == selected_key and not is_correct:
                option_label.setStyleSheet(
                    "background: #fff0ed; border-radius: 6px; padding: 6px;"
                )
            else:
                option_label.setStyleSheet("padding: 6px;")
            layout.addWidget(option_label)

        if not selected_key:
            missing = QLabel("You did not answer this question.")
            missing.setWordWrap(True)
            missing.setStyleSheet("color: #667085;")
            layout.addWidget(missing)

        if question.explanation:
            explanation = QLabel(question.explanation)
            explanation.setWordWrap(True)
            layout.addWidget(explanation)

        return card

    def retake_same_test(self) -> None:
        self.current_index = 0
        self.answers = {}
        self.submitted_questions = set()
        self.flagged_questions = set()
        if self.mode == MODE_FULL_TEST:
            self.build_full_test_screen()
        else:
            self.build_question_screen()

    def randomize_again(self) -> None:
        self.questions = self.prepare_questions(self.raw_questions)
        self.current_index = 0
        self.answers = {}
        self.submitted_questions = set()
        self.flagged_questions = set()
        if self.mode == MODE_FULL_TEST:
            self.build_full_test_screen()
        else:
            self.build_question_screen()

    def confirm_back_to_setup(self) -> None:
        response = QMessageBox.question(
            self,
            "Return to Setup",
            "Return to setup? Current test progress will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if response == QMessageBox.StandardButton.Yes:
            self.build_setup_screen()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    if hasattr(app, "setApplicationDisplayName"):
        app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    icon = load_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    app.setStyleSheet(APP_STYLESHEET)
    window = MCQWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
