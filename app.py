#pip install streamlit python-dotenv supabase bcrypt openai edge-tts

# ========================================
# AI 학습 도우미 - 메인 앱 (Streamlit)
# ========================================
# 이 앱은 웹 브라우저에서 실행됩니다.
# 1) 왼쪽 사이드바에서 로그인/회원가입을 할 수 있어요.
# 2) 로그인 후 역할(관리자/교사/학생)에 맞는 기본 화면이 보여요.
# 3) 나머지 상세 페이지는 pages/ 폴더에 나누어 작성할 수 있어요.
# ========================================

import streamlit as st

import config
from utils.session_manager import init_session, is_logged_in, get_current_user, logout_user
from auth.auth_manager import ensure_super_admin, login_with_username_password, signup_teacher, signup_student
from auth.invite_codes import create_teacher_code, create_student_code
from utils.helpers import show_success, show_error, show_info
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation


# ========================================
# 디버그 출력 (터미널 확인용)
# ========================================

def debug_print(message, level="INFO"):
    if config.DEBUG_MODE:
        try:
            print(f"[APP-{level}] {message}")
        except Exception:
            pass


# ========================================
# 앱 시작 설정
# ========================================

st.set_page_config(**config.PAGE_CONFIG)
init_session()

ok, err = config.validate_config()
if not ok:
    st.error("필수 설정값이 없습니다. 좌측 상단의 터미널 로그를 참고하여 .env 또는 Secrets를 설정해주세요.")
    st.stop()

# 데이터베이스 연결 초기화 (앱 시작 시)
try:
    from database.supabase_manager import get_supabase_client
    import traceback
    
    debug_print("앱 시작: 데이터베이스 연결 시도...", "INFO")
    db_client = get_supabase_client()
    
    if not db_client:
        # 조용히 계속 진행하고, 실제 액션 시도 시에만 오류 표출
        pass
    
    debug_print("앱 시작: 데이터베이스 연결 성공!", "SUCCESS")
    
except Exception as e:
    st.error(f"❌ 데이터베이스 연결 오류: {str(e)}")
    st.error(f"오류 타입: {type(e).__name__}")
    
    if config.DEBUG_MODE:
        import traceback
        with st.expander("🐛 자세한 오류 정보"):
            st.code(traceback.format_exc(), language='python')
    
    debug_print(f"앱 시작: 데이터베이스 연결 예외 발생: {str(e)}", "ERROR")
    debug_print(traceback.format_exc(), "ERROR")
    st.stop()

# 최초 관리자 계정 보장
try:
    ensure_super_admin()
except Exception as e:
    debug_print(f"관리자 계정 생성 중 오류: {str(e)}", "ERROR")
    # 오류가 있어도 앱은 계속 실행


# ========================================
# 사이드바 - 로그인/회원가입
# ========================================

with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()


# ========================================
# 메인 영역 - 역할별 기본 화면 (간단버전)
# ========================================

st.caption("우리반 AI 에이전트")
render_auth_modals()

if not is_logged_in():
    st.info("왼쪽 하단의 '로그인' 또는 '회원가입' 버튼을 이용해주세요.")
    st.stop()

user = get_current_user()
role = user['role']

if role == 'super_admin':
    st.subheader("👑 관리자 대시보드 (간단 체험용)")
    st.write("교사 가입용 인증코드를 만들 수 있어요.")
    col1, col2 = st.columns(2)
    with col1:
        memo = st.text_input("교사 코드 메모", placeholder="예: 서울초 김선생님")
        days = st.number_input("유효기간(일)", min_value=1, max_value=365, value=30, step=1)
        if st.button("교사 인증코드 생성"):
            code = create_teacher_code(admin_user_id=user['id'], days_valid=int(days), memo=memo)
            if code:
                st.success(f"새 코드: {code['code']}")
            else:
                st.error("코드 생성 실패")
    with col2:
        st.info("상단 메뉴의 Pages에 관리자/교사용 페이지를 점차 추가할 예정입니다.")

elif role == 'teacher':
    st.subheader("👨‍🏫 교사 대시보드 (간단 체험용)")
    st.write("학생 가입용 인증코드를 만들 수 있어요.")
    col1, col2 = st.columns(2)
    with col1:
        class_name = st.text_input("학급명", placeholder="예: 3학년 2반")
        uses = st.number_input("최대 사용 횟수", min_value=1, max_value=200, value=10, step=1)
        days = st.number_input("유효기간(일)", min_value=1, max_value=60, value=7, step=1)
        memo = st.text_input("메모", placeholder="신규 전학생용 등")
        if st.button("학생 인증코드 생성"):
            code = create_student_code(teacher_user_id=user['id'], class_name=class_name, uses=int(uses), days_valid=int(days), memo=memo)
            if code:
                st.success(f"새 코드: {code['code']}")
            else:
                st.error("코드 생성 실패")
    with col2:
        st.info("상단 메뉴의 Pages에 교사 전용 카테고리(교육/생기부/상담/고민)를 추가할 예정입니다.")

else:
    st.subheader("👨‍🎓 학생 대시보드 (간단 체험용)")
    st.write("왼쪽 상단의 Pages에서 학습/퀴즈/단어장/통계 페이지로 이동하게 될 거예요.")

st.caption(f"버전: {config.VERSION}")
