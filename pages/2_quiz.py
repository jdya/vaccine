#pip install streamlit openai

# ========================================
# 퀴즈 페이지 (간단 체험용)
# ========================================
# 이 페이지에서는 간단히 퀴즈를 생성하고 풀어볼 수 있어요.
# ========================================

import streamlit as st

from utils.session_manager import require_login, get_current_user
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation
from quiz.quiz_generator import generate_quiz

st.set_page_config(page_title="🎯 퀴즈", page_icon="🎯", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_login()
user = get_current_user()

st.title("🎯 퀴즈")

col1, col2, col3 = st.columns(3)
with col1:
    category = st.selectbox("과목", ["english","math","science","korean","coding"], index=0)
with col2:
    qtype = st.selectbox("유형", ["multiple","true_false","short_answer"], index=0)
with col3:
    count = st.number_input("문항 수", min_value=1, max_value=10, value=5, step=1)

difficulty = st.slider("난이도", 1, 5, 2)

if st.button("퀴즈 생성하기"):
    data = generate_quiz(category, user.get('grade'), qtype, int(count), int(difficulty))
    st.session_state["quiz_data"] = data
    st.session_state["quiz_answers"] = {}
    st.success("퀴즈가 생성되었어요!")

quiz = st.session_state.get("quiz_data")
answers = st.session_state.get("quiz_answers", {})

if quiz:
    st.subheader("문제")
    for idx, q in enumerate(quiz.get("questions", [])):
        with st.container(border=True):
            st.markdown(f"**Q{idx+1}. {q.get('question','')}**")
            qtype = q.get("type", "multiple")
            key = f"ans_{idx}"
            if qtype == "multiple":
                options = q.get("options", ["1","2","3","4"])  # 안전장치
                answers[key] = st.radio("보기", options, key=key, index=0)
            elif qtype == "true_false":
                answers[key] = st.radio("정답 선택", ["true","false"], key=key)
            else:
                answers[key] = st.text_input("정답을 입력하세요", key=key)
            st.caption(q.get("explanation",""))
    st.session_state["quiz_answers"] = answers

    if st.button("정답 채점하기"):
        correct = 0
        total = len(quiz.get("questions", []))
        for idx, q in enumerate(quiz.get("questions", [])):
            key = f"ans_{idx}"
            user_ans = answers.get(key, "")
            real_ans = str(q.get("answer", "")).strip()
            if str(user_ans).strip().lower() == real_ans.lower():
                correct += 1
        st.success(f"점수: {correct}/{total} (정답률 {round((correct/total*100) if total else 0, 1)}%)")
else:
    st.info("먼저 '퀴즈 생성하기'를 눌러주세요.")
