import streamlit as st

from utils.session_manager import require_login, get_current_user, set_current_page, get_current_session_id
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation, show_success, show_error
from ai.deepseek_handler import stream_chat_response
from database.supabase_manager import get_category_by_name, save_conversation

st.set_page_config(page_title="📝 국어 글쓰기 개요", page_icon="📝", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_login()
user = get_current_user()
set_current_page('korean_outline_student')

st.title("📝 국어 글쓰기 개요 (학생)")
st.caption("주제와 핵심 키워드를 입력하면 학생 눈높이에 맞춰 개요를 만들어줘요.")

with st.form("outline_form"):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        topic = st.text_input("주제", placeholder="예: 친구와의 갈등을 해결하는 방법")
    with col2:
        keywords_raw = st.text_input("핵심 키워드(쉼표로 구분)", placeholder="예: 갈등, 대화, 존중")
    with col3:
        points = st.slider("본론 요점 개수", min_value=2, max_value=5, value=3)

    c_aud, c_style = st.columns([1,1])
    with c_aud:
        audience = st.selectbox("대상", ["초등", "청소년", "성인"], index=0)
    with c_style:
        style = st.selectbox("글 종류", ["설명문", "주장문", "서사문"], index=0)

    submit = st.form_submit_button("개요 생성하기")

if submit:
    topic_clean = (topic or "").strip()
    keywords = [k.strip() for k in (keywords_raw or "").split(",") if k.strip()]
    if not topic_clean:
        show_error("주제를 입력해주세요.")
    elif len(keywords) < 1:
        show_error("핵심 키워드를 최소 1개 이상 입력해주세요.")
    else:
        st.subheader("개요 결과")
        box = st.empty()
        full_text = ""

        # 사용자 프롬프트 구성 (국어 개요 생성 지시)
        outline_prompt = f"""
        [지시]
        - 대상: {audience} 학습자에게 맞춘 어휘/문장 난이도와 톤으로 작성하세요.
        - 글 종류: {style}
        - 주제: {topic_clean}
        - 핵심 키워드: {', '.join(keywords)}
        - 본론 요점은 {points}개로 구성하세요.
        - 각 본론 요점에는 1~2문장의 구체적 예시를 반드시 포함하세요.
        - 출력 형식(마크다운):
          제목
          서론: 배경/문제 제기(2~3문장)
          본론:
            - 요점1: 근거 / 예시
            - 요점2: 근거 / 예시
            - 요점3: 근거 / 예시
            (요점 개수는 위 지시에 맞춰 조정)
          결론: 요약과 제언(2~3문장)
        - 마지막에 "예시 모음" 섹션을 추가하여 본론의 예시 문장만 모아 다시 제시하세요.
        - 불필요한 장문 서술 없이, 개요 항목만 또렷하게 제시하세요.
        """.strip()

        for chunk in stream_chat_response(
            category='korean',
            grade=user.get('grade'),
            is_teacher=False,
            conversation_messages=[{"role": "user", "content": outline_prompt}],
            temperature=st.session_state.get('ai_temperature', 0.7),
            max_tokens=st.session_state.get('ai_max_tokens', 800)
        ):
            full_text += chunk or ""
            box.markdown(full_text)

        if full_text.strip():
            show_success("개요 생성을 완료했어요.")
            # 대화 저장 (카테고리: korean)
            try:
                cat_row = get_category_by_name('korean')
                if cat_row and user:
                    user_message = (
                        f"주제: {topic_clean}\n"
                        f"키워드: {', '.join(keywords)}\n"
                        f"종류: {style}\n"
                        f"대상: {audience}"
                    )
                    save_conversation(
                        user_id=user['id'],
                        category_id=cat_row['id'],
                        user_message=user_message,
                        ai_response=full_text,
                        session_id=get_current_session_id(),
                        is_private=False,
                    )
            except Exception:
                pass

            # 다운로드 버튼 제공
            st.download_button(
                "🗂️ 개요 다운로드(.txt)",
                data=full_text,
                file_name="korean_outline.txt",
            )
        else:
            show_error("개요 생성에 실패했어요. 다시 시도해주세요.")