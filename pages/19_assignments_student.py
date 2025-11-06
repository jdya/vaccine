import streamlit as st

from utils.session_manager import require_role, get_current_user
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation, show_success, show_error
from database.supabase_manager import (
    list_assignments,
    get_student_submission,
    select_assignment,
    submit_assignment,
)
from datetime import datetime

st.set_page_config(page_title="📚 과제 게시판", page_icon="📚", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_role('student')
user = get_current_user()

st.title("📚 과제 게시판 (학생)")
st.caption("교사가 낸 과제를 확인하고 선택·제출할 수 있어요.")

assignments = list_assignments(created_by=None, grade=user.get('grade'), active_only=True)

if not assignments:
    st.info("현재 공개된 과제가 없어요.")
else:
    for a in assignments:
        with st.container(border=True):
            st.markdown(f"**{a.get('title')}**")
            desc = a.get('description') or ""
            if desc:
                st.caption(desc)
            due = a.get('due_date')
            st.write(f"대상 학년: {a.get('target_grade') or '전체'} / 마감: {due or '없음'}")

            # 제출 상태 확인
            sub = get_student_submission(a['id'], user['id'])
            status = sub.get('status') if sub else None
            score = sub.get('score') if sub else None
            feedback = sub.get('feedback') if sub else None
            st.caption(f"내 상태: {status or '미선택'}" + (f" · 점수 {score}" if score is not None else "") + (f" · 피드백: {feedback}" if feedback else ""))

            cols = st.columns([1, 3])
            with cols[0]:
                if st.button("선택하기", disabled=(status in ['selected','submitted','graded']), key=f"select_{a['id']}"):
                    ok = select_assignment(a['id'], user['id'])
                    if ok:
                        show_success("과제를 선택했어요.")
                        st.rerun()
                    else:
                        show_error("선택 처리 중 오류가 발생했어요.")

            with cols[1]:
                # 제출 폼 (텍스트 답안)
                with st.form(f"submit_form_{a['id']}"):
                    default_text = (sub.get('answers', {}) or {}).get('text') if sub else ""
                    answer_text = st.text_area("답안", value=default_text, placeholder="여기에 답안을 적어주세요")
                    submitted = st.form_submit_button("제출하기")
                    if submitted:
                        if not answer_text.strip():
                            show_error("답안을 입력하세요.")
                        else:
                            ok = submit_assignment(a['id'], user['id'], answers={'text': answer_text.strip()})
                            if ok:
                                show_success("답안을 제출했어요.")
                                st.rerun()
                            else:
                                show_error("제출 중 오류가 발생했어요.")