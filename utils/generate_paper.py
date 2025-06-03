# utils/generate_paper.py
import streamlit as st
import anthropic
import json
import re

@st.cache_data(ttl=3600, show_spinner=False)
def generate_research_paper(topic, research_idea, references=""):
    """
    선택된 연구 아이디어에 대한 논문 형식의 연구 계획을 생성
    """
    try:
        client = anthropic.Anthropic(api_key=st.secrets["api"]["claude_key"])
        
        # 🔥 레퍼런스 요구사항 간소화
        system_prompt = """
        고등학생 연구 계획서를 JSON 형식으로 작성해주세요.

        반드시 이 JSON 형식만 사용:
        {"abstract": "초록내용", "introduction": "서론내용", "methods": "방법내용", "results": "결과내용", "visuals": "시각자료내용", "conclusion": "결론내용", "references": "검색가이드"}

        각 섹션 요구사항:
        - abstract: 연구목적과 예상결과 요약 (150-200단어) - 학술논문 형식
        - introduction: 배경→문제→목적 순서 (250-300단어) - 학술논문 형식
        - methods: 실험단계를 명확히 구분해서 구체적으로 상세하게 작성 (300-350단어)
        - results: 예상되는 구체적 결과들 (200-250단어)
        - visuals: 필요한 그래프/차트 설명 (150-200단어)
        - conclusion: 실험을 통해 증명하려는 과학적 결론과 학술적 의의 (150-200단어)
        - references: "참고문헌은 자동으로 검색 가이드가 제공됩니다" (간단히 한 문장만)

        실험방법 작성법:
        1단계: [제목] - (장비/재료 필요한 사항을 명시)
        2단계: [제목] - "먼저 ~를 준비합니다. 다음으로 ~를 설정합니다" 형태로 친절하게 구체적으로 서술
        3단계: [제목] - "그 후에 ~를 진행합니다. 이때 주의할 점은 ~입니다" 형태로 친절하게 구체적으로 서술  
        4단계: [제목] - "마지막으로 ~를 측정합니다. ~를 기록합니다" 형태로 친절하게 구체적으로 서술
        """
        
        user_prompt = f"""
        주제: {topic}
        아이디어: {research_idea}

        위 내용으로 학술 연구계획서를 JSON으로 작성해주세요.
        
        주의사항:
        - 초록과 서론: 학술논문 형식으로 작성
        - 실험방법: "먼저 ~를 합니다. 다음으로 ~를 설정합니다" 친절한 구체적인 서술형
        - 참고문헌: 간단한 한 문장만 작성
        """
        
        # Claude 호출
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3500,  # 참고문헌 고정으로 토큰 절약
            temperature=0.2,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        response_text = response.content[0].text.strip()
        print(f"=== Claude 응답 원본 ===")
        print(response_text[:300] + "...")
        
        # JSON 추출
        paper_data = extract_json_robust(response_text)
        
        # JSON 추출
        if paper_data:
            paper_data = validate_and_fix_sections(paper_data, topic)
        
        return paper_data if paper_data else create_error_response(topic)
        
    except Exception as e:
        print(f"❌ 전체 논문 생성 오류: {e}")
        return create_error_response(topic)

def extract_json_robust(text):
    """간소화된 JSON 추출"""
    try:
        # 방법 1: 직접 파싱
        try:
            return json.loads(text)
        except:
            pass
        
        # 방법 2: 코드블록 제거
        if "```json" in text:
            content = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            content = text.split("```")[1].strip()
        else:
            content = text
        
        try:
            return json.loads(content)
        except:
            pass
        
        # 방법 3: 수동 파싱
        return manual_parse_sections(text)
        
    except:
        return None

def manual_parse_sections(text):
    """수동으로 섹션 파싱"""
    try:
        sections = {
            "abstract": "",
            "introduction": "",
            "methods": "",
            "results": "",
            "visuals": "",
            "conclusion": "",
            "references": ""
        }
        
        keywords = {
            'abstract': ['초록', 'abstract', '요약'],
            'introduction': ['서론', 'introduction', '배경'],
            'methods': ['방법', 'method', '실험'],
            'results': ['결과', 'result', '예상'],
            'visuals': ['시각', 'visual', '그래프'],
            'conclusion': ['결론', 'conclusion'],
            'references': ['참고', 'reference', '문헌']
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 섹션 감지
            found_section = None
            for section, kws in keywords.items():
                if any(kw in line.lower() for kw in kws):
                    found_section = section
                    break
            
            if found_section:
                current_section = found_section
            elif current_section and not line.startswith('"'):
                if sections[current_section]:
                    sections[current_section] += " " + line
                else:
                    sections[current_section] = line
        
        return sections
        
    except:
        return None

def validate_and_fix_sections(paper_data, topic):
    """섹션별 검증 및 수정"""
    try:
        required_sections = ['abstract', 'introduction', 'methods', 'results', 'visuals', 'conclusion', 'references']
        
        for section in required_sections:
            if section == 'references':
                # references는 무조건 검색 가이드로 대체
                paper_data[section] = get_search_guide_template(topic)
            elif section not in paper_data or not paper_data[section] or len(paper_data[section].strip()) < 20:
                paper_data[section] = get_default_content(section, topic)
        
        return paper_data
        
    except:
        return paper_data

def get_search_guide_template(topic):
    """🔥 줄바꿈 정렬된 검색 가이드"""
    return f"""📚 추가 연구를 위한 검색 가이드

아래 링크에서 "{topic}" 관련 키워드를 검색하여 관련논문들을 읽어보세요:

**국내 학술 검색 사이트:**

네이버 학술정보: https://academic.naver.com/

RISS 학술연구정보: https://www.riss.kr/

DBpia 논문검색: https://www.dbpia.co.kr/

한국과학기술정보연구원: https://www.ndsl.kr/

**해외 학술 검색 사이트:**

구글 학술검색: https://scholar.google.com/

IEEE Xplore: https://ieeexplore.ieee.org/

PubMed: https://pubmed.ncbi.nlm.nih.gov/

💡 **검색 팁:** "{topic}"와 함께 "실험", "분석", "응용", "최신 연구" 등의 키워드를 조합해서 검색해보세요."""

def get_default_content(section, topic):
    """기본 내용 제공"""
    defaults = {
        'abstract': "본 연구는 제시된 주제에 대해 체계적인 실험을 통해 과학적 근거를 확보하고자 한다. 실험을 통해 얻은 데이터를 분석하여 의미있는 결론을 도출할 예정이다. 이 연구 결과는 관련 분야의 이해를 넓히는 데 기여할 것으로 기대된다.",
        'introduction': "현재 관련 분야에서는 다양한 연구가 진행되고 있지만, 여전히 해결되지 않은 문제들이 존재한다. 기존 연구들의 한계점을 보완하고 새로운 관점을 제시하기 위해 본 연구를 수행한다. 본 연구의 목적은 실험적 접근을 통해 이론적 가설을 검증하는 것이다.",
        'methods': "1단계: 실험 재료 준비\n필요한 실험 도구와 재료를 준비합니다.\n\n2단계: 실험 환경 설정\n먼저 실험실의 조명을 조절하여 적절한 환경을 만듭니다. 다음으로 실험 장비를 안정적인 곳에 배치합니다.\n\n3단계: 데이터 수집 진행\n그 후에 실험을 단계적으로 진행하며 각 단계마다 결과를 기록합니다.\n\n4단계: 결과 분석 및 정리\n마지막으로 수집된 데이터를 체계적으로 분석합니다. 그래프나 표로 정리하여 패턴을 찾아냅니다.",
        'results': "실험을 통해 다음과 같은 결과를 얻을 것으로 예상된다: 측정값들 간의 상관관계, 가설의 검증 결과, 그리고 이론적 모델과의 일치성 평가이다. 이러한 결과는 관련 분야의 이론적 토대를 강화하는 데 기여할 것이다.",
        'visuals': "실험 결과를 효과적으로 표현하기 위해 다음과 같은 시각자료를 제작할 예정입니다: 실험 과정을 보여주는 사진, 데이터 변화를 나타내는 그래프, 결과를 요약한 표 등입니다.",
        'conclusion': "본 연구를 통해 제시된 가설이 실험적으로 검증될 것으로 예상된다. 이는 관련 분야의 이론적 이해를 깊게 하고, 후속 연구의 방향성을 제시하는 중요한 의미를 갖는다.",
        'references': get_search_guide_template(topic)
    }
    return defaults.get(section, f"{section} 섹션 내용이 생성되지 않았습니다.")

def create_error_response(topic):
    """에러 발생 시 기본 응답"""
    return {
        "abstract": "논문 초록 생성 중 오류가 발생했습니다. 주제를 더 구체적으로 입력하고 다시 시도해주세요.",
        "introduction": "서론 생성 중 오류가 발생했습니다. 연구 배경을 다시 검토해주세요.",
        "methods": "연구 방법 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        "results": "예상 결과 생성 중 오류가 발생했습니다. 네트워크 상태를 확인해주세요.",
        "visuals": "시각자료 제안 생성 중 오류가 발생했습니다.",
        "conclusion": "결론 생성 중 오류가 발생했습니다.",
        "references": get_search_guide_template(topic)
    }
