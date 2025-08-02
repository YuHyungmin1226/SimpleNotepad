# 📝 SimpleNotepad - 고급 메모장 애플리케이션

**SimpleNotepad**는 Python과 tkinter로 개발된 고급 메모장 애플리케이션입니다. 다크모드 지원, 자동 저장, 고급 검색 기능 등 현대적인 텍스트 에디터의 기능을 제공합니다.

## ✨ 주요 기능

### 🎨 테마 지원
- **다크모드/라이트모드** 자동 감지 및 전환
- 시스템 설정에 따른 자동 테마 적용
- Ctrl+T로 수동 테마 전환 가능

### 🔍 고급 검색 기능
- **Ctrl+F** 단축키로 검색 창 열기
- **이전/다음 찾기** 기능
- 실시간 검색 결과 하이라이트

### 💾 자동 저장 시스템
- **1분/5분/10분/30분** 간격 설정 가능
- 변경사항 자동 감지
- 안전한 백업 시스템

### 🎯 글꼴 및 UI
- **글꼴 크기 조정** (8pt~36pt, Ctrl++/Ctrl+-)
- **크로스 플랫폼 지원** (Windows, macOS, Linux)
- **반응형 디자인**

### 🔧 시스템 통합
- **기본 프로그램 등록** (.txt 파일 연결)
- **명령줄 통합** (`python SimpleNotepad.py file.txt`)
- **드래그 앤 드롭** 지원

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/YuHyungmin1226/SimpleNotepad.git
cd SimpleNotepad
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 실행
```bash
# 기본 실행
python SimpleNotepad.py

# 파일과 함께 실행
python SimpleNotepad.py myfile.txt
```

## 🎮 단축키

| 기능 | 단축키 |
|------|--------|
| 새 메모 | Ctrl+N |
| 열기 | Ctrl+O |
| 저장 | Ctrl+S |
| 다른 이름으로 저장 | Ctrl+Shift+S |
| 검색 | Ctrl+F |
| 테마 전환 | Ctrl+T |
| 글꼴 크게 | Ctrl++ |
| 글꼴 작게 | Ctrl+- |
| 모두 선택 | Ctrl+A |

## 🏗️ 빌드

PyInstaller를 사용하여 독립 실행형 애플리케이션을 빌드할 수 있습니다:

```bash
# Windows
pyinstaller --onefile --noconsole --name "SimpleNotepad" SimpleNotepad.py

# macOS
pyinstaller --onefile --windowed --name "SimpleNotepad" SimpleNotepad.py

# Linux
pyinstaller --onefile --name "SimpleNotepad" SimpleNotepad.py
```

## 📁 파일 구조

```
SimpleNotepad/
├── SimpleNotepad.py      # 메인 애플리케이션
├── requirements.txt      # Python 의존성
├── README.md            # 프로젝트 문서
├── .gitignore           # Git 무시 파일
└── build/               # 빌드 스크립트
    └── build.py         # 자동 빌드 스크립트
```

## 🔧 설정

### 자동 저장 설정
- **도구 > 자동 저장** 메뉴에서 설정 가능
- 1분, 5분, 10분, 30분 간격 선택
- 설정은 자동으로 저장됨

### 기본 프로그램 등록
- **파일 > 기본 프로그램으로 등록** 메뉴 사용
- 운영체제별 자동 설정

## 🐛 문제 해결

### 디버그 모드
애플리케이션 실행 시 디버그 정보가 콘솔에 출력됩니다. 문제 발생 시 다음 파일을 확인하세요:
- `~/Desktop/simplenotepad_debug.log`
- `~/Desktop/simplenotepad_error.log`

### 일반적인 문제
1. **파일이 열리지 않는 경우**: 인코딩 문제일 수 있습니다. UTF-8로 저장된 파일을 사용하세요.
2. **색상이 제대로 표시되지 않는 경우**: 테마 전환(Ctrl+T)을 시도해보세요.
3. **자동 저장이 작동하지 않는 경우**: 파일이 이미 저장된 상태인지 확인하세요.

## 📊 시스템 요구사항

- **Python**: 3.7 이상
- **운영체제**: Windows 10+, macOS 10.14+, Linux
- **메모리**: 최소 50MB
- **저장공간**: 최소 10MB

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 👨‍💻 개발자

**YuHyungmin1226** - [GitHub](https://github.com/YuHyungmin1226)

## 🔄 최근 업데이트

- ✅ **2025-01-XX**: 별도 저장소로 분리
- ✅ **2025-01-XX**: README.md 완전 최신화
- ✅ **2025-01-XX**: 빌드 스크립트 추가

---

⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요! 