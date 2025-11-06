#pip install supabase

# ========================================
# AI 학습 도우미 - Supabase 데이터베이스 관리
# ========================================
# Supabase PostgreSQL 데이터베이스와 연결하여
# 데이터를 저장하고 불러오는 모듈
# ========================================

from supabase import create_client, Client
from datetime import datetime
import config


# ========================================
# 사용자가 설정할 변수 (없음 - config.py에서 가져옴)
# ========================================


def debug_print(message, level="INFO"):
    """
    디버그 메시지 출력
    
    매개변수:
        message: 출력할 메시지
        level: 로그 레벨
    """
    if config.DEBUG_MODE:
        # Windows/Powershell 환경에서 ANSI 코드로 인해 출력 오류가 날 수 있어
        # 색상 코드를 제거하고 안전하게 출력합니다.
        try:
            print(f"[DB-{level}] {message}")
        except Exception:
            # 어떤 출력 오류도 앱 동작에 영향을 주지 않도록 무시합니다.
            pass


# ========================================
# Supabase 클라이언트 초기화
# ========================================

_supabase_client = None

def get_supabase_client():
    """
    Supabase 클라이언트를 반환 (싱글톤 패턴)
    Streamlit 환경에서는 세션 상태를 사용
    """
    global _supabase_client
    
    # Streamlit 환경 확인
    try:
        import streamlit as st
        use_streamlit = True
    except:
        use_streamlit = False
    
    # Streamlit 환경에서는 세션 상태 사용
    if use_streamlit:
        if 'supabase_client' not in st.session_state:
            try:
                debug_print("Supabase 클라이언트 생성 (Streamlit 세션)...", "INFO")
                
                url = config.SUPABASE_URL
                key = config.SUPABASE_KEY
                
                if not url or not key:
                    debug_print("Supabase URL 또는 KEY가 설정되지 않았습니다!", "ERROR")
                    return None
                
                debug_print(f"URL: {url[:30]}..., KEY: {key[:10]}...", "INFO")
                
                # 클라이언트 생성
                client = create_client(url, key)
                
                # 연결 테스트
                try:
                    client.table('users').select('id').limit(1).execute()
                    debug_print("Supabase 연결 성공 (Streamlit)!", "SUCCESS")
                except Exception as test_error:
                    debug_print(f"연결 테스트 실패(무시): {str(test_error)}", "WARNING")
                    # 테스트가 실패해도 클라이언트를 유지합니다 (일부 환경에서 첫 쿼리 실패 사례 우회)
                st.session_state.supabase_client = client
            except Exception as e:
                debug_print(f"Supabase 연결 실패 (Streamlit): {str(e)}", "ERROR")
                import traceback
                debug_print(f"추적: {traceback.format_exc()}", "ERROR")
                return None
        
        return st.session_state.supabase_client
    
    # 일반 환경 (싱글톤 패턴)
    if _supabase_client is not None:
        try:
            # 클라이언트가 여전히 유효한지 확인 (간단한 테스트)
            _supabase_client.table('users').select('id').limit(1).execute()
            return _supabase_client
        except Exception as e:
            debug_print(f"기존 클라이언트 무효화: {str(e)}", "WARNING")
            _supabase_client = None
    
    # 클라이언트 생성
    try:
        debug_print("Supabase 연결 시도...", "INFO")
        
        url = config.SUPABASE_URL
        key = config.SUPABASE_KEY
        
        if not url or not key:
            debug_print("Supabase URL 또는 KEY가 설정되지 않았습니다!", "ERROR")
            return None
        
        debug_print(f"URL: {url[:30]}..., KEY: {key[:10]}...", "INFO")
        
        # 클라이언트 생성 시도
        _supabase_client = create_client(url, key)
        
        # 연결 테스트
        try:
            _supabase_client.table('users').select('id').limit(1).execute()
            debug_print("Supabase 연결 성공!", "SUCCESS")
        except Exception as test_error:
            debug_print(f"연결 테스트 실패(무시): {str(test_error)}", "WARNING")
            # 테스트 실패를 무시하고 클라이언트를 반환합니다
        
        return _supabase_client
        
    except Exception as e:
        debug_print(f"Supabase 연결 실패: {str(e)}", "ERROR")
        debug_print(f"오류 타입: {type(e).__name__}", "ERROR")
        import traceback
        debug_print(f"추적: {traceback.format_exc()}", "ERROR")
        _supabase_client = None
        return None


# ========================================
# 카테고리 도우미
# ========================================

def get_category_by_name(name: str):
    """
    카테고리 이름으로 row 조회 (없으면 None)
    """
    try:
        client = get_supabase_client()
        if not client:
            return None
        res = client.table('categories').select('*').eq('name', name).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as e:
        debug_print(f"카테고리 조회 오류: {str(e)}", "ERROR")
        return None


# ========================================
# 사용자 관리
# ========================================

def create_user(username, password_hash, full_name, role, grade=None, invite_code_used=None, created_by=None):
    """
    새 사용자 생성
    
    매개변수:
        username: 아이디 (한글 가능)
        password_hash: 해싱된 비밀번호
        full_name: 이름
        role: 역할 ('super_admin', 'teacher', 'student')
        grade: 학년 (학생인 경우)
        invite_code_used: 사용한 인증코드
        created_by: 생성자 ID
    
    반환값:
        성공 시 사용자 정보, 실패 시 None
    """
    try:
        debug_print(f"사용자 생성 시도: {username} ({role})", "INFO")
        
        client = get_supabase_client()
        if not client:
            return None
        
        data = {
            'username': username,
            'password_hash': password_hash,
            'full_name': full_name,
            'role': role,
            'grade': grade,
            'invite_code_used': invite_code_used,
            'created_by': created_by,
            'created_at': datetime.now().isoformat(),
            'is_active': True
        }
        
        result = client.table('users').insert(data).execute()
        
        if result.data:
            debug_print(f"사용자 생성 성공: {username}", "SUCCESS")
            return result.data[0]
        else:
            debug_print("사용자 생성 실패: 결과 없음", "ERROR")
            return None
    
    except Exception as e:
        debug_print(f"사용자 생성 중 오류: {str(e)}", "ERROR")
        return None


def get_user_by_username(username):
    """
    아이디로 사용자 조회
    
    매개변수:
        username: 아이디
    
    반환값:
        사용자 정보 또는 None
    """
    try:
        debug_print(f"사용자 조회: {username}", "INFO")
        
        client = get_supabase_client()
        if not client:
            return None
        
        result = client.table('users').select('*').eq('username', username).execute()
        
        if result.data and len(result.data) > 0:
            debug_print(f"사용자 찾음: {username}", "SUCCESS")
            return result.data[0]
        else:
            debug_print(f"사용자 없음: {username}", "WARNING")
            return None
    
    except Exception as e:
        debug_print(f"사용자 조회 중 오류: {str(e)}", "ERROR")
        return None


def get_user_by_id(user_id):
    """
    ID로 사용자 조회
    
    매개변수:
        user_id: 사용자 ID
    
    반환값:
        사용자 정보 또는 None
    """
    try:
        client = get_supabase_client()
        if not client:
            return None
        
        result = client.table('users').select('*').eq('id', user_id).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    
    except Exception as e:
        debug_print(f"사용자 조회 중 오류: {str(e)}", "ERROR")
        return None


def update_last_login(user_id):
    """
    마지막 로그인 시각 업데이트
    
    매개변수:
        user_id: 사용자 ID
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        client.table('users').update({
            'last_login': datetime.now().isoformat()
        }).eq('id', user_id).execute()
        
        debug_print(f"마지막 로그인 시각 업데이트: 사용자 {user_id}", "INFO")
        return True
    
    except Exception as e:
        debug_print(f"로그인 시각 업데이트 오류: {str(e)}", "ERROR")
        return False


def update_user(user_id, **kwargs):
    """
    사용자 정보 업데이트
    
    매개변수:
        user_id: 사용자 ID
        **kwargs: 업데이트할 필드들 (password_hash, full_name, role, grade 등)
    
    반환값:
        성공 시 True, 실패 시 False
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        # None 값은 제외
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        if not update_data:
            return False
        
        result = client.table('users').update(update_data).eq('id', user_id).execute()
        
        if result.data:
            debug_print(f"사용자 정보 업데이트 성공: 사용자 {user_id}", "SUCCESS")
            return True
        return False
    
    except Exception as e:
        debug_print(f"사용자 정보 업데이트 오류: {str(e)}", "ERROR")
        return False


def get_all_teachers():
    """
    모든 교사 조회 (관리자용)
    
    반환값:
        교사 리스트
    """
    try:
        client = get_supabase_client()
        if not client:
            return []
        
        result = client.table('users').select('*').eq('role', 'teacher').execute()
        return result.data if result.data else []
    
    except Exception as e:
        debug_print(f"교사 조회 중 오류: {str(e)}", "ERROR")
        return []


def get_students_by_teacher(teacher_id):
    """
    특정 교사의 학생들 조회
    
    매개변수:
        teacher_id: 교사 ID
    
    반환값:
        학생 리스트
    """
    try:
        client = get_supabase_client()
        if not client:
            return []
        
        result = client.table('users').select('*').eq('role', 'student').eq('created_by', teacher_id).execute()
        return result.data if result.data else []
    
    except Exception as e:
        debug_print(f"학생 조회 중 오류: {str(e)}", "ERROR")
        return []


# ========================================
# 인증코드 관리
# ========================================

def create_teacher_invite_code(code, created_by, expires_at, memo=None):
    """
    교사 인증코드 생성
    
    매개변수:
        code: 인증코드
        created_by: 생성자 ID (관리자)
        expires_at: 만료 시각
        memo: 메모
    
    반환값:
        성공 시 코드 정보, 실패 시 None
    """
    try:
        debug_print(f"교사 인증코드 생성: {code}", "INFO")
        
        client = get_supabase_client()
        if not client:
            return None
        
        data = {
            'code': code,
            'created_by': created_by,
            'expires_at': expires_at.isoformat() if expires_at else None,
            'memo': memo,
            'is_active': True,
            'created_at': datetime.now().isoformat()
        }
        
        result = client.table('teacher_invite_codes').insert(data).execute()
        
        if result.data:
            debug_print(f"교사 인증코드 생성 성공: {code}", "SUCCESS")
            return result.data[0]
        return None
    
    except Exception as e:
        debug_print(f"교사 인증코드 생성 오류: {str(e)}", "ERROR")
        return None


def get_teacher_invite_code(code):
    """
    교사 인증코드 조회
    
    매개변수:
        code: 인증코드
    
    반환값:
        코드 정보 또는 None
    """
    try:
        client = get_supabase_client()
        if not client:
            return None
        
        result = client.table('teacher_invite_codes').select('*').eq('code', code).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    
    except Exception as e:
        debug_print(f"교사 인증코드 조회 오류: {str(e)}", "ERROR")
        return None


def use_teacher_invite_code(code, teacher_id):
    """
    교사 인증코드 사용 처리
    
    매개변수:
        code: 인증코드
        teacher_id: 사용하는 교사 ID
    
    반환값:
        성공 여부
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        client.table('teacher_invite_codes').update({
            'used_by': teacher_id,
            'used_at': datetime.now().isoformat(),
            'is_active': False
        }).eq('code', code).execute()
        
        debug_print(f"교사 인증코드 사용 처리: {code}", "SUCCESS")
        return True
    
    except Exception as e:
        debug_print(f"교사 인증코드 사용 처리 오류: {str(e)}", "ERROR")
        return False


def create_student_invite_code(code, created_by, class_name=None, max_uses=10, expires_at=None, memo=None):
    """
    학생 인증코드 생성
    
    매개변수:
        code: 인증코드
        created_by: 생성자 ID (교사)
        class_name: 학급명
        max_uses: 최대 사용 횟수
        expires_at: 만료 시각
        memo: 메모
    
    반환값:
        성공 시 코드 정보, 실패 시 None
    """
    try:
        debug_print(f"학생 인증코드 생성: {code}", "INFO")
        
        client = get_supabase_client()
        if not client:
            return None
        
        data = {
            'code': code,
            'created_by': created_by,
            'class_name': class_name,
            'max_uses': max_uses,
            'used_count': 0,
            'expires_at': expires_at.isoformat() if expires_at else None,
            'memo': memo,
            'is_active': True,
            'created_at': datetime.now().isoformat()
        }
        
        result = client.table('student_invite_codes').insert(data).execute()
        
        if result.data:
            debug_print(f"학생 인증코드 생성 성공: {code}", "SUCCESS")
            return result.data[0]
        return None
    
    except Exception as e:
        debug_print(f"학생 인증코드 생성 오류: {str(e)}", "ERROR")
        return None


def get_student_invite_code(code):
    """
    학생 인증코드 조회
    
    매개변수:
        code: 인증코드
    
    반환값:
        코드 정보 또는 None
    """
    try:
        client = get_supabase_client()
        if not client:
            return None
        
        result = client.table('student_invite_codes').select('*').eq('code', code).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    
    except Exception as e:
        debug_print(f"학생 인증코드 조회 오류: {str(e)}", "ERROR")
        return None


def use_student_invite_code(code):
    """
    학생 인증코드 사용 (사용 횟수 증가)
    
    매개변수:
        code: 인증코드
    
    반환값:
        성공 여부
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        # 현재 정보 조회
        code_info = get_student_invite_code(code)
        if not code_info:
            return False
        
        new_count = code_info['used_count'] + 1
        
        # 최대 사용 횟수 도달 시 비활성화
        is_active = new_count < code_info['max_uses']
        
        client.table('student_invite_codes').update({
            'used_count': new_count,
            'is_active': is_active
        }).eq('code', code).execute()
        
        debug_print(f"학생 인증코드 사용: {code} (사용: {new_count}/{code_info['max_uses']})", "SUCCESS")
        return True
    
    except Exception as e:
        debug_print(f"학생 인증코드 사용 처리 오류: {str(e)}", "ERROR")
        return False


def get_teacher_codes(teacher_id):
    """
    교사가 생성한 학생 인증코드 목록 조회
    
    매개변수:
        teacher_id: 교사 ID
    
    반환값:
        코드 리스트
    """
    try:
        client = get_supabase_client()
        if not client:
            return []
        
        result = client.table('student_invite_codes').select('*').eq('created_by', teacher_id).order('created_at', desc=True).execute()
        return result.data if result.data else []
    
    except Exception as e:
        debug_print(f"교사 인증코드 목록 조회 오류: {str(e)}", "ERROR")
        return []


def get_admin_teacher_codes(admin_id):
    """
    관리자가 생성한 교사 인증코드 목록 조회
    
    매개변수:
        admin_id: 관리자 사용자 ID
    
    반환값:
        코드 리스트
    """
    try:
        client = get_supabase_client()
        if not client:
            return []
        res = client.table('teacher_invite_codes').select('*').eq('created_by', admin_id).order('created_at', desc=True).execute()
        return res.data or []
    except Exception as e:
        debug_print(f"관리자 교사 인증코드 목록 조회 오류: {str(e)}", "ERROR")
        return []


# ========================================
# 대화 기록 관리
# ========================================

def save_conversation(user_id, category_id, user_message, ai_response, session_id, is_private=False):
    """
    대화 기록 저장
    
    매개변수:
        user_id: 사용자 ID
        category_id: 카테고리 ID
        user_message: 사용자 메시지
        ai_response: AI 응답
        session_id: 세션 ID
        is_private: 비공개 여부 (교사 고민)
    
    반환값:
        성공 시 대화 정보, 실패 시 None
    """
    try:
        debug_print("대화 기록 저장 시도", "INFO")
        
        client = get_supabase_client()
        if not client:
            return None
        
        data = {
            'user_id': user_id,
            'category_id': category_id,
            'user_message': user_message,
            'ai_response': ai_response,
            'session_id': session_id,
            'is_private': is_private,
            'created_at': datetime.now().isoformat()
        }
        
        result = client.table('conversations').insert(data).execute()
        
        if result.data:
            debug_print("대화 기록 저장 성공", "SUCCESS")
            return result.data[0]
        return None
    
    except Exception as e:
        debug_print(f"대화 기록 저장 오류: {str(e)}", "ERROR")
        return None


def get_user_conversations(user_id, category_id=None, limit=50):
    """
    사용자의 대화 기록 조회
    
    매개변수:
        user_id: 사용자 ID
        category_id: 카테고리 ID (선택사항)
        limit: 최대 개수
    
    반환값:
        대화 기록 리스트
    """
    try:
        client = get_supabase_client()
        if not client:
            return []
        
        query = client.table('conversations').select('*').eq('user_id', user_id)
        
        if category_id:
            query = query.eq('category_id', category_id)
        
        result = query.order('created_at', desc=True).limit(limit).execute()
        return result.data if result.data else []
    
    except Exception as e:
        debug_print(f"대화 기록 조회 오류: {str(e)}", "ERROR")
        return []


def get_conversations_by_session(user_id, session_id, limit=500):
    """
    특정 사용자/세션 ID의 대화 기록 조회 (오름차순)
    """
    try:
        client = get_supabase_client()
        if not client:
            return []

        result = (
            client
            .table('conversations')
            .select('*')
            .eq('user_id', user_id)
            .eq('session_id', session_id)
            .order('created_at', desc=False)
            .limit(limit)
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        debug_print(f"세션별 대화 조회 오류: {str(e)}", "ERROR")
        return []


# ========================================
# 퀴즈 기록 관리
# ========================================

def save_quiz_attempt(user_id, category_id, quiz_data, user_answer, is_correct, time_taken=None):
    """
    퀴즈 시도 기록 저장
    
    매개변수:
        user_id: 사용자 ID
        category_id: 카테고리 ID
        quiz_data: 퀴즈 데이터 (dict)
        user_answer: 사용자 답변
        is_correct: 정답 여부
        time_taken: 풀이 시간 (초)
    
    반환값:
        성공 시 퀴즈 정보, 실패 시 None
    """
    try:
        debug_print("퀴즈 기록 저장 시도", "INFO")
        
        client = get_supabase_client()
        if not client:
            return None
        
        data = {
            'user_id': user_id,
            'category_id': category_id,
            'quiz_data': quiz_data,
            'user_answer': user_answer,
            'is_correct': is_correct,
            'time_taken': time_taken,
            'created_at': datetime.now().isoformat()
        }
        
        result = client.table('quiz_attempts').insert(data).execute()
        
        if result.data:
            debug_print("퀴즈 기록 저장 성공", "SUCCESS")
            return result.data[0]
        return None
    
    except Exception as e:
        debug_print(f"퀴즈 기록 저장 오류: {str(e)}", "ERROR")
        return None


def get_user_quiz_stats(user_id, category_id=None):
    """
    사용자의 퀴즈 통계 조회
    
    매개변수:
        user_id: 사용자 ID
        category_id: 카테고리 ID (선택사항)
    
    반환값:
        통계 정보 dict
    """
    try:
        client = get_supabase_client()
        if not client:
            return {'total': 0, 'correct': 0, 'accuracy': 0}
        
        query = client.table('quiz_attempts').select('*').eq('user_id', user_id)
        
        if category_id:
            query = query.eq('category_id', category_id)
        
        result = query.execute()
        attempts = result.data if result.data else []
        
        total = len(attempts)
        correct = sum(1 for a in attempts if a['is_correct'])
        accuracy = (correct / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'correct': correct,
            'accuracy': round(accuracy, 1)
        }
    
    except Exception as e:
        debug_print(f"퀴즈 통계 조회 오류: {str(e)}", "ERROR")
        return {'total': 0, 'correct': 0, 'accuracy': 0}


# ========================================
# 단어장 관리
# ========================================

def add_vocabulary(user_id, word, meaning, example=None, pronunciation=None):
    """
    단어장에 단어 추가
    
    매개변수:
        user_id: 사용자 ID
        word: 단어
        meaning: 뜻
        example: 예문
        pronunciation: 발음 기호
    
    반환값:
        성공 시 단어 정보, 실패 시 None
    """
    try:
        debug_print(f"단어 추가: {word}", "INFO")
        
        client = get_supabase_client()
        if not client:
            return None
        
        data = {
            'user_id': user_id,
            'word': word,
            'meaning': meaning,
            'example': example,
            'pronunciation': pronunciation,
            'mastered': False,
            'created_at': datetime.now().isoformat()
        }
        
        result = client.table('vocabulary').insert(data).execute()
        
        if result.data:
            debug_print(f"단어 추가 성공: {word}", "SUCCESS")
            return result.data[0]
        return None
    
    except Exception as e:
        debug_print(f"단어 추가 오류: {str(e)}", "ERROR")
        return None


def get_user_vocabulary(user_id, mastered=None):
    """
    사용자의 단어장 조회
    
    매개변수:
        user_id: 사용자 ID
        mastered: 숙달 여부 필터 (None, True, False)
    
    반환값:
        단어 리스트
    """
    try:
        client = get_supabase_client()
        if not client:
            return []
        
        query = client.table('vocabulary').select('*').eq('user_id', user_id)
        
        if mastered is not None:
            query = query.eq('mastered', mastered)
        
        result = query.order('created_at', desc=True).execute()
        return result.data if result.data else []
    
    except Exception as e:
        debug_print(f"단어장 조회 오류: {str(e)}", "ERROR")
        return []


def update_vocabulary_mastery(vocab_id, mastered):
    """
    단어 숙달 상태 업데이트
    
    매개변수:
        vocab_id: 단어 ID
        mastered: 숙달 여부
    
    반환값:
        성공 여부
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        client.table('vocabulary').update({'mastered': mastered}).eq('id', vocab_id).execute()
        
        debug_print(f"단어 숙달 상태 업데이트: {vocab_id}", "SUCCESS")
        return True
    
    except Exception as e:
        debug_print(f"단어 숙달 상태 업데이트 오류: {str(e)}", "ERROR")
        return False


# ========================================
# 완료!
# ========================================
debug_print("supabase_manager.py 로드 완료!", "SUCCESS")


def count_users_by_role(role: str) -> int:
    """해당 역할 사용자 수 카운트"""
    try:
        client = get_supabase_client()
        if not client:
            return 0
        res = client.table('users').select('*', count='exact').eq('role', role).execute()
        return int(res.count or 0)
    except Exception as e:
        debug_print(f"사용자 수 카운트 오류: {str(e)}", "ERROR")
        return 0


def count_all_users() -> int:
    try:
        client = get_supabase_client()
        if not client:
            return 0
        res = client.table('users').select('*', count='exact').execute()
        return int(res.count or 0)
    except Exception as e:
        debug_print(f"전체 사용자 수 카운트 오류: {str(e)}", "ERROR")
        return 0


def count_conversations(user_id: int | None = None) -> int:
    try:
        client = get_supabase_client()
        if not client:
            return 0
        q = client.table('conversations').select('*', count='exact')
        if user_id:
            q = q.eq('user_id', user_id)
        res = q.execute()
        return int(res.count or 0)
    except Exception as e:
        debug_print(f"대화 수 카운트 오류: {str(e)}", "ERROR")
        return 0


def fetch_recent_conversations(user_id: int | None = None, limit: int = 50):
    try:
        client = get_supabase_client()
        if not client:
            return []
        q = client.table('conversations').select('*').order('created_at', desc=True).limit(limit)
        if user_id:
            q = q.eq('user_id', user_id)
        res = q.execute()
        return res.data or []
    except Exception as e:
        debug_print(f"최근 대화 조회 오류: {str(e)}", "ERROR")
        return []


def get_quiz_attempts(user_id: int | None = None):
    try:
        client = get_supabase_client()
        if not client:
            return []
        q = client.table('quiz_attempts').select('*').order('created_at', desc=True)
        if user_id:
            q = q.eq('user_id', user_id)
        res = q.execute()
        return res.data or []
    except Exception as e:
        debug_print(f"퀴즈 조회 오류: {str(e)}", "ERROR")
        return []


def list_teachers(limit: int = 100):
    try:
        client = get_supabase_client()
        if not client:
            return []
        res = client.table('users').select('*').eq('role', 'teacher').order('created_at', desc=True).limit(limit).execute()
        return res.data or []
    except Exception as e:
        debug_print(f"교사 목록 조회 오류: {str(e)}", "ERROR")
        return []


# ========================================
# 문제은행 (교사용)
# ========================================

def create_question_bank_item(created_by: int, qtype: str, question: str, options: list | None, answer: str, explanation: str | None, category: str | None, grade: str | None, difficulty: int | None, tags: list | None):
    """
    문제은행 문항 생성
    options와 tags는 JSON으로 저장합니다.
    """
    try:
        client = get_supabase_client()
        if not client:
            return None
        data = {
            'created_by': created_by,
            'type': qtype,
            'question': question,
            'options': options or [],
            'answer': answer,
            'explanation': explanation,
            'category': category,
            'grade': grade,
            'difficulty': difficulty,
            'tags': tags or [],
            'is_active': True,
            'created_at': datetime.now().isoformat(),
        }
        res = client.table('question_bank').insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        debug_print(f"문제은행 문항 생성 오류: {str(e)}", "ERROR")
        return None


def list_question_bank_items(created_by: int, category: str | None = None, search: str | None = None, limit: int = 200):
    """
    교사가 만든 문제은행 문항 목록 조회
    """
    try:
        client = get_supabase_client()
        if not client:
            return []
        q = client.table('question_bank').select('*').eq('created_by', created_by).eq('is_active', True)
        if category:
            q = q.eq('category', category)
        # Supabase는 간단한 like 제공
        if search:
            q = q.like('question', f"%{search}%")
        res = q.order('created_at', desc=True).limit(limit).execute()
        return res.data or []
    except Exception as e:
        debug_print(f"문제은행 목록 조회 오류: {str(e)}", "ERROR")
        return []


# ========================================
# 과제 관리 (교사/학생)
# ========================================

def create_assignment(created_by: int, title: str, description: str | None = None, grade: str | None = None, due_date: datetime | None = None, is_active: bool = True):
    """
    과제 생성 (교사용)
    """
    try:
        client = get_supabase_client()
        if not client:
            return None
        data = {
            'created_by': created_by,
            'title': title,
            'description': description,
            'target_grade': grade,
            'due_date': due_date.isoformat() if due_date else None,
            'is_active': is_active,
            'created_at': datetime.now().isoformat(),
        }
        res = client.table('assignments').insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        debug_print(f"과제 생성 오류: {str(e)}", "ERROR")
        return None


def list_assignments(created_by: int | None = None, grade: str | None = None, active_only: bool = True, limit: int = 200):
    """
    과제 목록 조회
    created_by가 있으면 해당 교사가 만든 과제만, 없으면 전체
    grade 필터는 앱 단에서 후처리로도 적용합니다 (NULL 포함 처리 위해)
    """
    try:
        client = get_supabase_client()
        if not client:
            return []
        q = client.table('assignments').select('*')
        if created_by is not None:
            q = q.eq('created_by', created_by)
        if active_only:
            q = q.eq('is_active', True)
        res = q.order('created_at', desc=True).limit(limit).execute()
        rows = res.data or []
        # grade 필터 후처리 (NULL 허용)
        if grade:
            rows = [r for r in rows if (r.get('target_grade') is None) or (r.get('target_grade') == grade)]
        return rows
    except Exception as e:
        debug_print(f"과제 목록 조회 오류: {str(e)}", "ERROR")
        return []


def get_assignment_by_id(assignment_id: int):
    """과제 단건 조회"""
    try:
        client = get_supabase_client()
        if not client:
            return None
        res = client.table('assignments').select('*').eq('id', assignment_id).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        debug_print(f"과제 조회 오류: {str(e)}", "ERROR")
        return None


def get_student_submission(assignment_id: int, student_id: int):
    """학생의 과제 제출/선택 상태 조회"""
    try:
        client = get_supabase_client()
        if not client:
            return None
        res = client.table('assignment_submissions').select('*')\
            .eq('assignment_id', assignment_id).eq('student_id', student_id).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        debug_print(f"과제 제출 조회 오류: {str(e)}", "ERROR")
        return None


def select_assignment(assignment_id: int, student_id: int):
    """
    학생이 과제를 선택 (assignment_submissions 생성/갱신)
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        # 기존 제출 내역 확인
        existing = client.table('assignment_submissions').select('*')\
            .eq('assignment_id', assignment_id).eq('student_id', student_id).limit(1).execute()
        now_iso = datetime.now().isoformat()
        if existing.data:
            # 갱신
            client.table('assignment_submissions').update({
                'status': 'selected',
            }).eq('id', existing.data[0]['id']).execute()
        else:
            # 신규 생성
            client.table('assignment_submissions').insert({
                'assignment_id': assignment_id,
                'student_id': student_id,
                'status': 'selected',
                # created_at은 기본값으로 현재 시각 저장됨
            }).execute()
        return True
    except Exception as e:
        debug_print(f"과제 선택 처리 오류: {str(e)}", "ERROR")
        return False


def submit_assignment(assignment_id: int, student_id: int, answers: dict | None = None):
    """
    학생이 과제 제출 (텍스트/문항 답안을 answers에 JSON으로 저장)
    기존 선택 레코드가 있으면 갱신, 없으면 생성
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        existing = client.table('assignment_submissions').select('*')\
            .eq('assignment_id', assignment_id).eq('student_id', student_id).limit(1).execute()
        now_iso = datetime.now().isoformat()
        # 텍스트 답안만 사용하는 스키마에 맞춰 매핑
        text_answer = None
        if isinstance(answers, dict):
            text_answer = answers.get('text')
        elif isinstance(answers, str):
            text_answer = answers
        payload = {
            'answer_text': text_answer or '',
            'status': 'submitted',
            'submitted_at': now_iso,
        }
        if existing.data:
            client.table('assignment_submissions').update(payload).eq('id', existing.data[0]['id']).execute()
        else:
            payload.update({
                'assignment_id': assignment_id,
                'student_id': student_id,
                'selected_at': now_iso,
            })
            client.table('assignment_submissions').insert(payload).execute()
        return True
    except Exception as e:
        debug_print(f"과제 제출 처리 오류: {str(e)}", "ERROR")
        return False


def list_submissions(assignment_id: int):
    """특정 과제의 모든 제출/선택 현황 조회 (교사용)"""
    try:
        client = get_supabase_client()
        if not client:
            return []
        res = client.table('assignment_submissions').select('*').eq('assignment_id', assignment_id).order('created_at', desc=True).execute()
        return res.data or []
    except Exception as e:
        debug_print(f"과제 제출 목록 조회 오류: {str(e)}", "ERROR")
        return []


def grade_submission(submission_id: int, score: int | None = None, feedback: str | None = None):
    """교사가 과제 채점"""
    try:
        client = get_supabase_client()
        if not client:
            return False
        client.table('assignment_submissions').update({
            'score': score,
            'feedback': feedback,
            'graded_at': datetime.now().isoformat(),
            'status': 'graded',
        }).eq('id', submission_id).execute()
        return True
    except Exception as e:
        debug_print(f"과제 채점 처리 오류: {str(e)}", "ERROR")
        return False


def assignment_stats(assignment_id: int):
    """
    과제별 간단 통계 집계 (선택/제출/채점 수, 평균 점수)
    """
    try:
        client = get_supabase_client()
        if not client:
            return {
                'selected': 0,
                'submitted': 0,
                'graded': 0,
                'avg_score': None,
            }
        res = client.table('assignment_submissions').select('*').eq('assignment_id', assignment_id).execute()
        rows = res.data or []
        selected = sum(1 for r in rows if r.get('status') == 'selected')
        submitted = sum(1 for r in rows if r.get('status') == 'submitted')
        graded = sum(1 for r in rows if r.get('status') == 'graded')
        scores = [r.get('score') for r in rows if r.get('score') is not None]
        avg_score = (sum(scores) / len(scores)) if scores else None
        return {
            'selected': selected,
            'submitted': submitted,
            'graded': graded,
            'avg_score': avg_score,
        }
    except Exception as e:
        debug_print(f"과제 통계 조회 오류: {str(e)}", "ERROR")
        return {
            'selected': 0,
            'submitted': 0,
            'graded': 0,
            'avg_score': None,
        }


# ========================================
# 문서/RAG 헬퍼
# ========================================

def create_document(user_id: int, title: str | None, file_name: str, content_type: str | None):
    """
    문서 메타 생성 후 행 반환
    """
    try:
        client = get_supabase_client()
        if not client:
            return None
        data = {
            'user_id': user_id,
            'title': title or file_name,
            'file_name': file_name,
            'content_type': content_type,
            'created_at': datetime.now().isoformat()
        }
        res = client.table('documents').insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        debug_print(f"문서 생성 오류: {str(e)}", "ERROR")
        return None


def add_document_chunk(document_id: int, user_id: int, content: str, embedding: list[float], chunk_index: int, metadata: dict | None = None):
    """
    문서 청크와 임베딩 저장
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        data = {
            'document_id': document_id,
            'user_id': user_id,
            'chunk_index': chunk_index,
            'content': content,
            'embedding': embedding,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat()
        }
        client.table('document_chunks').insert(data).execute()
        return True
    except Exception as e:
        # 업로드 시 수백 개 청크에서 동일 오류가 반복되어 콘솔이 과도하게 지저분해질 수 있어
        # 개별 청크 오류 로그는 생략하고, 호출측(UI)에서 실패 개수만 요약 표시합니다.
        return False


def search_document_chunks(user_id: int, query_embedding: list[float], match_count: int = 5, document_id: int | None = None):
    """
    RPC를 통해 사용자 문서 청크 중에서 유사도 높은 상위 결과를 반환합니다.
    """
    try:
        client = get_supabase_client()
        if not client:
            return []
        params = {
            'query_embedding': query_embedding,
            'match_count': match_count,
            'user_id_input': user_id,
            'document_id_input': document_id
        }
        res = client.rpc('match_document_chunks', params).execute()
        return res.data or []
    except Exception as e:
        debug_print(f"문서 청크 검색 오류: {str(e)}", "ERROR")
        return []


def list_documents(user_id: int):
    """
    사용자 문서 목록 반환
    """
    try:
        client = get_supabase_client()
        if not client:
            return []
        res = client.table('documents').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return res.data or []
    except Exception as e:
        debug_print(f"문서 목록 조회 오류: {str(e)}", "ERROR")
        return []

