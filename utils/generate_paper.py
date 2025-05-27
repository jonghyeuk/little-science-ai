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
        
        # 🔥 간단하고 명확한 시스템 프롬프트로 수정
        system_prompt = """
        고등학생 연구 계획서를 JSON 형식으로 작성해주세요.

        반드시 이 JSON 형식만 사용:
        {"abstract": "초록내용", "introduction": "서론내용", "methods": "방법내용", "results": "결과내용", "visuals": "시각자료내용", "conclusion": "결론내용", "references": "참고문헌내용"}

        각 섹션 요구사항:
        - abstract: 연구목적과 예상결과 요약 (100-150단어) - 학술논문 형식, 교육 대상 언급 금지
        - introduction: 배경→문제→목적 순서 (200-250단어) - 학술논문 형식, 교육 대상 언급 금지
        - methods: 실험단계를 명확히 구분해서 작성 (250-300단어)
        - results: 예상되는 구체적 결과들 (150-200단어)
        - visuals: 필요한 그래프/차트 설명 (100-150단어)
        - conclusion: 실험을 통해 증명하려는 과학적 결론과 학술적 의의 (100-150단어)
        - references: 실제 확인가능한 자료 3-4개 (반드시 실제 링크 포함)

        실험방법 작성법:
        1단계: [제목] - (장비/재료 간단히)
        2단계: [제목] - "먼저 ~를 준비합니다. 다음으로 ~를 설정합니다" 형태로 친절하게 서술
        3단계: [제목] - "그 후에 ~를 진행합니다. 이때 주의할 점은 ~입니다" 형태로 친절하게 서술  
        4단계: [제목] - "마지막으로 ~를 측정합니다. ~를 기록합니다" 형태로 친절하게 서술
        (각 단계마다 고등학생이 따라할 수 있도록 구체적이고 친절한 서술형으로)

        참고문헌 작성법:
        1. 자료제목
        - 내용: 핵심내용 2문장 설명  
        - 링크: 다음 중 하나만 사용
          * https://ieeexplore.ieee.org (공학/전자 관련)
          * https://www.nature.com/subjects (자연과학 관련)  
          * https://www.nist.gov (측정/표준 관련)
          * https://energy.mit.edu (에너지 관련)
          * https://www.nsf.gov/discoveries (일반 과학)
        - 활용: 연구에 어떻게 도움되는지
        
        중요: Google Scholar 검색 링크 절대 사용 금지! 위 실제 기관 사이트만 사용하세요.
        """
        
        # 🔥 간단한 사용자 프롬프트
        user_prompt = f"""
        주제: {topic}
        아이디어: {research_idea}

        위 내용으로 학술 연구계획서를 JSON으로 작성해주세요.
        
        주의사항:
        - 초록과 서론: 학술논문 형식으로, "고등학생" 등 교육 대상 언급 금지
        - 결론: 실험을 통해 증명하려는 과학적 결론과 학술적 의의 중심
        - 실험방법: "먼저 ~를 합니다. 다음으로 ~를 설정합니다" 친절한 서술형
        - 참고문헌: 반드시 실제 클릭 가능한 링크 포함
        """
        
        # Claude 호출
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2500,  # 토큰 줄여서 더 집중된 응답
            temperature=0.2,  # 더 일관된 응답
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        response_text = response.content[0].text.strip()
        print(f"=== Claude 응답 원본 ===")
        print(response_text[:300] + "...")
        
        # 🔥 더 강력한 JSON 추출
        paper_data = extract_json_robust(response_text)
        
        # 🔥 섹션별 검증 및 수정
        if paper_data:
            paper_data = validate_and_fix_sections(paper_data)
        
        return paper_data if paper_data else create_error_response()
        
    except Exception as e:
        print(f"❌ 전체 논문 생성 오류: {e}")
        return create_error_response()

def extract_json_robust(text):
    """더 강력한 JSON 추출"""
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
        
        # 방법 3: 정규식으로 JSON 찾기
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict) and 'abstract' in data:
                    return data
            except:
                continue
        
        # 방법 4: 수동 파싱
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
        
        # 더 유연한 키워드 검색
        keywords = {
            'abstract': ['초록', 'abstract', '요약'],
            'introduction': ['서론', 'introduction', '배경', '도입'],
            'methods': ['방법', 'method', '실험', '절차'],
            'results': ['결과', 'result', '예상'],
            'visuals': ['시각', 'visual', '그래프', '차트'],
            'conclusion': ['결론', 'conclusion', '결과'],
            'references': ['참고', 'reference', '문헌']
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('{') or line.startswith('}'):
                continue
            
            # 섹션 감지
            found_section = None
            for section, kws in keywords.items():
                if any(kw in line.lower() for kw in kws):
                    found_section = section
                    break
            
            if found_section:
                current_section = found_section
            elif current_section and not line.startswith('"') and not line.startswith(','):
                # 내용 추가
                if sections[current_section]:
                    sections[current_section] += " " + line
                else:
                    sections[current_section] = line
        
        # 빈 섹션 처리
        for key, value in sections.items():
            if not value.strip():
                sections[key] = get_default_content(key)
        
        return sections
        
    except:
        return None

def validate_and_fix_sections(paper_data):
    """섹션별 검증 및 수정"""
    try:
        required_sections = ['abstract', 'introduction', 'methods', 'results', 'visuals', 'conclusion', 'references']
        
        for section in required_sections:
            if section not in paper_data or not paper_data[section] or len(paper_data[section].strip()) < 20:
                paper_data[section] = get_default_content(section)
        
        # methods 섹션 특별 처리 (너무 길면 단축)
        if len(paper_data['methods']) > 1000:
            methods_text = paper_data['methods'][:800] + "...\n\n데이터 수집 및 분석: 실험 결과를 체계적으로 기록하고 통계적으로 분석합니다."
            paper_data['methods'] = methods_text
        
        # references 섹션 정리
        if paper_data['references']:
            paper_data['references'] = clean_references(paper_data['references'])
        
        return paper_data
        
    except:
        return paper_data

def get_default_content(section):
    """기본 내용 제공"""
    defaults = {
        'abstract': "본 연구는 제시된 주제에 대해 체계적인 실험을 통해 과학적 근거를 확보하고자 한다. 실험을 통해 얻은 데이터를 분석하여 의미있는 결론을 도출할 예정이다. 이 연구 결과는 관련 분야의 이해를 넓히는 데 기여할 것으로 기대된다.",
        'introduction': "현재 관련 분야에서는 다양한 연구가 진행되고 있지만, 여전히 해결되지 않은 문제들이 존재한다. 기존 연구들의 한계점을 보완하고 새로운 관점을 제시하기 위해 본 연구를 수행한다. 본 연구의 목적은 실험적 접근을 통해 이론적 가설을 검증하는 것이다.",
        'methods': "1단계: 실험 재료 준비\n필요한 실험 도구와 재료를 준비합니다.\n\n2단계: 실험 환경 설정\n먼저 실험실의 조명을 조절하여 적절한 환경을 만듭니다. 다음으로 실험 장비를 안정적인 곳에 배치합니다. 이때 주의할 점은 장비가 흔들리지 않도록 고정하는 것입니다.\n\n3단계: 데이터 수집 진행\n그 후에 실험을 단계적으로 진행하며 각 단계마다 결과를 기록합니다. 측정값이 정확한지 확인하면서 진행합니다. 실험 중에는 외부 요인이 영향을 주지 않도록 주의합니다.\n\n4단계: 결과 분석 및 정리\n마지막으로 수집된 데이터를 체계적으로 분석합니다. 그래프나 표로 정리하여 패턴을 찾아냅니다. 예상 결과와 비교하여 의미있는 결론을 도출합니다.",
        'results': "실험을 통해 다음과 같은 결과를 얻을 것으로 예상된다: 측정값들 간의 상관관계, 가설의 검증 결과, 그리고 이론적 모델과의 일치성 평가이다. 이러한 결과는 관련 분야의 이론적 토대를 강화하는 데 기여할 것이다.",
        'visuals': "실험 결과를 효과적으로 표현하기 위해 다음과 같은 시각자료를 제작할 예정입니다: 실험 과정을 보여주는 사진, 데이터 변화를 나타내는 그래프, 결과를 요약한 표 등입니다.",
        'conclusion': "본 연구를 통해 제시된 가설이 실험적으로 검증될 것으로 예상된다. 이는 관련 분야의 이론적 이해를 깊게 하고, 후속 연구의 방향성을 제시하는 중요한 의미를 갖는다. 또한 본 연구에서 개발된 실험 방법론은 유사 연구에 활용될 수 있을 것이다.",
        'references': "1. 관련 주제 연구 동향\n- 내용: 해당 분야의 최신 연구 동향과 주요 발견사항을 정리한 자료입니다. 국내외 연구 현황을 파악할 수 있습니다.\n- 링크: https://scholar.google.com/scholar?q=related+research+trends+2024\n- 활용: 연구 배경 이해와 방향 설정에 도움이 됩니다.\n\n2. 실험 방법론 가이드\n- 내용: 과학적 실험 설계와 데이터 분석 방법에 대한 종합적 안내서입니다.\n- 링크: https://www.physics.org/experimental-methods\n- 활용: 체계적인 실험 진행을 위한 참고자료로 활용합니다.\n\n3. 정부 연구 보고서\n- 내용: 관련 분야에 대한 정부 차원의 연구 및 정책 자료입니다.\n- 링크: https://www.ndsl.kr\n- 활용: 국가적 관점에서의 연구 방향성 파악에 도움이 됩니다."
    }
    return defaults.get(section, f"{section} 섹션 내용이 생성되지 않았습니다.")

def clean_references(ref_text):
    """참고문헌 정리 - 한국+영문 DB 사이트로 교체 (한국 4개, 영문 3개)"""
    try:
        cleaned = ref_text
        
        # 🔥 모든 링크를 실제 DB 사이트로 교체
        import re
        
        # 모든 링크 패턴 찾기 (scholar, sciencedirect 등)
        all_links = re.findall(r'https://[^\s]*', cleaned)
        
        # 교체용 링크 (한국 4개 + 영문 3개)
        replacement_links = [
            'https://www.dbpia.co.kr/search/topSearch?searchName=',  # 한국 1
            'https://www.riss.kr/search/Search.do?queryText=',       # 한국 2  
            'https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci', # 한국 3
            'https://www.ndsl.kr/ndsl/search/detail/trend/trendSearchResultDetail.do', # 한국 4
            'https://www.sciencedirect.com/search?qs=',             # 영문 1
            'https://ieeexplore.ieee.org/search/searchresult.jsp?queryText=', # 영문 2
            'https://pubmed.ncbi.nlm.nih.gov/?term='               # 영문 3
        ]
        
        # 발견된 링크를 순서대로 교체
        for i, old_link in enumerate(all_links):
            if i < len(replacement_links):
                replacement_link = replacement_links[i]
                cleaned = cleaned.replace(old_link, replacement_link, 1)
            else:
                # 7개 초과 시 순환
                replacement_link = replacement_links[i % len(replacement_links)]
                cleaned = cleaned.replace(old_link, replacement_link, 1)
        
        return cleaned.strip()
    except:
        return ref_text

def parse_text_response(text):
    """JSON 파싱 실패 시 텍스트에서 섹션별로 추출"""
    return manual_parse_sections(text)

def create_error_response():
    """에러 발생 시 기본 응답"""
    return {
        "abstract": "논문 초록 생성 중 오류가 발생했습니다. 주제를 더 구체적으로 입력하고 다시 시도해주세요.",
        "introduction": "서론 생성 중 오류가 발생했습니다. 연구 배경을 다시 검토해주세요.",
        "methods": "연구 방법 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        "results": "예상 결과 생성 중 오류가 발생했습니다. 네트워크 상태를 확인해주세요.",
        "visuals": "시각자료 제안 생성 중 오류가 발생했습니다.",
        "conclusion": "결론 생성 중 오류가 발생했습니다.",
        "references": "참고문헌 생성 중 오류가 발생했습니다."
    }
