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


st.set_page_config(page_title="📈 추천주식", page_icon="📈", layout="wide")
set_current_page("stock_recommendations")


def _build_user_prompt(
    base_question: str,
    market: str,
    style: str,
    risk: str,
    horizon: str,
    sectors: list[str],
    count: int,
    min_cap: str,
) -> str:
    sector_str = ", ".join(sectors) if sectors else "제한 없음"
    base = (
        "교사용 교육 목적의 관심종목/ETF 제안을 해주세요. "
        "구체적 매수/매도 추천은 하지 말고, 후보 리스트와 선택 이유(간단 논리)를 제시해주세요. "
        "가능하면 유동성/거시 환경을 간단히 고려하고, 리스크/주의사항도 덧붙여주세요.\n\n"
        f"시장: {market} / 스타일: {style} / 위험 선호: {risk} / 기간: {horizon}\n"
        f"섹터: {sector_str} / 제안 수: {count} / 최소 시총: {min_cap or '기준 없음'}\n"
        "출력 형식:\n"
        "1) 후보 목록: 티커/이름(가능하면), 한 줄 이유\n"
        "2) 간단 근거: 스타일/섹터/거시 관점에서의 적합성\n"
        "3) 대안/분산 아이디어: ETF 또는 다른 섹터\n"
        "4) 리스크/주의: 과도한 확신을 피하고 주의점 명시\n"
        "주의: 투자 권유가 아니며, 학습용 관심종목 제안입니다.\n"
    )
    if base_question.strip():
        return base + "추가 조건/요청: " + base_question.strip()
    return base


def main():
    with st.sidebar:
        render_sidebar_navigation()
        render_sidebar_auth_controls()
    render_auth_modals()
    require_teacher_or_admin()
    user = get_current_user()
    set_current_page("stock_recommendations")

    st.title("📈 추천주식 (교사용)")
    st.caption("교육 목적의 관심종목/ETF 제안. 투자 권유가 아닙니다.")

    with st.expander("요청 옵션", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            market = st.selectbox("시장", ["미국", "한국"], index=0)
        with col2:
            style = st.selectbox("스타일", ["성장", "가치", "배당", "모멘텀", "혼합"], index=4)
        with col3:
            risk = st.selectbox("위험 선호", ["보수적", "중간", "공격적"], index=1)

        col4, col5, col6 = st.columns(3)
        with col4:
            horizon = st.selectbox("기간", ["단기(1~3개월)", "중기(6~12개월)", "장기(12개월 이상)"], index=1)
        with col5:
            sectors = st.multiselect(
                "섹터(선택)",
                [
                    "IT/테크",
                    "반도체",
                    "통신/미디어",
                    "헬스케어",
                    "금융",
                    "산업재",
                    "소비재",
                    "에너지",
                    "원자재",
                    "유틸리티",
                ],
                default=[],
            )
        with col6:
            count = st.slider("제안 수", min_value=3, max_value=8, value=5)

        min_cap = st.text_input("최소 시총(예: 미국 $5B / 한국 2조원)", value="")

    # 기존 메시지 보여주기
    st.subheader("대화")
    for m in get_messages():
        st.chat_message(m["role"]).write(m["content"])

    question = st.chat_input("조건을 적거나 바로 제안을 요청해보세요…")
    if question is not None:
        add_message("user", question)

        enriched_user = _build_user_prompt(
            base_question=question,
            market=market,
            style=style,
            risk=risk,
            horizon=horizon,
            sectors=sectors,
            count=count,
            min_cap=min_cap,
        )

        # 마지막 사용자 메시지를 보강 프롬프트로 교체
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

        if full_text.strip():
            add_message("assistant", full_text)
            cat_row = get_category_by_name('stocks_expert')
            try:
                if cat_row:
                    save_conversation(
                        user_id=user['id'],
                        category_id=cat_row['id'],
                        user_message=(
                            f"[추천 요청]\n시장={market}, 스타일={style}, 위험={risk}, 기간={horizon}, "
                            f"섹터={', '.join(sectors) if sectors else '제한 없음'}, 제안 수={count}, 최소 시총={min_cap or '없음'}\n\n"
                            + question
                        ),
                        ai_response=full_text,
                        session_id=get_current_session_id(),
                        is_private=False,
                    )
            except Exception as e:
                st.warning(f"대화 저장 중 문제가 발생했습니다: {e}")
            st.rerun()

    st.info(
        "교육 목적의 관심종목/ETF 제안입니다. 투자 권유가 아니며 구체적 매수/매도 추천을 포함하지 않습니다."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("대화 지우기"):
            clear_messages()
            st.rerun()
    with col2:
        render_new_chat_controls(page_key='stock_recommendations', category_name='stocks_expert')


if __name__ == "__main__":
    main()