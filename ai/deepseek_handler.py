#pip install openai python-dotenv streamlit

# ========================================
# AI 학습 도우미 - DeepSeek 핸들러
# ========================================
# 이 파일은 DeepSeek API를 사용하여 AI 답변을 만들어 줍니다.
# DeepSeek는 OpenAI와 비슷한 방식으로 사용할 수 있어요.
# - 환경 변수에 DEEPSEEK_API_KEY가 있어야 합니다.
# - (선택) DEEPSEEK_BASE_URL을 설정하면 커스텀 엔드포인트를 쓸 수 있어요.
# ========================================

import os
import streamlit as st
from openai import OpenAI, APIError, RateLimitError, APITimeoutError

import config
from ai.prompts import build_system_prompt


# ========================================
# 디버그 출력 함수
# ========================================

def debug_print(message, level="INFO"):
    if config.DEBUG_MODE:
        # Windows 콘솔 호환을 위해 ANSI 색상 제거
        print(f"[AI-{level}] {message}")


# ========================================
# 클라이언트 초기화 (싱글톤)
# ========================================

_client = None

def get_client() -> OpenAI | None:
    global _client
    if _client is None:
        try:
            api_key = config.DEEPSEEK_API_KEY
            if not api_key:
                debug_print("DEEPSEEK_API_KEY가 설정되지 않았습니다.", "ERROR")
                return None
            base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            _client = OpenAI(api_key=api_key, base_url=base_url)
            debug_print("DeepSeek 클라이언트 초기화 성공", "SUCCESS")
        except Exception as e:
            debug_print(f"클라이언트 초기화 오류: {str(e)}", "ERROR")
            return None
    return _client


# ========================================
# 채팅 응답 생성
# ========================================

def generate_chat_response(
    category: str,
    grade: str | None,
    is_teacher: bool,
    conversation_messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> tuple[bool, str]:
    """
    AI에게 메시지를 보내고 답변을 받아옵니다.
    
    매개변수:
        category: 카테고리 이름 (예: 'english', 'education')
        grade: 학년 (예: '초등 3학년')
        is_teacher: 교사 모드 여부
        conversation_messages: [{"role":"user|assistant", "content":"..."}]
    
    반환값:
        (성공여부, 응답 텍스트)
    """
    try:
        client = get_client()
        if not client:
            return False, "AI 설정이 완료되지 않았어요. 환경 변수를 확인해주세요."
        
        system_prompt = build_system_prompt(category, grade, is_teacher)
        debug_print(f"시스템 프롬프트 준비 완료 (category={category}, grade={grade})", "INFO")
        
        # OpenAI 호환 Chat Completions
        messages = [{"role": "system", "content": system_prompt}] + conversation_messages
        
        # 모델 이름: DeepSeek에서 제공하는 최신 모델명을 사용하세요.
        # 여기서는 예시로 'deepseek-chat'을 사용합니다.
        temp = 0.7 if temperature is None else float(temperature)
        tokens = 800 if max_tokens is None else int(max_tokens)
        completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=temp,
            max_tokens=tokens,
        )
        
        content = completion.choices[0].message.content.strip()
        debug_print("AI 응답 생성 성공", "SUCCESS")
        return True, content
    
    except (RateLimitError, APITimeoutError) as e:
        debug_print(f"AI 속도 제한 또는 시간 초과: {str(e)}", "ERROR")
        return False, "AI가 잠시 바쁜가 봐요. 잠시 후 다시 시도해주세요."
    except APIError as e:
        debug_print(f"AI API 오류: {str(e)}", "ERROR")
        return False, "AI 요청 중 문제가 발생했어요."
    except Exception as e:
        debug_print(f"알 수 없는 오류: {str(e)}", "ERROR")
        return False, "AI 처리 중 알 수 없는 오류가 발생했어요."


# ========================================
# 채팅 응답 스트리밍 (지연 체감 감소)
# ========================================

def stream_chat_response(
    category: str,
    grade: str | None,
    is_teacher: bool,
    conversation_messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
):
    """
    스트리밍 가능한 제너레이터를 반환합니다.
    UI에서 st.chat_message("assistant").write_stream(...) 또는
    placeholder 반복 갱신으로 사용할 수 있습니다.
    """
    client = get_client()
    if not client:
        yield "AI 설정이 완료되지 않았어요. 환경 변수를 확인해주세요."
        return

    system_prompt = build_system_prompt(category, grade, is_teacher)
    messages = [{"role": "system", "content": system_prompt}] + conversation_messages

    try:
        temp = 0.7 if temperature is None else float(temperature)
        tokens = 800 if max_tokens is None else int(max_tokens)
        for chunk in client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=temp,
            max_tokens=tokens,
            stream=True,
        ):
            try:
                delta = chunk.choices[0].delta
                if delta and getattr(delta, "content", None):
                    yield delta.content
            except Exception:
                # 조용히 건너뜀 (일부 이벤트 타입은 delta가 없음)
                continue
    except (RateLimitError, APITimeoutError) as e:
        debug_print(f"AI 속도 제한/시간 초과 (stream): {str(e)}", "ERROR")
        yield "AI가 잠시 바쁜가 봐요. 잠시 후 다시 시도해주세요."
    except APIError as e:
        debug_print(f"AI API 오류 (stream): {str(e)}", "ERROR")
        yield "AI 요청 중 문제가 발생했어요."
    except Exception as e:
        debug_print(f"알 수 없는 오류 (stream): {str(e)}", "ERROR")
        yield "AI 처리 중 알 수 없는 오류가 발생했어요."
