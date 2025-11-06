import streamlit as st

from utils.session_manager import (
    require_teacher_or_admin,
    get_current_user,
    add_message,
    get_messages,
    clear_messages,
    set_current_page,
    get_current_session_id,
)
from utils.helpers import (
    render_auth_modals,
    render_sidebar_auth_controls,
    render_sidebar_navigation,
    render_new_chat_controls,
)
from ai.deepseek_handler import stream_chat_response
from database.supabase_manager import get_category_by_name, save_conversation

st.set_page_config(page_title="🤖 주식 챗봇", page_icon="🤖", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_teacher_or_admin()
user = get_current_user()
set_current_page('stock_chatbot')

st.title("🤖 주식 챗봇 (교사용)")
st.caption("한국 최고의 주식전문가 역할로 교육적 분석을 제공합니다. 투자 권유가 아닙니다. 질문에 종목/시장/기간 정보를 직접 포함해 주세요.")

# 입력 필드 제거: 사용자가 질문에 종목/시장/기간을 자유롭게 기술하도록 변경

# 빠른 질문 버튼
st.caption("빠른 질문")
cols = st.columns(5)
quick = [
    "단기 전망과 리스크 요인",
    "장기(12개월) 시나리오와 조건",
    "업황/거시 이슈가 미치는 영향",
    "실적/밸류에이션 간단 비교",
    "포트폴리오 관점의 분산/리밸런싱"
]
for i, q in enumerate(quick):
    if cols[i].button(q):
        add_message('user', q)

with st.container(border=True):
    st.subheader("대화")
    last_ai = None
    for m in get_messages():
        st.chat_message(m['role']).write(m['content'])
        if m['role'] == 'assistant':
            last_ai = m['content']

    prompt = st.chat_input("주식에 대해 궁금한 것을 물어보세요… (종목/시장/기간은 질문에 직접 적어주세요)")
    if prompt:
        add_message('user', prompt)
        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""
        for chunk in stream_chat_response(
            category='stocks_expert',
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
            cat_row = get_category_by_name('stocks_expert')
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
    if st.button("대화 지우기"):
        clear_messages()
        st.rerun()
with col2:
    st.caption("역할: 한국 최고의 주식전문가(교육적 분석). 구체적 매수/매도 추천은 피합니다.")
with col3:
    st.caption("실제 투자 판단은 사용자 책임입니다.")
    render_new_chat_controls(page_key='stock_chatbot', category_name='stocks_expert')