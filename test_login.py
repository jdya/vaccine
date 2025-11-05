#pip install streamlit python-dotenv supabase bcrypt

"""
간단한 로그인 테스트 스크립트
터미널에서 실행: python test_login.py
"""

from auth.auth_manager import login_with_username_password, ensure_super_admin
from database.supabase_manager import get_user_by_username
from auth.auth_manager import verify_password, hash_password

print("=" * 50)
print("로그인 테스트 시작")
print("=" * 50)

# 1. 최고관리자 계정 확인 및 생성
print("\n1. 최고관리자 계정 확인 중...")
ensure_super_admin()

# 2. admin 계정 조회
print("\n2. admin 계정 조회 중...")
user = get_user_by_username('admin')
if user:
    print(f"   ✓ 계정 존재: {user.get('username')}")
    print(f"   ✓ 역할: {user.get('role')}")
    print(f"   ✓ 비밀번호 해시: {user.get('password_hash', '')[:50]}...")
else:
    print("   ✗ 계정을 찾을 수 없습니다!")
    exit(1)

# 3. 비밀번호 테스트
print("\n3. 비밀번호 검증 테스트 중...")
test_password = 'test1234!'
stored_hash = user.get('password_hash', '')
if stored_hash:
    is_valid = verify_password(test_password, stored_hash)
    print(f"   입력 비밀번호: '{test_password}'")
    print(f"   검증 결과: {'✓ 성공' if is_valid else '✗ 실패'}")
else:
    print("   ✗ 저장된 비밀번호 해시가 없습니다!")

# 4. 로그인 함수 테스트
print("\n4. 로그인 함수 테스트 중...")
ok, msg = login_with_username_password('admin', 'test1234!')
print(f"   로그인 결과: {'✓ 성공' if ok else '✗ 실패'}")
print(f"   메시지: {msg}")

print("\n" + "=" * 50)
print("테스트 완료")
print("=" * 50)

if ok:
    print("\n✅ 로그인이 정상적으로 작동합니다!")
    print("   브라우저에서 다시 시도해보세요.")
else:
    print("\n❌ 로그인에 문제가 있습니다.")
    print("   터미널 로그를 확인하거나 위의 오류 메시지를 확인하세요.")

