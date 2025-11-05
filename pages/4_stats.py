#pip install streamlit plotly pandas

# ========================================
# 통계 대시보드 (개인 통계 연결)
# ========================================

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.session_manager import require_login, get_current_user
from database.supabase_manager import fetch_recent_conversations, get_quiz_attempts
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation

st.set_page_config(page_title="📊 통계", page_icon="📊", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_login()
user = get_current_user()

st.title("📊 나의 학습 통계")

# 대화 기록 로드
convs = fetch_recent_conversations(user_id=user['id'], limit=200)
quizzes = get_quiz_attempts(user_id=user['id'])

# 요약
total_msgs = len(convs)
quiz_total = len(quizzes)
quiz_correct = sum(1 for q in quizzes if q.get('is_correct'))
quiz_acc = round((quiz_correct/quiz_total*100) if quiz_total else 0, 1)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("대화 메시지 수", total_msgs)
with col2:
    st.metric("퀴즈 시도 수", quiz_total)
with col3:
    st.metric("퀴즈 정답률", f"{quiz_acc}%")

# 일자별 메시지 수 그래프
if convs:
    df_msgs = pd.DataFrame([
        {"date": c.get('created_at', '')[:10], "count": 1, "category": c.get('category_id')} for c in convs
    ])
    daily = df_msgs.groupby('date')['count'].sum().reset_index()
    fig = px.bar(daily, x='date', y='count', title='일자별 대화 메시지 수')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("아직 대화 기록이 충분하지 않아요.")

# 퀴즈 정확도 표
if quizzes:
    df_q = pd.DataFrame([
        {"date": q.get('created_at', '')[:10], "correct": 1 if q.get('is_correct') else 0} for q in quizzes
    ])
    daily_q = df_q.groupby('date')['correct'].mean().reset_index()
    daily_q['accuracy(%)'] = (daily_q['correct']*100).round(1)
    st.subheader("일자별 퀴즈 정확도")
    st.dataframe(daily_q[['date','accuracy(%)']], use_container_width=True)
else:
    st.info("퀴즈 기록이 아직 없어요.")
