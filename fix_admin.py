#pip install streamlit python-dotenv supabase bcrypt

"""
관리자 계정 비밀번호 강제 재설정 스크립트
터미널에서 실행: python fix_admin.py
"""

from database.supabase_manager import get_user_by_username, update_user, get_supabase_client
from auth.auth_manager import hash_password, verify_password

print("=" * 50)
print("관리자 계정 비밀번호 강제 재설정")
print("=" * 50)

# 1. admin 계정 조회
print("\n1. admin 계정 조회 중...")
user = get_user_by_username('admin')
if not user:
    print("   ✗ admin 계정을 찾을 수 없습니다!")
    print("   최고관리자 계정을 생성합니다...")
    from auth.auth_manager import ensure_super_admin
    ensure_super_admin()
    user = get_user_by_username('admin')
    if not user:
        print("   ✗ 계정 생성 실패!")
        exit(1)

print(f"   ✓ 계정 발견: ID={user.get('id')}, 역할={user.get('role')}")

# 2. 현재 비밀번호 해시 확인
print("\n2. 현재 비밀번호 해시 확인 중...")
current_hash = user.get('password_hash', '')
print(f"   현재 해시: {current_hash[:50]}..." if current_hash else "   ✗ 해시가 없습니다!")

# 3. 새로운 비밀번호 설정
print("\n3. 비밀번호 재설정 중...")
new_password = 'test1234!'
new_hash = hash_password(new_password)
print(f"   새 비밀번호: '{new_password}'")
print(f"   새 해시: {new_hash[:50]}...")

# 4. 비밀번호 업데이트
print("\n4. 데이터베이스 업데이트 중...")
result = update_user(user.get('id'), password_hash=new_hash)
if result:
    print("   ✓ 비밀번호 업데이트 성공!")
else:
    print("   ✗ 비밀번호 업데이트 실패!")
    exit(1)

# 5. 검증
print("\n5. 비밀번호 검증 중...")
updated_user = get_user_by_username('admin')
if updated_user:
    test_result = verify_password(new_password, updated_user.get('password_hash', ''))
    if test_result:
        print("   ✓ 비밀번호 검증 성공!")
    else:
        print("   ✗ 비밀번호 검증 실패!")
        exit(1)
else:
    print("   ✗ 업데이트된 계정을 찾을 수 없습니다!")
    exit(1)

print("\n" + "=" * 50)
print("✅ 완료! 관리자 계정 비밀번호가 재설정되었습니다.")
print("=" * 50)
print("\n로그인 정보:")
print(f"   아이디: admin")
print(f"   비밀번호: test1234!")
print("\n이제 브라우저에서 다시 로그인해보세요.")

