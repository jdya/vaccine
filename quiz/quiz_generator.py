#pip install openai streamlit

# ========================================
# AI 학습 도우미 - 퀴즈 생성기
# ========================================
# 이 파일은 DeepSeek AI에게 요청해서 퀴즈를 자동으로 만들어줍니다.
# - 객관식/OX/단답형을 지원합니다.
# - 혹시 AI가 이상한 형식으로 보내면 안전하게 '기본 퀴즈'로 대체합니다.
# ========================================

import json
import streamlit as st
from typing import Literal

from ai.deepseek_handler import generate_chat_response
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
        print(f"{color}[QUIZ-{level}]{reset} {message}")


QuizType = Literal["multiple", "true_false", "short_answer"]


def _build_quiz_prompt(category: str, grade: str | None, quiz_type: QuizType, count: int, difficulty: int) -> str:
    return f"""
당신은 학생을 위한 퀴즈 출제 도우미입니다.

요구사항:
- 카테고리: {category}
- 학년: {grade or '미정'}
- 유형: {quiz_type}  # multiple(객관식), true_false(OX), short_answer(단답형)
- 문제 수: {count}
- 난이도: {difficulty}  # 1(쉬움)~5(어려움)

JSON만 반환하세요. 형식은 아래 예시를 정확히 따르세요.

{{
  "questions": [
    {{
      "type": "{quiz_type}",
      "question": "문제 내용",
      "options": ["보기1", "보기2", "보기3", "보기4"],  # OX/단답형이면 생략 가능
      "answer": "정답 텍스트 또는 보기 인덱스(0부터)",
      "explanation": "간단한 해설"
    }}
  ]
}}
"""


def _fallback_quiz(quiz_type: QuizType, count: int) -> dict:
    """AI 실패 시 기본 퀴즈를 만들어 돌려줍니다."""
    questions = []
    for i in range(count):
        if quiz_type == "multiple":
            questions.append({
                "type": "multiple",
                "question": f"{i+1} + {i+2} = ?",
                "options": [str(i), str(i+1), str(i+2), str(i+3)],
                "answer": "2",  # 보기 인덱스가 아닌 텍스트 정답으로 통일
                "explanation": "간단한 덧셈 문제예요."
            })
        elif quiz_type == "true_false":
            questions.append({
                "type": "true_false",
                "question": "물은 100도에서 끓는다.",
                "answer": "true",
                "explanation": "표준 기압에서 물의 끓는점은 100도입니다."
            })
        else:
            questions.append({
                "type": "short_answer",
                "question": "사과를 영어로 뭐라고 하나요?",
                "answer": "apple",
                "explanation": "사과는 apple이라고 해요."
            })
    return {"questions": questions}


def generate_quiz(category: str, grade: str | None, quiz_type: QuizType = "multiple", count: int = 5, difficulty: int = 2) -> dict:
    try:
        prompt = _build_quiz_prompt(category, grade, quiz_type, count, difficulty)
        ok, text = generate_chat_response(
            category=category,
            grade=grade,
            is_teacher=False,
            conversation_messages=[{"role": "user", "content": prompt}]
        )
        if not ok:
            debug_print("AI 생성 실패 → 기본 퀴즈로 대체", "WARNING")
            return _fallback_quiz(quiz_type, count)
        
        # JSON 파싱 시도
        try:
            # 코드 블록 형태로 오면 제거
            cleaned = text.strip().strip('`')
            # 첫/마지막 ```json 제거
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
            data = json.loads(cleaned)
            if "questions" in data and isinstance(data["questions"], list) and len(data["questions"]) > 0:
                debug_print("퀴즈 JSON 파싱 성공", "SUCCESS")
                return data
            else:
                debug_print("퀴즈 JSON 구조가 비정상 → 기본 퀴즈", "WARNING")
                return _fallback_quiz(quiz_type, count)
        except Exception as e:
            debug_print(f"JSON 파싱 오류: {str(e)} → 기본 퀴즈", "ERROR")
            return _fallback_quiz(quiz_type, count)
    except Exception as e:
        debug_print(f"퀴즈 생성 중 알 수 없는 오류: {str(e)}", "ERROR")
        return _fallback_quiz(quiz_type, count)

