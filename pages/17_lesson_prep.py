import streamlit as st

from utils.session_manager import require_teacher_or_admin, get_current_user, add_message, get_messages, clear_messages, set_current_page, get_current_session_id
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation, render_new_chat_controls
from ai.deepseek_handler import stream_chat_response
from database.supabase_manager import get_category_by_name, save_conversation

st.set_page_config(page_title="🧰 수업준비", page_icon="🧰", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_teacher_or_admin()
user = get_current_user()
set_current_page('lesson_prep')

st.title("🧰 수업준비 (교사용)")
st.caption("단원/학습목표/시간/평가까지 포함해 구조화된 수업안을 빠르게 준비하세요.")

with st.expander("기본 정보", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        subject = st.selectbox("과목", ["국어","영어","수학","과학","사회","정보","예체능","통합"], index=1)
        grade = st.text_input("학년", value=user.get('grade') or "")
    with col2:
        unit = st.text_input("단원/주제", value="의사소통 전략")
        duration = st.selectbox("수업 시간", ["40분","45분","50분","2차시","3차시"], index=1)
    with col3:
        emphasis = st.multiselect("강조 요소", ["핵심 개념","협력학습","형성평가","개별화","프로젝트","실험/탐구"], default=["핵심 개념","형성평가"])
        include_rubric = st.checkbox("루브릭 포함", value=True)

with st.container(border=True):
    st.subheader("대화 / 생성")
    # 기존 대화 표시
    for m in get_messages():
        st.chat_message(m['role']).write(m['content'])

    # 프롬프트 구성
    base_prompt = (
        f"[수업준비]\n과목:{subject}\n학년:{grade or '미정'}\n단원/주제:{unit}\n시간:{duration}\n"
        f"강조요소:{', '.join(emphasis) if emphasis else '기본'}\n"
        f"요청: 학습목표(명확한 성취기준 연계)→도입→전개→정리→형성평가(문항 예시)"
        + ("→루브릭" if include_rubric else "")
        + "→보정 활동(미달 학생 지원)까지 구조화해서 제시해줘."
    )

    prompt = st.chat_input("수업안 생성 요청이나 추가 지시를 입력하세요…", key="lesson_prep_input")
    if prompt:
        # 사용자 메시지 기록
        add_message('user', prompt)
        # 스트리밍 응답
        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""
        for chunk in stream_chat_response(
            category='education',  # DB/프롬프트 호환을 위해 'education' 카테고리 사용
            grade=user.get('grade'),
            is_teacher=True,
            conversation_messages=[{"role": m['role'], "content": m['content']} for m in get_messages()] + [{"role":"user","content": base_prompt}],
            temperature=st.session_state.get('ai_temperature', 0.7),
            max_tokens=st.session_state.get('ai_max_tokens', 800)
        ):
            full_text += chunk or ""
            placeholder.markdown(full_text)

        if full_text.strip():
            add_message('assistant', full_text)
            cat_row = get_category_by_name('education')
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
    st.caption("학년과 강조 요소에 맞춰 구조와 난이도가 조정돼요.")
with col3:
    render_new_chat_controls(page_key='lesson_prep', category_name='education')