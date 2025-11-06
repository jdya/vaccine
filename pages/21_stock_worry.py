import streamlit as st
from utils.session_manager import require_teacher_or_admin, get_current_user
from utils.session_manager import add_message, get_messages, clear_messages, set_current_page
from utils.helpers import render_auth_modals, render_sidebar_auth_controls, render_sidebar_navigation, show_error, show_success
from ai.deepseek_handler import stream_chat_response
from database.supabase_manager import get_category_by_name, save_conversation

import csv
from io import StringIO
from urllib.request import urlopen
from urllib.parse import quote
from datetime import datetime, timedelta
import json
import xml.etree.ElementTree as ET

st.set_page_config(page_title="💹 주식 고민", page_icon="💹", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_teacher_or_admin()
user = get_current_user()
set_current_page('stock_worry')

st.title("💹 주식 고민 (뉴스/검색/전망)")
st.caption("키워드 기반 뉴스와 웹 검색을 보고, AI로 교육적 관점의 전망을 생성합니다. 투자 권유가 아닙니다.")

col_a, col_b, col_c = st.columns([2, 1, 2])
with col_a:
    base_ticker = st.text_input("종목 코드", value="AAPL", help="미국: AAPL, MSFT / 한국: 005930(삼성전자) 등")
with col_b:
    market = st.selectbox("시장", options=["미국", "한국"], index=0)
with col_c:
    query_text = st.text_input("뉴스/검색 키워드", value="AAPL stock")

suffix = ".us" if market == "미국" else ".kr"
symbol = f"{base_ticker.lower()}{suffix}"

def fetch_stooq_csv(sym: str):
    try:
        url = f"https://stooq.com/q/d/l/?s={sym}&i=d"
        with urlopen(url, timeout=10) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        show_error(f"시세 데이터를 가져오지 못했어요: {e}")
        return None

def parse_timeseries(raw_csv: str, days: int = 90):
    reader = csv.DictReader(StringIO(raw_csv))
    items = []
    for r in reader:
        try:
            dt = datetime.strptime(r["Date"], "%Y-%m-%d")
            close = float(r.get("Close") or 0)
            items.append({"date": dt, "close": close})
        except Exception:
            continue
    cutoff = datetime.now() - timedelta(days=days)
    fil = [x for x in items if x["date"] >= cutoff]
    fil.sort(key=lambda x: x["date"])  # 날짜 오름차순
    return fil

def fetch_google_news(query: str, max_items: int = 10):
    try:
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
        with urlopen(url, timeout=10) as resp:
            xml = resp.read().decode("utf-8", errors="ignore")
        root = ET.fromstring(xml)
        items = []
        for item in root.findall(".//item")[:max_items]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            items.append({"title": title, "link": link, "pubDate": pub})
        return items
    except Exception as e:
        show_error(f"뉴스를 가져오지 못했어요: {e}")
        return []

def fetch_duckduckgo(query: str, max_items: int = 10):
    try:
        url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_redirect=1&no_html=1"
        with urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        results = []
        abstract = data.get("AbstractText") or data.get("Abstract") or ""
        if abstract:
            results.append({"text": abstract, "url": data.get("AbstractURL") or ""})
        for rt in (data.get("RelatedTopics") or [])[:max_items]:
            text = rt.get("Text") or rt.get("FirstURL") or ""
            url = rt.get("FirstURL") or ""
            if text:
                results.append({"text": text, "url": url})
        return results[:max_items]
    except Exception as e:
        show_error(f"웹 검색을 가져오지 못했어요: {e}")
        return []

tab_news, tab_search, tab_outlook = st.tabs(["뉴스", "검색", "전망"])

with tab_news:
    st.subheader("최신 뉴스")
    q = query_text.strip() or f"{base_ticker} stock"
    news = fetch_google_news(q, max_items=10)
    if news:
        for n in news:
            with st.container(border=True):
                st.markdown(f"- [{n['title']}]({n['link']})")
                if n.get('pubDate'):
                    st.caption(n['pubDate'])
    else:
        st.info("뉴스 결과가 없어요. 키워드를 바꿔보세요.")

with tab_search:
    st.subheader("웹 검색 요약")
    q = query_text.strip() or f"{base_ticker} stock"
    results = fetch_duckduckgo(q, max_items=10)
    if results:
        for r in results:
            with st.container(border=True):
                st.write(r['text'])
                if r.get('url'):
                    st.caption(r['url'])
    else:
        st.info("검색 결과가 적어요. 다른 키워드를 시도해보세요.")

with tab_outlook:
    st.subheader("교육적 관점의 전망")
    tone = st.radio("분석 톤", options=["보수적", "중립", "적극적"], index=1, horizontal=True)
    days = st.selectbox("참조 기간(시세)", options=[30, 90, 180, 365], index=1, format_func=lambda d: f"최근 {d}일")
    ask = st.chat_input("전망 요청(예: 장기 전망, 이슈 영향 분석, 리스크/시나리오 등)")

    # 컨텍스트 준비 (시세 + 뉴스 요약)
    ts_raw = fetch_stooq_csv(symbol)
    latest_close = None
    change_pct = None
    if ts_raw:
        series = parse_timeseries(ts_raw, days=days)
        if series:
            latest_close = series[-1]['close']
            first_close = series[0]['close']
            change_pct = ((latest_close - first_close) / first_close * 100) if first_close else None

    headlines = [n['title'] for n in fetch_google_news(query_text.strip() or base_ticker, max_items=5)]
    context_lines = [
        f"티커: {base_ticker} ({market}, {symbol})",
        f"참조 기간: 최근 {days}일",
        f"최신 종가: {latest_close:.2f}" if latest_close is not None else "최신 종가: N/A",
        f"기간 변동률: {change_pct:.2f}%" if change_pct is not None else "기간 변동률: N/A",
        f"헤드라인: " + ("; ".join(headlines) if headlines else "없음"),
        "주의: 본 분석은 교육적 목적이며 투자 권유가 아닙니다.",
    ]

    if ask:
        enriched = "\n".join(context_lines) + "\n\n요청: " + ask + f"\n분석 톤: {tone}"
        add_message('user', enriched)
        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""
        temp_map = {"보수적": 0.3, "중립": 0.7, "적극적": 1.0}
        for chunk in stream_chat_response(
            category='stocks',
            grade=user.get('grade'),
            is_teacher=True,
            conversation_messages=[{"role": m['role'], "content": m['content']} for m in get_messages()],
            temperature=temp_map.get(tone, 0.7),
            max_tokens=800,
        ):
            full_text += chunk or ""
            placeholder.markdown(full_text)

        if full_text.strip():
            add_message('assistant', full_text)
            cat_row = get_category_by_name('stocks')
            if cat_row:
                save_conversation(user['id'], cat_row['id'], enriched, full_text, session_id='teacher_stock_worry', is_private=False)
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("대화 지우기"):
            clear_messages()
            st.rerun()
    with col2:
        st.caption("투자 권유가 아니며 교육적 분석입니다. 실제 투자 결정은 본인 책임입니다.")