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
        연구 계획서를 JSON 형식으로 작성해주세요.

        반드시 이 JSON 형식만 사용:
        {"abstract": "초록내용", "introduction": "서론내용", "methods": "방법내용", "results": "결과내용", "visuals": "시각자료내용", "conclusion": "결론내용", "references": "검색가이드"}

        각 섹션 요구사항:
        - abstract: 연구목적과 예상결과 요약 (150-225단어) - 학술논문 형식
        - introduction: 배경→문제→목적 순서 (300-375단어) - 학술논문 형식
        - methods: 실험단계를 명확히 구분해서 구체적으로 상세하게 작성 (375-450단어)
        - results: 예상되는 구체적 결과들 (150-200단어)
        - visuals: 필요한 그래프/차트 설명 (100-150단어)
        - conclusion: 실험을 통해 증명하려는 과학적 결론과 학술적 의의 (100-150단어)
        - references: "참고문헌은 자동으로 검색 가이드가 제공됩니다" (간단히 한 문장만)

        실험방법 작성법:
        1단계: [제목] - (장비/재료 간단히)
        2단계: [제목] - "먼저 ~를 준비합니다. 다음으로 ~를 설정합니다" 형태로 친절하게 구체적으로 서술
        3단계: [제목] - "그 후에 ~를 진행합니다. 이때 주의할 점은 ~입니다" 형태로 친절하게 구체적으로 서술  
        4단계: [제목] - "마지막으로 ~를 측정합니다. ~를 기록합니다" 형태로 친절하게 구체적으로 서술
        5단계: [제목] - 추가적인 실험 단계나 검증 과정을 상세히 서술
        """
        
        user_prompt = f"""
        주제: {topic}
        아이디어: {research_idea}

        위 내용으로 학술 연구계획서를 JSON으로 작성해주세요.
        
        주의사항:
        - 초록과 서론: 학술논문 형식으로 작성
        - 실험방법: 필요한 재료/물품 목록을 포함하고 "먼저 ~를 합니다. 다음으로 ~를 설정합니다" 친절한 구체적인 서술형으로 상세하게
        - 예상결과: "실험을 통해 다음과 같은 결과를 확인하였다... 그림 1에서 보면... 그림 2에서는... 표 1에 정리된 데이터를 보면..." 형태로 실제 결과 분석처럼 작성
        - 시각자료: 구체적인 그림 번호(그림1, 그림2)와 표 번호(표1, 표2)를 명시하여 제안
        - 참고문헌: 간단한 한 문장만 작성
        """
        
        # Claude 호출
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4500,  # 토큰 수 증가 (더 긴 내용 생성을 위해)
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
        'abstract': "본 연구는 제시된 주제에 대해 체계적인 실험적 접근을 통해 과학적 근거를 확보하고자 한다. 연구의 목적은 이론적 가설을 실험적으로 검증하고, 기존 연구의 한계점을 보완하여 새로운 관점을 제시하는 것이다. 실험을 통해 얻은 데이터를 정량적으로 분석하여 통계적으로 유의미한 결론을 도출할 예정이며, 이를 통해 해당 분야의 과학적 이해를 심화시키고자 한다. 본 연구 결과는 관련 분야의 이론적 토대를 강화하고 후속 연구의 방향성을 제시하는 데 중요한 기여를 할 것으로 기대된다. 또한 실용적 응용 가능성을 탐구하여 사회적 가치 창출에도 기여할 수 있을 것으로 예상된다.",
        
        'introduction': "현재 관련 분야에서는 다양한 연구가 활발히 진행되고 있지만, 여전히 해결되지 않은 핵심적인 문제들이 존재한다. 기존 연구들을 종합적으로 분석한 결과, 몇 가지 중요한 한계점들이 확인되었다. 첫째, 실험 조건의 표준화가 부족하여 연구 결과들 간의 일관성이 떨어지는 문제가 있다. 둘째, 장기적인 영향에 대한 체계적인 분석이 부족하여 현상의 전체적인 이해가 제한적이다. 셋째, 다양한 변수들 간의 상호작용에 대한 깊이 있는 연구가 필요한 상황이다. 이러한 문제점들을 해결하기 위해서는 보다 정밀한 실험 설계와 체계적인 접근이 필요하다. 따라서 본 연구에서는 기존 연구들의 한계점을 보완하고 새로운 실험적 방법론을 도입하여 더욱 정확하고 신뢰할 수 있는 결과를 얻고자 한다. 본 연구의 궁극적인 목적은 실험적 접근을 통해 이론적 가설을 엄밀하게 검증하고, 해당 분야의 과학적 지식을 한 단계 발전시키는 것이다.",
        
        'methods': "1단계: 실험 재료 및 장비 준비 (필요 물품: 정밀저울, 온도계, pH미터, 스탠드, 비커, 피펫, 시약)\n본 실험에서는 정밀한 측정을 위해 고정밀 장비와 표준화된 재료들을 사용한다. 먼저 실험에 필요한 모든 재료들의 순도와 품질을 확인하고, 각 재료의 특성을 사전에 분석한다. 실험 장비는 사용 전에 교정(calibration)을 실시하여 측정 오차를 최소화한다.\n\n2단계: 실험 환경 조성 및 초기 설정\n먼저 실험실의 온도를 25±2℃, 습도를 50±5%로 일정하게 유지하여 외부 변수의 영향을 최소화합니다. 다음으로 실험 장비를 진동이 없는 안정적인 실험대에 배치하고 외부 간섭을 차단할 수 있는 환경을 조성합니다. 실험 과정에서 발생할 수 있는 오차 요인들을 사전에 파악하고 이를 제어하기 위한 장치들을 설치합니다.\n\n3단계: 예비 실험 및 조건 최적화\n그 후에 본 실험에 앞서 예비 실험을 3회 진행하여 최적의 실험 조건을 찾습니다. 이때 주의할 점은 각 변수들이 결과에 미치는 영향을 개별적으로 분석하는 것입니다. 예비 실험 결과를 바탕으로 실험 매개변수들을 조정하고, 재현성 있는 결과를 얻을 수 있는 조건을 확립합니다.\n\n4단계: 본 실험 진행 및 데이터 수집\n마지막으로 확립된 조건 하에서 본 실험을 체계적으로 진행합니다. 각 실험 단계마다 정확한 시간을 기록하고 모든 측정값을 엑셀 시트에 실시간으로 저장합니다. 통계적 유의성을 확보하기 위해 최소 10회의 반복 실험을 수행하며, 각 반복 실험마다 동일한 조건을 유지하도록 세심하게 관리합니다.",
        
        'results': "실험을 통해 다음과 같은 결과를 확인하였다. 첫째, 측정된 주요 변수들 간에 강한 양의 상관관계(r=0.87, p<0.001)가 관찰되었으며, 이는 이론적 예측과 일치하는 결과로 사료된다. 그림 1에서 보면 시간에 따른 변화량이 지수함수적으로 증가하는 패턴을 보여주는데, 이는 초기 반응 단계에서의 촉매 효과에 의한 것으로 판단된다. 특히 실험 초기 30분 동안 급격한 변화를 보이다가 이후 안정화되는 경향을 확인할 수 있었다. 그림 2에서는 온도 변화에 따른 반응 속도의 변화를 나타내는데, 25℃에서 최적의 조건을 보였으며 이는 앞서 언급한 촉매 활성도와 밀접한 관련이 있는 것으로 보인다. 표 1에 정리된 데이터를 분석한 결과, 실험군과 대조군 간에 통계적으로 유의미한 차이(p<0.05)를 확인할 수 있었다. 실제로 그림 3에서는 이러한 결과를 더욱 명확하게 보여주었으며, 농도 증가에 따른 선형적 관계(R²=0.94)를 확인할 수 있었다. 이는 이론적 모델과 높은 일치성을 보여주는 결과로, 가설이 실험적으로 검증되었음을 의미한다.",
        
        'visuals': "실험 결과를 효과적으로 표현하기 위해 다음과 같은 시각자료를 제작할 예정입니다. **그림 1: 시간에 따른 변화량 그래프** - X축은 시간(분), Y축은 측정값으로 하여 실험 진행 과정에서의 변화 패턴을 선 그래프로 나타냅니다. **그림 2: 온도별 반응 속도 비교 차트** - 다양한 온도 조건(15℃, 20℃, 25℃, 30℃, 35℃)에서의 반응 속도를 막대그래프로 비교 분석합니다. **그림 3: 농도-반응성 상관관계 산점도** - 농도 변화에 따른 반응성의 변화를 산점도로 나타내고 추세선을 추가하여 상관관계를 명확히 보여줍니다. **표 1: 실험군과 대조군 비교 데이터** - 각 조건별 평균값, 표준편차, p-value를 정리한 비교표를 작성합니다. **표 2: 통계 분석 결과 요약** - 상관계수, 회귀분석 결과, 신뢰구간 등 주요 통계값들을 체계적으로 정리합니다. 이러한 시각자료들은 실험 결과의 이해를 돕고 연구의 신뢰성을 높이는 데 중요한 역할을 할 것입니다.",
        
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
