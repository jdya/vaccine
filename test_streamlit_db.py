#pip install streamlit python-dotenv supabase

"""
Streamlit 환경에서 데이터베이스 연결 테스트
"""

# Streamlit 환경 시뮬레이션
import sys
import types

# realtime 모킹 (app.py와 동일)
if 'realtime' not in sys.modules:
    fake_realtime = types.ModuleType('realtime')
    
    class FakeAuthorizationError(Exception):
        pass
    class FakeNotConnectedError(Exception):
        pass
    
    fake_realtime.AuthorizationError = FakeAuthorizationError
    fake_realtime.NotConnectedError = FakeNotConnectedError
    
    class FakeAsyncRealtimeChannel:
        def __init__(self, *args, **kwargs):
            pass
    class FakeAsyncRealtimeClient:
        def __init__(self, *args, **kwargs):
            pass
    class FakeSyncRealtimeChannel:
        def __init__(self, *args, **kwargs):
            pass
    class FakeSyncRealtimeClient:
        def __init__(self, *args, **kwargs):
            pass
    class FakeRealtimeChannelOptions:
        def __init__(self, *args, **kwargs):
            pass
    
    fake_realtime.AsyncRealtimeChannel = FakeAsyncRealtimeChannel
    fake_realtime.AsyncRealtimeClient = FakeAsyncRealtimeClient
    fake_realtime.SyncRealtimeChannel = FakeSyncRealtimeChannel
    fake_realtime.SyncRealtimeClient = FakeSyncRealtimeClient
    fake_realtime.RealtimeChannelOptions = FakeRealtimeChannelOptions
    
    fake_message = types.ModuleType('realtime.message')
    fake_message.HEARTBEAT_PAYLOAD = b'\x00'
    fake_message.PHOENIX = 'phoenix'
    fake_realtime.message = fake_message
    
    fake_async = types.ModuleType('realtime._async')
    fake_client = types.ModuleType('realtime._async.client')
    fake_async.client = fake_client
    fake_realtime._async = fake_async
    
    sys.modules['realtime'] = fake_realtime
    sys.modules['realtime.message'] = fake_message
    sys.modules['realtime._async'] = fake_async
    sys.modules['realtime._async.client'] = fake_client

print("=" * 50)
print("Streamlit 환경 데이터베이스 연결 테스트")
print("=" * 50)

try:
    print("\n1. supabase import 시도...")
    from supabase import create_client, Client
    print("   ✓ supabase import 성공")
except Exception as e:
    print(f"   ✗ supabase import 실패: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

try:
    print("\n2. database.supabase_manager import 시도...")
    from database.supabase_manager import get_supabase_client
    print("   ✓ supabase_manager import 성공")
except Exception as e:
    print(f"   ✗ supabase_manager import 실패: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

try:
    print("\n3. Supabase 클라이언트 생성 시도...")
    client = get_supabase_client()
    if client:
        print("   ✓ 클라이언트 생성 성공")
        print(f"   클라이언트 타입: {type(client)}")
    else:
        print("   ✗ 클라이언트 생성 실패 (None 반환)")
        exit(1)
except Exception as e:
    print(f"   ✗ 클라이언트 생성 실패: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

try:
    print("\n4. 데이터베이스 연결 테스트...")
    result = client.table('users').select('id').limit(1).execute()
    print("   ✓ 연결 테스트 성공")
    print(f"   결과: {result.data}")
except Exception as e:
    print(f"   ✗ 연결 테스트 실패: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 50)
print("✅ 모든 테스트 통과!")
print("=" * 50)

