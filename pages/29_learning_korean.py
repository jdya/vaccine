import streamlit as st

from utils.session_manager import require_login, get_current_user, add_message, get_messages, clear_messages, set_current_page, get_current_session_id
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation
from ai.deepseek_handler import stream_chat_response
from database.supabase_manager import get_category_by_name, save_conversation

st.set_page_config(page_title="📚 학습 - 국어", page_icon="📚", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_login()
user = get_current_user()
set_current_page('learning_korean')

st.title("📚 학습 - 국어")
st.caption("문장 다듬기, 어휘 확장, 맞춤법/문법을 학생 눈높이에 맞게 설명해요.")

with st.container(border=True):
    st.subheader("대화")
    for m in get_messages():
        st.chat_message(m['role']).write(m['content'])

    prompt = st.chat_input("문장/질문을 입력하세요… 예: 이 문장을 더 자연스럽게 고쳐줘")
    if prompt:
        add_message('user', prompt)
        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""
        for chunk in stream_chat_response(
            category='korean',
            grade=user.get('grade'),
            is_teacher=False,
            conversation_messages=[{"role": m['role'], "content": m['content']} for m in get_messages()],
            temperature=st.session_state.get('ai_temperature', 0.7),
            max_tokens=st.session_state.get('ai_max_tokens', 800)
        ):
            full_text += chunk or ""
            placeholder.markdown(full_text)

        if full_text.strip():
            add_message('assistant', full_text)
            cat_row = get_category_by_name('korean')
            if cat_row and user:
                save_conversation(
                    user_id=user['id'],
                    category_id=cat_row['id'],
                    user_message=prompt,
                    ai_response=full_text,
                    session_id=get_current_session_id(),
                    is_private=False
                )
            st.rerun()

col1, col2 = st.columns(2)
with col1:
    if st.button("대화 지우기"):
        clear_messages()
        st.rerun()
with col2:
    st.caption("맞춤법 교정 시 근거 규칙을 간단히 설명해 드려요.")