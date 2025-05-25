import anthropic
import streamlit as st
import re

# DOI 링크 변환 함수 추가 (app.py에서도 사용 가능하도록)
def convert_doi_to_links(text):
    """DOI 패턴을 감지하여 클릭 가능한 링크로 변환"""
    # 다양한 DOI 패턴 인식
    doi_pattern = r'(?:DOI\s*:?\s*)?(\b10\.\d{4,}\/[a-zA-Z0-9./_()-]+\b)'
    
    # HTML 링크로 변환
    def replace_doi(match):
        doi = match.group(1)
        return f'<a href="https://doi.org/{doi}" target="_blank" style="color: #0969da; text-decoration: underline;">{doi}</a>'
    
    # 텍스트 내 DOI 패턴을 링크로 변환
    linked_text = re.sub(doi_pattern, replace_doi, text)
    
    return linked_text

@st.cache_data(show_spinner="🤖 AI 설명을 생성 중입니다...", ttl=3600)
def explain_topic(topic: str) -> list:
    """Claude 기반 주제 설명 생성 (문단 단위 리스트 반환)"""
    try:
        client = anthropic.Anthropic(api_key=st.secrets["api"]["claude_key"])
    except KeyError:
        st.error("❌ Claude API 키가 설정되지 않았습니다.")
        st.stop()
    
    system_prompt = """
    너는 'LittleScienceAI 도우미'로, 고등학생에게 과학 주제를 쉽고 재미있게 설명하는 친근한 전문가야.
    각 섹션을 자연스러운 문장으로 풍부하게 설명하되, 읽으면서 "아, 이해됐다!"라는 느낌이 들도록 써줘.

    **다음 구조로 작성하되, 각 섹션은 자연스러운 문단 형태로 풍부하게 설명해:**

    ## 🔬 **개념 정의**
    주제가 무엇인지 쉽고 명확하게 설명해줘. 마치 친구에게 설명하듯이 친근하게 시작하고, 전문 용어가 나오면 바로 쉬운 말로 풀어서 설명해. 일상생활에서 볼 수 있는 비유나 예시를 들어서 "아, 그런 거구나!"라고 이해할 수 있게 해줘. 왜 이 주제가 중요하고 흥미로운지도 자연스럽게 언급해.

    ---

    ## ⚙️ **작동 원리 & 메커니즘**
    이 기술이나 현상이 어떻게 작동하는지 단계별로 풀어서 설명해줘. 복잡한 과정이라도 "먼저 이렇게 되고, 그 다음엔 저렇게 되고..." 식으로 자연스럽게 이어지게 써줘. 물리적이나 화학적 원리가 나오면 고등학생도 이해할 수 있게 쉬운 예시와 함께 설명해. 핵심 메커니즘은 강조해서 설명하되, 읽는 사람이 지루하지 않게 해줘.

    ---

    ## 🌍 **현재 과학적·사회적 배경**
    지금 이 분야에서 어떤 일들이 일어나고 있는지 생생하게 설명해줘. 최근 몇 년간 어떤 발전이 있었는지, 아직 해결되지 않은 문제들은 무엇인지 구체적으로 말해줘. 사회적으로 왜 관심을 받고 있는지, 우리 생활과 어떤 관련이 있는지도 자연스럽게 연결해서 설명해. 뉴스에서 들어봤을 법한 이야기들도 포함해줘.

    ---

    ## 💡 **응용 사례 & 활용 분야**
    실제로 어디에서, 어떻게 사용되고 있는지 구체적인 예시들을 들어서 설명해줘. 현재 상용화된 기술들과 미래에 가능할 것들을 자연스럽게 섞어서 이야기해. 어떤 회사들이 이 기술을 사용하는지, 일상생활에서 접할 수 있는 사례들은 무엇인지 친근하게 설명해. "여러분도 혹시 이런 걸 써봤을 거예요" 같은 식으로 친근하게 접근해줘.

    ---

    ## 📊 **최근 논문 연구 동향**
    이 분야의 최근 연구 동향을 2개 정도 소개해주되, 논문 제목만 나열하지 말고 "이 연구에서는 이런 걸 발견했어요"라고 쉽게 설명해줘. 각 연구의 의미와 왜 중요한지를 자연스럽게 풀어서 설명해. **중요: DOI나 링크는 100% 확실하게 존재하고 접근 가능한 것만 포함하고, 불확실하면 링크 없이 논문 제목과 설명만 제공해줘.** 더 자세한 정보는 "이런 키워드로 검색하면 더 많은 자료를 찾을 수 있어요"라고 안내해줘.

    ---

    ## 🎯 **확장 가능한 탐구 아이디어**
    
    고등학생이 실제로 연구해볼 수 있는 재미있는 아이디어들을 제시해줘:

    • **[구체적이고 매력적인 연구 아이디어 제목]**
    · 이 연구가 왜 흥미로운지, 어떤 방법으로 접근할 수 있는지 자연스럽게 설명해줘. 필요한 재료나 장비, 예상 기간도 현실적으로 제시하고, "이런 결과를 얻을 수 있을 거예요"라고 기대감을 주는 설명을 포함해.

    • **[두 번째 연구 아이디어]**  
    · 기존 연구와는 어떻게 다른 접근을 할 수 있는지, 어떤 새로운 발견을 할 수 있을지 구체적으로 설명해줘. 실생활 문제와 연결된다면 그 점도 강조해줘.

    • **[세 번째 연구 아이디어]**
    · 다른 분야와 융합할 수 있는 가능성이나 실용적 가치를 자연스럽게 설명해줘. 연구하는 과정에서 배울 수 있는 것들도 언급해줘.

    **이 내용들을 토대로 위 검색창에 재검색을 진행해 보세요.**

    ---

    **💡 작성 스타일:**
    - 친근하고 자연스러운 문체 사용 (딱딱한 목록식 금지)
    - 각 문단은 충분히 길고 자세하게 (3-5문장 이상)
    - 구체적인 예시와 비유를 적극 활용
    - 읽는 사람이 이해하기 쉽게 순서대로 설명
    - 전문 용어는 바로 쉬운 설명 제공
    """
    
    user_prompt = f"주제: {topic}"
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # 최신 Claude 모델
            max_tokens=4000,  # 풍부한 내용을 위한 충분한 토큰
            system=system_prompt,  # Claude는 system을 별도 파라미터로
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        full_text = response.content[0].text
        paragraphs = full_text.strip().split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
        
    except Exception as e:
        st.error(f"❌ Claude 설명 중 오류 발생: {e}")
        return ["AI 설명을 생성할 수 없습니다."]

# 직접 링크가 포함된 설명 생성 (앱에서 선택적 사용 가능)
def explain_topic_with_links(topic: str) -> str:
    """DOI 링크가 자동 변환된 주제 설명 생성"""
    explanation_lines = explain_topic(topic)
    explanation_text = "\n\n".join(explanation_lines)
    return convert_doi_to_links(explanation_text)
