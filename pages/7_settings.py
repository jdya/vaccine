#pip install streamlit

# ========================================
# 설정 페이지 (간단 체험용)
# ========================================

import streamlit as st

from utils.session_manager import require_login, get_current_user, login_user
from database.supabase_manager import update_user, get_user_by_id
from utils.helpers import show_success, show_error, write_text_file
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation

st.set_page_config(page_title="⚙️ 설정", page_icon="⚙️", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_login()
user = get_current_user()

st.title("⚙️ 설정")

st.subheader("내 정보")
with st.container(border=True):
    st.write(f"**아이디:** {user.get('username')}")
    st.write(f"**이름:** {user.get('full_name')}")
    st.write(f"**역할:** {user.get('role')}")
    if user.get('role') == 'student':
        st.write(f"**학년:** {user.get('grade')}")

st.divider()

st.subheader("이름 변경")
with st.form("update_name_form"):
    new_name = st.text_input(
        "새 이름",
        value=user.get('full_name') or user.get('username'),
        key="new_name_input",
        help="이름을 변경할 수 있습니다. 비워두면 아이디가 이름으로 사용됩니다."
    )
    submitted = st.form_submit_button("이름 변경", use_container_width=True)
    
    if submitted:
        if not new_name or not new_name.strip():
            # 비워두면 아이디를 기본값으로 사용
            new_name = user.get('username')
        
        if update_user(user.get('id'), full_name=new_name.strip()):
            # 데이터베이스에서 업데이트된 사용자 정보를 다시 가져와서 세션 업데이트
            updated_user = get_user_by_id(user.get('id'))
            if updated_user:
                login_user({
                    'id': updated_user.get('id'),
                    'username': updated_user.get('username'),
                    'full_name': updated_user.get('full_name'),
                    'role': updated_user.get('role'),
                    'grade': updated_user.get('grade'),
                })
            show_success("이름이 변경되었습니다!")
            st.rerun()
        else:
            show_error("이름 변경 중 오류가 발생했습니다.")

st.divider()

st.subheader("색깔 테마")
pastel_themes = {
    "블로썸 핑크": {
        "primaryColor": "#FF6B9D",
        "backgroundColor": "#FFFBF5",
        "secondaryBackgroundColor": "#FFE5EC",
        "textColor": "#2C3E50",
    },
    "민트 그린": {
        "primaryColor": "#7BD389",
        "backgroundColor": "#F7FFF8",
        "secondaryBackgroundColor": "#E8F5E9",
        "textColor": "#2C3E50",
    },
    "스카이 블루": {
        "primaryColor": "#76B3E6",
        "backgroundColor": "#F5FBFF",
        "secondaryBackgroundColor": "#E8F1F8",
        "textColor": "#2C3E50",
    },
    "라벤더 퍼플": {
        "primaryColor": "#B58ED7",
        "backgroundColor": "#FBF7FF",
        "secondaryBackgroundColor": "#EEE8F9",
        "textColor": "#2C3E50",
    },
    "피치 오렌지": {
        "primaryColor": "#FFB07C",
        "backgroundColor": "#FFF8F2",
        "secondaryBackgroundColor": "#FEE9D6",
        "textColor": "#2C3E50",
    },
}

with st.container(border=True):
    theme_name = st.selectbox("테마 선택", list(pastel_themes.keys()), index=0)
    theme = pastel_themes[theme_name]

    # 간단 미리보기
    st.write("미리보기")
    st.markdown(
        f"""
        <div style='border:1px solid #ddd; border-radius:8px; overflow:hidden;'>
          <div style='background:{theme["backgroundColor"]}; padding:12px;'>
            <div style='background:{theme["secondaryBackgroundColor"]}; padding:12px; border-radius:6px;'>
              <span style='color:{theme["textColor"]};'>텍스트</span>
              <button style='margin-left:8px; background:{theme["primaryColor"]}; color:white; border:none; padding:6px 10px; border-radius:4px;'>버튼</button>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("테마 저장", use_container_width=True):
        # config.toml 전체를 다시 작성하여 테마를 저장 (서버/클라이언트 설정은 유지)
        config_text = f"""
[theme]
primaryColor = "{theme['primaryColor']}"
backgroundColor = "{theme['backgroundColor']}"
secondaryBackgroundColor = "{theme['secondaryBackgroundColor']}"
textColor = "{theme['textColor']}"
font = "sans serif"

[server]
headless = true
maxUploadSize = 200
enableXsrfProtection = true
enableCORS = false

[client]
showSidebarNavigation = false
"""
        write_text_file(".streamlit/config.toml", config_text.strip())
        show_success("테마를 저장했어요! 새로고침하면 적용됩니다.")

st.divider()

st.subheader("대화 설정")
with st.container(border=True):
    confirm_default = st.session_state.get('confirm_on_new_chat', True)
    clear_default = st.session_state.get('clear_on_new_chat', True)

    confirm_toggle = st.checkbox(
        "새 대화 시작 시 확인 창 띄우기",
        value=confirm_default,
        help="실수로 대화를 지우지 않도록 새 대화 전에 확인합니다."
    )
    clear_toggle = st.checkbox(
        "새 대화 시 기존 메시지 비우기",
        value=clear_default,
        help="끄면 새 세션을 시작해도 이전 메시지를 그대로 유지합니다."
    )

    if st.button("대화 설정 저장", use_container_width=True):
        st.session_state.confirm_on_new_chat = confirm_toggle
        st.session_state.clear_on_new_chat = clear_toggle
        show_success("대화 설정을 저장했어요! 새 대화 버튼에 즉시 반영됩니다.")
