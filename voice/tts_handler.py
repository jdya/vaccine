#pip install edge-tts streamlit

# ========================================
# AI 학습 도우미 - 텍스트를 음성으로 (TTS)
# ========================================
# 이 파일은 Edge TTS(무료)를 사용해서 텍스트를 mp3 파일로 바꿉니다.
# - 한국어/영어 등 다양한 목소리를 사용할 수 있어요.
# - 파일 경로에 한글이 있어도 문제 없도록 안전하게 처리했습니다.
# ========================================

import os
import asyncio
import edge_tts
import streamlit as st

import config
from utils.helpers import sanitize_filename


# ========================================
# 디버그 출력
# ========================================

def debug_print(message, level="INFO"):
    if config.DEBUG_MODE:
        # ANSI 색상 제거로 Windows 콘솔 호환성 확보
        print(f"[TTS-{level}] {message}")


# ========================================
# 음성 합성 (mp3 파일 생성)
# ========================================

DEFAULT_VOICE = "en-US-JennyNeural"   # 영어 여성
KOREAN_VOICE = "ko-KR-SunHiNeural"    # 한국어 여성


async def _synthesize_async(text: str, filepath: str, voice: str):
    tts = edge_tts.Communicate(text=text, voice=voice)
    await tts.save(filepath)


def synthesize_to_file(text: str, filename: str = "tts_output.mp3", voice: str | None = None) -> str | None:
    """
    텍스트를 mp3 파일로 저장합니다.
    
    매개변수:
        text: 읽어줄 텍스트
        filename: 저장할 파일명 (기본값: tts_output.mp3)
        voice: Edge TTS 음성 이름 (선택)
    
    반환값:
        생성된 mp3 파일의 절대 경로 (실패 시 None)
    """
    try:
        if not text or not text.strip():
            debug_print("빈 텍스트는 음성으로 만들 수 없어요.", "WARNING")
            return None
        
        # 저장 폴더: 프로젝트 루트의 temp/
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "temp")
        temp_dir = os.path.normpath(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)
        
        safe_name = sanitize_filename(filename)
        out_path = os.path.join(temp_dir, safe_name)
        out_path = os.path.normpath(out_path)
        
        chosen_voice = voice or DEFAULT_VOICE
        debug_print(f"TTS 시작 (voice={chosen_voice}, file={out_path})", "INFO")
        
        # asyncio 이벤트 루프 안전 실행
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Streamlit 환경 등 이미 루프가 돌고 있을 때
                coro = _synthesize_async(text, out_path, chosen_voice)
                asyncio.ensure_future(coro)
                # 즉시 파일이 만들어지지 않을 수 있으니, 간단 대기
                import time
                time.sleep(0.5)
            else:
                loop.run_until_complete(_synthesize_async(text, out_path, chosen_voice))
        except RuntimeError:
            # 루프가 없으면 새로 만들어 실행
            asyncio.run(_synthesize_async(text, out_path, chosen_voice))
        
        if os.path.exists(out_path):
            debug_print("TTS 파일 생성 성공", "SUCCESS")
            return out_path
        else:
            debug_print("TTS 파일 생성 실패", "ERROR")
            return None
    
    except Exception as e:
        debug_print(f"TTS 오류: {str(e)}", "ERROR")
        return None
