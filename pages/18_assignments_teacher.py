import streamlit as st

from utils.session_manager import require_teacher_or_admin, get_current_user
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation, show_success, show_error
from database.supabase_manager import (
    create_assignment,
    list_assignments,
    list_submissions,
    grade_submission,
    assignment_stats,
)
import config
from datetime import datetime, time

st.set_page_config(page_title="📝 과제 출제", page_icon="📝", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_teacher_or_admin()
user = get_current_user()

st.title("📝 과제 출제 (교사용)")
st.caption("과제를 만들고, 제출 현황을 확인하고, 학생별 통계를 볼 수 있어요.")

tab_create, tab_submissions, tab_stats = st.tabs(["과제 출제", "제출 현황/채점", "통계"])

with tab_create:
    st.subheader("새 과제 만들기")
    with st.form("create_assignment_form"):
        title = st.text_input("제목", placeholder="예: 영어 어휘 테스트(1주차)")
        description = st.text_area("설명", placeholder="과제 설명을 적어주세요")
        grade_opt = ["전체 학년"] + config.GRADES
        grade_choice = st.selectbox("대상 학년", options=grade_opt, index=0)
        due_date_d = st.date_input("마감 날짜", value=None)
        due_date_t = st.time_input("마감 시간", value=time(23, 59))
        is_active = st.checkbox("활성화", value=True, help="비활성화하면 학생에게 보이지 않아요")
        submitted = st.form_submit_button("과제 생성")

        if submitted:
            if not title:
                show_error("제목을 입력하세요.")
            else:
                grade_val = None if grade_choice == "전체 학년" else grade_choice
                due_val = None
                try:
                    if due_date_d:
                        due_val = datetime.combine(due_date_d, due_date_t)
                except Exception:
                    due_val = None
                created = create_assignment(
                    created_by=user['id'],
                    title=title,
                    description=description,
                    grade=grade_val,
                    due_date=due_val,
                    is_active=is_active,
                )
                if created:
                    show_success("과제를 생성했어요!")
                else:
                    show_error("과제 생성 중 오류가 발생했어요.")

    st.divider()
    st.subheader("내가 만든 과제")
    my_assignments = list_assignments(created_by=user['id'], active_only=False)
    if my_assignments:
        for a in my_assignments:
            with st.container(border=True):
                st.markdown(f"**{a.get('title')}**")
                desc = a.get('description') or ""
                if desc:
                    st.caption(desc)
                st.write(f"대상 학년: {a.get('target_grade') or '전체'} / 활성화: {'✅' if a.get('is_active') else '❌'}")
                st.write(f"마감: {a.get('due_date') or '없음'} / 생성: {a.get('created_at')}")
    else:
        st.info("아직 만든 과제가 없어요.")

with tab_submissions:
    st.subheader("제출 현황 및 채점")
    my_assignments = list_assignments(created_by=user['id'], active_only=False)
    options = {a['id']: a['title'] for a in my_assignments} if my_assignments else {}
    if not options:
        st.info("먼저 과제를 만들어 주세요.")
    else:
        selected_id = st.selectbox("과제 선택", options=list(options.keys()), format_func=lambda x: options.get(x, str(x)))
        subs = list_submissions(selected_id)
        if subs:
            for srow in subs:
                with st.container(border=True):
                    st.markdown(f"**학생 ID:** {srow.get('student_id')} · **상태:** {srow.get('status')}")
                    st.caption(f"선택: {srow.get('created_at')} / 제출: {srow.get('submitted_at')} / 채점: {srow.get('graded_at')}")
                    # 답안 요약 표시
                    text_ans = srow.get('answer_text')
                    if text_ans:
                        st.write("학생 답안")
                        st.code(str(text_ans))

                    # 채점 입력
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        score_val = st.number_input("점수", min_value=0, max_value=100, value=int(srow.get('score') or 0), key=f"score_{srow['id']}")
                    with col2:
                        feedback_val = st.text_input("피드백", value=srow.get('feedback') or "", key=f"feedback_{srow['id']}")
                    with col3:
                        if st.button("채점 저장", key=f"grade_btn_{srow['id']}"):
                            ok = grade_submission(srow['id'], score=score_val, feedback=feedback_val)
                            if ok:
                                show_success("채점을 저장했어요.")
                                st.rerun()
                            else:
                                show_error("채점 저장 중 오류가 발생했어요.")
        else:
            st.caption("아직 제출/선택 내역이 없어요.")

with tab_stats:
    st.subheader("과제별 통계")
    my_assignments = list_assignments(created_by=user['id'], active_only=False)
    options = {a['id']: a['title'] for a in my_assignments} if my_assignments else {}
    if not options:
        st.info("먼저 과제를 만들어 주세요.")
    else:
        selected_id = st.selectbox("과제 선택", options=list(options.keys()), format_func=lambda x: options.get(x, str(x)), key="stats_select")
        stats = assignment_stats(selected_id)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("선택 수", stats.get('selected', 0))
        with col2:
            st.metric("제출 수", stats.get('submitted', 0))
        with col3:
            st.metric("채점 수", stats.get('graded', 0))
        with col4:
            avg = stats.get('avg_score')
            st.metric("평균 점수", f"{avg:.1f}" if avg is not None else "-")