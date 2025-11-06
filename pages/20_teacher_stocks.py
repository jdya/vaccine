import streamlit as st
from utils.session_manager import require_teacher_or_admin, get_current_user
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation, show_error, show_success

import csv
from io import StringIO
from urllib.request import urlopen
from datetime import datetime, timedelta

st.set_page_config(page_title="📈 주식", page_icon="📈", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_teacher_or_admin()
user = get_current_user()

st.title("📈 주식 (교사용)")
st.caption("무료 데이터 소스(Stooq) 기반으로 간단한 시세와 차트를 확인합니다.")

col_a, col_b, col_c = st.columns([2, 1, 1])
with col_a:
    base_ticker = st.text_input("종목 코드", value="AAPL", help="미국: AAPL, MSFT 등 / 한국: 005930, 035420 등")
with col_b:
    market = st.selectbox("시장", options=["미국", "한국"], index=0)
with col_c:
    days = st.selectbox("기간", options=[7, 30, 90, 180, 365], index=2, format_func=lambda d: f"최근 {d}일")

suffix = ".us" if market == "미국" else ".kr"
symbol = f"{base_ticker.lower()}{suffix}"
data_url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"

def fetch_csv(url: str):
    try:
        with urlopen(url, timeout=10) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            return content
    except Exception as e:
        show_error(f"데이터를 가져오지 못했어요: {e}")
        return None

raw = fetch_csv(data_url)
if raw:
    reader = csv.DictReader(StringIO(raw))
    rows = []
    for r in reader:
        # 기본 컬럼: Date,Open,High,Low,Close,Volume
        try:
            dt = datetime.strptime(r["Date"], "%Y-%m-%d")
            close = float(r.get("Close") or 0)
            rows.append({"date": dt, "close": close})
        except Exception:
            continue

    if rows:
        # 기간 필터링
        cutoff = datetime.now() - timedelta(days=days)
        filtered = [x for x in rows if x["date"] >= cutoff]
        filtered.sort(key=lambda x: x["date"])  # 날짜 오름차순

        if filtered:
            # 최신 지표
            latest = filtered[-1]
            first = filtered[0]
            change = ((latest["close"] - first["close"]) / first["close"]) * 100 if first["close"] else 0

            m1, m2 = st.columns(2)
            with m1:
                st.metric("최신 종가", f"{latest['close']:.2f}")
            with m2:
                st.metric("기간 변동률", f"{change:.2f}%")

            # 차트 (pandas/plotly이 없을 경우 기본 라인차트)
            try:
                import pandas as pd
                df = pd.DataFrame(filtered)
                df.set_index("date", inplace=True)
                st.line_chart(df["close"], height=300)
            except Exception:
                st.line_chart([x["close"] for x in filtered], height=300)

            st.caption(f"데이터 출처: Stooq ({symbol})")
        else:
            st.info("선택한 기간에 데이터가 없어요. 기간을 늘려보세요.")
    else:
        st.info("데이터를 파싱하지 못했어요. 종목 코드/시장 설정을 확인하세요.")
else:
    st.stop()