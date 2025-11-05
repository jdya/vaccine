#pip install streamlit

# ========================================
# 인증코드 관리 (간단 체험용)
# ========================================

import streamlit as st

from utils.session_manager import require_login, get_current_user
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation
from database.supabase_manager import get_teacher_codes, get_admin_teacher_codes
from auth.invite_codes import create_teacher_code, create_student_code

st.set_page_config(page_title="🎫 인증코드", page_icon="🎫", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_login()
user = get_current_user()

st.title("🎫 인증코드 관리")

if user['role'] == 'super_admin':
    st.subheader("관리자: 교사 인증코드 만들기")
    memo = st.text_input("메모", placeholder="예: 서울초 김선생님")
    days = st.number_input("유효기간(일)", min_value=1, max_value=365, value=30)
    if st.button("교사 코드 생성"):
        code = create_teacher_code(user['id'], int(days), memo)
        if code:
            st.success(f"교사 코드: {code['code']}")
        else:
            st.error("생성 실패")

    st.caption("아래 목록에서 기존 교사 인증코드를 항상 확인할 수 있어요.")
    admin_codes = get_admin_teacher_codes(user['id'])
    if admin_codes:
        st.write("관리자가 만든 교사 인증코드 목록")
        for c in admin_codes:
            cols = st.columns([2,2,2,2,2])
            with cols[0]:
                st.code(c.get('code'))
            with cols[1]:
                st.write(f"상태: {'활성' if c.get('is_active') else '사용됨/만료'}")
            with cols[2]:
                st.write(f"만료: {c.get('expires_at') or '-'}")
            with cols[3]:
                st.write(f"사용자: {c.get('used_by') or '-'}")
            with cols[4]:
                st.write(f"메모: {c.get('memo') or ''}")
    else:
        st.info("아직 생성한 교사 인증코드가 없어요.")

if user['role'] in ('teacher','super_admin'):
    st.subheader("교사: 학생 인증코드 만들기")
    class_name = st.text_input("학급명", placeholder="예: 3학년 2반")
    uses = st.number_input("최대 사용 횟수", min_value=1, max_value=300, value=10)
    days2 = st.number_input("유효기간(일)", min_value=1, max_value=60, value=7)
    memo2 = st.text_input("메모", placeholder="예: 신입생용")
    if st.button("학생 코드 생성"):
        code = create_student_code(user['id'], class_name, int(uses), int(days2), memo2)
        if code:
            st.success(f"학생 코드: {code['code']}")
        else:
            st.error("생성 실패")

    st.caption("아래 목록에서 기존 학생 인증코드를 항상 확인할 수 있어요.")
    my_student_codes = get_teacher_codes(user['id'])
    if my_student_codes:
        st.write("내가 만든 학생 인증코드 목록")
        for c in my_student_codes:
            cols = st.columns([2,2,2,2,2])
            with cols[0]:
                st.code(c.get('code'))
            with cols[1]:
                st.write(f"사용: {c.get('used_count',0)}/{c.get('max_uses',0)}")
            with cols[2]:
                st.write(f"상태: {'활성' if c.get('is_active') else '비활성'}")
            with cols[3]:
                st.write(f"만료: {c.get('expires_at') or '-'}")
            with cols[4]:
                st.write(f"메모: {c.get('memo') or ''}")
    else:
        st.info("아직 생성한 학생 인증코드가 없어요.")
