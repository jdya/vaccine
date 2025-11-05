#pip install streamlit openai

# ========================================
# 교사용: 교육 상담 (고도화)
# ========================================

import streamlit as st

from utils.session_manager import require_teacher_or_admin, get_current_user, add_message, get_messages, clear_messages, set_current_page
from ai.deepseek_handler import generate_chat_response, stream_chat_response
from database.supabase_manager import get_category_by_name, save_conversation
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation

st.set_page_config(page_title="📖 교육 상담", page_icon="📖", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_teacher_or_admin()
user = get_current_user()
set_current_page('education')

st.title("📖 교육 상담 (교사용)")

st.caption("빠른 질문")
cols = st.columns(5)
quick = [
    "분수 나눗셈 수업 아이디어 5가지",
    "형성평가 문항 예시 10개",
    "학습 부진아 맞춤 전략",
    "프로젝트 수업 루브릭 템플릿",
    "차별화 수업 방안"
]
for i, q in enumerate(quick):
    if cols[i].button(q):
        add_message('user', q)
        st.session_state.trigger_edu = True

with st.container(border=True):
    st.subheader("대화")
    last_ai = None
    for m in get_messages():
        st.chat_message(m['role']).write(m['content'])
        if m['role'] == 'assistant':
            last_ai = m['content']

    do_prompt = st.chat_input("수업 아이디어/교수법/평가 등 무엇이든 질문하세요...")
    if st.session_state.get('trigger_edu') and not do_prompt:
        do_prompt = get_messages()[-1]['content'] if get_messages() else ""
        st.session_state.trigger_edu = False

    if do_prompt:
        add_message('user', do_prompt)
        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""
        for chunk in stream_chat_response(
            category='education',
            grade=user.get('grade'),
            is_teacher=True,
            conversation_messages=[{"role": m['role'], "content": m['content']} for m in get_messages()],
            temperature=st.session_state.get('ai_temperature', 0.7),
            max_tokens=st.session_state.get('ai_max_tokens', 800)
        ):
            full_text += chunk or ""
            placeholder.markdown(full_text)

        if full_text.strip():
            add_message('assistant', full_text)
            cat_row = get_category_by_name('education')
            if cat_row:
                save_conversation(user['id'], cat_row['id'], do_prompt, full_text, session_id='teacher_education', is_private=False)
            st.rerun()

col1, col2 = st.columns(2)
with col1:
    if st.button("대화 지우기"):
        clear_messages()
        st.rerun()
with col2:
    if last_ai:
        st.download_button("🗂️ 제안 다운로드(.txt)", data=last_ai, file_name="education_advice.txt")
