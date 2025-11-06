#pip install streamlit

# ========================================
# AI 학습 도우미 - 세션 관리
# ========================================
# 사용자 로그인 상태를 관리하는 모듈
# Streamlit의 session_state를 사용합니다
# ========================================

import streamlit as st
from datetime import datetime, timedelta


# ========================================
# 사용자가 설정할 변수 (없음 - 세션 관리만)
# ========================================


def debug_print(message, level="INFO"):
    """
    디버그 메시지 출력
    
    매개변수:
        message: 출력할 메시지
        level: 로그 레벨
    """
    colors = {
        "INFO": "\033[94m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "SUCCESS": "\033[92m",
    }
    reset = "\033[0m"
    color = colors.get(level, colors["INFO"])
    print(f"{color}[SESSION-{level}]{reset} {message}")


# ========================================
# 세션 초기화
# ========================================

def init_session():
    """
    Streamlit 세션 초기화
    처음 실행할 때 필요한 변수들을 설정합니다
    """
    debug_print("세션 초기화 시작", "INFO")
    
    # 로그인 상태
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        debug_print("로그인 상태 초기화: False", "INFO")
    
    # 사용자 정보
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    if 'full_name' not in st.session_state:
        st.session_state.full_name = None
    
    if 'role' not in st.session_state:
        st.session_state.role = None  # 'super_admin', 'teacher', 'student'
    
    if 'grade' not in st.session_state:
        st.session_state.grade = None
    
    # 현재 카테고리
    if 'current_category' not in st.session_state:
        st.session_state.current_category = None
    
    # 대화 세션 ID
    if 'conversation_session_id' not in st.session_state:
        from utils.helpers import generate_session_id
        st.session_state.conversation_session_id = generate_session_id()
    
    # 대화 기록 (메모리에 임시 저장)
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # 페이지별 대화 세션 저장소
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = {}

    # 현재 페이지 키 (메뉴/페이지별로 채팅을 분리하기 위한 키)
    if 'current_page' not in st.session_state:
        st.session_state.current_page = None

    # 페이지별 개별 대화 세션 ID 보관소
    if 'page_session_ids' not in st.session_state:
        st.session_state.page_session_ids = {}
    
    debug_print("세션 초기화 완료", "SUCCESS")


# ========================================
# 로그인 처리
# ========================================

def login_user(user_data):
    """
    사용자 로그인 처리
    
    매개변수:
        user_data: 사용자 정보 딕셔너리
            {
                'id': 사용자 ID,
                'username': 아이디,
                'full_name': 이름,
                'role': 역할,
                'grade': 학년 (학생인 경우)
            }
    """
    try:
        st.session_state.logged_in = True
        st.session_state.user_id = user_data.get('id')
        st.session_state.username = user_data.get('username')
        st.session_state.full_name = user_data.get('full_name')
        st.session_state.role = user_data.get('role')
        st.session_state.grade = user_data.get('grade')
        
        debug_print(f"로그인 성공: {st.session_state.username} ({st.session_state.role})", "SUCCESS")
        return True
    
    except Exception as e:
        debug_print(f"로그인 처리 중 오류: {str(e)}", "ERROR")
        return False


# ========================================
# 로그아웃 처리
# ========================================

def logout_user():
    """
    사용자 로그아웃 처리
    모든 세션 데이터를 초기화합니다
    """
    try:
        username = st.session_state.get('username', '알 수 없음')
        
        # 세션 초기화
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.full_name = None
        st.session_state.role = None
        st.session_state.grade = None
        st.session_state.current_category = None
        st.session_state.messages = []
        st.session_state.chat_sessions = {}
        st.session_state.current_page = None
        
        # 새 세션 ID 생성
        from utils.helpers import generate_session_id
        st.session_state.conversation_session_id = generate_session_id()
        
        debug_print(f"로그아웃 성공: {username}", "SUCCESS")
        return True
    
    except Exception as e:
        debug_print(f"로그아웃 처리 중 오류: {str(e)}", "ERROR")
        return False


# ========================================
# 로그인 상태 확인
# ========================================

def is_logged_in():
    """
    로그인 여부 확인
    
    반환값:
        True/False
    """
    return st.session_state.get('logged_in', False)


def get_current_user():
    """
    현재 로그인한 사용자 정보 반환
    
    반환값:
        사용자 정보 딕셔너리 또는 None
    """
    if not is_logged_in():
        return None
    
    return {
        'id': st.session_state.get('user_id'),
        'username': st.session_state.get('username'),
        'full_name': st.session_state.get('full_name'),
        'role': st.session_state.get('role'),
        'grade': st.session_state.get('grade'),
    }


def get_user_role():
    """
    현재 사용자의 역할 반환
    
    반환값:
        'super_admin', 'teacher', 'student' 또는 None
    """
    return st.session_state.get('role')


def is_admin():
    """관리자인지 확인"""
    return get_user_role() == 'super_admin'


def is_teacher():
    """교사인지 확인"""
    return get_user_role() == 'teacher'


def is_student():
    """학생인지 확인"""
    return get_user_role() == 'student'


# ========================================
# 카테고리 관리
# ========================================

def set_category(category_name):
    """
    현재 학습 카테고리 설정
    
    매개변수:
        category_name: 카테고리 이름 (예: 'english', 'math')
    """
    st.session_state.current_category = category_name
    debug_print(f"카테고리 설정: {category_name}", "INFO")


def get_current_category():
    """
    현재 학습 카테고리 반환
    
    반환값:
        카테고리 이름 또는 None
    """
    return st.session_state.get('current_category')


# ========================================
# 대화 기록 관리
# ========================================

def set_current_page(page_key: str):
    """현재 페이지 키 설정 및 해당 페이지용 대화 리스트 준비"""
    try:
        st.session_state.current_page = page_key
        if 'chat_sessions' not in st.session_state:
            st.session_state.chat_sessions = {}
        if page_key not in st.session_state.chat_sessions:
            st.session_state.chat_sessions[page_key] = []
        debug_print(f"현재 페이지 설정: {page_key}", "INFO")
    except Exception as e:
        debug_print(f"현재 페이지 설정 오류: {str(e)}", "ERROR")

def get_current_page() -> str | None:
    """현재 페이지 키 반환"""
    return st.session_state.get('current_page')

def add_message(role, content):
    """
    대화 기록에 메시지 추가
    
    매개변수:
        role: 'user' 또는 'assistant'
        content: 메시지 내용
    """
    message = {
        'role': role,
        'content': content,
        'timestamp': datetime.now()
    }
    # 페이지 키가 없으면 'default'에 기록
    page_key = st.session_state.get('current_page') or 'default'
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = {}
    if page_key not in st.session_state.chat_sessions:
        st.session_state.chat_sessions[page_key] = []
    st.session_state.chat_sessions[page_key].append(message)
    debug_print(f"[{page_key}] 메시지 추가: {role} - {content[:50]}...", "INFO")


def get_messages():
    """
    대화 기록 반환
    
    반환값:
        메시지 리스트
    """
    page_key = st.session_state.get('current_page') or 'default'
    sessions = st.session_state.get('chat_sessions', {})
    return sessions.get(page_key, [])


def clear_messages():
    """대화 기록 초기화"""
    page_key = st.session_state.get('current_page') or 'default'
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = {}
    st.session_state.chat_sessions[page_key] = []
    debug_print(f"[{page_key}] 대화 기록 초기화", "INFO")


def get_conversation_session_id():
    """
    현재 대화 세션 ID 반환
    
    반환값:
        세션 ID 문자열
    """
    return st.session_state.get('conversation_session_id')


def get_current_session_id():
    """현재 페이지에 매핑된 대화 세션 ID 반환. 없으면 생성합니다."""
    from utils.helpers import generate_session_id
    page_key = st.session_state.get('current_page') or 'default'
    if 'page_session_ids' not in st.session_state:
        st.session_state.page_session_ids = {}
    if page_key not in st.session_state.page_session_ids:
        st.session_state.page_session_ids[page_key] = generate_session_id()
    return st.session_state.page_session_ids[page_key]


def new_conversation_for_current_page():
    """현재 페이지용 새로운 대화 세션을 시작하고, 해당 페이지의 메시지를 비웁니다."""
    from utils.helpers import generate_session_id
    page_key = st.session_state.get('current_page') or 'default'
    if 'page_session_ids' not in st.session_state:
        st.session_state.page_session_ids = {}
    # 새 세션 ID 발급
    st.session_state.page_session_ids[page_key] = generate_session_id()
    # 메시지 초기화
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = {}
    # 설정에 따라 메시지 초기화 여부 결정
    should_clear = st.session_state.get('clear_on_new_chat', True)
    if should_clear:
        st.session_state.chat_sessions[page_key] = []
    debug_print(f"[{page_key}] 새 대화 세션 시작: {st.session_state.page_session_ids[page_key]}", "INFO")


def load_session_messages(session_id: str):
    """DB에서 특정 세션의 대화를 불러와 현재 페이지 메시지로 채웁니다."""
    try:
        from database.supabase_manager import get_conversations_by_session
        user = get_current_user()
        if not user:
            return False
        rows = get_conversations_by_session(user['id'], session_id)
        # 현재 페이지 키 확인
        page_key = st.session_state.get('current_page') or 'default'
        if 'chat_sessions' not in st.session_state:
            st.session_state.chat_sessions = {}
        st.session_state.chat_sessions[page_key] = []
        # 시간 정보가 없을 수 있어 현재 시각으로 기록
        now = datetime.now()
        for r in rows:
            um = r.get('user_message')
            ar = r.get('ai_response')
            if um:
                st.session_state.chat_sessions[page_key].append({'role': 'user', 'content': um, 'timestamp': now})
            if ar:
                st.session_state.chat_sessions[page_key].append({'role': 'assistant', 'content': ar, 'timestamp': now})
        # 세션 ID도 현재 페이지에 적용
        if 'page_session_ids' not in st.session_state:
            st.session_state.page_session_ids = {}
        st.session_state.page_session_ids[page_key] = session_id
        debug_print(f"[{page_key}] 세션 불러오기 완료: {session_id} (메시지 {len(st.session_state.chat_sessions[page_key])}개)", "SUCCESS")
        return True
    except Exception as e:
        debug_print(f"세션 메시지 로드 오류: {str(e)}", "ERROR")
        return False


# ========================================
# 권한 확인
# ========================================

def require_login():
    """
    로그인이 필요한 페이지에서 사용
    로그인하지 않았으면 경고 표시 후 중단
    """
    if not is_logged_in():
        st.warning("⚠️ 로그인이 필요합니다!")
        st.info("오른쪽 상단 '로그인' 버튼을 눌러 로그인해주세요.")
        st.stop()


def require_role(required_role):
    """
    특정 역할이 필요한 페이지에서 사용
    
    매개변수:
        required_role: 필요한 역할 ('super_admin', 'teacher', 'student')
    """
    require_login()
    
    current_role = get_user_role()
    
    if current_role != required_role:
        st.error(f"❌ 이 페이지는 {required_role} 권한이 필요합니다!")
        st.stop()


def require_teacher_or_admin():
    """교사 또는 관리자만 접근 가능"""
    require_login()
    
    if not (is_teacher() or is_admin()):
        st.error("❌ 이 페이지는 교사 또는 관리자만 접근할 수 있습니다!")
        st.stop()


# ========================================
# 완료!
# ========================================
debug_print("session_manager.py 로드 완료!", "SUCCESS")


