#pip install streamlit plotly pandas

# ========================================
# 관리자 대시보드 (간단 통계/교사 목록 + 기간 필터/차트)
# ========================================

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.session_manager import require_login, get_current_user
from database.supabase_manager import count_all_users, count_users_by_role, count_conversations, list_teachers, fetch_recent_conversations
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation

st.set_page_config(page_title="👑 관리자", page_icon="👑", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_login()
user = get_current_user()

if user['role'] != 'super_admin':
    st.error("관리자만 접근 가능합니다.")
    st.stop()

st.title("👑 관리자 대시보드")

u_total = count_all_users()
teachers = count_users_by_role('teacher')
students = count_users_by_role('student')
convs = count_conversations()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("전체 사용자", u_total)
with col2:
    st.metric("교사 수", teachers)
with col3:
    st.metric("학생 수", students)
with col4:
    st.metric("총 대화 수", convs)

st.subheader("대화 추이 (최근 데이터 기반)")
limit = st.slider("가져올 개수(최대)", 100, 2000, 500, step=100)
rows = fetch_recent_conversations(user_id=None, limit=int(limit))
if rows:
    df = pd.DataFrame([{ 'date': r.get('created_at','')[:10], 'count': 1 } for r in rows])
    daily = df.groupby('date')['count'].sum().reset_index()
    fig = px.line(daily, x='date', y='count', title='일자별 대화 수')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("표시할 대화 데이터가 아직 충분하지 않습니다.")

st.subheader("최근 교사 목록")
rows_t = list_teachers(limit=100)
if rows_t:
    for r in rows_t:
        with st.container(border=True):
            st.write(f"아이디: {r.get('username')} / 이름: {r.get('full_name') or ''}")
            st.caption(f"가입일: {r.get('created_at','')}")
else:
    st.info("등록된 교사가 없습니다.")
