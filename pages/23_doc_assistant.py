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
    show_error,
    show_warning,
    show_success,
)
from ai.deepseek_handler import stream_chat_response
from database.supabase_manager import (
    get_category_by_name,
    save_conversation,
    create_document,
    add_document_chunk,
    search_document_chunks,
    list_documents,
    get_supabase_client,
)


st.set_page_config(page_title="📄 문서 도우미", page_icon="📄", layout="wide")
with st.sidebar:
    render_sidebar_navigation()
    render_sidebar_auth_controls()
render_auth_modals()
require_teacher_or_admin()
user = get_current_user()
set_current_page('doc_assistant')

st.title("📄 문서 도우미 (교사용)")
st.caption("PDF/텍스트를 업로드해 지식 베이스로 만들고, 근거를 인용하며 설명합니다.")


# ===== Embedding model loader =====
EMBED_DIM = 384

def _load_embed_model():
    try:
        import streamlit as st
        from sentence_transformers import SentenceTransformer

        @st.cache_resource(show_spinner=False)
        def _cached_model():
            return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

        return _cached_model()
    except Exception as e:
        # 가벼운 폴백 임베더: 384차원 영벡터 반환 (업로드/검색은 제한적이지만 서버 중단 방지)
        show_warning(f"임베딩 모델 로드 오류: {str(e)}. 임시로 폴백 임베더(영벡터)를 사용합니다. 'pip install sentence-transformers' 설치 후 재시도하세요.")
        class ZeroEmbedder:
            def encode(self, texts, normalize_embeddings=True):
                # 순수 파이썬으로 고정 영벡터 반환 (numpy 미의존)
                return [[0.0] * EMBED_DIM for _ in range(len(texts))]
        return ZeroEmbedder()

def _embed_texts(model, texts: list[str], batch_size: int = 32) -> list[list[float]]:
    try:
        # 대량 텍스트는 배치로 나눠 인코딩해 메모리/CPU 급증을 방지
        all_vecs: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            vecs = model.encode(batch, normalize_embeddings=True)
            # encode 결과가 numpy 배열 또는 파이썬 리스트 모두 지원
            try:
                all_vecs.extend([v.tolist() for v in vecs])
            except Exception:
                all_vecs.extend([list(v) for v in vecs])
        return all_vecs
    except Exception as e:
        show_error(f"텍스트 임베딩 오류: {str(e)}")
        return []


# ===== Text chunking =====
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    text = text or ""
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


# ===== PDF/Text parsers =====
def parse_pdf_bytes(pdf_bytes: bytes) -> list[tuple[int, str]]:
    """Return list of (page_no, text) for each page."""
    try:
        import fitz  # PyMuPDF
    except Exception:
        show_error("PDF 처리를 위해 'pip install pymupdf' 설치가 필요합니다.")
        return []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype='pdf')
        pages = []
        for i in range(doc.page_count):
            page = doc.load_page(i)
            text = page.get_text("text") or ""
            pages.append((i + 1, text))
        return pages
    except Exception as e:
        show_error(f"PDF 파싱 오류: {str(e)}")
        return []

def read_text_bytes(txt_bytes: bytes) -> str:
    for enc in ('utf-8', 'cp949', 'euc-kr', 'utf-16'):
        try:
            return txt_bytes.decode(enc)
        except Exception:
            continue
    return txt_bytes.decode('utf-8', errors='ignore')


# ===== Upload & index UI =====
with st.container(border=True):
    st.subheader("문서 업로드/인덱싱")
    files = st.file_uploader("PDF 또는 텍스트 파일 업로드", type=["pdf", "txt"], accept_multiple_files=True)
    if files:
        model = _load_embed_model()
        if not model:
            st.stop()
        # Supabase 연결 확인 (환경 변수 미설정/연결 실패 시 명확한 안내)
        client = get_supabase_client()
        if not client:
            show_error("Supabase 연결 설정(SUPABASE_URL/SUPABASE_KEY)이 필요합니다. Supabase 대시보드 SQL Editor에서 database/schema.sql을 실행해 테이블/RPC도 준비하세요.")
            st.stop()
        progress = st.progress(0.0, text="인덱싱 준비 중…")
        total_chunks = 0
        failed_chunks = 0
        processed_files = 0
        for idx, f in enumerate(files, start=1):
            try:
                file_bytes = f.read()
                content_type = 'application/pdf' if f.type == 'application/pdf' or f.name.lower().endswith('.pdf') else 'text/plain'
                doc_row = create_document(user_id=user['id'], title=f.name, file_name=f.name, content_type=content_type)
                if not doc_row:
                    show_error(f"문서 메타 저장 실패: {f.name}")
                    continue

                if content_type == 'application/pdf':
                    # 페이지를 한 번에 메모리에 올리지 않고, 페이지별로 청크를 생성하며 제한을 적용
                    page_chunks = []
                    meta_list = []
                    try:
                        import fitz  # PyMuPDF
                        pdf = fitz.open(stream=file_bytes, filetype='pdf')
                        MAX_CHUNKS = 500
                        for pno in range(pdf.page_count):
                            if len(page_chunks) >= MAX_CHUNKS:
                                show_warning(f"페이지 {pno+1}부터는 청크 제한({MAX_CHUNKS})으로 건너뜁니다.")
                                break
                            page = pdf.load_page(pno)
                            ptxt = page.get_text("text") or ""
                            cks = chunk_text(ptxt)
                            for ck in cks:
                                if len(page_chunks) >= MAX_CHUNKS:
                                    break
                                page_chunks.append(ck)
                                meta_list.append({"page": pno + 1, "file": f.name})
                        pdf.close()
                    except Exception as e:
                        show_error(f"PDF 파싱 오류: {str(e)}")
                        page_chunks = []
                        meta_list = []
                else:
                    text = read_text_bytes(file_bytes)
                    page_chunks = chunk_text(text)
                    meta_list = [{"file": f.name} for _ in page_chunks]

                # 너무 많은 청크는 제한해 서버 과부하 방지
                MAX_CHUNKS = 500
                if len(page_chunks) > MAX_CHUNKS:
                    show_warning(f"청크가 {len(page_chunks)}개로 너무 많아 {MAX_CHUNKS}개만 저장합니다.")
                    page_chunks = page_chunks[:MAX_CHUNKS]
                    meta_list = meta_list[:MAX_CHUNKS]

                # embed and store (배치 처리)
                embeddings = _embed_texts(model, page_chunks, batch_size=32)
                for ci, (ck, emb, meta) in enumerate(zip(page_chunks, embeddings, meta_list)):
                    ok = add_document_chunk(
                        document_id=doc_row['id'],
                        user_id=user['id'],
                        content=ck,
                        embedding=emb,
                        chunk_index=ci,
                        metadata=meta,
                    )
                    if ok:
                        total_chunks += 1
                    else:
                        failed_chunks += 1
                processed_files += 1
                progress.progress(processed_files / len(files), text=f"{processed_files}/{len(files)} 파일 처리 완료")
            except Exception as e:
                show_error(f"파일 처리 오류({f.name}): {str(e)}")
        if failed_chunks > 0:
            show_error(f"인덱싱 일부 실패: 총 {processed_files}개 파일, {total_chunks} 청크 저장, {failed_chunks} 청크 실패")
        else:
            show_success(f"인덱싱 완료: 총 {processed_files}개 파일, {total_chunks} 청크 저장")

    # Show my documents
    try:
        docs = list_documents(user['id'])
        if docs:
            with st.expander("내 문서 목록", expanded=False):
                for d in docs:
                    st.caption(f"• {d.get('file_name')} ({d.get('content_type')}) · {str(d.get('created_at'))[:16]}")
        else:
            st.caption("아직 업로드한 문서가 없어요.")
    except Exception:
        pass


# ===== Chat with RAG =====
st.divider()
with st.container(border=True):
    st.subheader("문서 기반 대화")
    last_ai = None
    for m in get_messages():
        st.chat_message(m['role']).write(m['content'])
        if m['role'] == 'assistant':
            last_ai = m['content']

    question = st.chat_input("문서에 대해 궁금한 점을 물어보세요…")
    if question:
        model = _load_embed_model()
        if not model:
            st.stop()
        add_message('user', question)

        # retrieve relevant chunks
        q_emb = _embed_texts(model, [question])
        q_vec = q_emb[0] if q_emb else None
        top_chunks = []
        if q_vec:
            top_chunks = search_document_chunks(user_id=user['id'], query_embedding=q_vec, match_count=5)

        # build context
        context_lines = []
        citations = []
        for r in top_chunks:
            meta = r.get('metadata') or {}
            origin = meta.get('file', '문서')
            page = meta.get('page')
            cite = f"{origin}{' p.' + str(page) if page else ''}"
            citations.append(cite)
            snippet = (r.get('content') or '').strip().replace('\n', ' ')
            snippet = snippet[:400]
            context_lines.append(f"- {cite}: {snippet}")
        context_text = "\n".join(context_lines) if context_lines else "(관련 근거를 찾지 못했습니다.)"

        assistant_box = st.chat_message("assistant")
        placeholder = assistant_box.empty()
        full_text = ""
        for chunk in stream_chat_response(
            category='doc_assistant',
            grade=user.get('grade'),
            is_teacher=True,
            conversation_messages=[
                {"role": m['role'], "content": m['content']} for m in get_messages()
            ] + ([{"role": "system", "content": f"다음은 관련 근거 청크입니다:\n{context_text}"}] if context_text else []),
            temperature=st.session_state.get('ai_temperature', 0.5),
            max_tokens=st.session_state.get('ai_max_tokens', 800)
        ):
            full_text += chunk or ""
            placeholder.markdown(full_text)

        if full_text.strip():
            # append citations as a small footer
            if citations:
                full_text += "\n\n참고: " + ", ".join(citations)
            add_message('assistant', full_text)
            cat_row = get_category_by_name('doc_assistant')
            if cat_row:
                save_conversation(
                    user_id=user['id'],
                    category_id=cat_row['id'],
                    user_message=question,
                    ai_response=full_text,
                    session_id=get_current_session_id(),
                    is_private=False
                )
            st.rerun()

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("대화 지우기"):
        clear_messages()
        st.rerun()
with col2:
    st.caption("원문 근거를 인용하고, 모르면 모른다고 말합니다.")
with col3:
    st.caption("PDF/텍스트 업로드 후 질문하면 문서 기반으로 답해요.")
    render_new_chat_controls(page_key='doc_assistant', category_name='doc_assistant')