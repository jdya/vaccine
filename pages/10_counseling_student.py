#pip install streamlit openai

# ========================================
# 교사용: 학생 상담 도우미 (고도화)
# ========================================

import streamlit as st

from utils.session_manager import get_current_user, add_message, get_messages, clear_messages, set_current_page, get_current_session_id, new_conversation_for_current_page
from ai.deepseek_handler import generate_chat_response, stream_chat_response
from database.supabase_manager import get_category_by_name, save_conversation
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation, render_new_chat_controls

st.set_page_config(page_title="💭 학생 상담", page_icon="💭", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
user = get_current_user()
set_current_page('student_counseling')

st.title("💭 학생 고민 상담")

stype = st.selectbox("어떤 고민이에요?", ["공부","친구","학교생활","집/가정","진로","기타"], index=0)

with st.expander("간단한 내 상황 (선택)", expanded=False):
    sev = st.slider("요즘 마음이 얼마나 힘들어요?", 1, 5, 3)
    duration = st.selectbox("얼마나 오래 걱정됐나요?", ["1주 미만","1~4주","1~3개월","3개월 이상"])
    tried = st.multiselect("이미 해본 것", ["친구/가족과 이야기","선생님께 상담","일기 쓰기","운동하거나 쉬기","계획 세우기"]) 

with st.container(border=True):
    st.subheader("대화")
    last_ai = None
    for m in get_messages():
        st.chat_message(m['role']).write(m['content'])
        if m['role'] == 'assistant':
            last_ai = m['content']

    prompt = st.chat_input("편하게 고민을 적어줘. 함께 방법을 찾아볼게!")
    if prompt:
        meta = f"[상담유형:{stype}] [심각도:{sev}] [지속:{duration}] [시도:{','.join(tried) if tried else '없음'}]"
        enriched = f"{meta}\n{prompt}"
        add_message('user', enriched)
        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""
        for chunk in stream_chat_response(
            category='counseling',
            grade=(user or {}).get('grade'),
            is_teacher=False,
            conversation_messages=[{"role": m['role'], "content": m['content']} for m in get_messages()],
            temperature=st.session_state.get('ai_temperature', 0.7),
            max_tokens=st.session_state.get('ai_max_tokens', 800)
        ):
            full_text += chunk or ""
            placeholder.markdown(full_text)

        if full_text.strip():
            add_message('assistant', full_text)
            cat_row = get_category_by_name('counseling')
            if cat_row and user:
                save_conversation(user['id'], cat_row['id'], enriched, full_text, session_id=get_current_session_id(), is_private=False)
            st.rerun()

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("대화 비우기"):
        clear_messages()
        st.rerun()
with col2:
    if last_ai:
        st.download_button("🗂️ 함께 정리한 내용 다운로드(.txt)", data=last_ai, file_name="my_counseling_notes.txt")
with col3:
    render_new_chat_controls(page_key='student_counseling', category_name='counseling')
