# PySide6 기반 마크다운 에디터
import sys
import os
import markdown2
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QWidget,
    QVBoxLayout,
    QStatusBar,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class MarkdownEditor(QMainWindow):
    # 상수 정의
    DEFAULT_TITLE = "Markdown Editor (PySide6)"
    DEFAULT_WIDTH = 1000
    DEFAULT_HEIGHT = 800
    SAVE_DIR_NAME = "MarkdownFiles"

    # 메뉴 텍스트 및 단축키
    MENU_FILE = "파일"
    MENU_NEW_FILE = "새 파일"
    MENU_OPEN = "열기"
    MENU_SAVE = "저장"
    MENU_SAVE_AS = "다른 이름으로 저장"
    MENU_EXIT = "종료"
    MENU_EDIT = "편집"
    MENU_UNDO = "실행 취소"
    MENU_REDO = "다시 실행"
    MENU_MARKDOWN = "마크다운"
    MENU_BOLD = "굵게"
    MENU_ITALIC = "기울임"
    MENU_STRIKETHROUGH = "취소선"
    MENU_CODE = "코드"
    MENU_HEADER1 = "헤더 1"
    MENU_HEADER2 = "헤더 2"
    MENU_HEADER3 = "헤더 3"
    MENU_UNORDERED_LIST = "순서 없는 목록"
    MENU_VIEW = "보기"
    MENU_TOGGLE_VIEW = "편집/미리보기 전환"
    MENU_TOGGLE_THEME = "테마 전환"
    MENU_HELP = "도움말"
    MENU_ABOUT = "정보"

    SHORTCUT_NEW_FILE = "Ctrl+N"
    SHORTCUT_OPEN = "Ctrl+O"
    SHORTCUT_SAVE = "Ctrl+S"
    SHORTCUT_SAVE_AS = "Ctrl+Shift+S"
    SHORTCUT_UNDO = "Ctrl+Z"
    SHORTCUT_REDO = "Ctrl+Y"
    SHORTCUT_BOLD = "Ctrl+B"
    SHORTCUT_ITALIC = "Ctrl+I"
    SHORTCUT_STRIKETHROUGH = "Ctrl+Shift+S"
    SHORTCUT_CODE = "Ctrl+Shift+C"
    SHORTCUT_HEADER1 = "Ctrl+1"
    SHORTCUT_HEADER2 = "Ctrl+2"
    SHORTCUT_HEADER3 = "Ctrl+3"
    SHORTCUT_UNORDERED_LIST = "Ctrl+L"
    SHORTCUT_TOGGLE_VIEW = "F5"
    SHORTCUT_TOGGLE_THEME = "F6"

    # 상태바 메시지
    STATUS_READY = "준비"
    STATUS_PREVIEW_MODE = "미리보기 모드"
    STATUS_EDIT_MODE = "편집 모드"
    STATUS_FILE_OPENED = "파일 열기: {}"
    STATUS_FILE_SAVED = "파일 저장됨: {}"
    STATUS_THEME_TOGGLED = "테마 전환: {}"

    # 메시지 박스 텍스트
    MSG_UNSAVED_CHANGES_TITLE = "저장 확인"
    MSG_UNSAVED_CHANGES_TEXT = "저장되지 않은 변경사항이 있습니다. 저장하시겠습니까?"
    MSG_ERROR_FILE_NOT_FOUND = "파일을 찾을 수 없습니다."
    MSG_ERROR_PERMISSION_DENIED = "파일에 접근/쓸 권한이 없습니다."
    MSG_ERROR_IO = "파일 입출력 오류가 발생했습니다: {}"
    MSG_ERROR_UNKNOWN = "알 수 없는 오류가 발생했습니다: {}"
    MSG_ABOUT_TITLE = "Markdown Editor"
    MSG_ABOUT_TEXT = "간단한 마크다운 편집기 (PySide6)\n\n버전: 2.0"

    def __init__(self, file_to_open=None):
        super().__init__()
        self.base_title = self.DEFAULT_TITLE
        self.setWindowTitle(self.base_title)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        self.is_dark = False
        self.view_mode = "editor"  # editor or preview
        self.current_file_path = None
        self.unsaved_changes = False
        # ...existing code...
        self.save_directory = os.path.join(
            os.path.expanduser("~"), "Documents", "MarkdownFiles"
        )
        os.makedirs(self.save_directory, exist_ok=True)

        self.init_ui()
        if file_to_open:
            self.open_file(file_to_open)

    def init_ui(self):
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Splitter for editor/preview
        self.splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.splitter)

        # Editor
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.editor.textChanged.connect(self.on_modified)
        self.splitter.addWidget(self.editor)

        # Preview
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFont(QFont("Arial", 12))
        self.splitter.addWidget(self.preview)
        self.preview.hide()

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(self.STATUS_READY)

        # Menu
        self.create_menu()
        # Shortcuts
        self.create_shortcuts()

    def create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu(self.MENU_FILE)
        file_menu.addAction(self.MENU_NEW_FILE, self.new_document, self.SHORTCUT_NEW_FILE)
        file_menu.addAction(self.MENU_OPEN, self.open_document, self.SHORTCUT_OPEN)
        file_menu.addAction(self.MENU_SAVE, self.save_document, self.SHORTCUT_SAVE)
        file_menu.addAction(
            self.MENU_SAVE_AS, self.save_document_as, self.SHORTCUT_SAVE_AS
        )
        file_menu.addSeparator()
        file_menu.addAction(self.MENU_EXIT, self.close)

        edit_menu = menubar.addMenu(self.MENU_EDIT)
        edit_menu.addAction(self.MENU_UNDO, self.editor.undo, self.SHORTCUT_UNDO)
        edit_menu.addAction(self.MENU_REDO, self.editor.redo, self.SHORTCUT_REDO)

        markdown_menu = menubar.addMenu(self.MENU_MARKDOWN)
        markdown_menu.addAction(
            self.MENU_BOLD, lambda: self.apply_markdown("bold"), self.SHORTCUT_BOLD
        )
        markdown_menu.addAction(
            self.MENU_ITALIC, lambda: self.apply_markdown("italic"), self.SHORTCUT_ITALIC
        )
        markdown_menu.addAction(
            self.MENU_STRIKETHROUGH, lambda: self.apply_markdown("strike"), self.SHORTCUT_STRIKETHROUGH
        )
        markdown_menu.addAction(
            self.MENU_CODE, lambda: self.apply_markdown("code"), self.SHORTCUT_CODE
        )
        markdown_menu.addSeparator()
        markdown_menu.addAction(self.MENU_HEADER1, lambda: self.apply_markdown("h1"), self.SHORTCUT_HEADER1)
        markdown_menu.addAction(self.MENU_HEADER2, lambda: self.apply_markdown("h2"), self.SHORTCUT_HEADER2)
        markdown_menu.addAction(self.MENU_HEADER3, lambda: self.apply_markdown("h3"), self.SHORTCUT_HEADER3)
        markdown_menu.addSeparator()
        markdown_menu.addAction(
            self.MENU_UNORDERED_LIST, lambda: self.apply_markdown("ul"), self.SHORTCUT_UNORDERED_LIST
        )

        view_menu = menubar.addMenu(self.MENU_VIEW)
        view_menu.addAction(self.MENU_TOGGLE_VIEW, self.toggle_view, self.SHORTCUT_TOGGLE_VIEW)
        view_menu.addAction(self.MENU_TOGGLE_THEME, self.toggle_theme, self.SHORTCUT_TOGGLE_THEME)

        help_menu = menubar.addMenu(self.MENU_HELP)
        help_menu.addAction(self.MENU_ABOUT, self.show_about)

    # 툴바 제거됨

    def create_shortcuts(self):
        self.editor.setTabChangesFocus(False)

    def apply_markdown(self, style):
        cursor = self.editor.textCursor()
        selected_text = cursor.selectedText()
        if not selected_text:
            return

        markdown_styles = {
            "bold": lambda text: f"**{text}**",
            "italic": lambda text: f"*{text}*",
            "strike": lambda text: f"~~{text}~~",
            "code": lambda text: f"`{text}`",
            "ul": lambda text: f"- {text}",
            "h1": lambda text: f"# {text}",
            "h2": lambda text: f"## {text}",
            "h3": lambda text: f"### {text}",
        }

        new_text_func = markdown_styles.get(style)
        if new_text_func is None:
            return
        new_text = new_text_func(selected_text)

        cursor.insertText(new_text)
        self.editor.setTextCursor(cursor)
        self.unsaved_changes = True
        self.setWindowTitle(self.windowTitle() + " *")

    def toggle_view(self):
        if self.view_mode == "editor":
            self.view_mode = "preview"
            self.editor.hide()
            self.update_preview()
            self.preview.show()
            self.status.showMessage("미리보기 모드")
        else:
            self.view_mode = "editor"
            self.preview.hide()
            self.editor.show()
            self.status.showMessage("편집 모드")

    def update_preview(self):
        markdown_text = self.editor.toPlainText().strip()
        if not markdown_text:
            html_text = "<h1>새 파일을 만들거나 기존 파일을 열어주세요.</h1>"
        else:
            html_text = markdown2.markdown(
                markdown_text,
                extras=[
                    "fenced-code-blocks",
                    "tables",
                    "strike",
                    "code-friendly",
                ],
            )
        self.preview.setHtml(html_text)

    def on_modified(self):
        if not self.unsaved_changes:
            self.unsaved_changes = True
            self.update_title()

    def new_document(self):
        if self.check_unsaved_changes():
            self.editor.clear()
            self.current_file_path = None
            self.unsaved_changes = False
            self.update_title()
            if self.view_mode == "preview":
                self.update_preview()

    def open_document(self):
        if not self.check_unsaved_changes():
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.MENU_OPEN,
            self.save_directory,
            "Markdown 파일 (*.md);;텍스트 파일 (*.txt);;모든 파일 (*.*)",
        )
        if file_path:
            self.open_file(file_path)

    def open_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            self.editor.setPlainText(content)
            self.current_file_path = file_path
            self.unsaved_changes = False
            self.update_title(os.path.basename(file_path))
            if self.view_mode == "preview":
                self.update_preview()
            self.status.showMessage(self.STATUS_FILE_OPENED.format(file_path))
        except FileNotFoundError:
            QMessageBox.critical(self, "오류", self.MSG_ERROR_FILE_NOT_FOUND)
        except PermissionError:
            QMessageBox.critical(self, "오류", self.MSG_ERROR_PERMISSION_DENIED)
        except IOError as e:
            QMessageBox.critical(self, "오류", self.MSG_ERROR_IO.format(e))
        except Exception as e:
            QMessageBox.critical(self, "오류", self.MSG_ERROR_UNKNOWN.format(e))

    def save_document(self):
        if self.current_file_path:
            try:
                content = self.editor.toPlainText()
                with open(
                    self.current_file_path, "w", encoding="utf-8"
                ) as file:
                    file.write(content)
                self.unsaved_changes = False
                self.update_title(os.path.basename(self.current_file_path))
                self.status.showMessage(self.STATUS_FILE_SAVED.format(self.current_file_path))
                return True
            except FileNotFoundError:
                QMessageBox.critical(self, "오류", self.MSG_ERROR_FILE_NOT_FOUND)
            except PermissionError:
                QMessageBox.critical(self, "오류", self.MSG_ERROR_PERMISSION_DENIED)
            except IOError as e:
                QMessageBox.critical(self, "오류", self.MSG_ERROR_IO.format(e))
            except Exception as e:
                QMessageBox.critical(self, "오류", self.MSG_ERROR_UNKNOWN.format(e))
        return self.save_document_as()

    def update_title(self, filename=None):
        if filename:
            self.base_title = f"Markdown Editor (PySide6) - {filename}"
        title = self.base_title
        if self.unsaved_changes:
            title += " *"
        self.setWindowTitle(title)

    def save_document_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.MENU_SAVE_AS,
            os.path.join(self.save_directory, "untitled.md"),
            "Markdown 파일 (*.md);;텍스트 파일 (*.txt);;모든 파일 (*.*)",
        )
        if file_path:
            self.current_file_path = file_path
            return self.save_document()
        return False

    def check_unsaved_changes(self):
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                self.MSG_UNSAVED_CHANGES_TITLE,
                self.MSG_UNSAVED_CHANGES_TEXT,
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Yes:
                return self.save_document()
            elif reply == QMessageBox.No:
                return True
            else:
                return False
        return True

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        if self.is_dark:
            self.setStyleSheet(
                """
                QMainWindow { background: #121212; color: #fff; }
                QTextEdit { background: #1E1E1E; color: #fff; }
                QMenuBar, QMenu, QStatusBar { background: #121212; color: #fff; }
            """
            )
        else:
            self.setStyleSheet("")
        self.status.showMessage(
            self.STATUS_THEME_TOGGLED.format(
                '다크모드' if self.is_dark else '라이트모드'
            )
        )

    def show_about(self):
        QMessageBox.information(
            self, self.MSG_ABOUT_TITLE, self.MSG_ABOUT_TEXT
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    file_to_open = sys.argv[1] if len(sys.argv) > 1 else None
    window = MarkdownEditor(file_to_open)
    window.show()
    app.exec()