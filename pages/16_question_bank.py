#pip install streamlit

# ========================================
# 문제은행 (교사용)
# ========================================

import streamlit as st

from utils.session_manager import require_teacher_or_admin, get_current_user
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation, show_success, show_error
from database.supabase_manager import create_question_bank_item, list_question_bank_items
from quiz.quiz_generator import generate_quiz


st.set_page_config(page_title="📚 문제은행", page_icon="📚", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_teacher_or_admin()
user = get_current_user()

st.title("📚 문제은행")
st.caption("교사가 만든 문항을 저장하고 관리할 수 있어요.")

tab_make, tab_list = st.tabs(["문제 생성", "문항 목록"])

with tab_make:
    st.subheader("AI로 문제 생성")
    with st.form("qb_gen_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            category = st.text_input("카테고리", value="english", help="예: english, math, science, korean, coding")
            grade = st.text_input("학년", value=user.get('grade') or "")
        with col2:
            quiz_type = st.selectbox("유형", options=["multiple", "true_false", "short_answer"], index=0)
            count = st.number_input("문제 수", min_value=1, max_value=20, value=5, step=1)
        with col3:
            difficulty = st.slider("난이도", min_value=1, max_value=5, value=2)
        submit = st.form_submit_button("생성")
    if submit:
        data = generate_quiz(category=category, grade=grade or None, quiz_type=quiz_type, count=int(count), difficulty=int(difficulty))
        st.session_state.qb_generated = data.get("questions", [])
        if st.session_state.qb_generated:
            show_success(f"{len(st.session_state.qb_generated)}문제를 생성했어요.")
        else:
            show_error("생성된 문제가 없어요.")

    # 생성된 문제 표시 및 저장
    generated = st.session_state.get("qb_generated", [])
    if generated:
        st.write("아래 문제들을 검토하고 저장하세요.")
        cols = st.columns(2)
        with cols[0]:
            save_all = st.button("모두 저장")
        with cols[1]:
            st.button("새로 생성", on_click=lambda: st.session_state.pop("qb_generated", None))

        if save_all:
            saved = 0
            for q in generated:
                item = create_question_bank_item(
                    created_by=user['id'],
                    qtype=q.get('type') or quiz_type,
                    question=q.get('question', ''),
                    options=q.get('options') or [],
                    answer=str(q.get('answer') or ''),
                    explanation=q.get('explanation') or None,
                    category=category,
                    grade=grade or None,
                    difficulty=int(difficulty),
                    tags=[],
                )
                if item:
                    saved += 1
            if saved > 0:
                show_success(f"{saved}문제를 저장했어요.")
            else:
                show_error("저장에 실패했어요.")

        for i, q in enumerate(generated, start=1):
            with st.expander(f"문제 {i}: {q.get('question', '')[:40]}"):
                st.write(q.get('question', ''))
                opts = q.get('options') or []
                if isinstance(opts, list) and opts:
                    st.write("보기:")
                    for idx, o in enumerate(opts):
                        st.write(f"- {idx+1}. {o}")
                st.write(f"정답: {q.get('answer')}")
                if q.get('explanation'):
                    st.caption(q.get('explanation'))
                if st.button("저장", key=f"save_{i}"):
                    item = create_question_bank_item(
                        created_by=user['id'],
                        qtype=q.get('type') or quiz_type,
                        question=q.get('question', ''),
                        options=q.get('options') or [],
                        answer=str(q.get('answer') or ''),
                        explanation=q.get('explanation') or None,
                        category=category,
                        grade=grade or None,
                        difficulty=int(difficulty),
                        tags=[],
                    )
                    if item:
                        show_success("저장했어요.")
                    else:
                        show_error("저장 실패")

    # 직접 추가 섹션 제거: 요청에 따라 수동 입력 UI를 비활성화했습니다.


with tab_list:
    st.subheader("내 문항 목록")
    f_col1, f_col2, f_col3 = st.columns([1,1,1])
    with f_col1:
        f_category = st.text_input("카테고리 필터", value="")
    with f_col2:
        f_search = st.text_input("검색어", value="")
    with f_col3:
        refresh = st.button("새로고침")

    if refresh:
        st.session_state._qb_list_refresh = True

    # 목록 조회
    items = list_question_bank_items(
        created_by=user['id'],
        category=(f_category.strip() or None),
        search=(f_search.strip() or None),
        limit=200,
    )

    if items:
        st.caption(f"총 {len(items)}문항")
        for it in items:
            with st.container(border=True):
                st.write(f"[{it.get('type')}] {it.get('question')}")
                opts = it.get('options') or []
                if isinstance(opts, list) and opts:
                    st.caption("보기: " + " | ".join([str(o) for o in opts]))
                st.caption(f"정답: {it.get('answer')} / 난이도: {it.get('difficulty') or '-'} / 카테고리: {it.get('category') or '-'} / 학년: {it.get('grade') or '-'}")
                st.caption(f"작성시각: {it.get('created_at')}")
    else:
        st.info("아직 저장된 문항이 없어요. 위에서 생성하거나 직접 추가해보세요.")