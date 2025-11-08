import streamlit as st

from utils.session_manager import require_teacher_or_admin, get_current_user
from utils.helpers import (
    render_auth_modals,
    render_sidebar_auth_controls,
    render_sidebar_navigation,
    show_success,
    show_error,
)
from database.supabase_manager import create_question_bank_item, list_question_bank_items
from quiz.quiz_generator import generate_quiz


st.set_page_config(page_title="🏫 중학교 문제은행", page_icon="🏫", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_teacher_or_admin()
user = get_current_user()

st.title("🏫 중학교 문제은행")
st.caption("중학생 수준에 맞는 문항을 AI로 생성하고 저장할 수 있어요.")


# 과목 라벨 ↔ 카테고리 키 매핑
SUBJECT_MAP = {
    "영어": "english",
    "수학": "math",
    "과학": "science",
    "국어": "korean",
    "코딩": "coding",
    "역사": "history",
    "독서": "reading",
    "영어문법": "english_grammar",
}


tab_make, tab_list = st.tabs(["문제 생성", "문항 목록"])

with tab_make:
    st.subheader("AI로 중학교 문제 생성")
    with st.form("ms_qb_gen_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            subject_label = st.selectbox("과목", options=list(SUBJECT_MAP.keys()), index=1)
            grade = "중학생"  # 고정 톤 적용
            st.text_input("학년", value=grade, disabled=True, help="중학생 기준으로 생성합니다.")
        with col2:
            quiz_type = st.selectbox("유형", options=["multiple", "true_false", "short_answer"], index=0)
            count = st.number_input("문제 수", min_value=1, max_value=20, value=5, step=1)
        with col3:
            difficulty = st.slider("난이도", min_value=1, max_value=5, value=3)
        submit = st.form_submit_button("생성")

    if submit:
        category = SUBJECT_MAP.get(subject_label, "english")
        data = generate_quiz(
            category=category,
            grade=grade,
            quiz_type=quiz_type,
            count=int(count),
            difficulty=int(difficulty),
        )
        st.session_state.ms_qb_generated = data.get("questions", [])
        if st.session_state.ms_qb_generated:
            show_success(f"{len(st.session_state.ms_qb_generated)}문제를 생성했어요.")
        else:
            show_error("생성된 문제가 없어요.")

    generated = st.session_state.get("ms_qb_generated", [])
    if generated:
        st.write("아래 문제들을 검토하고 저장하세요.")
        cols = st.columns(2)
        with cols[0]:
            save_all = st.button("모두 저장")
        with cols[1]:
            st.button("새로 생성", on_click=lambda: st.session_state.pop("ms_qb_generated", None))

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
                    category=SUBJECT_MAP.get(st.session_state.get('ms_subject_label', subject_label), 'english'),
                    grade="중학생",
                    difficulty=int(difficulty),
                    tags=["중학교", subject_label],
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
                if st.button("저장", key=f"ms_save_{i}"):
                    item = create_question_bank_item(
                        created_by=user['id'],
                        qtype=q.get('type') or quiz_type,
                        question=q.get('question', ''),
                        options=q.get('options') or [],
                        answer=str(q.get('answer') or ''),
                        explanation=q.get('explanation') or None,
                        category=SUBJECT_MAP.get(st.session_state.get('ms_subject_label', subject_label), 'english'),
                        grade="중학생",
                        difficulty=int(difficulty),
                        tags=["중학교", subject_label],
                    )
                    if item:
                        show_success("저장했어요.")
                    else:
                        show_error("저장 실패")


with tab_list:
    st.subheader("내 중학교 문항 목록")
    f_col1, f_col2, f_col3 = st.columns([1,1,1])
    with f_col1:
        f_subject = st.selectbox("과목 필터", options=["(전체)"] + list(SUBJECT_MAP.keys()), index=0)
    with f_col2:
        f_search = st.text_input("검색어", value="")
    with f_col3:
        refresh = st.button("새로고침")

    if refresh:
        st.session_state._ms_qb_list_refresh = True

    # 목록 조회 및 중학생 필터
    cat = SUBJECT_MAP.get(f_subject) if f_subject and f_subject != "(전체)" else None
    items = list_question_bank_items(
        created_by=user['id'],
        category=cat,
        search=(f_search.strip() or None),
        limit=300,
    )
    items = [it for it in items if (it.get('grade') or '') == '중학생']

    if items:
        st.caption(f"총 {len(items)}문항")
        for it in items:
            with st.container(border=True):
                st.write(f"[{it.get('type')}] {it.get('question')}")
                opts = it.get('options') or []
                if isinstance(opts, list) and opts:
                    st.caption("보기: " + " | ".join([str(o) for o in opts]))
                st.caption(
                    f"정답: {it.get('answer')} / 난이도: {it.get('difficulty') or '-'} / 카테고리: {it.get('category') or '-'} / 태그: {', '.join(it.get('tags') or [])}"
                )
                st.caption(f"작성시각: {it.get('created_at')}")
    else:
        st.info("아직 중학교 문항이 없어요. 위에서 생성하거나 저장해보세요.")