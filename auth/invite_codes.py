#pip install streamlit

# ========================================
# AI 학습 도우미 - 인증코드 유틸리티
# ========================================
# 이 파일은 '교사/학생 인증코드'를 만들고 관리하는 기능을 제공합니다.
# - 교사용 인증코드: 최고 관리자가 생성 → 교사가 가입 시 사용
# - 학생용 인증코드: 교사가 생성 → 학생이 가입 시 사용
# ========================================

from datetime import datetime, timedelta
import streamlit as st

from database import supabase_manager as db
from utils.helpers import generate_invite_code
import config


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
        print(f"{color}[INVITE-{level}]{reset} {message}")


# ========================================
# 교사 인증코드 생성 (관리자 전용)
# ========================================

def create_teacher_code(admin_user_id: int, days_valid: int = 30, memo: str | None = None) -> dict | None:
    try:
        code = generate_invite_code(length=6, prefix="TEACHER-")
        expires_at = datetime.now() + timedelta(days=days_valid)
        result = db.create_teacher_invite_code(code=code, created_by=admin_user_id, expires_at=expires_at, memo=memo)
        if result:
            debug_print(f"교사 코드 생성: {code}", "SUCCESS")
        return result
    except Exception as e:
        debug_print(f"교사 코드 생성 오류: {str(e)}", "ERROR")
        return None


# ========================================
# 학생 인증코드 생성 (교사 전용)
# ========================================

def create_student_code(teacher_user_id: int, class_name: str | None = None, uses: int = 10, days_valid: int = 7, memo: str | None = None) -> dict | None:
    try:
        code = generate_invite_code(length=6, prefix="")
        expires_at = datetime.now() + timedelta(days=days_valid)
        result = db.create_student_invite_code(
            code=code,
            created_by=teacher_user_id,
            class_name=class_name,
            max_uses=uses,
            expires_at=expires_at,
            memo=memo
        )
        if result:
            debug_print(f"학생 코드 생성: {code}", "SUCCESS")
        return result
    except Exception as e:
        debug_print(f"학생 코드 생성 오류: {str(e)}", "ERROR")
        return None

