# utils/generate_paper.py
import streamlit as st
from openai import OpenAI

@st.cache_data(ttl=3600, show_spinner=False)
def generate_research_paper(topic, research_idea, references=""):
    """
    선택된 연구 아이디어에 대한 논문 형식의 연구 계획을 생성
    
    Args:
        topic: 주요 연구 주제
        research_idea: 선택된 확장 가능한 연구 아이디어
        references: 관련 참고 문헌 및 내용 (선택적)
    
    Returns:
        각 섹션별 논문 내용이 포함된 딕셔너리
    """
    try:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])
        
        # 시스템 프롬프트 작성
        system_prompt = """
        당신은 과학 연구 계획을 작성하는 전문가입니다. 고등학생이 선택한 연구 아이디어를 바탕으로 논문 형식의 연구 계획을 작성해주세요.
        결과는 다음 섹션으로 구성되어야 합니다:
        
        1. 초록 (Abstract): 연구의 목적, 방법, 예상 결과를 간단히 요약 (150-200단어)
        2. 실험 방법 (Methods): 연구를 수행하기 위한 구체적인 절차와 방법론 제안 (300-400단어)
        3. 예상 결과 (Expected Results): 연구를 통해 얻을 수 있는 잠재적 결과 및 의미 (200-300단어)
        4. 시각자료 제안 (Suggested Visualizations): 결과를 시각화할 방법을 텍스트로 설명 (100-200단어) - 그래프 X/Y축 변수, 표 구조, 다이어그램 등 텍스트로만 설명
        5. 결론 (Conclusion): 연구의 잠재적 영향과 중요성 (150-200단어)
        6. 참고문헌 (References): 참고할 만한 문헌 목록 (앞서 제공된 관련 논문 활용)
        
        다음 지침을 따라주세요:
        - 고등학생 수준에서 실행 가능한 현실적인 연구 계획을 제안하세요
        - 각 섹션은 명확하고 구체적이어야 합니다
        - 모든 내용은 한국어로 작성해주세요
        - 시각자료는 텍스트로만 설명하고, 실제 이미지를 생성하지 마세요
        - 실험 방법은 실제로 수행 가능한 구체적인 절차를 포함해야 합니다
        
        응답 형식은 다음과 같이 각 섹션을 명확히 구분하여 제공해주세요:
        ```
        {
          "abstract": "초록 내용...",
          "methods": "실험 방법 내용...",
          "results": "예상 결과 내용...",
          "visuals": "시각자료 제안 내용...",
          "conclusion": "결론 내용...",
          "references": "참고문헌 목록..."
        }
        ```
        
        JSON 형식으로 응답해야 하며, 각 섹션의 키 이름은 위의 예시와 동일해야 합니다.
        """
        
        # 사용자 프롬프트 작성
        user_prompt = f"""
        주제: {topic}
        
        선택된 연구 아이디어: {research_idea}
        
        관련 자료 및 참고문헌:
        {references}
        
        위 정보를 바탕으로 논문 형식의 연구 계획을 작성해주세요.
        """
        
        # GPT 호출
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # 응답 파싱
        import json
        paper_data = json.loads(response.choices[0].message.content)
        
        return paper_data
        
    except Exception as e:
        print(f"연구 계획 생성 오류: {e}")
        return {
            "abstract": "초록 생성 중 오류가 발생했습니다.",
            "methods": "실험 방법 생성 중 오류가 발생했습니다.",
            "results": "예상 결과 생성 중 오류가 발생했습니다.",
            "visuals": "시각자료 제안 생성 중 오류가 발생했습니다.",
            "conclusion": "결론 생성 중 오류가 발생했습니다.",
            "references": "참고문헌 생성 중 오류가 발생했습니다."
        }
