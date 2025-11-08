import streamlit as st
from utils.session_manager import (
    set_current_page,
    get_current_user,
    require_teacher_or_admin,
    add_message,
    get_messages,
    get_current_session_id,
    clear_messages,
    new_conversation_for_current_page,
)
from utils.helpers import (
    render_sidebar_navigation,
    render_sidebar_auth_controls,
    render_auth_modals,
)
from database.supabase_manager import save_conversation, get_category_by_name
from ai.deepseek_handler import stream_chat_response


st.set_page_config(page_title="주식 트렌드", page_icon="📊", layout="wide")
set_current_page("stock_trends")


def _system_prompt(market: str, horizon: str, tone: str, focuses: list[str]) -> str:
    focus_str = ", ".join(focuses) if focuses else "전반적 동향"
    return (
        "당신은 교사용 주식 시장 트렌드 분석가입니다. "
        "미국/한국 주식의 최근 동향과 전망을 교육용으로 설명하세요. "
        "종목(개별 티커) 언급이나 추천은 절대 하지 마세요. "
        "가능하면 지수/섹터/거시 지표 수준에서만 다루세요.\n\n"
        f"시장: {market} / 기간: {horizon} / 톤: {tone} / 포커스: {focus_str}.\n"
        "출력 형식:\n"
        "1) 개요(핵심 트렌드 3~5개 요약)\n"
        "2) 거시/유동성: 금리, 인플레이션, 경기, 달러, 유동성 흐름\n"
        "3) 섹터 하이라이트: 2~4개 섹터의 상대 흐름과 논점\n"
        "4) 실적/밸류에이션 관점(지수/섹터 레벨)\n"
        "5) 전망: 기본/낙관/비관 시나리오와 촉발 요인\n"
        "6) 리스크/관찰 포인트: 정책, 지정학, 변동성, 이벤트\n"
        "7) 정리: 수업용 요약 문장 3줄\n\n"
        "주의사항: 최신성을 의도하되 특정 날짜/수치 단정은 피하고, "
        "특정 종목 추천/언급 금지. 교육 목적 고지 포함."
    )


def _build_user_prompt(question: str, market: str, horizon: str, focuses: list[str]) -> str:
    focus_str = ", ".join(focuses) if focuses else "전반적 동향"
    base = (
        f"[{market}] 주식 시장의 {horizon} 트렌드와 전망을 {focus_str} 관점에서 설명해줘. "
        "개별 종목은 언급하지 말고 지수/섹터/거시 수준에서만 다뤄줘."
    )
    if question.strip():
        return base + "\n추가 질문: " + question.strip()
    return base


def main():
    with st.sidebar:
        render_sidebar_navigation()
        render_sidebar_auth_controls()
    render_auth_modals()
    require_teacher_or_admin()
    user = get_current_user()
    set_current_page("stock_trends")

    st.title("📊 주식 트렌드")
    st.caption("미국/한국 주식의 최신 트렌드 및 전망(종목 검색/추천 금지)")

    with st.expander("요청 옵션", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            market = st.selectbox("시장", ["미국", "한국"], index=0)
        with col2:
            horizon = st.selectbox(
                "기간",
                ["단기(1~3개월)", "중기(6~12개월)", "장기(12개월 이상)"],
                index=0,
            )
        with col3:
            tone = st.selectbox("톤", ["보수적", "중립", "적극적"], index=1)

        focuses = st.multiselect(
            "포커스",
            [
                "거시경제",
                "금리/유동성",
                "섹터 동향",
                "실적 모멘텀",
                "밸류에이션",
                "리스크 요인",
                "정책/규제",
                "자금 흐름",
            ],
            default=["거시경제", "섹터 동향"],
        )

    # 채팅 영역
    st.subheader("대화")
    messages = get_messages()
    for m in messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    question = st.chat_input("트렌드/전망에 대해 궁금한 점을 적어주세요…")
    if question is not None:
        # 사용자 원문 메시지 먼저 표시용으로 추가
        add_message("user", question)

        # 옵션을 반영한 보강 프롬프트 생성
        enriched_user = _build_user_prompt(question, market, horizon, focuses)

        # 기존 메시지 목록을 스트리밍 입력 형식으로 변환하면서 마지막 사용자 발화를 보강 프롬프트로 대체
        base_msgs = [{"role": m["role"], "content": m["content"]} for m in get_messages()]
        if base_msgs and base_msgs[-1]["role"] == "user":
            base_msgs[-1]["content"] = enriched_user

        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""

        for chunk in stream_chat_response(
            category='stocks_expert',
            grade=user.get('grade'),
            is_teacher=True,
            conversation_messages=base_msgs,
            temperature=st.session_state.get('ai_temperature', 0.7),
            max_tokens=st.session_state.get('ai_max_tokens', 800),
        ):
            full_text += chunk or ""
            placeholder.markdown(full_text)

        # 스트리밍 결과 반영 및 저장
        if full_text.strip():
            add_message("assistant", full_text)
            try:
                cat = get_category_by_name("stocks_expert")
                category_id = cat["id"] if isinstance(cat, dict) else cat
                session_id = get_current_session_id()
                save_conversation(
                    user_id=user["id"],
                    category_id=category_id,
                    user_message=f"{enriched_user}\n\n[옵션] 시장={market}, 기간={horizon}, 톤={tone}, 포커스={', '.join(focuses)}",
                    ai_response=full_text,
                    session_id=session_id,
                )
            except Exception as e:
                st.warning(f"대화 저장 중 문제가 발생했습니다: {e}")
            st.rerun()

    st.info(
        "이 콘텐츠는 교육 목적의 시장 동향 안내입니다. 특정 종목(티커) 언급 및 투자 추천은 포함하지 않습니다."
    )

    # 페이지 전용 컨트롤: 다른 챗봇 세션 목록을 불러오지 않고 이 페이지 대화만 관리합니다.
    col1, col2 = st.columns(2)
    with col1:
        if st.button("대화 비우기"):
            clear_messages()
            st.rerun()
    with col2:
        if st.button("새 대화 시작"):
            new_conversation_for_current_page()
            st.rerun()


if __name__ == "__main__":
    main()