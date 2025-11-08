#pip install streamlit

# ========================================
# AI 학습 도우미 - 유틸리티 함수들
# ========================================
# 여러 곳에서 사용되는 유용한 함수들을 모아둔 파일
# ========================================

import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
import streamlit as st


# ========================================
# 사용자가 설정할 변수 (없음 - 공통 함수만 있음)
# ========================================


def debug_print(message, level="INFO"):
    """
    디버그 메시지 출력 (ANSI 색상 제거 - Windows 콘솔 호환)
    
    매개변수:
        message: 출력할 메시지
        level: 로그 레벨 (INFO, WARNING, ERROR, SUCCESS)
    """
    print(f"[HELPER-{level}] {message}")


# ========================================
# 파일 경로 처리 (한글 지원)
# ========================================

def get_safe_path(filename):
    """
    한글이 포함된 파일명을 안전하게 처리
    
    매개변수:
        filename: 파일 이름
    
    반환값:
        안전한 경로
    """
    try:
        # 현재 실행 중인 파일의 경로
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 상위 폴더 (vaccine/)
        base_dir = os.path.dirname(current_dir)
        # 파일 경로 조합
        file_path = os.path.join(base_dir, filename)
        
        # 경로를 UTF-8로 인코딩하여 안전하게 처리
        safe_path = os.path.normpath(file_path)
        
        debug_print(f"안전한 경로 생성: {safe_path}", "INFO")
        return safe_path
    
    except Exception as e:
        debug_print(f"경로 생성 중 오류: {str(e)}", "ERROR")
        return filename


def ensure_directory(directory_path):
    """
    디렉토리가 없으면 생성
    
    매개변수:
        directory_path: 생성할 디렉토리 경로
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            debug_print(f"디렉토리 생성: {directory_path}", "SUCCESS")
        return True
    except Exception as e:
        debug_print(f"디렉토리 생성 실패: {str(e)}", "ERROR")
        return False


# ========================================
# JSON 파일 처리
# ========================================

def read_json_file(filepath):
    """
    JSON 파일을 읽어서 딕셔너리로 반환
    파일이 없으면 빈 딕셔너리 반환
    
    매개변수:
        filepath: JSON 파일 경로
    
    반환값:
        딕셔너리 또는 빈 딕셔너리
    """
    try:
        if os.path.exists(filepath):
            # UTF-8로 읽기 (한글 지원)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                debug_print(f"JSON 파일 읽기 성공: {filepath}", "SUCCESS")
                return data
        else:
            debug_print(f"JSON 파일이 없습니다: {filepath}", "WARNING")
            return {}
    
    except Exception as e:
        debug_print(f"JSON 파일 읽기 오류: {str(e)}", "ERROR")
        return {}


def write_json_file(filepath, data):
    """
    딕셔너리를 JSON 파일로 저장
    파일이 없으면 자동 생성
    
    매개변수:
        filepath: 저장할 파일 경로
        data: 저장할 데이터 (딕셔너리)
    
    반환값:
        성공 여부 (True/False)
    """
    try:
        # 디렉토리 확인 및 생성
        directory = os.path.dirname(filepath)
        if directory:
            ensure_directory(directory)
        
        # UTF-8로 저장 (한글 지원)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            debug_print(f"JSON 파일 저장 성공: {filepath}", "SUCCESS")
            return True
    
    except Exception as e:
        debug_print(f"JSON 파일 저장 오류: {str(e)}", "ERROR")
        return False


# ========================================
# 텍스트 파일 처리
# ========================================

def read_text_file(filepath):
    """
    텍스트 파일을 읽어서 문자열로 반환
    파일이 없으면 빈 문자열 반환
    
    매개변수:
        filepath: 텍스트 파일 경로
    
    반환값:
        문자열 또는 빈 문자열
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                debug_print(f"텍스트 파일 읽기 성공: {filepath}", "SUCCESS")
                return content
        else:
            debug_print(f"텍스트 파일이 없습니다: {filepath}", "WARNING")
            return ""
    
    except Exception as e:
        debug_print(f"텍스트 파일 읽기 오류: {str(e)}", "ERROR")
        return ""


def write_text_file(filepath, content):
    """
    문자열을 텍스트 파일로 저장
    파일이 없으면 자동 생성
    
    매개변수:
        filepath: 저장할 파일 경로
        content: 저장할 내용 (문자열)
    
    반환값:
        성공 여부 (True/False)
    """
    try:
        # 디렉토리 확인 및 생성
        directory = os.path.dirname(filepath)
        if directory:
            ensure_directory(directory)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            debug_print(f"텍스트 파일 저장 성공: {filepath}", "SUCCESS")
            return True
    
    except Exception as e:
        debug_print(f"텍스트 파일 저장 오류: {str(e)}", "ERROR")
        return False


# ========================================
# 날짜/시간 처리
# ========================================

def get_current_datetime():
    """
    현재 날짜와 시간을 반환
    
    반환값:
        datetime 객체
    """
    return datetime.now()


def format_datetime(dt, format_string="%Y-%m-%d %H:%M:%S"):
    """
    datetime 객체를 문자열로 변환
    
    매개변수:
        dt: datetime 객체
        format_string: 날짜 형식
    
    반환값:
        형식화된 문자열
    """
    try:
        return dt.strftime(format_string)
    except:
        return str(dt)


def get_relative_time(dt):
    """
    상대적인 시간 표시 (예: "5분 전", "2일 전")
    
    매개변수:
        dt: datetime 객체
    
    반환값:
        상대 시간 문자열
    """
    try:
        now = datetime.now()
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "방금 전"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}분 전"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}시간 전"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days}일 전"
        else:
            return format_datetime(dt, "%Y-%m-%d")
    
    except:
        return "알 수 없음"


# ========================================
# ID 생성
# ========================================

def generate_unique_id():
    """
    고유한 ID 생성 (UUID4 사용)
    
    반환값:
        고유 ID 문자열
    """
    return str(uuid.uuid4())


def generate_session_id():
    """
    세션 ID 생성
    
    반환값:
        세션 ID 문자열
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = str(uuid.uuid4())[:8]
    return f"session_{timestamp}_{random_part}"


def generate_invite_code(length=6, prefix=""):
    """
    인증코드 생성
    
    매개변수:
        length: 코드 길이
        prefix: 접두사 (예: "TEACHER-")
    
    반환값:
        인증코드 문자열
    """
    import random
    import string
    
    # 헷갈리는 문자 제외 (0, O, I, 1)
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    
    code = ''.join(random.choice(chars) for _ in range(length))
    return f"{prefix}{code}"


# ========================================
# 해시 함수
# ========================================

def hash_string(text):
    """
    문자열을 SHA256으로 해싱
    
    매개변수:
        text: 해싱할 문자열
    
    반환값:
        해시 문자열
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


# ========================================
# 문자열 처리
# ========================================

def truncate_string(text, max_length=50, suffix="..."):
    """
    긴 문자열을 자르고 ... 추가
    
    매개변수:
        text: 원본 문자열
        max_length: 최대 길이
        suffix: 끝에 붙일 문자
    
    반환값:
        잘린 문자열
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + suffix


def sanitize_filename(filename):
    """
    파일명에서 허용되지 않는 문자 제거
    
    매개변수:
        filename: 원본 파일명
    
    반환값:
        안전한 파일명
    """
    import re
    # Windows에서 허용되지 않는 문자 제거
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    return filename


# ========================================
# Streamlit 헬퍼
# ========================================

def show_success(message):
    """Streamlit 성공 메시지 표시"""
    st.success(f"✅ {message}")
    debug_print(message, "SUCCESS")


def show_error(message):
    """Streamlit 오류 메시지 표시"""
    st.error(f"❌ {message}")
    debug_print(message, "ERROR")


def show_warning(message):
    """Streamlit 경고 메시지 표시"""
    st.warning(f"⚠️ {message}")
    debug_print(message, "WARNING")


def show_info(message):
    """Streamlit 정보 메시지 표시"""
    st.info(f"ℹ️ {message}")
    debug_print(message, "INFO")


# ========================================
# 완료!
# ========================================
debug_print("helpers.py 로드 완료!", "SUCCESS")


# ========================================
# 상단 우측 로그인/회원가입 헤더 및 중앙 폼
# ========================================

def render_auth_header():
    """
    페이지 상단 우측에 로그인/회원가입 또는 사용자/로그아웃 버튼을 표시합니다.
    버튼 클릭 시 중앙 폼 표시 플래그를 토글합니다.
    """
    try:
        # 세션 기본값
        if "show_login_form" not in st.session_state:
            st.session_state.show_login_form = False
        if "show_signup_form" not in st.session_state:
            st.session_state.show_signup_form = False

        cols = st.columns([8, 1, 1])
        with cols[1]:
            if not st.session_state.get('is_logged_in'):
                if st.button("로그인", use_container_width=True):
                    st.session_state.show_login_form = True
                    st.session_state.show_signup_form = False
            else:
                user = st.session_state.get('user') or {}
                st.caption(f"{user.get('full_name') or user.get('username')} 님")
        with cols[2]:
            if not st.session_state.get('is_logged_in'):
                if st.button("회원가입", use_container_width=True):
                    st.session_state.show_signup_form = True
                    st.session_state.show_login_form = False
            else:
                if st.button("로그아웃", use_container_width=True):
                    try:
                        from utils.session_manager import logout_user
                        logout_user()
                        st.rerun()
                    except Exception as e:
                        show_error(f"로그아웃 중 오류: {str(e)}")
    except Exception as e:
        debug_print(f"헤더 렌더링 오류: {str(e)}", "ERROR")


def render_auth_modals():
    """
    중앙에 로그인/회원가입 폼을 렌더링합니다.
    비로그인 상태에서만 표시됩니다.
    """
    try:
        if st.session_state.get('is_logged_in'):
            return

        show_login = st.session_state.get('show_login_form', False)
        show_signup = st.session_state.get('show_signup_form', False)

        if not (show_login or show_signup):
            return

        # 중앙 폼 폭을 넓게 조정
        left, center, right = st.columns([1, 2, 1])
        with center:
            # 폼 최대 너비를 제한하는 CSS
            st.markdown("""
                <style>
                div[data-testid='stForm'] { max-width: 720px; margin: 0 auto; }
                </style>
            """, unsafe_allow_html=True)
            with st.container(border=True):
                if show_login:
                    st.subheader("로그인")
                    with st.form("top_login_form"):
                        username = st.text_input("아이디", key="top_login_username")
                        password = st.text_input("비밀번호", type="password", key="top_login_password")
                        submitted = st.form_submit_button("로그인 하기", use_container_width=True)
                        if submitted:
                            if not username or not password:
                                show_error("아이디와 비밀번호를 모두 입력해주세요.")
                            else:
                                try:
                                    from auth.auth_manager import login_with_username_password
                                    ok, msg = login_with_username_password(username, password)
                                    if ok:
                                        show_success(msg)
                                        st.session_state.show_login_form = False
                                        st.rerun()
                                    else:
                                        show_error(msg)
                                except Exception as e:
                                    show_error(f"로그인 오류: {str(e)}")

                if show_signup:
                    st.subheader("회원가입")
                    st.caption("교사/학생 모두 인증코드가 필요합니다.")
                    tabs = st.tabs(["교사", "학생"])

                    with tabs[0]:
                        with st.form("top_signup_teacher"):
                            t_username = st.text_input("아이디", key="top_signup_t_username")
                            t_full = st.text_input("닉네임(선택)", key="top_signup_t_full", help="비워두면 아이디와 동일하게 표시됩니다.")
                            t_password = st.text_input("비밀번호", type="password", key="top_signup_t_password", help="영문과 숫자만 사용해도 됩니다.")
                            t_code = st.text_input("교사 인증코드", key="top_signup_t_code")
                            submitted_t = st.form_submit_button("교사 회원가입", use_container_width=True)
                            if submitted_t:
                                if not (t_username and t_password and t_code):
                                    show_error("필수 항목(아이디/비밀번호/인증코드)을 입력해주세요.")
                                else:
                                    try:
                                        from auth.auth_manager import signup_teacher, login_with_username_password
                                        # 닉네임 비워두면 아이디로 처리는 서버에서 보장
                                        ok, msg = signup_teacher(t_username, t_full, t_password, t_code)
                                        if ok:
                                            show_success(msg)
                                            ok2, msg2 = login_with_username_password(t_username, t_password)
                                            if ok2:
                                                show_success("자동 로그인되었습니다.")
                                                st.session_state.show_signup_form = False
                                                st.rerun()
                                            else:
                                                show_info("상단 우측 '로그인' 버튼으로 접속해주세요.")
                                        else:
                                            show_error(msg)
                                    except Exception as e:
                                        show_error(f"회원가입 오류: {str(e)}")

                    with tabs[1]:
                        with st.form("top_signup_student"):
                            s_username = st.text_input("아이디", key="top_signup_s_username")
                            s_full = st.text_input("닉네임(선택)", key="top_signup_s_full", help="비워두면 아이디와 동일하게 표시됩니다.")
                            s_password = st.text_input("비밀번호", type="password", key="top_signup_s_password", help="영문과 숫자만 사용해도 됩니다.")
                            import config as _cfg
                            s_grade = st.selectbox("학년", options=_cfg.GRADES, key="top_signup_s_grade")
                            s_code = st.text_input("학생 인증코드", key="top_signup_s_code")
                            submitted_s = st.form_submit_button("학생 회원가입", use_container_width=True)
                            if submitted_s:
                                if not (s_username and s_password and s_grade and s_code):
                                    show_error("필수 항목(아이디/비밀번호/학년/인증코드)을 입력해주세요.")
                                else:
                                    try:
                                        from auth.auth_manager import signup_student, login_with_username_password
                                        ok, msg = signup_student(s_username, s_full, s_password, s_grade, s_code)
                                        if ok:
                                            show_success(msg)
                                            ok2, msg2 = login_with_username_password(s_username, s_password)
                                            if ok2:
                                                show_success("자동 로그인되었습니다.")
                                                st.session_state.show_signup_form = False
                                                st.rerun()
                                            else:
                                                show_info("상단 우측 '로그인' 버튼으로 접속해주세요.")
                                        else:
                                            show_error(msg)
                                    except Exception as e:
                                        show_error(f"회원가입 오류: {str(e)}")
    except Exception as e:
        debug_print(f"중앙 폼 렌더링 오류: {str(e)}", "ERROR")


def render_sidebar_auth_controls():
    """
    사이드바 왼쪽 하단에 로그인/회원가입 또는 로그아웃 버튼을 렌더링합니다.
    페이지 스크립트에서 `with st.sidebar:` 블록 내에서 호출하세요.
    """
    try:
        # 스페이서를 제거하여 설정 섹션 바로 아래에 표시되도록 조정
        from utils.session_manager import is_logged_in, get_current_user, logout_user
        if is_logged_in():
            user = get_current_user()
            st.caption(f"{user['full_name'] or user['username']} 님 ({user['role']})")
            if st.button("로그아웃", use_container_width=True):
                logout_user()
                st.rerun()
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("로그인", use_container_width=True):
                    st.session_state.show_login_form = True
                    st.session_state.show_signup_form = False
            with col_b:
                if st.button("회원가입", use_container_width=True):
                    st.session_state.show_signup_form = True
                    st.session_state.show_login_form = False

        # --- 개발자 모드 토글 ---
        try:
            st.divider()
            dev_label = "개발자 모드"
            # 기본값 True, 세션 키는 'dev_mode'로 유지
            st.checkbox(dev_label, value=bool(st.session_state.get('dev_mode', True)), key='dev_mode')
            st.caption("테스트 계정 자동 로그인: 아이디 `test`, 비번 `test1234!`")
            # 토글이 켜져 있고 아직 로그인되지 않은 경우 자동 로그인 시도
            if st.session_state.get('dev_mode', False) and not is_logged_in():
                try:
                    from utils.session_manager import _dev_auto_login_if_enabled
                    _dev_auto_login_if_enabled()
                    st.rerun()
                except Exception:
                    pass
        except Exception:
            pass

        # --- AI 반응 설정 (왼쪽 하단) ---
        try:
            st.divider()
            with st.expander("AI 반응 설정", expanded=False):
                # Temperature: 반응 다양성 (낮음=보수적, 높음=창의적)
                st.slider(
                    "반응 다양성 (Temperature)",
                    min_value=0.0,
                    max_value=1.5,
                    value=float(st.session_state.get('ai_temperature', 0.7)),
                    step=0.05,
                    key='ai_temperature'
                )
                # Max tokens: 답변 길이 제한
                st.slider(
                    "최대 토큰 수",
                    min_value=100,
                    max_value=4000,
                    value=int(st.session_state.get('ai_max_tokens', 800)),
                    step=50,
                    key='ai_max_tokens'
                )
                st.caption("온도↑: 창의적, 온도↓: 정확·일관성. 토큰은 답변 길이에 영향.")
        except Exception:
            # 설정 UI가 실패해도 인증 UI는 정상 동작하도록 무시
            pass
    except Exception as e:
        debug_print(f"사이드바 인증 버튼 렌더링 오류: {str(e)}", "ERROR")


def render_sidebar_navigation():
    """
    사이드바 상단에 한글 메뉴 그룹(학생 / 교사 / 설정)을 렌더링합니다.
    각 항목은 개별 페이지로 이동하는 링크입니다.
    """
    try:
        import streamlit as st
        # 사이드바 로고 및 간격을 조금 더 좁게 만드는 CSS 적용
        st.markdown(
            """
            <style>
            /* 사이드바 상단 여백을 줄여 브랜드를 더 위로 */
            div[data-testid='stSidebar'] { padding-top: 0.2rem !important; }
            div[data-testid='stSidebar'] h2 { margin: 0.2rem 0 !important; }
            div[data-testid='stSidebar'] a { margin: 0.08rem 0 !important; padding-top: 0.08rem !important; padding-bottom: 0.08rem !important; }
            div[data-testid='stSidebar'] hr { margin: 0.35rem 0 !important; }
            .brand-title { font-weight: 700; font-size: 1.08rem; margin: 0 0 0.3rem 0; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div class='brand-title'>우리반AI에이전트</div>", unsafe_allow_html=True)
        st.subheader("학생")
        st.page_link("pages/13_learning_english.py", label="영어 학습")
        st.page_link("pages/14_learning_math.py", label="수학 학습")
        st.page_link("pages/15_learning_science.py", label="과학 학습")
        st.page_link("pages/26_learning_history.py", label="역사 학습")
        st.page_link("pages/27_learning_reading.py", label="독서 학습")
        st.page_link("pages/28_learning_english_grammar.py", label="영어문법 학습")
        st.page_link("pages/29_learning_korean.py", label="국어 학습")
        st.page_link("pages/30_learning_coding.py", label="코딩 학습")
        st.page_link("pages/31_learning_free.py", label="자유 학습")
        st.page_link("pages/2_quiz.py", label="퀴즈")
        st.page_link("pages/10_counseling_student.py", label="학생 고민 상담")
        st.page_link("pages/3_vocabulary.py", label="단어장")
        st.page_link("pages/19_assignments_student.py", label="과제 게시판")
        st.page_link("pages/24_korean_outline_student.py", label="국어 글쓰기 개요")
        st.page_link("pages/32_girlfriend_mode.py", label="여친 모드")

        st.divider()

        st.subheader("교사")
        st.page_link("pages/5_student_management.py", label="학생 관리")
        st.page_link("pages/6_invite_codes.py", label="코드 초대")
        st.page_link("pages/16_question_bank.py", label="문제은행")
        st.page_link("pages/34_ms_question_bank.py", label="중학교 문제은행")
        st.page_link("pages/17_lesson_prep.py", label="수업준비")
        st.page_link("pages/18_assignments_teacher.py", label="과제 출제")
        st.page_link("pages/20_teacher_stocks.py", label="주식")
        st.page_link("pages/21_stock_worry.py", label="주식 고민")
        st.page_link("pages/22_stock_chatbot.py", label="주식 챗봇")
        st.page_link("pages/25_stock_trends.py", label="주식 트렌드")
        st.page_link("pages/33_stock_recommendations.py", label="추천주식")
        st.page_link("pages/23_doc_assistant.py", label="문서 도우미")
        st.page_link("pages/8_counseling_education.py", label="교육 상담")
        st.page_link("pages/9_record.py", label="생기부")
        st.page_link("pages/4_stats.py", label="통계")
        st.page_link("pages/11_teacher_worry.py", label="교사 고민")
        st.page_link("pages/12_admin.py", label="관리자")

        st.divider()

        st.subheader("설정")
        st.page_link("pages/7_settings.py", label="설정")
    except Exception as e:
        debug_print(f"사이드바 내비게이션 렌더링 오류: {str(e)}", "ERROR")


# ========================================
# 새 대화 관리 UI (확인 + 최근 세션 불러오기)
# ========================================

def render_new_chat_controls(page_key: str, category_name: str | None = None):
    """
    새 대화 시작(확인 모달)과 최근 저장된 세션을 불러오는 컨트롤을 렌더링합니다.
    페이지의 우측 하단이나 적절한 위치에서 호출하세요.
    """
    try:
        from utils.session_manager import (
            new_conversation_for_current_page,
            load_session_messages,
            get_current_user,
        )
        from database.supabase_manager import (
            get_user_conversations,
            get_category_by_name,
        )

        # 새 대화 버튼 및 확인 모달
        confirm_needed = st.session_state.get('confirm_on_new_chat', True)
        if st.button("새 대화", key=f"btn_new_chat_{page_key}"):
            if confirm_needed:
                st.session_state[f"show_new_chat_modal_{page_key}"] = True
            else:
                new_conversation_for_current_page()
                try:
                    st.toast("새 대화를 시작했어요.")
                except Exception:
                    show_success("새 대화를 시작했어요.")
                st.rerun()

        if st.session_state.get(f"show_new_chat_modal_{page_key}", False):
            with st.modal("새 대화 확인", key=f"modal_new_chat_{page_key}"):
                st.write("현재 대화를 정리하고 새로 시작합니다. 진행할까요?")
                st.caption("설정에서 '새 대화 시 기존 메시지 비우기'를 변경할 수 있어요.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("확인", key=f"confirm_new_chat_{page_key}"):
                        new_conversation_for_current_page()
                        st.session_state[f"show_new_chat_modal_{page_key}"] = False
                        try:
                            st.toast("새 대화를 시작했어요.")
                        except Exception:
                            show_success("새 대화를 시작했어요.")
                        st.rerun()
                with c2:
                    if st.button("취소", key=f"cancel_new_chat_{page_key}"):
                        st.session_state[f"show_new_chat_modal_{page_key}"] = False

        # 최근 세션 불러오기 (카테고리별)
        user = get_current_user()
        session_options = []
        format_map = {}
        if user:
            cat_id = None
            if category_name:
                cat_row = get_category_by_name(category_name)
                cat_id = cat_row['id'] if cat_row else None
            recent = get_user_conversations(user['id'], category_id=cat_id, limit=200)
            # 세션별 메타 구성 (개수, 최신시각, 최신 사용자 프롬프트)
            from collections import defaultdict
            counts = defaultdict(int)
            latest_ts = {}
            latest_user_msg = {}
            latest_assistant_msg = {}
            for r in recent:
                sid = r.get('session_id')
                if not sid:
                    continue
                counts[sid] += 1
                # recent가 최신순이므로 첫 등장 레코드가 최신 교환
                if sid not in latest_ts:
                    latest_ts[sid] = r.get('created_at')
                    latest_user_msg[sid] = r.get('user_message')
                    latest_assistant_msg[sid] = r.get('assistant_message')
            # 최신순 정렬
            session_options = sorted(counts.keys(), key=lambda s: latest_ts.get(s, ''), reverse=True)

            def _fmt_time(ts: str | None) -> str:
                if not ts:
                    return "시간 정보 없음"
                # 간단 포맷: YYYY-MM-DD HH:MM
                try:
                    return ts.replace('T', ' ')[:16]
                except Exception:
                    return str(ts)[:16]

            for sid in session_options:
                ts_label = _fmt_time(latest_ts.get(sid))
                cat_label = category_name or "카테고리 없음"
                # 사용자 프롬프트가 없으면 어시스턴트 응답으로 대체
                prompt = latest_user_msg.get(sid) or latest_assistant_msg.get(sid) or "내용 없음"
                prompt = truncate_string(str(prompt), 40)
                cnt = counts.get(sid, 0)
                format_map[sid] = f"{ts_label} · {cat_label} · 대화 {cnt} · {prompt}"

        if session_options:
            st.selectbox(
                "최근 세션 불러오기",
                options=session_options,
                key=f"select_recent_session_{page_key}",
                format_func=lambda sid: format_map.get(sid, str(sid)),
            )
            if st.button("불러오기", key=f"btn_load_session_{page_key}"):
                selected = st.session_state.get(f"select_recent_session_{page_key}")
                if selected:
                    ok = load_session_messages(selected)
                    if ok:
                        try:
                            st.toast("이전 대화를 불러왔어요.")
                        except Exception:
                            show_success("이전 대화를 불러왔어요.")
                        st.rerun()
                    else:
                        show_error("세션을 불러오지 못했어요.")
        else:
            st.caption("저장된 최근 대화가 아직 없어요.")
    except Exception as e:
        debug_print(f"새 대화 컨트롤 렌더링 오류: {str(e)}", "ERROR")

