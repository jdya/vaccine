import streamlit as st

from utils.session_manager import require_login, get_current_user, add_message, get_messages, clear_messages, set_current_page, get_current_session_id
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation
from ai.deepseek_handler import stream_chat_response
from database.supabase_manager import get_category_by_name, save_conversation

st.set_page_config(page_title="💻 학습 - 코딩", page_icon="💻", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_login()
user = get_current_user()
set_current_page('learning_coding')

st.title("💻 학습 - 코딩")
st.caption("개념 설명, 코드 예제, 디버깅 힌트를 학생 눈높이에 맞게 제공합니다.")

language = st.selectbox("언어 선택", ["Python", "JavaScript", "C", "C++", "Java"], index=0)

with st.container(border=True):
    st.subheader("대화")
    for m in get_messages():
        st.chat_message(m['role']).write(m['content'])

    prompt = st.chat_input("질문/코드 조각을 입력하세요… 예: for문과 while문 차이")
    if prompt:
        enriched = f"[{language}] {prompt}"
        add_message('user', enriched)
        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""
        for chunk in stream_chat_response(
            category='coding',
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
            cat_row = get_category_by_name('coding')
            if cat_row and user:
                save_conversation(
                    user_id=user['id'],
                    category_id=cat_row['id'],
                    user_message=enriched,
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
    st.caption("코드는 단계별로 설명하고, 오류 메시지의 의미를 풀이해 드려요.")