# utils/explain_topic.py

import openai

# GPT API 설정 (환경변수 또는 상위에서 세팅)
openai.api_key = "YOUR_API_KEY"

def explain_topic(topic: str) -> str:
    """입력 주제에 대해 과학적 개념, 원리, 현황 등을 상세히 설명"""
    system_prompt = """
    너는 과학 교육 전문가 AI야.
    고등학생이 이해할 수 있도록 과학 주제를 다음 형식으로 설명해줘:

    1. 개념 정의
    2. 작동 원리
    3. 현재 과학/사회적 상황
    4. 응용 분야 예시
    5. 관련 논문 제목 2~3개 (출처 포함)
    6. 확장 가능한 탐구 아이디어

    글은 한글로, 전문적이면서도 쉽게. 제목은 굵게, 본문은 문단별로 구분해줘.
    """

    user_prompt = f"주제: {topic}"

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )

    return response['choices'][0]['message']['content']
