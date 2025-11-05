#pip install streamlit openai

# ========================================
# 학습 페이지 (간단 체험용)
# ========================================
# 이 페이지에서는 간단히 카테고리를 선택하고 AI와 대화해볼 수 있어요.
# 실제 서비스에서는 카테고리별 UI와 기능이 더 풍부해질 예정입니다.
# ========================================

import streamlit as st

from utils.session_manager import require_login, get_current_user, add_message, get_messages, clear_messages, set_current_page, get_current_session_id, new_conversation_for_current_page
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation, render_new_chat_controls
from ai.deepseek_handler import generate_chat_response, stream_chat_response
from voice.tts_handler import synthesize_to_file
from database.supabase_manager import get_category_by_name, save_conversation
import config


def debug_print(message, level="INFO"):
    if config.DEBUG_MODE:
        colors = {"INFO":"\033[94m","WARNING":"\033[93m","ERROR":"\033[91m","SUCCESS":"\033[92m"}
        reset = "\033[0m"
        print(f"{colors.get(level, colors['INFO'])}[PAGE-LEARN-{level}]{reset} {message}")


st.set_page_config(page_title="📚 학습", page_icon="📚", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_login()
user = get_current_user()
set_current_page('learning')

st.title("📚 학습")

# 학생/교사 모두 공통 학습 카테고리 일부만 노출 (체험용)
cat = st.selectbox("학습할 카테고리를 골라보세요:", ["english","math","science","korean","coding","free"], index=0)

# 채팅 UI (간단)
with st.container(border=True):
    st.subheader("대화")
    # 기존 메시지 표시
    last_ai_text = None
    for m in get_messages():
        if m['role'] == 'user':
            st.chat_message("user").write(m['content'])
        else:
            st.chat_message("assistant").write(m['content'])
            last_ai_text = m['content']

    # 마지막 AI 답변 음성으로 듣기
    if last_ai_text and st.button("🔊 마지막 AI 답변 듣기"):
        mp3_path = synthesize_to_file(last_ai_text, filename="learn_last_ai.mp3")
        if mp3_path:
            st.audio(mp3_path)
        else:
            st.error("음성 생성에 실패했어요.")

    # 입력
    prompt = st.chat_input("메시지를 입력하세요...")
    if prompt:
        add_message('user', prompt)
        # 스트리밍 표시 (지연 체감 감소)
        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""
        for chunk in stream_chat_response(
            category=cat,
            grade=user.get('grade'),
            is_teacher=(user.get('role') == 'teacher'),
            conversation_messages=[{"role": m['role'], "content": m['content']} for m in get_messages()],
            temperature=st.session_state.get('ai_temperature', 0.7),
            max_tokens=st.session_state.get('ai_max_tokens', 800)
        ):
            full_text += chunk or ""
            placeholder.markdown(full_text)

        if full_text.strip():
            add_message('assistant', full_text)
            # DB 저장
            cat_row = get_category_by_name(cat)
            if cat_row:
                save_conversation(
                    user_id=user['id'],
                    category_id=cat_row['id'],
                    user_message=prompt,
                    ai_response=full_text,
                    session_id=get_current_session_id(),
                    is_private=False
                )
            st.rerun()

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("대화 비우기"):
        clear_messages()
        st.rerun()
with col2:
    st.caption("카테고리와 학년에 따라 말투와 난이도가 달라져요.")
with col3:
    render_new_chat_controls(page_key='learning', category_name=cat)
