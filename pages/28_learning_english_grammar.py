import streamlit as st

from utils.session_manager import require_login, get_current_user, add_message, get_messages, clear_messages, set_current_page, get_current_session_id
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation
from ai.deepseek_handler import stream_chat_response
from database.supabase_manager import get_category_by_name, save_conversation

st.set_page_config(page_title="📚 학습 - 영어문법", page_icon="📚", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_login()
user = get_current_user()
set_current_page('learning_english_grammar')

st.title("📚 학습 - 영어문법")
st.caption("규칙→예문→오류 교정→연습 순으로 문법을 익혀요.")

with st.container(border=True):
    st.subheader("대화")
    for m in get_messages():
        st.chat_message(m['role']).write(m['content'])

    prompt = st.chat_input("문법 주제를 입력하세요… 예: 현재완료와 과거의 차이")
    if prompt:
        add_message('user', prompt)
        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""
        for chunk in stream_chat_response(
            category='english_grammar',
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
            cat_row = get_category_by_name('english_grammar')
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
    st.caption("형태-의미-사용 맥락을 함께 보고 최소-확장 예문으로 연습해요.")