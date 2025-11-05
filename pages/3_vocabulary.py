#pip install streamlit

# ========================================
# 단어장 페이지 (간단 체험용)
# ========================================

import streamlit as st

from utils.session_manager import require_login, get_current_user
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation
from database.supabase_manager import add_vocabulary, get_user_vocabulary, update_vocabulary_mastery

st.set_page_config(page_title="📖 단어장", page_icon="📖", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_login()
user = get_current_user()

st.title("📖 나의 단어장")

with st.form("add_vocab"):
    word = st.text_input("단어")
    meaning = st.text_input("뜻")
    example = st.text_input("예문 (선택)")
    submitted = st.form_submit_button("추가하기")
    if submitted and word and meaning:
        result = add_vocabulary(user['id'], word, meaning, example, None)
        if result:
            st.success("단어가 추가되었어요!")
        else:
            st.error("추가 중 오류가 발생했어요.")

st.subheader("내 단어들")
rows = get_user_vocabulary(user['id'])
if rows:
    for r in rows:
        with st.container(border=True):
            st.markdown(f"**{r['word']}** — {r.get('meaning','')}")
            if r.get('example'):
                st.caption(r['example'])
            col1, col2 = st.columns([1,1])
            with col1:
                st.write("숙달:", "✅" if r.get('mastered') else "❌")
            with col2:
                if st.button("숙달 토글", key=f"m_{r['id']}"):
                    update_vocabulary_mastery(r['id'], not r.get('mastered'))
                    st.rerun()
else:
    st.info("아직 단어가 없어요. 위에서 추가해보세요.")
