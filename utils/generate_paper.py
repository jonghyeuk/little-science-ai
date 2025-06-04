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
        - results: 예상되는 구체적 결과들 그리고 뒷받침하는 검증된 이론내용 (250-300단어)
        - visuals: 필요한 그래프/차트 설명를 자세히 작성 (150-250단어)
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
        - 예상결과: "실험을 통해 다음과 같은 결과를 확인하였다... 그림 1에서 보면... 그림 2에서는... 표 1에 정리된 데이터를 보면..." 형태로 실제 결과 분석처럼 작성하고 내용을 추가설명 가능한 검증된 이론설명을들 함께 서술
        - 시각자료: 예상결과에서 언급한 그림/표와 정확히 매칭되도록 구체적인 그림 번호(그림1, 그림2)와 표 번호(표1, 표2), X축/Y축 정보, 스케일 정보를 명시하여 제안
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
    """오류 발생 시 재시도 안내 메시지 제공"""
    error_messages = {
        'abstract': "⚠️ **초록 생성에 실패했습니다**\n\n🔄 **해결 방법:**\n- 페이지를 새로고침하고 다시 시도해주세요\n- 브라우저 캐시를 삭제해보세요\n- 잠시 후 다시 시도해주세요\n- 인터넷 연결 상태를 확인해주세요\n\n💡 **계속 이런 결과가 나올 경우 다른 틈새주제를 선택해서 시도해보세요**",
        
        'introduction': "⚠️ **서론 생성에 실패했습니다**\n\n🔄 **해결 방법:**\n- 페이지를 새로고침하고 다시 시도해주세요\n- 몇 분 후 다시 시도해주세요\n- 브라우저 캐시를 지워보세요\n\n💡 **계속 이런 결과가 나올 경우 다른 틈새주제를 선택해서 시도해보세요**",
        
        'methods': "⚠️ **실험 방법 생성에 실패했습니다**\n\n🔄 **해결 방법:**\n- 브라우저를 새로고침해주세요\n- 몇 분 후 다시 시도해주세요\n- 네트워크 연결을 확인해주세요\n\n💡 **계속 이런 결과가 나올 경우 다른 틈새주제를 선택해서 시도해보세요**",
        
        'results': "⚠️ **예상 결과 생성에 실패했습니다**\n\n🔄 **해결 방법:**\n- 페이지를 새로고침해주세요\n- 네트워크 상태를 확인해주세요\n- 몇 분 후 다시 시도해주세요\n\n💡 **계속 이런 결과가 나올 경우 다른 틈새주제를 선택해서 시도해보세요**",
        
        'visuals': "⚠️ **시각자료 제안 생성에 실패했습니다**\n\n🔄 **해결 방법:**\n- 새로고침 후 재시도해주세요\n- 브라우저 캐시를 지워보세요\n\n💡 **계속 이런 결과가 나올 경우 다른 틈새주제를 선택해서 시도해보세요**",
        
        'conclusion': "⚠️ **결론 생성에 실패했습니다**\n\n🔄 **해결 방법:**\n- 새로고침 후 재시도해주세요\n- 인터넷 연결을 확인해주세요\n\n💡 **계속 이런 결과가 나올 경우 다른 틈새주제를 선택해서 시도해보세요**",
        
        'references': get_search_guide_template(topic)  # 이건 그대로 유지
    }
    return error_messages.get(section, f"⚠️ **{section} 생성 실패**\n\n🔄 새로고침 후 재시도하거나\n💡 다른 틈새주제를 선택해보세요")

def create_error_response(topic):
    """에러 발생 시 기본 응답 - 오류 메시지로 통일"""
    return {
        "abstract": "⚠️ **논문 초록 생성 중 오류가 발생했습니다**\n\n🔄 **해결 방법:**\n- 새로고침 후 다시 시도해주세요\n- 네트워크 상태를 확인해주세요\n\n💡 **계속 문제가 발생하면 다른 틈새주제를 선택해보세요**",
        
        "introduction": "⚠️ **서론 생성 중 오류가 발생했습니다**\n\n🔄 **해결 방법:**\n- 페이지를 새로고침해주세요\n- 몇 분 후 재시도해주세요\n\n💡 **계속 문제가 발생하면 다른 틈새주제를 선택해보세요**",
        
        "methods": "⚠️ **연구 방법 생성 중 오류가 발생했습니다**\n\n🔄 **해결 방법:**\n- 브라우저 새로고침 후 재시도해주세요\n- 인터넷 연결을 확인해주세요\n\n💡 **계속 문제가 발생하면 다른 틈새주제를 선택해보세요**",
        
        "results": "⚠️ **예상 결과 생성 중 오류가 발생했습니다**\n\n🔄 **해결 방법:**\n- 네트워크 상태를 확인해주세요\n- 새로고침 후 재시도해주세요\n\n💡 **계속 문제가 발생하면 다른 틈새주제를 선택해보세요**",
        
        "visuals": "⚠️ **시각자료 제안 생성 중 오류가 발생했습니다**\n\n🔄 **해결 방법:**\n- 페이지 새로고침 후 재시도해주세요\n\n💡 **계속 문제가 발생하면 다른 틈새주제를 선택해보세요**",
        
        "conclusion": "⚠️ **결론 생성 중 오류가 발생했습니다**\n\n🔄 **해결 방법:**\n- 새로고침 후 재시도해주세요\n\n💡 **계속 문제가 발생하면 다른 틈새주제를 선택해보세요**",
        
        "references": get_search_guide_template(topic)
    }
