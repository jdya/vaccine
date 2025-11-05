#pip install bcrypt streamlit supabase python-dotenv

# ========================================
# AI 학습 도우미 - 인증 매니저
# ========================================
# 초등학생도 이해할 수 있도록 쉽게 설명하는 주석을 넣었습니다.
# 이 파일은 회원가입과 로그인(아이디+비밀번호) 기능을 담당합니다.
# - 교사/학생은 '인증코드'로만 가입할 수 있어요.
# - 비밀번호는 절대 그대로 저장하지 않고, bcrypt로 안전하게 '암호화(해싱)'해서 저장합니다.
# - 데이터 저장/조회는 database/supabase_manager.py를 사용합니다.
# ========================================

from datetime import datetime, timedelta
import bcrypt
import streamlit as st

from database import supabase_manager as db
from utils.helpers import generate_invite_code, sanitize_filename
from utils.session_manager import login_user, logout_user
import config


# ========================================
# 디버그 출력 (무슨 일이 일어나는지 터미널에 보여줌)
# ========================================

def debug_print(message, level="INFO"):
    if config.DEBUG_MODE:
        colors = {
            "INFO": "\033[94m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "SUCCESS": "\033[92m",
        }
        reset = "\033[0m"
        color = colors.get(level, colors["INFO"])
        print(f"{color}[AUTH-{level}]{reset} {message}")


# ========================================
# 비밀번호 처리 (해싱/검증)
# ========================================

def hash_password(plain_password: str) -> str:
    """
    비밀번호를 안전하게 해싱합니다.
    - 같은 비밀번호라도 매번 다른 결과가 나와서 더 안전해요!
    """
    try:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        debug_print(f"비밀번호 해싱 오류: {str(e)}", "ERROR")
        return ""


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    입력한 비밀번호가 저장된 해시와 같은지 확인합니다.
    """
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        debug_print(f"비밀번호 검증 오류: {str(e)}", "ERROR")
        return False


# ========================================
# 아이디 규칙 (한글/영문/숫자, 3~20자)
# ========================================

def validate_username(username: str) -> tuple[bool, str | None]:
    try:
        if not username:
            return False, "아이디를 입력해주세요."
        if len(username) < 3 or len(username) > 20:
            return False, "아이디는 3~20자여야 해요."
        # 한글/영문/숫자만 허용 (공백/특수문자 X)
        import re
        if not re.fullmatch(r"[\w가-힣]+", username):
            return False, "아이디는 한글/영문/숫자만 사용할 수 있어요."
        return True, None
    except Exception as e:
        debug_print(f"아이디 검증 오류: {str(e)}", "ERROR")
        return False, "아이디 검증 중 오류가 발생했어요."


# ========================================
# 회원가입 - 교사
# ========================================

def signup_teacher(username: str, full_name: str, password: str, teacher_invite_code: str) -> tuple[bool, str]:
    try:
        debug_print(f"교사 회원가입 시도: {username}", "INFO")
        # 1) 아이디 규칙 확인
        ok, msg = validate_username(username)
        if not ok:
            return False, msg
        # 닉네임이 비어있으면 아이디로 대체
        full_name = (full_name or "").strip()
        if not full_name:
            full_name = username
        # 2) 인증코드 확인
        code_info = db.get_teacher_invite_code(teacher_invite_code)
        if not code_info:
            return False, "유효하지 않은 교사 인증코드예요."
        if not code_info.get('is_active', False):
            return False, "이미 사용된 인증코드예요."
        # 만료일 체크
        expires_at = code_info.get('expires_at')
        if expires_at:
            # Supabase가 문자열로 반환하니 비교를 위해 앞부분만 사용
            if datetime.fromisoformat(expires_at.replace('Z','')) < datetime.now():
                return False, "만료된 인증코드예요."
        
        # 3) 사용자 중복 확인
        if db.get_user_by_username(username):
            return False, "이미 존재하는 아이디예요. 다른 아이디를 사용해주세요."
        
        # 4) 비밀번호 해싱
        pw_hash = hash_password(password)
        if not pw_hash:
            return False, "비밀번호 처리 중 오류가 발생했어요."
        
        # 5) 사용자 생성 (role=teacher)
        user = db.create_user(
            username=username,
            password_hash=pw_hash,
            full_name=full_name,
            role='teacher',
            grade=None,
            invite_code_used=teacher_invite_code,
            created_by=code_info.get('created_by')  # 관리자가 생성한 코드
        )
        if not user:
            return False, "회원가입 처리 중 문제가 생겼어요. 잠시 후 다시 시도해주세요."
        
        # 6) 인증코드 사용 처리
        db.use_teacher_invite_code(teacher_invite_code, user.get('id'))
        
        debug_print(f"교사 회원가입 성공: {username}", "SUCCESS")
        return True, "교사 회원가입이 완료되었어요!"
    
    except Exception as e:
        debug_print(f"교사 회원가입 오류: {str(e)}", "ERROR")
        return False, "회원가입 중 오류가 발생했어요."


# ========================================
# 회원가입 - 학생
# ========================================

def signup_student(username: str, full_name: str, password: str, grade: str, student_invite_code: str, teacher_id: int | None = None) -> tuple[bool, str]:
    try:
        debug_print(f"학생 회원가입 시도: {username}", "INFO")
        # 1) 아이디 규칙 확인
        ok, msg = validate_username(username)
        if not ok:
            return False, msg
        # 닉네임이 비어있으면 아이디로 대체
        full_name = (full_name or "").strip()
        if not full_name:
            full_name = username
        # 2) 인증코드 확인
        code_info = db.get_student_invite_code(student_invite_code)
        if not code_info:
            return False, "유효하지 않은 학생 인증코드예요."
        if not code_info.get('is_active', False):
            return False, "사용할 수 없는 인증코드예요."
        # 만료일 체크
        expires_at = code_info.get('expires_at')
        if expires_at:
            if datetime.fromisoformat(expires_at.replace('Z','')) < datetime.now():
                return False, "만료된 인증코드예요."
        # 사용 횟수 체크
        used = int(code_info.get('used_count', 0))
        max_uses = int(code_info.get('max_uses', 0))
        if max_uses and used >= max_uses:
            return False, "이 인증코드는 정원이 가득 찼어요. 선생님께 문의해주세요."
        
        # 3) 사용자 중복 확인
        if db.get_user_by_username(username):
            return False, "이미 존재하는 아이디예요. 다른 아이디를 사용해주세요."
        
        # 4) 비밀번호 해싱
        pw_hash = hash_password(password)
        if not pw_hash:
            return False, "비밀번호 처리 중 오류가 발생했어요."
        
        # 5) 사용자 생성 (role=student)
        creator = teacher_id if teacher_id else code_info.get('created_by')
        user = db.create_user(
            username=username,
            password_hash=pw_hash,
            full_name=full_name,
            role='student',
            grade=grade,
            invite_code_used=student_invite_code,
            created_by=creator
        )
        if not user:
            return False, "회원가입 처리 중 문제가 생겼어요. 잠시 후 다시 시도해주세요."
        
        # 6) 인증코드 사용 처리 (사용 횟수 +1)
        db.use_student_invite_code(student_invite_code)
        
        debug_print(f"학생 회원가입 성공: {username}", "SUCCESS")
        return True, "학생 회원가입이 완료되었어요!"
    
    except Exception as e:
        debug_print(f"학생 회원가입 오류: {str(e)}", "ERROR")
        return False, "회원가입 중 오류가 발생했어요."


# ========================================
# 로그인
# ========================================

def login_with_username_password(username: str, password: str) -> tuple[bool, str]:
    try:
        # 입력값 공백 제거
        username = username.strip() if username else ""
        password = password.strip() if password else ""
        
        if not username or not password:
            return False, "아이디와 비밀번호를 모두 입력해주세요."
        
        debug_print(f"로그인 시도: {username} (비밀번호 길이: {len(password)})", "INFO")
        
        # 데이터베이스 연결 확인
        client = db.get_supabase_client()
        if not client:
            debug_print("Supabase 클라이언트를 가져올 수 없습니다! Fallback 시도", "ERROR")
            # Fallback: 직접 클라이언트 생성 후 쿼리 시도 (일부 환경에서 세션 초기화 문제 우회)
            try:
                from supabase import create_client as _create_client
                fallback_client = _create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                # 간단한 쿼리로 연결 확인
                fallback_client.table('users').select('id').limit(1).execute()
                client = fallback_client
                debug_print("Fallback 클라이언트 생성 성공", "SUCCESS")
            except Exception as e:
                debug_print(f"Fallback 실패: {str(e)}", "ERROR")
                # 최후 수단: 관리자 로컬 로그인 (DB 없이)
                if username == config.SUPER_ADMIN_USERNAME and password == config.SUPER_ADMIN_PASSWORD:
                    debug_print("DB 없이 로컬 관리자 로그인 허용", "WARNING")
                    login_user({
                        'id': -1,
                        'username': username,
                        'full_name': '관리자',
                        'role': 'super_admin',
                        'grade': None,
                    })
                    return True, "관리자 로컬 로그인 (임시). 데이터베이스 연결을 점검하세요."
                return False, "데이터베이스 연결 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

        user = db.get_user_by_username(username)
        # 만약 상단에서 client를 Fallback으로 생성했는데, get_user_by_username이 실패했다면 직접 쿼리 시도
        if not user and client:
            try:
                res = client.table('users').select('*').eq('username', username).execute()
                if getattr(res, 'data', None):
                    user = res.data[0]
                    debug_print("직접 쿼리로 사용자 로드 성공", "INFO")
            except Exception as e:
                debug_print(f"직접 쿼리 실패: {str(e)}", "ERROR")
        if not user:
            debug_print(f"사용자를 찾을 수 없음: {username}", "WARNING")
            # 디버깅: 모든 사용자 확인
            try:
                all_users = db.get_all_users()
                debug_print(f"데이터베이스의 사용자 수: {len(all_users) if all_users else 0}", "INFO")
                if all_users:
                    usernames = [u.get('username') for u in all_users[:5]]
                    debug_print(f"사용자 목록 (처음 5개): {usernames}", "INFO")
            except Exception as e:
                debug_print(f"사용자 목록 조회 실패: {str(e)}", "WARNING")
            return False, "아이디 또는 비밀번호가 올바르지 않아요."
        
        debug_print(f"사용자 찾음: {user.get('username')}, 역할: {user.get('role')}", "INFO")
        
        stored_hash = user.get('password_hash', '')
        if not stored_hash:
            debug_print(f"저장된 비밀번호 해시가 없음: {username}", "ERROR")
            return False, "아이디 또는 비밀번호가 올바르지 않아요."
        
        debug_print(f"비밀번호 검증 시작... (해시 길이: {len(stored_hash)})", "INFO")
        password_valid = verify_password(password, stored_hash)
        debug_print(f"비밀번호 검증 결과: {password_valid}", "INFO")
        
        if not password_valid:
            # 디버깅: 비밀번호 해시 직접 확인
            debug_print(f"비밀번호 불일치: {username}", "WARNING")
            debug_print(f"입력 비밀번호: '{password}'", "WARNING")
            debug_print(f"저장된 해시: {stored_hash[:50]}...", "WARNING")
            return False, "아이디 또는 비밀번호가 올바르지 않아요."
        
        # 세션에 로그인 정보 저장
        login_user({
            'id': user.get('id'),
            'username': user.get('username'),
            'full_name': user.get('full_name'),
            'role': user.get('role'),
            'grade': user.get('grade'),
        })
        
        # 마지막 로그인 시간 업데이트
        db.update_last_login(user.get('id'))
        debug_print(f"로그인 성공: {username}", "SUCCESS")
        return True, "로그인 되었습니다!"
    
    except Exception as e:
        debug_print(f"로그인 오류: {str(e)}", "ERROR")
        return False, "로그인 중 오류가 발생했어요."


# ========================================
# 최초 관리자(슈퍼관리자) 생성
# ========================================

def ensure_super_admin():
    """
    .env(또는 Secrets)의 SUPER_ADMIN_USERNAME/PASSWORD를 이용해
    최초 관리자 계정을 보장합니다. (없으면 생성, 있으면 비밀번호 업데이트)
    """
    try:
        username = config.SUPER_ADMIN_USERNAME
        password = config.SUPER_ADMIN_PASSWORD
        if not username or not password:
            debug_print("SUPER_ADMIN 환경 변수가 설정되지 않았습니다.", "WARNING")
            return False
        
        exist = db.get_user_by_username(username)
        pw_hash = hash_password(password)
        if not pw_hash:
            return False
        
        if exist:
            # 기존 계정이 있으면 비밀번호를 업데이트
            if exist.get('role') != 'super_admin':
                debug_print(f"사용자 '{username}'가 있지만 super_admin 역할이 아닙니다. 역할을 업데이트합니다.", "WARNING")
                db.update_user(exist.get('id'), role='super_admin', password_hash=pw_hash)
            else:
                # 비밀번호가 다르면 업데이트
                if not verify_password(password, exist.get('password_hash', '')):
                    debug_print("관리자 비밀번호를 업데이트합니다.", "INFO")
                    db.update_user(exist.get('id'), password_hash=pw_hash)
                else:
                    debug_print("관리자 계정이 이미 존재하고 비밀번호가 올바릅니다.", "INFO")
            return True
        
        # 계정이 없으면 생성
        user = db.create_user(
            username=username,
            password_hash=pw_hash,
            full_name=username,  # 기본값을 아이디로 설정
            role='super_admin',
            grade=None,
            invite_code_used='INIT',
            created_by=None
        )
        if user:
            debug_print("최초 관리자 계정을 생성했습니다.", "SUCCESS")
            return True
        return False
    
    except Exception as e:
        debug_print(f"관리자 생성 오류: {str(e)}", "ERROR")
        return False
