-- ========================================
-- AI 학습 도우미 - 데이터베이스 스키마
-- ========================================
-- Supabase SQL Editor에서 실행하세요
-- 
-- 실행 방법:
-- 1. Supabase 대시보드 접속
-- 2. SQL Editor 메뉴 클릭
-- 3. 이 파일의 전체 내용을 복사해서 붙여넣기
-- 4. Run 버튼 클릭
-- ========================================

-- 1. 사용자 테이블
-- 관리자, 교사, 학생 모두 저장됩니다
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,  -- 한글 가능! (예: "김철수")
  password_hash TEXT NOT NULL,     -- 비밀번호 (bcrypt 해싱)
  full_name TEXT,                  -- 실제 이름
  role TEXT NOT NULL CHECK (role IN ('super_admin', 'teacher', 'student')),  -- 역할
  grade TEXT,                      -- 학년 (학생인 경우)
  invite_code_used TEXT,           -- 어떤 인증코드로 가입했는지
  created_by INTEGER REFERENCES users(id),  -- 누가 초대했는지
  created_at TIMESTAMP DEFAULT NOW(),
  last_login TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE
);

-- 사용자명으로 빠르게 검색하기 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);


-- 2. 교사 인증코드 테이블
-- 관리자가 생성, 교사가 사용
CREATE TABLE IF NOT EXISTS teacher_invite_codes (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,       -- 인증코드 (예: TEACHER-ABC123)
  created_by INTEGER REFERENCES users(id),  -- 관리자 ID
  used_by INTEGER REFERENCES users(id),     -- 사용한 교사 ID
  used_at TIMESTAMP,               -- 사용 시각
  expires_at TIMESTAMP,            -- 만료 시각
  memo TEXT,                       -- 메모 (예: "서울초등학교 김선생님")
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teacher_codes_code ON teacher_invite_codes(code);


-- 3. 학생 인증코드 테이블
-- 교사가 생성, 학생이 사용
CREATE TABLE IF NOT EXISTS student_invite_codes (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,       -- 인증코드 (예: ABC123)
  created_by INTEGER REFERENCES users(id),  -- 교사 ID
  class_name TEXT,                 -- 학급명 (예: "3학년 2반")
  max_uses INTEGER DEFAULT 10,     -- 최대 사용 횟수
  used_count INTEGER DEFAULT 0,    -- 현재 사용 횟수
  expires_at TIMESTAMP,            -- 만료 시각
  memo TEXT,                       -- 메모
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_student_codes_code ON student_invite_codes(code);


-- 4. 카테고리 테이블
-- 학습 카테고리 (영어, 수학, 생기부 등)
CREATE TABLE IF NOT EXISTS categories (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,       -- 영어 이름 (예: 'english', 'saeungbu')
  icon TEXT,                       -- 이모지 (예: '🌍')
  display_name TEXT,               -- 한글 표시명 (예: '영어 학습')
  description TEXT,                -- 설명
  target_role TEXT CHECK (target_role IN ('all', 'student', 'teacher')),  -- 누가 사용?
  is_active BOOLEAN DEFAULT TRUE
);

-- 기본 카테고리 삽입
INSERT INTO categories (name, icon, display_name, description, target_role) VALUES
-- 학생용 카테고리
('english', '🌍', '영어 학습', 'AI와 함께하는 영어 공부', 'all'),
('math', '🔢', '수학 학습', 'AI와 함께하는 수학 공부', 'all'),
('science', '🔬', '과학 학습', 'AI와 함께하는 과학 탐구', 'all'),
('korean', '📚', '국어 학습', 'AI와 함께하는 국어 공부', 'all'),
('coding', '💻', '코딩 학습', 'AI와 함께하는 코딩 배우기', 'all'),
('free', '💬', '자유 대화', 'AI와 자유롭게 대화하기', 'all'),
-- 교사 전용 카테고리
('education', '📖', '교육 상담', '수업 아이디어와 교수법 상담', 'teacher'),
('saeungbu', '📝', '생기부 작성', '생활기록부 작성 도우미', 'teacher'),
('counseling', '💭', '학생 상담', '학생 상담 전략 도우미', 'teacher'),
('worry', '🤔', '교사 고민', '교사를 위한 비공개 상담', 'teacher')
ON CONFLICT (name) DO NOTHING;


-- 5. 대화 기록 테이블
-- 사용자와 AI의 모든 대화를 저장
CREATE TABLE IF NOT EXISTS conversations (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  category_id INTEGER REFERENCES categories(id),
  user_message TEXT NOT NULL,      -- 사용자가 입력한 메시지
  ai_response TEXT,                -- AI의 답변
  session_id TEXT,                 -- 세션 ID (대화 묶음)
  is_private BOOLEAN DEFAULT FALSE,  -- 교사 고민은 true
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_category ON conversations(category_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at DESC);


-- 6. 퀴즈 시도 테이블
-- 학생이 푼 퀴즈 기록
CREATE TABLE IF NOT EXISTS quiz_attempts (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  category_id INTEGER REFERENCES categories(id),
  quiz_data JSONB,                 -- 퀴즈 문제 전체 (JSON 형식)
  user_answer TEXT,                -- 학생의 답
  is_correct BOOLEAN,              -- 정답 여부
  time_taken INTEGER,              -- 풀이 시간 (초)
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quiz_user ON quiz_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_category ON quiz_attempts(category_id);


-- 7. 단어장 테이블
-- 학생별 단어장
CREATE TABLE IF NOT EXISTS vocabulary (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  word TEXT NOT NULL,              -- 단어
  meaning TEXT,                    -- 뜻
  example TEXT,                    -- 예문
  pronunciation TEXT,              -- 발음 기호
  mastered BOOLEAN DEFAULT FALSE,  -- 숙달 여부
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vocab_user ON vocabulary(user_id);


-- 8. 세션 테이블
-- 로그인 상태 관리
CREATE TABLE IF NOT EXISTS sessions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  session_token TEXT UNIQUE NOT NULL,  -- 세션 토큰
  expires_at TIMESTAMP NOT NULL,       -- 만료 시각
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);


-- 9. 학습 통계 테이블 (일별 집계)
-- 매일의 학습 활동 요약
CREATE TABLE IF NOT EXISTS learning_stats (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  date DATE DEFAULT CURRENT_DATE,
  study_minutes INTEGER DEFAULT 0,     -- 학습 시간 (분)
  message_count INTEGER DEFAULT 0,     -- 대화 횟수
  quiz_count INTEGER DEFAULT 0,        -- 퀴즈 수
  quiz_correct INTEGER DEFAULT 0,      -- 정답 수
  categories_used TEXT[],              -- 사용한 카테고리들
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_stats_user_date ON learning_stats(user_id, date DESC);


-- ========================================
-- 10. 문제은행 테이블 (교사용)
-- 교사가 직접 만든 문항을 저장합니다
CREATE TABLE IF NOT EXISTS question_bank (
  id SERIAL PRIMARY KEY,
  created_by INTEGER REFERENCES users(id),
  type TEXT CHECK (type IN ('multiple','true_false','short_answer')),
  question TEXT NOT NULL,
  options JSONB,              -- 객관식 보기 배열
  answer TEXT NOT NULL,       -- 정답 텍스트
  explanation TEXT,           -- 해설
  category TEXT,              -- 과목/분류 (예: english, math, science)
  grade TEXT,                 -- 학년
  difficulty INTEGER,         -- 난이도(1~5)
  tags JSONB,                 -- 태그 배열
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_question_bank_created_by ON question_bank(created_by);
CREATE INDEX IF NOT EXISTS idx_question_bank_category ON question_bank(category);
CREATE INDEX IF NOT EXISTS idx_question_bank_created_at ON question_bank(created_at);


-- ========================================
-- 완료!
-- ========================================
-- 데이터베이스 테이블이 모두 생성되었습니다.
-- 이제 Python 코드에서 사용할 수 있습니다.
-- ========================================

-- ========================================
-- 11. 과제 테이블 (교사용)
-- 교사가 생성한 과제를 저장합니다
CREATE TABLE IF NOT EXISTS assignments (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,               -- 과제 제목
  description TEXT,                  -- 과제 설명/지시사항
  created_by INTEGER REFERENCES users(id), -- 만든 교사 ID
  target_grade TEXT,                 -- 대상 학년 (선택)
  due_date TIMESTAMP,                -- 마감일 (선택)
  is_active BOOLEAN DEFAULT TRUE,    -- 활성 여부
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assignments_created_by ON assignments(created_by);
CREATE INDEX IF NOT EXISTS idx_assignments_due_date ON assignments(due_date DESC);

-- 12. 과제 제출 테이블 (학생용)
-- 학생이 과제를 선택/제출/채점받은 기록을 저장합니다
CREATE TABLE IF NOT EXISTS assignment_submissions (
  id SERIAL PRIMARY KEY,
  assignment_id INTEGER REFERENCES assignments(id) ON DELETE CASCADE,
  student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  status TEXT CHECK (status IN ('selected','submitted','graded')) DEFAULT 'selected',
  answer_text TEXT,                  -- 학생 답안 텍스트
  score INTEGER,                     -- 점수 (선택)
  feedback TEXT,                     -- 교사 피드백 (선택)
  selected_at TIMESTAMP DEFAULT NOW(),
  submitted_at TIMESTAMP,
  graded_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(assignment_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_submissions_assignment ON assignment_submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_submissions_student ON assignment_submissions(student_id);


-- ========================================
-- 13. 문서/RAG 테이블 및 벡터 검색 함수
-- NotebookLM 유사 기능 구현을 위한 스키마
-- ========================================

-- pgvector 확장
CREATE EXTENSION IF NOT EXISTS vector;

-- 문서 메타 테이블
CREATE TABLE IF NOT EXISTS documents (
  id BIGSERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  title TEXT,
  file_name TEXT,
  content_type TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Row Level Security: 이 프로젝트는 Supabase Auth를 사용하지 않으므로 비활성화하여 애플리케이션 키(anon)로 접근 가능하게 합니다
ALTER TABLE documents DISABLE ROW LEVEL SECURITY;

-- 문서 청크 테이블 (임베딩 저장)
CREATE TABLE IF NOT EXISTS document_chunks (
  id BIGSERIAL PRIMARY KEY,
  document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  chunk_index INTEGER,
  content TEXT,
  embedding VECTOR(384),
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- RLS 비활성화: 애플리케이션에서 자체 사용자 테이블을 사용하므로 권한 관리는 앱에서 처리합니다
ALTER TABLE document_chunks DISABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_user ON document_chunks(user_id);
-- 코사인 유사도용 벡터 인덱스 (성능 향상). 테이블에 데이터가 충분히 있을 때 생성 권장
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists=100);

-- 벡터 검색 RPC: 쿼리 임베딩과 가장 가까운 청크를 반환
CREATE OR REPLACE FUNCTION match_document_chunks(
  query_embedding VECTOR(384),
  match_count INT,
  user_id_input INT,
  document_id_input BIGINT DEFAULT NULL
)
RETURNS TABLE(
  id BIGINT,
  document_id BIGINT,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE SQL STABLE AS $$
  SELECT dc.id, dc.document_id, dc.content, dc.metadata,
         1 - (dc.embedding <=> query_embedding) AS similarity
  FROM document_chunks dc
  WHERE dc.user_id = user_id_input
    AND (document_id_input IS NULL OR dc.document_id = document_id_input)
  ORDER BY dc.embedding <-> query_embedding
  LIMIT match_count;
$$;

-- 새 카테고리 추가 (중복 삽입 방지)
INSERT INTO categories (name, icon, display_name, description, target_role) VALUES
('stocks', '📈', '주식 개요', '시장/종목 학습 보조', 'teacher'),
('stocks_expert', '🧠', '주식 챗봇', '교육용 분석', 'teacher'),
('doc_assistant', '📄', '문서 도우미', '업로드 문서 기반 설명', 'teacher')
ON CONFLICT (name) DO NOTHING;

