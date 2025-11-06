#pip install python-dotenv streamlit

# ========================================
# AI 학습 도우미 - 환경 설정
# ========================================
# 이 파일은 환경 변수를 읽어와서
# 다른 파일들에서 쉽게 사용할 수 있게 합니다
# ========================================

import os
import sys
from dotenv import load_dotenv
import streamlit as st

# ========================================
# 디버그 모드 설정
# ========================================
# True로 하면 터미널에 자세한 로그가 표시됩니다
DEBUG_MODE = True

def debug_print(message, level="INFO"):
    """
    디버그 메시지를 출력하는 함수
    
    매개변수:
        message: 출력할 메시지
        level: 로그 레벨 (INFO, WARNING, ERROR, SUCCESS)
    """
    if DEBUG_MODE:
        colors = {
            "INFO": "\033[94m",     # 파란색
            "WARNING": "\033[93m",  # 노란색
            "ERROR": "\033[91m",    # 빨간색
            "SUCCESS": "\033[92m",  # 초록색
        }
        reset = "\033[0m"
        color = colors.get(level, colors["INFO"])
        print(f"{color}[{level}]{reset} {message}")


# ========================================
# 한글 경로 처리
# ========================================
# Windows에서 한글 파일명이 깨지지 않도록 설정
try:
    if sys.platform.startswith('win'):
        import locale
        # 한글 출력을 위한 인코딩 설정
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        debug_print("한글 경로 처리 설정 완료", "SUCCESS")
except Exception as e:
    debug_print(f"한글 경로 설정 중 오류: {str(e)}", "WARNING")


# ========================================
# 현재 실행 경로 가져오기
# ========================================
# 파이썬 파일이 실행되는 폴더의 절대 경로
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
debug_print(f"현재 실행 경로: {CURRENT_DIR}", "INFO")


# ========================================
# 환경 변수 로드
# ========================================
# .env 파일에서 설정값을 읽어옵니다

# 로컬 개발 시: .env 파일 사용
env_path = os.path.join(CURRENT_DIR, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    debug_print(".env 파일을 찾았습니다!", "SUCCESS")
else:
    debug_print(".env 파일이 없습니다. Streamlit Cloud Secrets를 사용합니다.", "WARNING")


def get_env(key, default=None):
    """
    환경 변수를 가져오는 함수
    
    Streamlit Cloud에서는 st.secrets를 사용하고
    로컬에서는 .env 파일을 사용합니다
    
    매개변수:
        key: 환경 변수 이름
        default: 기본값 (환경 변수가 없을 때)
    
    반환값:
        환경 변수 값
    """
    try:
        # Streamlit Cloud에서 실행 중인 경우
        if hasattr(st, 'secrets'):
            try:
                value = st.secrets.get(key, default)
                if value:
                    debug_print(f"환경 변수 '{key}' 로드 성공 (Streamlit Secrets)", "SUCCESS")
                    return value
            except:
                pass
        
        # 로컬 개발 환경
        value = os.getenv(key, default)
        if value:
            debug_print(f"환경 변수 '{key}' 로드 성공 (.env)", "SUCCESS")
        else:
            debug_print(f"환경 변수 '{key}'를 찾을 수 없습니다", "WARNING")
        return value
    
    except Exception as e:
        debug_print(f"환경 변수 '{key}' 로드 중 오류: {str(e)}", "ERROR")
        return default


# ========================================
# 필수 환경 변수
# ========================================
# 사용자가 설정해야 하는 값들

# Supabase (데이터베이스)
SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_KEY = get_env("SUPABASE_KEY")

# DeepSeek (AI)
DEEPSEEK_API_KEY = get_env("DEEPSEEK_API_KEY")

# 최초 관리자 계정
SUPER_ADMIN_USERNAME = get_env("SUPER_ADMIN_USERNAME", "admin")
SUPER_ADMIN_PASSWORD = get_env("SUPER_ADMIN_PASSWORD")


# ========================================
# 환경 변수 검증
# ========================================
def validate_config():
    """
    필수 환경 변수가 모두 설정되었는지 확인
    
    반환값:
        (성공 여부, 오류 메시지)
    """
    debug_print("환경 변수 검증 시작...", "INFO")
    
    missing = []
    
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")
    if not DEEPSEEK_API_KEY:
        missing.append("DEEPSEEK_API_KEY")
    if not SUPER_ADMIN_PASSWORD:
        missing.append("SUPER_ADMIN_PASSWORD")
    
    if missing:
        error_msg = f"다음 환경 변수가 설정되지 않았습니다: {', '.join(missing)}"
        debug_print(error_msg, "ERROR")
        return False, error_msg
    
    debug_print("모든 환경 변수가 정상적으로 설정되었습니다!", "SUCCESS")
    return True, None


# ========================================
# 앱 설정
# ========================================
APP_NAME = "AI 학습 도우미"
APP_ICON = "🎓"
VERSION = "1.0.0"

# 세션 만료 시간 (일)
SESSION_EXPIRE_DAYS = 7

# 페이지 설정
PAGE_CONFIG = {
    "page_title": APP_NAME,
    "page_icon": APP_ICON,
    "layout": "wide",  # 또는 "centered"
    "initial_sidebar_state": "expanded",
}


# ========================================
# 카테고리 정보
# ========================================
# 학습 카테고리 목록
CATEGORIES = {
    # 학생용
    "english": {"icon": "🌍", "name": "영어 학습", "color": "#FF6B9D"},
    "math": {"icon": "🔢", "name": "수학 학습", "color": "#4A90E2"},
    "science": {"icon": "🔬", "name": "과학 학습", "color": "#A8E6CF"},
    "korean": {"icon": "📚", "name": "국어 학습", "color": "#FFD3B6"},
    "coding": {"icon": "💻", "name": "코딩 학습", "color": "#7B68EE"},
    "free": {"icon": "💬", "name": "자유 대화", "color": "#FFB6C1"},
    
    # 교사 전용
    "education": {"icon": "📖", "name": "교육 상담", "color": "#98D8C8"},
    "saeungbu": {"icon": "📝", "name": "생기부 작성", "color": "#F7B733"},
    "counseling": {"icon": "💭", "name": "학생 상담", "color": "#95E1D3"},
    "worry": {"icon": "🤔", "name": "교사 고민", "color": "#AA96DA"},
}


# ========================================
# 학년 목록
# ========================================
GRADES = [
    "초등 1학년",
    "초등 2학년",
    "초등 3학년",
    "초등 4학년",
    "초등 5학년",
    "초등 6학년",
    "중학생",
]


# ========================================
# 디렉토리 생성
# ========================================
# 필요한 폴더들을 자동으로 만듭니다

def create_directories():
    """
    필요한 디렉토리를 생성하는 함수
    """
    directories = [
        os.path.join(CURRENT_DIR, 'temp'),      # 임시 파일 저장
        os.path.join(CURRENT_DIR, 'logs'),      # 로그 파일
        os.path.join(CURRENT_DIR, 'database'),  # 데이터베이스 관련
        os.path.join(CURRENT_DIR, 'auth'),      # 인증 관련
        os.path.join(CURRENT_DIR, 'ai'),        # AI 관련
        os.path.join(CURRENT_DIR, 'voice'),     # 음성 관련
        os.path.join(CURRENT_DIR, 'quiz'),      # 퀴즈 관련
        os.path.join(CURRENT_DIR, 'utils'),     # 유틸리티
        os.path.join(CURRENT_DIR, 'pages'),     # Streamlit 페이지
    ]
    
    for directory in directories:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                debug_print(f"폴더 생성: {directory}", "SUCCESS")
        except Exception as e:
            debug_print(f"폴더 생성 실패 {directory}: {str(e)}", "ERROR")


# 앱 시작 시 폴더 생성
create_directories()


# ========================================
# 완료!
# ========================================
debug_print("config.py 로드 완료!", "SUCCESS")


