# 🎓 AI 학습 도우미

초등학교 교사와 학생을 위한 AI 기반 맞춤형 학습 플랫폼

## ✨ 주요 기능

### 👨‍🎓 학생용 기능
- 🌍 영어, 🔢 수학, 🔬 과학, 📚 국어, 💻 코딩 학습
- 🎯 AI 퀴즈 자동 생성
- 📖 나만의 단어장
- 📊 학습 통계 및 분석
- 🔊 발음 듣기 (Edge TTS)

### 👨‍🏫 교사용 기능
- 📝 **생기부 작성 도우미** (핵심 기능!)
- 📖 교육 상담 (수업 아이디어, 교수법)
- 💭 학생 상담 도우미
- 🤔 교사 고민 상담 (비공개)
- 👥 학생 관리 (무제한)

### 👑 관리자 기능
- 🎫 교사 인증코드 발급
- 📊 전체 통계 확인
- 시스템 관리

---

## 🚀 설치 방법

### 1️⃣ 저장소 클론

```bash
git clone https://github.com/your-username/vaccine.git
cd vaccine
```

### 2️⃣ 가상환경 생성 (선택사항이지만 권장)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ 패키지 설치

```bash
pip install -r requirements.txt
```

### 4️⃣ 환경 변수 설정

**env_example.txt 파일을 참고하여 .env 파일을 만드세요:**

```bash
# Windows
copy env_example.txt .env

# Mac/Linux
cp env_example.txt .env
```

그 다음 `.env` 파일을 열고 실제 값을 입력하세요:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_actual_key
DEEPSEEK_API_KEY=sk-your_actual_key
SUPER_ADMIN_USERNAME=admin
SUPER_ADMIN_PASSWORD=your_secure_password
```

### 5️⃣ Supabase 데이터베이스 설정

1. https://supabase.com 접속
2. 새 프로젝트 생성
3. SQL Editor에서 `database/schema.sql` 파일 내용을 복사해서 실행

### 6️⃣ 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 🌐 Streamlit Cloud 배포

### 1️⃣ GitHub에 푸시

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2️⃣ Streamlit Cloud 설정

1. https://streamlit.io/cloud 접속
2. "New app" 클릭
3. Repository 선택
4. **Secrets 설정:**

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your_key"
DEEPSEEK_API_KEY = "sk-your_key"
SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_PASSWORD = "your_password"
```

5. Deploy!

---

## 🛠️ 배포 트러블슈팅 (Cloud)

- `enableXsrfProtection`/`enableCORS` 경고가 보여요
  - `.streamlit/config.toml`에서 `enableXsrfProtection = true`, `enableCORS = false` 설정은 일반적인 배포에서 안전합니다.
  - 외부 도메인에서 임베드/프록시할 경우 Nginx 리버스 프록시를 권장합니다. 단순 임베드 목적이면 `enableCORS = true`로 변경하세요.
- Secrets가 적용되지 않아요
  - Streamlit Cloud의 App → Settings → Secrets에 키가 정확히 들어갔는지 확인하세요.
  - 로컬 개발은 `.env` 파일을 사용합니다(`env_example.txt` 복사).
- Supabase 권한 오류
  - `SUPABASE_KEY`는 anon/public 키를 사용해야 합니다. 서비스 키(service role)는 Cloud 프런트엔드에서 사용하지 마세요.
- 관리자 로그인 실패
  - Cloud Secrets에 `SUPER_ADMIN_PASSWORD`가 설정되어 있어야 합니다.
  - 필요 시 `fix_admin.py`를 로컬에서 실행해 비밀번호를 초기화할 수 있습니다.

---

## 🐳 Docker (선택 사항)

Docker는 학교 내부 서버/사설망에서 운영하거나 실행 환경을 고정하고 싶을 때만 사용하세요. Cloud 배포가 기본 권장입니다.

```bash
# 빌드
docker build -t vaccine-app .

# 실행 (필요한 환경 변수 지정)
docker run -d \
  -p 8501:8501 \
  -e SUPABASE_URL=https://your-project.supabase.co \
  -e SUPABASE_KEY=your_supabase_anon_key_here \
  -e DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here \
  -e SUPER_ADMIN_USERNAME=admin \
  -e SUPER_ADMIN_PASSWORD=your_secure_password \
  vaccine-app

# 또는 docker-compose 사용
docker-compose up -d
```

> 참고: Docker/Compose 파일은 저장소에 포함되어 있으며, 필요할 때만 사용하시면 됩니다.

---

## 🚢 GitHub Actions + GHCR (자동 빌드)

리포지토리에 푸시하면 Docker 이미지를 자동으로 빌드해 `GHCR`에 업로드합니다.

- 워크플로 경로: `.github/workflows/docker-ghcr.yml`
- 이미지 이름: `ghcr.io/<owner>/<repo>:latest` (태그 푸시 시 버전 태그도 함께 생성)
- 권한 설정: 워크플로에 `permissions: packages: write`가 포함되어 있습니다.

사용 방법

1. GitHub 리포지토리를 생성하고 코드를 푸시합니다.
2. 워크플로가 자동 실행되어 GHCR로 이미지가 업로드됩니다.
3. 서버에서 다음과 같이 실행할 수 있습니다:

```bash
docker pull ghcr.io/<owner>/<repo>:latest
docker run -d -p 8501:8501 \
  -e SUPABASE_URL=... \
  -e SUPABASE_KEY=... \
  -e DEEPSEEK_API_KEY=... \
  -e SUPER_ADMIN_USERNAME=admin \
  -e SUPER_ADMIN_PASSWORD=... \
  ghcr.io/<owner>/<repo>:latest
```

> 참고: `GITHUB_TOKEN`으로 GHCR 로그인/푸시가 자동 처리됩니다. 추가 설정 없이 작동합니다.



## 🔑 API 키 발급 방법

### Supabase (데이터베이스)
1. https://supabase.com 접속
2. 새 프로젝트 생성
3. Settings → API에서 **URL**과 **anon/public key** 복사

### DeepSeek (AI)
1. https://platform.deepseek.com 접속
2. 회원가입
3. API Keys에서 새 키 생성

---

## 💰 예상 비용

```
Streamlit Cloud: 무료 ✅
Supabase: 무료 ✅  
Edge TTS: 무료 ✅
DeepSeek: ~$5-10/월 (학생 100명 기준)
─────────────────
총: $5-10/월
```

---

## 📁 프로젝트 구조

```
vaccine/
├── app.py                    # 메인 앱 (로그인/회원가입)
├── config.py                 # 환경 설정
├── requirements.txt          # 패키지 목록
├── README.md                 # 이 파일
├── .gitignore                # Git 무시 파일
├── env_example.txt           # 환경 변수 템플릿
├── .streamlit/
│   └── config.toml           # 이쁜 테마 설정
├── database/
│   ├── supabase_manager.py   # DB 연결 및 쿼리
│   └── schema.sql            # DB 스키마
├── auth/
│   ├── auth_manager.py       # 로그인/회원가입
│   └── invite_codes.py       # 인증코드 관리
├── ai/
│   ├── deepseek_handler.py   # DeepSeek API
│   └── prompts.py            # 카테고리별 프롬프트
├── voice/
│   └── tts_handler.py        # Edge TTS (발음)
├── quiz/
│   └── quiz_generator.py     # AI 퀴즈 생성
├── utils/
│   ├── helpers.py            # 유틸리티 함수
│   └── session_manager.py    # 세션 관리
└── pages/
    ├── 1_📚_Learning.py      # 학습 페이지
    ├── 2_🎯_Quiz.py          # 퀴즈
    ├── 3_📖_Vocabulary.py    # 단어장
    ├── 4_📊_Dashboard.py     # 통계
    ├── 5_👥_Students.py      # 학생 관리
    ├── 6_🎫_Invite_Codes.py # 인증코드
    └── 7_⚙️_Settings.py      # 설정
```

---

## ⚠️ 보안 주의사항

- ❌ `.env` 파일은 절대 GitHub에 올리지 마세요!
- ✅ API 키는 안전하게 보관하세요
- ✅ 관리자 비밀번호는 강력하게 설정하세요
- ✅ Streamlit Cloud Secrets 사용하세요

---

## 📝 라이선스

MIT License

---

## 🤝 기여

Pull Request 환영합니다!

---

## 📧 문의

이슈 페이지에서 질문해주세요.

---

**⭐ 마음에 드셨다면 Star를 눌러주세요!**

