#pip install streamlit python-dotenv supabase bcrypt

"""
비밀번호 해시 확인 스크립트
"""

from database.supabase_manager import get_user_by_username
from auth.auth_manager import verify_password, hash_password

print("=" * 50)
print("비밀번호 해시 확인")
print("=" * 50)

user = get_user_by_username('admin')
if not user:
    print("❌ admin 계정을 찾을 수 없습니다!")
    exit(1)

print(f"\n✓ admin 계정 발견")
print(f"  ID: {user.get('id')}")
print(f"  Username: {user.get('username')}")

stored_hash = user.get('password_hash', '')
print(f"\n저장된 해시:")
print(f"  길이: {len(stored_hash)} 문자")
print(f"  전체: {stored_hash}")
print(f"  처음 30자: {stored_hash[:30]}...")

# bcrypt 해시는 보통 60자여야 함
if len(stored_hash) < 50:
    print(f"\n⚠️ 경고: 해시가 짧습니다! (bcrypt 해시는 보통 60자입니다)")
    print(f"   해시가 잘렸을 가능성이 있습니다.")

print("\n" + "=" * 50)
print("비밀번호 검증 테스트")
print("=" * 50)

test_password = 'test1234!'
print(f"\n테스트 비밀번호: '{test_password}'")

if not stored_hash:
    print("❌ 저장된 해시가 없습니다!")
    exit(1)

try:
    result = verify_password(test_password, stored_hash)
    print(f"\n검증 결과: {'✓ 성공' if result else '✗ 실패'}")
    
    if not result:
        print("\n해시가 잘못되었을 수 있습니다. 새 해시 생성 중...")
        new_hash = hash_password(test_password)
        print(f"새 해시 길이: {len(new_hash)} 문자")
        print(f"새 해시: {new_hash}")
        
        # 데이터베이스 업데이트
        from database.supabase_manager import update_user
        if update_user(user.get('id'), password_hash=new_hash):
            print("\n✓ 데이터베이스에 새 해시를 저장했습니다!")
            print("이제 로그인을 다시 시도해보세요.")
        else:
            print("\n✗ 데이터베이스 업데이트 실패!")
    else:
        print("\n✓ 해시가 정상입니다. 로그인 문제는 다른 원인일 수 있습니다.")
        
except Exception as e:
    print(f"\n✗ 검증 중 오류 발생: {str(e)}")
    import traceback
    traceback.print_exc()

