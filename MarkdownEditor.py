
# PySide6 기반 마크다운 에디터
import sys
import os
import markdown2
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QFileDialog, QMessageBox, QSplitter, QWidget, QVBoxLayout, QStatusBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class MarkdownEditor(QMainWindow):
    def __init__(self, file_to_open=None):
        super().__init__()
        self.base_title = "Markdown Editor (PySide6)"
        self.setWindowTitle(self.base_title)
        self.resize(1000, 800)

        self.is_dark = False
        self.view_mode = "editor"  # editor or preview
        self.current_file_path = None
        self.unsaved_changes = False
        # ...existing code...
        self.save_directory = os.path.join(os.path.expanduser("~"), "Documents", "MarkdownFiles")
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
        self.status.showMessage("준비")

        # Menu
        self.create_menu()
        # Shortcuts
        self.create_shortcuts()

    def create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("파일")
        file_menu.addAction("새 파일", self.new_document, "Ctrl+N")
        file_menu.addAction("열기", self.open_document, "Ctrl+O")
        file_menu.addAction("저장", self.save_document, "Ctrl+S")
        file_menu.addAction("다른 이름으로 저장", self.save_document_as, "Ctrl+Shift+S")
        file_menu.addSeparator()
        file_menu.addAction("종료", self.close)

        edit_menu = menubar.addMenu("편집")
        edit_menu.addAction("실행 취소", self.editor.undo, "Ctrl+Z")
        edit_menu.addAction("다시 실행", self.editor.redo, "Ctrl+Y")

        markdown_menu = menubar.addMenu("마크다운")
        markdown_menu.addAction("굵게", lambda: self.apply_markdown("bold"), "Ctrl+B")
        markdown_menu.addAction("기울임", lambda: self.apply_markdown("italic"), "Ctrl+I")
        markdown_menu.addAction("취소선", lambda: self.apply_markdown("strike"), "Ctrl+Shift+S")
        markdown_menu.addAction("코드", lambda: self.apply_markdown("code"), "Ctrl+Shift+C")
        markdown_menu.addSeparator()
        markdown_menu.addAction("헤더 1", lambda: self.apply_markdown("h1"), "Ctrl+1")
        markdown_menu.addAction("헤더 2", lambda: self.apply_markdown("h2"), "Ctrl+2")
        markdown_menu.addAction("헤더 3", lambda: self.apply_markdown("h3"), "Ctrl+3")
        markdown_menu.addSeparator()
        markdown_menu.addAction("순서 없는 목록", lambda: self.apply_markdown("ul"), "Ctrl+L")

        view_menu = menubar.addMenu("보기")
        view_menu.addAction("편집/미리보기 전환", self.toggle_view, "F5")
        view_menu.addAction("테마 전환", self.toggle_theme, "F6")

        help_menu = menubar.addMenu("도움말")
        help_menu.addAction("정보", self.show_about)

    # 툴바 제거됨

    def create_shortcuts(self):
        self.editor.setTabChangesFocus(False)

    def apply_markdown(self, style):
        cursor = self.editor.textCursor()
        selected_text = cursor.selectedText()
        if not selected_text:
            return
        if style == "bold":
            new_text = f"**{selected_text}**"
        elif style == "italic":
            new_text = f"*{selected_text}*"
        elif style == "strike":
            new_text = f"~~{selected_text}~~"
        elif style == "code":
            new_text = f"`{selected_text}`"
        elif style.startswith("h"):
            level = int(style[1:])
            new_text = f"{'#' * level} {selected_text}"
        elif style == "ul":
            new_text = f"- {selected_text}"
        else:
            return
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
            html_text = markdown2.markdown(markdown_text, extras=["fenced-code-blocks", "tables", "strike", "code-friendly"])
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
        file_path, _ = QFileDialog.getOpenFileName(self, "파일 열기", self.save_directory, "Markdown 파일 (*.md);;텍스트 파일 (*.txt);;모든 파일 (*.*)")
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
            self.status.showMessage(f"파일 열기: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"파일을 여는 중 오류가 발생했습니다: {e}")

    def save_document(self):
        if self.current_file_path:
            try:
                content = self.editor.toPlainText()
                with open(self.current_file_path, "w", encoding="utf-8") as file:
                    file.write(content)
                self.unsaved_changes = False
                self.update_title(os.path.basename(self.current_file_path))
                self.status.showMessage(f"파일 저장됨: {self.current_file_path}")
                return True
            except Exception as e:
                QMessageBox.critical(self, "오류", f"파일 저장 중 오류가 발생했습니다: {e}")
                return False
        return self.save_document_as()
    def update_title(self, filename=None):
        if filename:
            self.base_title = f"Markdown Editor (PySide6) - {filename}"
        title = self.base_title
        if self.unsaved_changes:
            title += " *"
        self.setWindowTitle(title)

    def save_document_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "다른 이름으로 저장", os.path.join(self.save_directory, "untitled.md"), "Markdown 파일 (*.md);;텍스트 파일 (*.txt);;모든 파일 (*.*)")
        if file_path:
            self.current_file_path = file_path
            return self.save_document()
        return False

    def check_unsaved_changes(self):
        if self.unsaved_changes:
            reply = QMessageBox.question(self, "저장 확인", "저장되지 않은 변경사항이 있습니다. 저장하시겠습니까?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
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
            self.setStyleSheet("""
                QMainWindow { background: #121212; color: #fff; }
                QTextEdit { background: #1E1E1E; color: #fff; }
                QMenuBar, QMenu, QStatusBar { background: #121212; color: #fff; }
            """)
        else:
            self.setStyleSheet("")
        self.status.showMessage(f"테마 전환: {'다크모드' if self.is_dark else '라이트모드'}")

    def show_about(self):
        QMessageBox.information(self, "Markdown Editor", "간단한 마크다운 편집기 (PySide6)\n\n버전: 2.0")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    file_to_open = sys.argv[1] if len(sys.argv) > 1 else None
    window = MarkdownEditor(file_to_open)
    window.show()
    app.exec()
