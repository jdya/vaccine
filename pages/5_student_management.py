#pip install streamlit

# ========================================
# 학생 관리 (교사용, 간단 체험용)
# ========================================

import streamlit as st

from utils.session_manager import require_teacher_or_admin, get_current_user
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation
from database.supabase_manager import get_students_by_teacher

st.set_page_config(page_title="👥 학생 관리", page_icon="👥", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_teacher_or_admin()
user = get_current_user()

st.title("👥 학생 관리")

if user['role'] == 'teacher':
    students = get_students_by_teacher(user['id'])
else:
    students = []

if students:
    st.subheader(f"내 학생 목록: {len(students)}명")
    for s in students:
        with st.container(border=True):
            st.write(f"이름: {s.get('full_name') or s.get('username')} / 아이디: {s.get('username')} / 학년: {s.get('grade')}")
else:
    st.info("아직 학생이 없어요. 사이드바에서 학생 인증코드를 만들어 공유해보세요.")
