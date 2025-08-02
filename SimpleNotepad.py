import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog
from datetime import datetime
import os
import platform
import sys
import traceback
import subprocess
import shutil
import stat
import re
import tempfile
import json

# 디버깅 모드 설정
DEBUG = True

def debug_print(message):
    """디버그 메시지 출력 함수"""
    if DEBUG:
        print(f"[DEBUG] {message}")

def is_dark_mode():
    """시스템이 다크모드인지 확인하는 함수"""
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            # macOS에서 다크모드 확인
            cmd = ["defaults", "read", "-g", "AppleInterfaceStyle"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout.strip() == "Dark"
        elif system == "Windows":  # Windows
            # Windows에서 다크모드 확인 (Windows 10 이상)
            import winreg
            try:
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return value == 0
            except FileNotFoundError:
                debug_print("다크모드 레지스트리 키를 찾을 수 없습니다.")
            except PermissionError:
                debug_print("레지스트리 접근 권한이 없습니다.")
            except Exception as e:
                debug_print(f"다크모드 감지 실패: {e}")
    except Exception as e:
        debug_print(f"다크모드 감지 실패: {e}")
    
    return False  # 기본적으로 라이트 모드 반환

class SimpleNotepad:
    def __init__(self, root, file_to_open=None):
        self.root = root
        self.root.title("Simple Notepad")
        self.root.geometry("800x600")
        
        # 다크모드 감지 (시스템 설정 반영)
        self.is_dark = is_dark_mode()
        debug_print(f"다크모드 감지: {'켜짐' if self.is_dark else '꺼짐'}")
        
        # 모든 변수 초기화
        
        # 글꼴 크기 관련 변수 초기화
        self.current_font_size = 11
        self.min_font_size = 8
        self.max_font_size = 36
        
        # 상태 표시줄 관련 변수
        self.status_message = tk.StringVar()
        self.status_message.set("")
        
        # 검색 관련 변수 초기화
        self.search_toplevel = None
        self.search_var = tk.StringVar()
        self.last_search_term = ""
        self.last_search_position = "1.0"
        
        # 자동 저장 관련 변수
        self.autosave_enabled = False
        self.autosave_interval = 60000  # 기본 1분 (밀리초)
        self.autosave_id = None
        self.unsaved_changes = False
        
        # 저장 경로 설정
        self.save_directory = os.path.join(os.path.expanduser("~"), "Documents", "SimpleNote")
        os.makedirs(self.save_directory, exist_ok=True)
        
        # 현재 문서명 초기화
        self.current_file_path = None
        
        # 설정 파일 경로
        self.config_dir = os.path.join(os.path.expanduser("~"), ".simplenotepad")
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # 설정 로드
        self.load_settings()
        
        # 테마 색상 설정
        self.setup_colors()
        
        # 폰트 설정
        self.setup_fonts()
        
        # ttk 스타일 설정
        self.setup_styles()
        
        # UI 구성
        self.create_ui()
        
        # 단축키 설정
        self.setup_shortcuts()
        
        # 제목 업데이트
        self.update_title("새 메모")
        
        # 명령줄에서 파일 경로를 받았다면 해당 파일 열기
        if file_to_open:
            debug_print(f"초기화 시 파일 열기: {file_to_open}")
            self.root.after(100, lambda: self.delayed_file_open(file_to_open))
        
        debug_print("SimpleNotepad 초기화 완료")

    def setup_colors(self):
        """테마 색상 설정"""
        if self.is_dark:
            # 다크 모드 색상 (가독성 확보)
            self.app_bg = "#121212"         # 앱 배경 (짙은 회색)
            self.workspace_bg = "#1E1E1E"   # 작업 영역 배경 (VSCode 다크 테마와 유사)
            self.workspace_fg = "#FFFFFF"   # 작업 영역 글자색 (밝은 흰색으로 변경)
            self.selection_bg = "#264F78"   # 선택 배경 (파란색 계열)
            self.selection_fg = "#FFFFFF"   # 선택 글자색 (흰색)
        else:
            # 라이트 모드 색상 (가독성 확보)
            self.app_bg = "#F5F5F5"         # 앱 배경 (연한 회색)
            self.workspace_bg = "#FFFFFF"   # 작업 영역 배경 (흰색)
            self.workspace_fg = "#000000"   # 작업 영역 글자색 (검정)
            self.selection_bg = "#ADD6FF"   # 선택 배경 (연한 파란색)
            self.selection_fg = "#000000"   # 선택 글자색 (검정)
        
        debug_print(f"색상 설정: 배경={self.workspace_bg}, 글자색={self.workspace_fg}")
        
        # 상태 표시줄 색상 업데이트 (다크모드 감지)
        if hasattr(self, 'status_bar'):
            self.status_bar.configure(style="App.TLabel")
        
        # 텍스트 영역 색상 업데이트 (이미 생성되어 있는 경우)
        if hasattr(self, 'content_text'):
            self.content_text.configure(
                bg=self.workspace_bg,
                fg=self.workspace_fg,
                insertbackground=self.workspace_fg,
                selectbackground=self.selection_bg,
                selectforeground=self.selection_fg
            )
            # 명시적으로 화면 갱신 요청
            self.content_text.update_idletasks()
            debug_print(f"텍스트 영역 색상 업데이트: bg={self.workspace_bg}, fg={self.workspace_fg}")
        
    def setup_fonts(self):
        """폰트 설정"""
        system = platform.system()
        
        # 운영체제별 기본 폰트 설정
        if system == "Windows":
            font_family = "맑은 고딕"
        elif system == "Darwin":  # macOS
            font_family = "AppleGothic"
        else:  # Linux 등
            font_family = "DejaVu Sans Mono"
        
        try:
            self.default_font = font.Font(family=font_family, size=11)
        except Exception as e:
            debug_print(f"폰트 설정 실패: {e}")
            self.default_font = font.Font(family="TkDefaultFont", size=11)

    def setup_styles(self):
        """ttk 스타일 설정"""
        self.style = ttk.Style()
        
        # 프레임 스타일
        self.style.configure("App.TFrame", background=self.app_bg)
        
        # 레이블 스타일
        self.style.configure("App.TLabel", background=self.app_bg, foreground=self.workspace_fg)
        
        # 버튼 스타일
        self.style.configure("TButton", background=self.app_bg, foreground=self.workspace_fg)
        
        # 스크롤바 스타일 - 배경색을, 텍스트 영역과 동일하게 설정
        self.style.configure("TScrollbar", 
                            background=self.workspace_bg,
                            troughcolor=self.workspace_bg,
                            arrowcolor=self.workspace_fg,
                            borderwidth=0,
                            relief="flat")
        
        # 스크롤바 요소 색상 설정
        self.style.map("TScrollbar", 
                      background=[('active', self.workspace_bg)],
                      troughcolor=[('active', self.workspace_bg)])

    def create_ui(self):
        """UI 구성 요소 생성"""
        # 루트 배경색 설정 
        self.root.configure(bg=self.workspace_bg)
        
        # 메인 프레임 (tk.Frame 사용, 배경색 통일)
        self.main_frame = tk.Frame(self.root, bg=self.workspace_bg)
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # 텍스트 에디터 (단일 전체 영역)
        system = platform.system()
        if system == "Darwin":  # macOS
            default_font = "Menlo"
        elif system == "Windows":
            default_font = "Consolas"
        else:  # Linux 등
            default_font = "DejaVu Sans Mono"
        
        self.content_text = tk.Text(
            self.main_frame,
            wrap="word",
            font=(default_font, self.current_font_size),
            bg=self.workspace_bg,
            fg=self.workspace_fg,
            selectbackground=self.selection_bg,
            selectforeground=self.selection_fg,
            insertbackground=self.workspace_fg,  # 커서 색상
            relief="flat",  # 테두리 완전 제거
            borderwidth=0,   # 테두리 두께 0
            highlightthickness=0,  # 포커스 테두리 완전 제거
            padx=20,
            pady=20,
            undo=True,  # undo/redo 기능 활성화
            maxundo=100  # 최대 undo 횟수
        )
        self.content_text.pack(side="left", fill="both", expand=True)
        
        # 기본 태그 설정 (텍스트 색상 강제 적용)
        self.content_text.tag_configure("default", foreground=self.workspace_fg)
        
        # 색상이 제대로 적용되었는지 디버그 로그
        debug_print(f"텍스트 생성 시 지정된 색상: bg={self.workspace_bg}, fg={self.workspace_fg}")
        debug_print(f"텍스트 현재 색상: bg={self.content_text['bg']}, fg={self.content_text['fg']}")
        
        # 텍스트 스크롤바
        self.text_scrollbar = ttk.Scrollbar(self.main_frame, 
                                          orient="vertical", 
                                          command=self.content_text.yview)
        self.content_text.config(yscrollcommand=self.on_scroll)
        
        # 텍스트 에디터와 파일 목록 하단에 상태 표시줄 추가
        self.status_bar = ttk.Label(
            self.main_frame, 
            textvariable=self.status_message,
            anchor="w",
            style="App.TLabel"
        )
        self.status_bar.pack(side="bottom", fill="x", padx=5, pady=2)
        
        # 메뉴바 생성
        self.create_menu()
    
    def setup_shortcuts(self):
        """키보드 단축키 설정"""
        self.root.bind("<Control-n>", lambda e: self.new_document(e))
        self.root.bind("<Control-o>", lambda e: self.open_document(e))
        self.root.bind("<Control-s>", lambda e: self.save_document(e))
        self.root.bind("<Control-Shift-s>", lambda e: self.save_document_as(e))
        
        # 편집 단축키 명시적 바인딩
        self.root.bind("<Control-z>", lambda e: self.content_text.event_generate("<<Undo>>"))
        self.root.bind("<Control-y>", lambda e: self.content_text.event_generate("<<Redo>>"))
        self.root.bind("<Control-x>", lambda e: self.content_text.event_generate("<<Cut>>"))
        self.root.bind("<Control-c>", lambda e: self.content_text.event_generate("<<Copy>>"))
        self.root.bind("<Control-v>", lambda e: self.content_text.event_generate("<<Paste>>"))
        self.root.bind("<Control-a>", lambda e: self.select_all(e))
        
        self.root.bind("<Control-t>", lambda e: self.toggle_theme(e))
        
        # 검색 단축키 추가
        self.root.bind("<Control-f>", lambda e: self.show_search_dialog(e))
        
        # 글꼴 크기 조정 단축키
        self.root.bind("<Control-plus>", lambda e: self.change_font_size(1))
        self.root.bind("<Control-equal>", lambda e: self.change_font_size(1))  # 추가 바인딩 (+ 기호는 = 키에 있음)
        self.root.bind("<Control-minus>", lambda e: self.change_font_size(-1))
        
        # 텍스트 위젯에 undo/redo 활성화
        self.content_text.config(undo=True, maxundo=100)
        
        # UI 설정 후 바인딩 설정
        self.setup_bindings()

    def create_menu(self):
        """메뉴바 생성"""
        menu_bar = tk.Menu(self.root)
        
        # 파일 메뉴
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="새 메모", command=lambda: self.new_document(None), accelerator="Ctrl+N")
        file_menu.add_command(label="열기", command=lambda: self.open_document(None), accelerator="Ctrl+O")
        file_menu.add_command(label="저장", command=lambda: self.save_document(None), accelerator="Ctrl+S")
        file_menu.add_command(label="다른 이름으로 저장", command=lambda: self.save_document_as(None), accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="기본 프로그램으로 등록", command=self.register_as_default)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.root.quit, accelerator="Alt+F4")
        menu_bar.add_cascade(label="파일", menu=file_menu)
        
        # 편집 메뉴
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="실행 취소", command=lambda: self.content_text.event_generate("<<Undo>>"), accelerator="Ctrl+Z")
        edit_menu.add_command(label="다시 실행", command=lambda: self.content_text.event_generate("<<Redo>>"), accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="잘라내기", command=lambda: self.content_text.event_generate("<<Cut>>"), accelerator="Ctrl+X")
        edit_menu.add_command(label="복사", command=lambda: self.content_text.event_generate("<<Copy>>"), accelerator="Ctrl+C")
        edit_menu.add_command(label="붙여넣기", command=lambda: self.content_text.event_generate("<<Paste>>"), accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="검색", command=lambda: self.show_search_dialog(None), accelerator="Ctrl+F")
        edit_menu.add_separator()
        edit_menu.add_command(label="모두 선택", command=lambda: self.select_all(None), accelerator="Ctrl+A")
        menu_bar.add_cascade(label="편집", menu=edit_menu)
        
        # 보기 메뉴
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="글꼴 크게", command=lambda: self.change_font_size(1), accelerator="Ctrl++")
        view_menu.add_command(label="글꼴 작게", command=lambda: self.change_font_size(-1), accelerator="Ctrl+-")
        view_menu.add_separator()
        view_menu.add_command(label="테마 전환", command=lambda: self.toggle_theme(None), accelerator="Ctrl+T")
        menu_bar.add_cascade(label="보기", menu=view_menu)
        
        # 도구 메뉴 추가
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        
        # 자동 저장 하위 메뉴
        autosave_menu = tk.Menu(tools_menu, tearoff=0)
        self.autosave_var = tk.BooleanVar(value=self.autosave_enabled)
        autosave_menu.add_checkbutton(label="자동 저장 활성화", 
                                    variable=self.autosave_var, 
                                    command=self.toggle_autosave)
        
        # 자동 저장 간격 메뉴 항목
        autosave_menu.add_separator()
        autosave_menu.add_command(label="1분마다", command=lambda: self.set_autosave_interval(60000))
        autosave_menu.add_command(label="5분마다", command=lambda: self.set_autosave_interval(300000))
        autosave_menu.add_command(label="10분마다", command=lambda: self.set_autosave_interval(600000))
        autosave_menu.add_command(label="30분마다", command=lambda: self.set_autosave_interval(1800000))
        
        tools_menu.add_cascade(label="자동 저장", menu=autosave_menu)
        menu_bar.add_cascade(label="도구", menu=tools_menu)
        
        # 도움말 메뉴
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="SimpleNotepad 정보", command=self.show_about)
        menu_bar.add_cascade(label="도움말", menu=help_menu)
        
        self.root.config(menu=menu_bar)

    def toggle_theme(self, event=None):
        """테마 전환 (다크모드/라이트모드)"""
        debug_print("단축키 호출: 테마 전환 (Ctrl+T)")
        try:
            self.is_dark = not self.is_dark
            debug_print(f"테마 전환: {'다크모드' if self.is_dark else '라이트모드'}")
            
            # 색상 테마 재설정
            self.setup_colors()
            
            # 스타일 재설정
            self.setup_styles()
            
            # UI 요소 색상 업데이트
            self.root.configure(bg=self.workspace_bg)  # workspace_bg로 변경
            self.main_frame.configure(style="App.TFrame")
            
            # 텍스트 영역 색상 업데이트
            self.content_text.config(
                bg=self.workspace_bg,
                fg=self.workspace_fg,
                insertbackground=self.workspace_fg,
                selectbackground=self.selection_bg,
                selectforeground=self.selection_fg
            )
            debug_print(f"테마 전환 후 텍스트 영역 색상: bg={self.workspace_bg}, fg={self.workspace_fg}")
            
            # 검색 창이 열려있으면 테마 변경
            if self.search_toplevel and self.search_toplevel.winfo_exists():
                self.search_toplevel.configure(bg=self.app_bg)
        except Exception as e:
            debug_print(f"테마 전환 오류: {e}")
            messagebox.showerror("오류", f"테마 전환 중 오류가 발생했습니다: {e}")

    def update_title(self, filename="새 메모"):
        """창 제목 업데이트"""
        self.root.title(f"Simple Notepad - {filename}")

    def new_document(self, event=None):
        """새 메모 작성"""
        debug_print("단축키 호출: 새 메모 (Ctrl+N)")
        # 현재 내용이 있는 경우 확인 메시지 표시
        if self.content_text.get("1.0", "end-1c").strip():
            if messagebox.askyesno("확인", "현재 내용이 저장되지 않을 수 있습니다. 계속하시겠습니까?"):
                self.content_text.delete("1.0", tk.END)
                self.current_file_path = None
                self.update_title("새 메모")
        else:
            self.content_text.delete("1.0", tk.END)
            self.current_file_path = None
            self.update_title("새 메모")
    
    def open_document(self, event=None):
        """문서 열기"""
        debug_print("단축키 호출: 열기 (Ctrl+O)")
        try:
            # 현재 내용이 있는 경우 확인
            if self.content_text.get("1.0", "end-1c").strip():
                if not messagebox.askyesno("확인", "현재 내용이 저장되지 않을 수 있습니다. 계속하시겠습니까?"):
                    return
            
            # 파일 대화상자 표시
            file_path = filedialog.askopenfilename(
                defaultextension=".txt",
                filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")],
                initialdir=self.save_directory
            )
            
            if file_path:
                debug_print(f"파일 선택됨: {file_path}")
                success = self.open_file(file_path)
                if success:
                    debug_print("파일 열기 성공")
                    # 성공적으로 파일을 열었으면 내용이 표시되는지 확인
                    text_content = self.content_text.get("1.0", "end-1c")
                    debug_print(f"로드된 내용 길이: {len(text_content)}, 텍스트 영역 색상: fg={self.workspace_fg}, bg={self.workspace_bg}")
                else:
                    debug_print("파일 열기 실패")
        except Exception as e:
            debug_print(f"문서 열기 오류: {e}")
            messagebox.showerror("오류", f"문서를 여는 중 오류가 발생했습니다: {e}")

    def save_document(self, event=None):
        """문서 저장"""
        debug_print("단축키 호출: 저장 (Ctrl+S)")
        try:
            content = self.content_text.get("1.0", tk.END)
            
            # 내용이 없으면 저장하지 않음
            if not content.strip():
                messagebox.showinfo("알림", "저장할 내용이 없습니다.")
                return
            
            # 현재 파일 경로가 있으면 해당 경로에 저장
            if self.current_file_path:
                with open(self.current_file_path, "w", encoding="utf-8") as file:
                    file.write(content)
                messagebox.showinfo("알림", "문서가 저장되었습니다.")
                debug_print(f"파일 저장 성공: {self.current_file_path}")
            else:
                # 현재 파일 경로가 없으면 새 파일로 저장
                self.save_document_as(event)
        except Exception as e:
            debug_print(f"문서 저장 오류: {e}")
            messagebox.showerror("오류", f"문서를 저장하는 중 오류가 발생했습니다: {e}")

    def save_document_as(self, event=None):
        """다른 이름으로 저장"""
        debug_print("단축키 호출: 다른 이름으로 저장 (Ctrl+Shift+S)")
        try:
            content = self.content_text.get("1.0", tk.END)
            
            # 내용이 없으면 저장하지 않음
            if not content.strip():
                messagebox.showinfo("알림", "저장할 내용이 없습니다.")
                return
            
            # 현재 날짜와 시간을 기본 파일명으로 사용
            default_filename = datetime.now().strftime("%Y%m%d%H%M%S.txt")
            
            # 파일 대화상자 표시
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")],
                initialdir=self.save_directory,
                initialfile=default_filename
            )
            
            if file_path:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(content)
                
                # 현재 파일 경로 및 제목 업데이트
                self.current_file_path = file_path
                filename = os.path.basename(file_path)
                self.update_title(filename)
                
                messagebox.showinfo("알림", "문서가 저장되었습니다.")
                debug_print(f"파일 저장 성공: {file_path}")
        except Exception as e:
            debug_print(f"문서 저장 오류: {e}")
            messagebox.showerror("오류", f"문서를 저장하는 중 오류가 발생했습니다: {e}")
    
    def select_all(self, event=None):
        """텍스트 모두 선택"""
        debug_print("단축키 호출: 모두 선택 (Ctrl+A)")
        self.content_text.tag_add(tk.SEL, "1.0", tk.END)
        self.content_text.mark_set(tk.INSERT, "1.0")
        self.content_text.see(tk.INSERT)
        return "break"  # 기본 동작 중지
    
    def show_about(self):
        """프로그램 정보 표시"""
        messagebox.showinfo(
            "SimpleNotepad 정보",
            "SimpleNotepad\n\n간단한 메모 작성을 위한 노트패드 애플리케이션입니다.\n\n"
            "버전: 1.0"
        )

    def register_as_default(self):
        """SimpleNotepad를 .txt 파일의 기본 프로그램으로 등록"""
        try:
            # 디버그 로그
            if DEBUG:
                log_dir = os.path.expanduser("~/Desktop")
                log_file = os.path.join(log_dir, "simplenotepad_debug.log")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n--- 기본 프로그램 등록 시도: {datetime.now()} ---\n")
            
            system = platform.system()
            script_path = os.path.abspath(sys.argv[0])
            python_path = sys.executable
            
            # 빌드된 실행 파일인지 확인
            is_built_exe = not script_path.endswith('.py')
            
            if DEBUG:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"운영체제: {system}\n")
                    f.write(f"실행 파일 경로: {script_path}\n")
                    f.write(f"Python 경로: {python_path}\n")
                    f.write(f"빌드된 실행 파일: {is_built_exe}\n")
            
            # PyInstaller 빌드 경로 확인
            if getattr(sys, 'frozen', False):
                app_path = sys._MEIPASS
                if DEBUG:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"PyInstaller 임시 경로: {app_path}\n")
            
            # 운영체제별 처리
            if system == "Windows":
                # Windows용 레지스트리 설정
                import winreg
                
                # 명확한 절대 경로로 설정
                script_full_path = os.path.abspath(script_path)
                
                if DEBUG:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"Windows 레지스트리 등록 시작\n")
                        f.write(f"전체 경로: {script_full_path}\n")
                
                try:
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.txt") as key:
                        winreg.SetValue(key, "", winreg.REG_SZ, "SimpleNotepad.Document")
                    
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\SimpleNotepad.Document") as key:
                        winreg.SetValue(key, "", winreg.REG_SZ, "텍스트 문서")
                        
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\SimpleNotepad.Document\shell\open\command") as key:
                        if is_built_exe:
                            command = f'"{script_full_path}" "%1"'
                        else:
                            command = f'"{python_path}" "{script_full_path}" "%1"'
                        winreg.SetValue(key, "", winreg.REG_SZ, command)
                    
                    # 파일 확장자 연결 알림
                    subprocess.run(["assoc", ".txt=SimpleNotepad.Document"], shell=True)
                    
                    if DEBUG:
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write(f"레지스트리 등록 완료, 명령: {command}\n")
                    
                    messagebox.showinfo("설정 완료", "SimpleNotepad가 .txt 파일의 기본 프로그램으로 등록되었습니다.")
                    debug_print(f"Windows 기본 프로그램 등록 완료: {command}")
                except PermissionError:
                    debug_print("레지스트리 접근 권한이 없습니다.")
                    messagebox.showerror("오류", "레지스트리 접근 권한이 없습니다.")
                except Exception as e:
                    debug_print(f"레지스트리 등록 오류: {e}")
                    messagebox.showerror("오류", f"레지스트리 등록 중 오류가 발생했습니다: {e}")
            
            elif system == "Darwin":  # macOS
                # 빌드된 앱 번들 위치 확인
                if is_built_exe:
                    # 실행 파일이 앱 번들 내부에 있는지 확인
                    app_bundle_path = None
                    if '.app/Contents/MacOS/' in script_path:
                        app_bundle_path = script_path.split('.app/')[0] + '.app'
                        if DEBUG:
                            with open(log_file, "a", encoding="utf-8") as f:
                                f.write(f"앱 번들 경로 감지: {app_bundle_path}\n")
                    
                    if app_bundle_path and os.path.exists(app_bundle_path):
                        # 앱 번들을 Applications 폴더로 복사
                        user_apps_path = os.path.expanduser("~/Applications")
                        os.makedirs(user_apps_path, exist_ok=True)
                        dest_app_path = os.path.join(user_apps_path, "SimpleNotepad.app")
                        
                        # 기존 앱 삭제 후 복사
                        if os.path.exists(dest_app_path):
                            import shutil
                            shutil.rmtree(dest_app_path)
                        
                        # 앱 번들 복사
                        import shutil
                        shutil.copytree(app_bundle_path, dest_app_path)
                        
                        if DEBUG:
                            with open(log_file, "a", encoding="utf-8") as f:
                                f.write(f"앱 번들 복사: {app_bundle_path} -> {dest_app_path}\n")
                        
                        # macOS 기본 앱 등록 안내
                        messagebox.showinfo("안내", 
                            "앱이 ~/Applications 폴더에 복사되었습니다.\n\n"
                            "텍스트 파일을 기본으로 이 앱에서 열려면:\n"
                            "1. 텍스트 파일(.txt)을 마우스 오른쪽 버튼으로 클릭합니다.\n"
                            "2. '정보 가져오기'를 선택합니다.\n"
                            "3. '다음으로 열기'에서 'SimpleNotepad'를 선택합니다.\n"
                            "4. '모두 변경'을 클릭합니다."
                        )
                    else:
                        # 앱 번들이 아닌 경우 스크립트 생성
                        self._create_mac_launcher()
                else:
                    # 스크립트인 경우 런처 생성
                    self._create_mac_launcher()
                
            elif system == "Linux":
                # Linux용 데스크톱 파일 생성
                desktop_file = (
                    "[Desktop Entry]\n"
                    "Type=Application\n"
                    "Name=SimpleNotepad\n"
                    "Comment=Simple Text Editor\n"
                    "Icon=accessories-text-editor\n"
                )
                
                # 빌드된 실행 파일이면 직접 경로 지정
                if is_built_exe:
                    desktop_file += f"Exec=\"{script_path}\" %f\n"
                else:
                    desktop_file += f"Exec={python_path} \"{script_path}\" %f\n"
                
                desktop_file += (
                    "Terminal=false\n"
                    "Categories=Utility;TextEditor;\n"
                    "MimeType=text/plain;\n"
                )
                
                desktop_path = os.path.expanduser("~/.local/share/applications/simplenotepad.desktop")
                
                with open(desktop_path, 'w') as f:
                    f.write(desktop_file)
                
                # 실행 권한 설정
                os.chmod(desktop_path, os.stat(desktop_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                
                # MIME 타입 연결 등록
                try:
                    subprocess.run(['xdg-mime', 'default', 'simplenotepad.desktop', 'text/plain'])
                    # 데스크톱 환경 갱신
                    subprocess.run(['update-desktop-database', os.path.expanduser('~/.local/share/applications/')])
                except Exception as e:
                    if DEBUG:
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write(f"MIME 타입 등록 오류: {e}\n")
                
                if DEBUG:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"Linux 데스크톱 파일 생성: {desktop_path}\n")
                        f.write(f"데스크톱 파일 내용:\n{desktop_file}\n")
                
                messagebox.showinfo("설정 완료", "SimpleNotepad가 .txt 파일의 기본 프로그램으로 등록되었습니다.")
                debug_print(f"Linux 기본 프로그램 등록 완료: {desktop_path}")
            
            else:
                messagebox.showwarning("지원되지 않는 OS", "현재 운영체제는 기본 프로그램 등록을 지원하지 않습니다.")
                
        except Exception as e:
            error_msg = f"기본 프로그램 등록 오류: {e}\n{traceback.format_exc()}"
            debug_print(error_msg)
            if DEBUG:
                log_dir = os.path.expanduser("~/Desktop")
                log_file = os.path.join(log_dir, "simplenotepad_debug.log")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"기본 프로그램 등록 오류: {error_msg}\n")
            messagebox.showerror("오류", f"기본 프로그램 등록 중 오류가 발생했습니다: {e}")
    
    def _create_mac_launcher(self):
        """macOS용 런처 생성"""
        try:
            script_path = os.path.abspath(sys.argv[0])
            python_path = sys.executable
            
            # macOS용 스크립트 생성
            app_script = (
                f'#!/bin/bash\n'
                f'cd "$(dirname "$0")"\n'
                f'{python_path} "{script_path}" "$@"\n'
            )
            
            # 실행 파일 생성 및 실행 권한 부여
            app_path = os.path.expanduser("~/Applications/SimpleNotepad")
            os.makedirs(app_path, exist_ok=True)
            launcher_path = os.path.join(app_path, "simplenotepad")
            
            with open(launcher_path, 'w') as f:
                f.write(app_script)
            
            # 실행 권한 설정
            os.chmod(launcher_path, os.stat(launcher_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            
            # macOS 기본 앱 등록 안내
            messagebox.showinfo("안내", 
                "macOS에서는 시스템 설정 > 기본 앱에서 직접 설정해야 합니다.\n\n"
                f"1. ~/Applications/SimpleNotepad 폴더에 실행 파일이 생성되었습니다.\n"
                "2. 텍스트 파일(.txt)을 마우스 오른쪽 버튼으로 클릭합니다.\n"
                "3. '정보 가져오기'를 선택합니다.\n"
                "4. '다음으로 열기'에서 '기타...'를 선택합니다.\n"
                "5. 방금 생성된 SimpleNotepad 실행 파일을 선택합니다.\n"
                "6. '모두 변경'을 클릭합니다."
            )
            
            if DEBUG:
                log_dir = os.path.expanduser("~/Desktop")
                log_file = os.path.join(log_dir, "simplenotepad_debug.log")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"macOS 런처 생성 완료: {launcher_path}\n")
        
        except Exception as e:
            if DEBUG:
                log_dir = os.path.expanduser("~/Desktop")
                log_file = os.path.join(log_dir, "simplenotepad_debug.log")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"macOS 런처 생성 오류: {e}\n{traceback.format_exc()}\n")

    def delayed_file_open(self, file_path):
        """약간의 지연 후 파일 열기 (UI가 완전히 로드된 후에 호출됨)"""
        debug_print(f"지연된 파일 열기 시작: {file_path}")
        if file_path and os.path.exists(file_path) and os.path.isfile(file_path):
            # 기존에 있을 수 있는 테스트 텍스트 모두 삭제
            self.content_text.delete("1.0", tk.END)
            
            # 파일 열기 시도
            success = self.open_file(file_path)
            debug_print(f"지연된 파일 열기 결과: {'성공' if success else '실패'}")
            
            # 파일이 열리지 않았거나 내용이 비어있으면 다시 시도
            if not success or self.content_text.get("1.0", tk.END).strip() == "":
                debug_print("파일 내용이 비어있어 다시 시도합니다")
                # 다시 한 번 시도
                self.root.after(200, lambda: self.open_file(file_path))
        else:
            debug_print(f"지연된 파일 열기 실패: 유효하지 않은 경로 - {file_path}")

    def open_file(self, file_path):
        """특정 파일 경로 열기"""
        try:
            # 디버그 로그
            log_file = None
            if DEBUG:
                log_dir = os.path.expanduser("~/Desktop")
                log_file = os.path.join(log_dir, "simplenotepad_debug.log")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\n--- 파일 열기 시도: {datetime.now()} ---\n")
                    f.write(f"파일 경로: {file_path}\n")
            
            # 파일 경로가 없거나 빈 문자열인 경우 확인
            if not file_path or file_path.strip() == "":
                debug_print("파일 경로가 비어 있음")
                if DEBUG and log_file:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write("파일 경로가 비어 있음\n")
                return False
            
            # 절대 경로로 변환
            file_path = os.path.abspath(file_path)
            
            if os.path.exists(file_path):
                # 파일 크기 확인
                file_size = os.path.getsize(file_path)
                debug_print(f"파일 크기: {file_size} 바이트")
                
                if DEBUG and log_file:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"파일 존재함: {file_path}, 크기: {file_size} 바이트\n")
                        f.write(f"파일 정보: {os.stat(file_path)}\n")
                
                # 파일이 비어있는지 확인
                if file_size == 0:
                    debug_print("빈 파일입니다")
                    self.content_text.delete("1.0", tk.END)
                    # 현재 파일 경로 및 제목 업데이트
                    self.current_file_path = file_path
                    filename = os.path.basename(file_path)
                    self.update_title(filename)
                    return True
                
                # test.txt 파일이 아닌지 확인 (오류 상황을 위한 특별 검사)
                is_test_file = os.path.basename(file_path).lower() == "test.txt"
                if is_test_file:
                    debug_print("주의: test.txt 파일을 여는 중입니다")
                    if DEBUG and log_file:
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write("주의: test.txt 파일을 여는 중입니다\n")
                
                # 다양한 인코딩 시도
                encodings = ['utf-8', 'cp949', 'euc-kr', 'latin1', 'ascii']
                success = False
                
                for encoding in encodings:
                    try:
                        with open(file_path, "r", encoding=encoding) as file:
                            content = file.read()
                            if content:  # 내용이 있는 경우에만 처리
                                # 기존 내용 삭제
                                debug_print(f"내용 삭제 전 상태: {self.content_text.get('1.0', '1.end')}")
                                self.content_text.delete("1.0", tk.END)
                                debug_print(f"내용 삭제 후 상태: {self.content_text.get('1.0', '1.end')}")
                                
                                # 새 내용 삽입
                                self.content_text.insert("1.0", content)
                                debug_print(f"내용 삽입 후 상태: {self.content_text.get('1.0', '1.end')}")
                                
                                # 문자열 내용 확인
                                content_preview = content[:100].replace('\n', '\\n')
                                debug_print(f"파일 내용 미리보기: {content_preview}")
                                
                                # 현재 파일 경로 및 제목 업데이트
                                self.current_file_path = file_path
                                filename = os.path.basename(file_path)
                                self.update_title(filename)
                                
                                # 텍스트 위젯에 포커스 주기
                                self.content_text.focus_set()
                                
                                # 텍스트 색상 명시적으로 다시 설정
                                self.content_text.configure(
                                    bg=self.workspace_bg,
                                    fg=self.workspace_fg
                                )
                                
                                # 명시적으로 위젯 갱신 및 포커스 강제 설정
                                self.content_text.update()
                                self.root.update_idletasks()
                                
                                # 강제로 텍스트 태그 색상 설정 (모든 텍스트에 적용)
                                self.content_text.tag_configure("visible", foreground=self.workspace_fg)
                                self.content_text.tag_add("visible", "1.0", "end")
                                
                                # 텍스트 포커스 재설정
                                self.content_text.focus_force()
                                
                                debug_print(f"파일 열기 성공 (인코딩: {encoding}): {file_path}")
                                if DEBUG and log_file:
                                    with open(log_file, "a", encoding="utf-8") as f:
                                        f.write(f"파일 열기 성공 (인코딩: {encoding}): {file_path}\n")
                                        f.write(f"내용 길이: {len(content)}\n")
                                        f.write(f"내용 일부: {content[:100]}...\n")
                                        f.write(f"텍스트 색상: bg={self.content_text['bg']}, fg={self.content_text['fg']}\n")
                                        f.write(f"현재 텍스트 위젯 내용: {self.content_text.get('1.0', '1.end')}\n")
                                
                                # 내용이 실제로 로드되었는지 최종 확인
                                current_content = self.content_text.get("1.0", tk.END).strip()
                                if not current_content:
                                    debug_print("경고: 파일이 열렸지만 내용이 표시되지 않습니다")
                                    if DEBUG and log_file:
                                        with open(log_file, "a", encoding="utf-8") as f:
                                            f.write("경고: 파일이 열렸지만 내용이 표시되지 않습니다\n")
                                    # 내용이 표시되지 않은 경우 재시도
                                    self.content_text.delete("1.0", tk.END)
                                    self.content_text.insert("1.0", content)
                                    self.content_text.tag_configure("visible", foreground=self.workspace_fg)
                                    self.content_text.tag_add("visible", "1.0", "end")
                                    self.content_text.update()
                                
                                success = True
                                break
                    except UnicodeDecodeError:
                        debug_print(f"인코딩 {encoding} 시도 실패: UnicodeDecodeError")
                        if DEBUG and log_file:
                            with open(log_file, "a", encoding="utf-8") as f:
                                f.write(f"인코딩 {encoding} 시도 실패: UnicodeDecodeError\n")
                        continue
                    except Exception as e:
                        debug_print(f"인코딩 {encoding} 시도 실패: {e}")
                        if DEBUG and log_file:
                            with open(log_file, "a", encoding="utf-8") as f:
                                f.write(f"인코딩 {encoding} 시도 실패: {e}\n")
                        continue
                
                # 성공 여부 반환
                if success:
                    return True
                
                # 모든 인코딩 시도 실패 시
                debug_print(f"파일 인코딩 오류: {file_path}")
                if DEBUG and log_file:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"파일 인코딩 오류: {file_path}\n")
                messagebox.showerror("오류", "텍스트 파일 형식이 아니거나 지원되지 않는 인코딩입니다.")
                return False
            else:
                debug_print(f"파일이 존재하지 않음: {file_path}")
                if DEBUG and log_file:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"파일이 존재하지 않음: {file_path}\n")
                messagebox.showerror("오류", f"파일을 찾을 수 없습니다:\n{file_path}")
                return False
        except Exception as e:
            debug_print(f"파일 열기 오류: {e}")
            if DEBUG:
                log_dir = os.path.expanduser("~/Desktop")
                log_file = os.path.join(log_dir, "simplenotepad_debug.log")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"파일 열기 오류: {e}\n{traceback.format_exc()}\n")
            messagebox.showerror("오류", f"파일을 여는 중 오류가 발생했습니다: {e}")
            return False

    def show_search_dialog(self, event=None):
        """검색 대화상자 표시"""
        debug_print("단축키 호출: 검색 (Ctrl+F)")
        
        # 이미 열려 있는 대화상자가 있다면 닫기
        if self.search_toplevel and self.search_toplevel.winfo_exists():
            self.search_toplevel.focus_force()
            return
        
        # 검색 대화상자 생성
        self.search_toplevel = tk.Toplevel(self.root)
        self.search_toplevel.title("텍스트 검색")
        self.search_toplevel.transient(self.root)
        self.search_toplevel.resizable(False, False)
        
        # 다크모드 감지하여 테마 적용
        if self.is_dark:
            self.search_toplevel.configure(bg=self.app_bg)
        else:
            self.search_toplevel.configure(bg=self.app_bg)
        
        # 검색 프레임 생성
        search_frame = ttk.Frame(self.search_toplevel, style="App.TFrame")
        search_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # 검색어 레이블 및 입력 필드
        ttk.Label(search_frame, text="검색어:", style="App.TLabel").grid(row=0, column=0, sticky="w", padx=(0,10), pady=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.grid(row=0, column=1, sticky="we", padx=5, pady=5)
        search_entry.focus_set()
        
        # 이전 검색어가 있으면 자동 입력
        if self.last_search_term:
            self.search_var.set(self.last_search_term)
            search_entry.select_range(0, tk.END)
        
        # 버튼 프레임
        button_frame = ttk.Frame(search_frame, style="App.TFrame")
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        # 이전 찾기 버튼
        ttk.Button(button_frame, text="이전 찾기", 
                  command=lambda: self.search_text(search_direction="backward")).pack(side="left", padx=5)
        
        # 다음 찾기 버튼
        ttk.Button(button_frame, text="다음 찾기", 
                  command=lambda: self.search_text(search_direction="forward")).pack(side="left", padx=5)
        
        # 닫기 버튼
        ttk.Button(button_frame, text="닫기", 
                  command=self.search_toplevel.destroy).pack(side="right", padx=5)
        
        # 단축키 설정
        self.search_toplevel.bind("<Return>", lambda e: self.search_text())
        self.search_toplevel.bind("<Escape>", lambda e: self.search_toplevel.destroy())
        
        # 대화상자 위치 조정 (부모 창 중앙)
        self.center_dialog(self.search_toplevel)
    
    def center_dialog(self, dialog):
        """대화상자를 부모 창 중앙에 위치시킴"""
        dialog.update_idletasks()
        
        # 부모 창 위치와 크기
        parent_x = self.root.winfo_rootx()
        parent_y = self.root.winfo_rooty()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()
        
        # 대화상자 크기
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()
        
        # 중앙 좌표 계산
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # 위치 설정
        dialog.geometry(f"+{x}+{y}")
    
    def search_text(self, search_direction="forward", event=None):
        """텍스트 검색 수행"""
        search_term = self.search_var.get()
        
        # 검색어가 없는 경우
        if not search_term:
            messagebox.showinfo("알림", "검색어를 입력하세요.")
            return
        
        # 현재 검색어가 이전과 다르면 처음부터 검색
        if search_term != self.last_search_term:
            self.last_search_term = search_term
            self.last_search_position = "1.0"
        
        # 현재 검색 위치 결정
        if search_direction == "forward":
            start_pos = self.last_search_position
            if self.content_text.tag_ranges("sel"):
                start_pos = self.content_text.index("sel.last")
            search_pos = self.content_text.search(search_term, start_pos, stopindex="end", regexp=False)
        else:  # backward
            end_pos = self.last_search_position
            if self.content_text.tag_ranges("sel"):
                end_pos = self.content_text.index("sel.first")
            search_pos = self.content_text.search(search_term, end_pos, stopindex="1.0", backwards=True, regexp=False)
        
        # 검색 결과가 없는 경우
        if not search_pos:
            messagebox.showinfo("검색 결과", f"'{search_term}'을(를) 찾을 수 없습니다.")
            self.last_search_position = "1.0" if search_direction == "forward" else "end"
            return
        
        # 검색 결과 위치 계산
        line, char = search_pos.split('.')
        end_pos = f"{line}.{int(char) + len(search_term)}"
        
        # 검색 결과 선택 및 표시
        self.content_text.tag_remove("sel", "1.0", "end")
        self.content_text.tag_add("sel", search_pos, end_pos)
        self.content_text.mark_set("insert", search_pos)
        self.content_text.see(search_pos)
        
        # 다음 검색을 위한 위치 업데이트
        self.last_search_position = end_pos if search_direction == "forward" else search_pos
        
        # 검색 결과 상태 표시줄 업데이트
        self.status_message.set(f"검색: '{search_term}' 찾음")
        self.root.after(2000, self.update_line_numbers)  # 2초 후 기본 상태로 복귀
        
        debug_print(f"검색 수행: '{search_term}', 위치: {search_pos}")

    def change_font_size(self, delta, event=None):
        """글꼴 크기 변경"""
        debug_print(f"단축키 호출: 글꼴 크기 변경 ({'+' if delta > 0 else '-'})")
        
        new_size = self.current_font_size + delta
        
        # 최소/최대 크기 제한
        if new_size < self.min_font_size or new_size > self.max_font_size:
            return
        
        # 새 글꼴 크기 적용
        current_font = font.Font(font=self.content_text['font'])
        current_font_family = current_font.actual('family')
        
        self.content_text.config(font=(current_font_family, new_size))
        self.current_font_size = new_size
        
        # 상태 표시줄 업데이트
        status_text = f"글꼴 크기: {self.current_font_size}pt"
        self.status_message.set(status_text)
        
        # 상태 표시줄 임시 표시 후 지우기 위한 타이머 설정
        self.root.after(2000, lambda: self.status_message.set(""))
        
        debug_print(f"글꼴 크기 변경: {self.current_font_size}")

    def update_line_numbers(self, event=None):
        """상태 표시줄 업데이트 (행/열 정보 없이)"""
        if not hasattr(self, 'content_text'):
            return
            
        # 선택된 영역 정보만 표시
        try:
            selection_ranges = self.content_text.tag_ranges("sel")
            if selection_ranges:
                # 선택 영역 크기 계산
                sel_start = self.content_text.index("sel.first")
                sel_end = self.content_text.index("sel.last")
                
                # 텍스트 길이 계산
                sel_text = self.content_text.get(sel_start, sel_end)
                chars = len(sel_text)
                lines = sel_text.count('\n') + 1
                
                status = f"선택됨: {lines}행, {chars}자"
                self.status_message.set(status)
            else:
                # 선택된 영역이 없으면 상태 표시줄 비우기
                self.status_message.set("")
        except Exception as e:
            debug_print(f"상태 표시줄 업데이트 오류: {e}")

    def setup_bindings(self):
        """텍스트 위젯 바인딩 설정"""
        # 선택 영역 변경시에만 상태 업데이트
        self.content_text.bind("<<Selection>>", self.update_line_numbers)
        
        # 저장 상태 확인 (수정 여부)
        self.content_text.bind("<<Modified>>", self.on_modified)

    def on_modified(self, event=None):
        """텍스트가 수정되었을 때 호출되는 함수"""
        if self.content_text.edit_modified():
            # 텍스트가 수정되었음을 표시
            if self.root.title()[-1] != "*":
                self.root.title(f"{self.root.title()} *")
            
            # 수정 플래그 리셋 (이벤트 중복 호출 방지)
            self.content_text.edit_modified(False)
            
            # 변경사항 있음 표시
            self.unsaved_changes = True

    def load_settings(self):
        """저장된 설정 로드"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
            
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                # 자동 저장 설정 로드
                if 'autosave_enabled' in settings:
                    self.autosave_enabled = settings['autosave_enabled']
                    
                if 'autosave_interval' in settings:
                    self.autosave_interval = settings['autosave_interval']
                    
                debug_print(f"설정 로드 완료: 자동저장={self.autosave_enabled}, 간격={self.autosave_interval/1000}초")
            except Exception as e:
                debug_print(f"설정 로드 오류: {e}")
    
    def save_settings(self):
        """현재 설정 저장"""
        try:
            settings = {
                'autosave_enabled': self.autosave_enabled,
                'autosave_interval': self.autosave_interval
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
                
            debug_print("설정 저장 완료")
        except Exception as e:
            debug_print(f"설정 저장 오류: {e}")
    
    def toggle_autosave(self):
        """자동 저장 활성화/비활성화 전환"""
        self.autosave_enabled = self.autosave_var.get()
        
        if self.autosave_enabled:
            self.start_autosave()
            self.status_message.set(f"자동 저장 활성화됨 ({self.autosave_interval/1000}초마다)")
        else:
            self.stop_autosave()
            self.status_message.set("자동 저장 비활성화됨")
            
        self.root.after(2000, lambda: self.status_message.set(""))
        self.save_settings()
        
        debug_print(f"자동 저장 {self.autosave_enabled}")
    
    def set_autosave_interval(self, interval):
        """자동 저장 간격 설정"""
        self.autosave_interval = interval
        
        # 자동 저장이 활성화된 경우 타이머 재시작
        if self.autosave_enabled:
            self.stop_autosave()
            self.start_autosave()
            
        # 간격 정보 표시
        minutes = interval / 60000
        unit = "분"
        if minutes < 1:
            seconds = interval / 1000
            self.status_message.set(f"자동 저장 간격: {seconds}초")
        else:
            self.status_message.set(f"자동 저장 간격: {minutes}분")
            
        self.root.after(2000, lambda: self.status_message.set(""))
        self.save_settings()
        
        debug_print(f"자동 저장 간격 설정: {interval/1000}초")
    
    def start_autosave(self):
        """자동 저장 타이머 시작"""
        # 이미 실행 중인 타이머가 있으면 중지
        self.stop_autosave()
        
        # 새 타이머 시작
        self.autosave_id = self.root.after(self.autosave_interval, self.perform_autosave)
        debug_print(f"자동 저장 타이머 시작: {self.autosave_interval/1000}초")
    
    def stop_autosave(self):
        """자동 저장 타이머 중지"""
        if self.autosave_id:
            self.root.after_cancel(self.autosave_id)
            self.autosave_id = None
            debug_print("자동 저장 타이머 중지")
    
    def perform_autosave(self):
        """자동 저장 수행"""
        debug_print("자동 저장 실행")
        
        # 변경사항이 있고 이미 저장된 파일인 경우에만 저장
        if self.unsaved_changes and self.current_file_path:
            try:
                self.save_file()
                self.status_message.set(f"자동 저장 완료: {os.path.basename(self.current_file_path)}")
                self.root.after(2000, lambda: self.status_message.set(""))
            except Exception as e:
                debug_print(f"자동 저장 오류: {e}")
                self.status_message.set("자동 저장 실패")
                self.root.after(2000, lambda: self.status_message.set(""))
        
        # 다음 자동 저장 예약
        self.autosave_id = self.root.after(self.autosave_interval, self.perform_autosave)
    
    def save_file(self, event=None):
        """현재 파일 저장"""
        if self.current_file_path:
            text_content = self.content_text.get(1.0, tk.END)
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as file:
                    file.write(text_content)
                
                # 저장 후 제목에서 * 제거
                title = self.root.title()
                if title.endswith(" *"):
                    self.root.title(title[:-2])
                
                self.unsaved_changes = False
                return True
            except FileNotFoundError:
                debug_print("파일을 찾을 수 없습니다.")
                messagebox.showerror("파일 저장 오류", "파일을 찾을 수 없습니다.")
                return False
            except PermissionError:
                debug_print("파일 저장 권한이 없습니다.")
                messagebox.showerror("파일 저장 오류", "파일 저장 권한이 없습니다.")
                return False
            except Exception as e:
                debug_print(f"파일 저장 오류: {e}")
                messagebox.showerror("파일 저장 오류", f"파일을 저장하는 중 오류가 발생했습니다:\n{e}")
                return False
        else:
            return self.save_as()
    
    def save_as(self, event=None):
        """다른 이름으로 저장"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
            )
            
            if file_path:
                self.current_file_path = file_path
                self.update_title(os.path.basename(file_path))
                
                # 파일 저장
                result = self.save_file()
                
                # 파일 경로 업데이트만 수행
                if result:
                    debug_print(f"다른 이름으로 저장 성공: {file_path}")
                    
                return result
            return False
        except Exception as e:
            debug_print(f"다른 이름으로 저장 오류: {e}")
            messagebox.showerror("저장 오류", f"파일을 저장하는 중 오류가 발생했습니다:\n{e}")
            return False
    
    def close_app(self, event=None):
        """애플리케이션 종료"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel("저장 확인", "저장되지 않은 변경사항이 있습니다. 저장하시겠습니까?")
            
            if result is None:  # 취소 선택
                return
            elif result:  # 저장 선택
                if not self.save_file():
                    return  # 저장 실패시 종료 취소
        
        # 설정 저장
        self.save_settings()
        
        # 자동 저장 타이머 중지
        self.stop_autosave()
        
        # 종료
        self.root.destroy()
        sys.exit(0)

    def on_scroll(self, *args):
        """스크롤 이벤트 핸들러 (yscrollcommand용)"""
        # args는 (first, last) 형태의 문자열이 들어옴
        try:
            first, last = float(args[0]), float(args[1])
            if first == 0.0 and last == 1.0:
                self.text_scrollbar.pack_forget()  # 스크롤이 필요 없을 때 숨김
            else:
                self.text_scrollbar.pack(side="right", fill="y", padx=0)  # 스크롤이 필요할 때 표시
            # 실제 스크롤 위치는 스크롤바가 제어하므로 별도 yview 호출 불필요
        except Exception as e:
            debug_print(f"on_scroll 오류: {e}")

if __name__ == "__main__":
    try:
        # 디버그 로그 파일 설정 (빌드된 앱에서 문제 추적용)
        if DEBUG:
            log_dir = os.path.expanduser("~/Desktop")
            log_file = os.path.join(log_dir, "simplenotepad_debug.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n--- SimpleNotepad 시작: {datetime.now()} ---\n")
                f.write(f"실행 경로: {os.path.abspath(sys.argv[0])}\n")
                f.write(f"명령줄 인수: {sys.argv}\n")
        
        root = tk.Tk()
        
        # 명령줄 인수로 파일 경로를 받았는지 확인
        file_to_open = None
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            # 따옴표 제거 (Windows에서 경로에 따옴표가 포함될 수 있음)
            if file_path.startswith('"') and file_path.endswith('"'):
                file_path = file_path[1:-1]
            
            # 절대 경로로 변환
            file_path = os.path.abspath(file_path)
            
            if DEBUG:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"처리된 파일 경로: {file_path}\n")
                    f.write(f"파일 존재 여부: {os.path.exists(file_path)}\n")
                    if os.path.exists(file_path):
                        f.write(f"파일 정보: {os.stat(file_path)}\n")
                        f.write(f"파일 크기: {os.path.getsize(file_path)} 바이트\n")
                        try:
                            with open(file_path, 'r', encoding='utf-8') as test_file:
                                content_preview = test_file.read(100)
                                f.write(f"파일 내용 미리보기: {content_preview}\n")
                        except Exception as e:
                            f.write(f"파일 내용 읽기 실패: {e}\n")
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                file_to_open = file_path
                debug_print(f"명령줄 인수로 받은 파일 경로: {file_to_open}")
        
        # 앱 초기화 후 root.mainloop() 호출 전에 파일 열기 시도
        app = SimpleNotepad(root, file_to_open)
        
        # 파일이 열렸는지 다시 확인하고, 내용이 없으면 다시 시도
        if file_to_open and app.content_text.get("1.0", tk.END).strip() == "":
            debug_print("파일 내용이 비어있어 다시 시도합니다")
            if DEBUG:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"파일 내용이 비어있어 다시 시도: {file_to_open}\n")
            
            # UI가 완전히 로드된 후 파일 열기 재시도
            def force_load_file():
                if app.content_text.get("1.0", tk.END).strip() == "":
                    debug_print("강제 파일 로드 시도")
                    app.content_text.delete("1.0", tk.END)
                    app.open_file(file_to_open)
            
            # 지연 후 다시 시도 (약간의 지연을 두고 재시도)
            root.after(500, force_load_file)
        
        root.mainloop()
    except Exception as e:
        error_msg = f"심각한 오류 발생: {e}\n{traceback.format_exc()}"
        print(error_msg)
        
        # 오류 로그 파일에 기록 (빌드된 앱에서 문제 추적용)
        if DEBUG:
            try:
                log_dir = os.path.expanduser("~/Desktop")
                log_file = os.path.join(log_dir, "simplenotepad_error.log")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\n--- 오류 발생: {datetime.now()} ---\n")
                    f.write(error_msg)
            except:
                pass
