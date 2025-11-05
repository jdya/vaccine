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

