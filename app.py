# app.py 수정본 (정보 설명을 사이드바로 이동 + DB 초기화 추가 + 틈새주제 선택 및 논문 생성 기능 추가)
import streamlit as st
import time
import re
from openai import OpenAI
from utils.layout import load_css
from utils.search_db import search_similar_titles, initialize_db
from utils.search_arxiv import search_arxiv
from utils.explain_topic import explain_topic
from utils.pdf_generator import generate_pdf

# 앱 시작 시 DB 초기화 (성능 최적화)
initialize_db()

# 틈새주제 파싱 함수
def parse_niche_topics(explanation_text):
    """explain_topic 결과에서 확장 가능한 탐구 아이디어 섹션을 파싱"""
    try:
        # "확장 가능한 탐구 아이디어" 섹션 찾기
        sections = explanation_text.split('\n\n')
        niche_section = ""
        
        for section in sections:
            if "확장 가능한 탐구 아이디어" in section or "탐구 아이디어" in section:
                niche_section = section
                break
        
        if not niche_section:
            return []
        
        # 개별 아이디어 추출 (• 또는 - 로 시작하는 라인)
        topics = []
        lines = niche_section.split('\n')
        
        current_topic = ""
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-'):
                if current_topic:
                    topics.append(current_topic.strip())
                current_topic = line[1:].strip()  # • 또는 - 제거
            elif current_topic and line.startswith('·'):
                # 설명 부분 추가
                current_topic += " " + line[1:].strip()
        
        # 마지막 주제 추가
        if current_topic:
            topics.append(current_topic.strip())
        
        # 최대 5개까지만 반환
        return topics[:5]
    
    except Exception as e:
        st.error(f"틈새주제 파싱 중 오류: {e}")
        return []

# 논문 형식 생성 함수
@st.cache_data(ttl=3600)
def generate_research_paper(selected_topics, original_topic):
    """선택된 틈새주제들을 기반으로 논문 형식 생성"""
    try:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])
        
        topics_text = "\n".join([f"- {topic}" for topic in selected_topics])
        
        system_prompt = f"""
        너는 고등학생을 위한 과학 논문 작성 전문가입니다. 
        주어진 원본 주제와 선택된 틈새주제들을 기반으로 체계적인 연구 논문을 작성해주세요.
        
        **중요한 지침:**
        1. 이 논문은 고등학생이 실제로 수행할 수 있는 연구여야 합니다
        2. 서론의 배경은 매우 상세하고 체계적으로 작성해주세요
        3. 실험방법은 누구든 따라할 수 있도록 구체적이고 단계별로 작성해주세요
        4. 모든 내용은 과학적으로 타당하고 현실적이어야 합니다
        5. 한국어로 작성해주세요
        
        **논문 구조:**
        
        # 제목
        [선택된 틈새주제들을 종합한 구체적이고 학술적인 제목]
        
        ## 초록
        [연구 목적, 방법, 기대 결과를 포함한 200-250자 요약]
        
        ## 1. 서론
        ### 1.1 연구 배경
        [원본 주제에 대한 상세한 배경 설명 - 최소 3-4개 문단]
        ### 1.2 문제 정의
        [현재 해결되지 않은 문제점들과 연구의 필요성]
        ### 1.3 연구 목적
        [이 연구가 달성하고자 하는 구체적인 목표들]
        ### 1.4 연구 가설
        [검증하고자 하는 가설들]
        
        ## 2. 실험 방법
        ### 2.1 실험 설계
        [전체적인 실험 설계와 접근 방법]
        ### 2.2 재료 및 장비
        [필요한 모든 재료와 장비의 구체적인 목록]
        ### 2.3 실험 절차
        [단계별로 따라할 수 있는 상세한 실험 과정 - 번호를 매겨서]
        ### 2.4 데이터 수집 및 분석 방법
        [어떤 데이터를 어떻게 수집하고 분석할 것인지]
        
        ## 3. 예상 결과
        ### 3.1 예상되는 실험 결과
        [가설에 따른 예상 결과들]
        ### 3.2 결과 해석 방법
        [결과를 어떻게 해석하고 분석할 것인지]
        
        ## 4. 결론
        ### 4.1 연구의 의의
        [이 연구가 갖는 학술적, 실용적 의의]
        ### 4.2 예상되는 한계점
        [연구의 한계와 개선 방향]
        ### 4.3 향후 연구 방향
        [이 연구를 발전시킬 수 있는 후속 연구 아이디어]
        
        **마지막에 다음 문구를 반드시 포함해주세요:**
        
        ---
        ⚠️ **중요 안내**
        - 이 내용은 AI가 추론하여 생성한 연구 계획안입니다
        - 실제 논문이 아니며, 참고용으로만 활용해주세요
        - 실제 연구 수행 시에는 지도교사와 상의하시기 바랍니다
        - 이 내용을 그대로 인용하거나 레퍼런스로 사용할 수 없습니다
        """
        
        user_prompt = f"""
        **원본 주제:** {original_topic}
        
        **선택된 틈새주제들:**
        {topics_text}
        
        위 정보를 바탕으로 고등학생이 수행할 수 있는 체계적인 연구 논문을 작성해주세요.
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        st.error(f"논문 생성 중 오류: {e}")
        return ""

# DOI 감지 및 링크 변환 함수
def convert_doi_to_links(text):
    """DOI 패턴을 감지하여 클릭 가능한 링크로 변환"""
    # DOI 패턴 정규 표현식: 10.XXXX/YYYY 형식
    doi_pattern = r'(?<!\w)(?:DOI\s*:\s*)?(\b10\.\d{4,}\/[a-zA-Z0-9./_()-]+\b)'
    
    # HTML 링크로 변환
    def replace_doi(match):
        doi = match.group(1)
        return f'<a href="https://doi.org/{doi}" target="_blank" style="color: #0969da; text-decoration: none;">{doi}</a>'
    
    # 텍스트 내 DOI 패턴을 링크로 변환
    linked_text = re.sub(doi_pattern, replace_doi, text)
    
    return linked_text

# 기본 설정
st.set_page_config(page_title="LittleScienceAI", layout="wide")
load_css()

# 중앙 정렬 CSS + 틈새주제 선택 UI 스타일
st.markdown("""
<style>
section.main > div.block-container {
    max-width: 800px !important; 
    margin: 0 auto !important;
    padding: 2rem 3rem !important;
    background-color: white !important;
}

.sidebar-info-box {
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 15px;
    border-left: 3px solid #4a86e8;
    font-size: 0.9em;
}

.sidebar-info-box h4 {
    margin-top: 0;
    color: #2c5aa0;
}

.sidebar-info-box.arxiv {
    border-left-color: #4caf50;
}

.sidebar-info-box.arxiv h4 {
    color: #2e7d32;
}

.niche-topic-card {
    background-color: #f8f9ff;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    transition: border-color 0.2s;
}

.niche-topic-card:hover {
    border-color: #3b82f6;
}

.niche-topic-card.selected {
    border-color: #3b82f6;
    background-color: #eff6ff;
}

.paper-section {
    background-color: #fafafa;
    border-left: 4px solid #2563eb;
    padding: 20px;
    margin: 20px 0;
    border-radius: 0 8px 8px 0;
}
</style>
""", unsafe_allow_html=True)

# 인증 시스템
ACCESS_KEYS = st.secrets["general"]["access_keys"]
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("## LittleScienceAI 로그인")
    user_key = st.text_input("🔑 인증 키를 입력하세요", type="password")
    
    if user_key in ACCESS_KEYS:
        st.session_state.authenticated = True
        st.rerun()
    elif user_key:
        st.warning("🚫 올바른 인증 키를 입력하세요.")
    st.stop()

# 세션 상태 초기화
if 'niche_topics' not in st.session_state:
    st.session_state.niche_topics = []
if 'selected_niche_topics' not in st.session_state:
    st.session_state.selected_niche_topics = []
if 'generated_paper' not in st.session_state:
    st.session_state.generated_paper = ""

# 사이드바
st.sidebar.title("🧭 탐색 단계")
st.sidebar.markdown("""
1. 주제 입력
2. 개념 해설 보기
3. 논문 추천 확인
4. 틈새주제 선택
5. 논문 형식 작성
6. PDF 저장
""")

# 사이드바에 학술 자료 설명 추가
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 학술 자료 정보")

# ISEF 설명 추가
st.sidebar.markdown("""
<div class="sidebar-info-box">
<h4>📊 ISEF</h4>
<p>
세계 최대 규모의 고등학생 과학 경진대회로, 80여 개국에서 1,800명 이상의 학생들이 참가하여 혁신적인 연구 프로젝트를 발표합니다. 1950년부터 시작된 이 대회는 과학, 기술, 공학, 수학(STEM) 분야의 차세대 인재를 발굴합니다.
</p>
</div>
""", unsafe_allow_html=True)

# arXiv 설명 추가
st.sidebar.markdown("""
<div class="sidebar-info-box arxiv">
<h4>📑 arXiv</h4>
<p>
물리학, 수학, 컴퓨터 과학 등의 분야에서 연구자들이 논문을 정식 출판 전에 공유하는 플랫폼입니다. 코넬 대학에서 운영하며, 최신 연구 동향을 빠르게 접할 수 있지만 일부는 아직 peer review를 거치지 않은 상태일 수 있습니다.
</p>
</div>
""", unsafe_allow_html=True)

# 메인 타이틀
st.title("🧪 과학논문 주제 탐색 도우미")

# 초기화
if 'full_text' not in st.session_state:
    st.session_state.full_text = ""

# 검색창
topic = st.text_input("🔬 연구하고 싶은 과학 주제를 입력하세요:", 
                     placeholder="예: 양자 컴퓨팅, 유전자 편집, 미생물 연료전지...")

# 주제가 입력된 경우
if topic:
    # 주제 해설 표시
    st.subheader("📘 주제 해설")
    
    # 즉시 해설 생성 및 표시 (DOI 링크 변환 추가)
    with st.spinner("🤖 AI가 주제 분석 중..."):
        try:
            explanation_lines = explain_topic(topic)
            explanation_text = "\n\n".join(explanation_lines)
            
            # 틈새주제 파싱 및 저장
            st.session_state.niche_topics = parse_niche_topics(explanation_text)
            
            # DOI 패턴을 링크로 변환 (화면 표시용)
            linked_explanation = convert_doi_to_links(explanation_text)
            
            # 링크가 포함된 설명 표시
            st.markdown(linked_explanation, unsafe_allow_html=True)
            
            # PDF용 텍스트는 원본 형식으로 저장 (마크다운 형식)
            st.session_state.full_text = f"# 📘 {topic} - 주제 해설\n\n{explanation_text}\n\n"
        except Exception as e:
            st.error(f"주제 해설 생성 중 오류: {str(e)}")
            st.session_state.full_text = f"# 📘 {topic} - 주제 해설\n\n생성 중 오류 발생\n\n"
    
    # 내부 DB 검색 결과 (정보 아이콘 제거)
    st.subheader("📄 ISEF (International Science and Engineering Fair) 출품논문")
    
    # 스피너 메시지 수정 (속도 개선 암시)
    with st.spinner("🔍 ISEF 관련 프로젝트를 빠르게 검색 중..."):
        try:
            internal_results = search_similar_titles(topic)
            
            if not internal_results:
                st.info("❗ 관련 프로젝트가 없습니다.")
                st.session_state.full_text += "## 📄 내부 DB 유사 논문\n\n❗ 관련 프로젝트가 없습니다.\n\n"
            else:
                st.session_state.full_text += "## 📄 내부 DB 유사 논문\n\n"
                
                for project in internal_results:
                    title = project.get('제목', '')
                    summary = project.get('요약', '')
                    
                    # 메타 정보
                    meta_parts = []
                    if project.get('연도'):
                        meta_parts.append(f"📅 {project['연도']}")
                    if project.get('분야'):
                        meta_parts.append(f"🔬 {project['분야']}")
                    if project.get('국가'):
                        loc = project['국가']
                        if project.get('지역'):
                            loc += f", {project['지역']}"
                        meta_parts.append(f"🌎 {loc}")
                    if project.get('수상'):
                        meta_parts.append(f"🏆 {project['수상']}")
                    
                    meta_text = " · ".join(meta_parts)
                    
                    # 내부 결과에서도 DOI 변환 적용
                    linked_summary = convert_doi_to_links(summary)
                    
                    # 카드 형태로 표시
                    st.markdown(f"""
                    <div style="background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin: 16px 0;">
                        <h3 style="color: #333; margin-top: 0;">📌 {title}</h3>
                        <p style="color: #666; font-style: italic; margin-bottom: 12px;">{meta_text}</p>
                        <p>{linked_summary}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.session_state.full_text += f"- **{title}**\n{summary}\n_{meta_text}_\n\n"
        except Exception as e:
            st.error(f"내부 DB 검색 중 오류: {str(e)}")
            st.session_state.full_text += "## 📄 내부 DB 유사 논문\n\n검색 중 오류 발생\n\n"
    
    # arXiv 결과 (정보 아이콘 제거)
    st.subheader("🌐 아카이브 arXiv 에서 찾은 관련 논문")
    
    with st.spinner("🔍 arXiv 논문 검색 중..."):
        try:
            arxiv_results = search_arxiv(topic)
            
            if not arxiv_results:
                st.info("❗ 관련 논문이 없습니다.")
                st.session_state.full_text += "## 🌐 arXiv 유사 논문\n\n❗ 관련 논문이 없습니다.\n\n"
            else:
                st.session_state.full_text += "## 🌐 arXiv 유사 논문\n\n"
                
                for paper in arxiv_results:
                    title = paper.get('title', '')
                    summary = paper.get('summary', '')
                    link = paper.get('link', '')
                    
                    # arXiv 결과에서도 DOI 변환 적용
                    linked_summary = convert_doi_to_links(summary)
                    
                    # 카드 형태로 표시 (프리프린트 표시 추가)
                    st.markdown(f"""
                    <div style="background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin: 16px 0;">
                        <h3 style="color: #333; margin-top: 0;">🌐 {title}</h3>
                        <p style="color: #666; font-style: italic; margin-bottom: 12px;">출처: arXiv (프리프린트 저장소)</p>
                        <p>{linked_summary}</p>
                        <a href="{link}" target="_blank" style="color: #0969da; text-decoration: none;">🔗 논문 링크 보기</a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.session_state.full_text += f"- **{title}**\n{summary}\n[링크]({link})\n\n"
        except Exception as e:
            st.error(f"arXiv 검색 중 오류: {str(e)}")
            st.session_state.full_text += "## 🌐 arXiv 유사 논문\n\n검색 중 오류 발생\n\n"
    
    # ========== 새로 추가된 틈새주제 선택 섹션 ==========
    if st.session_state.niche_topics:
        st.markdown("---")
        st.subheader("🔍 세부 틈새주제 선택")
        st.markdown("위 탐구 아이디어 중에서 **2-3개**를 선택하여 체계적인 논문 형식으로 작성해보세요.")
        
        # 틈새주제 선택 UI
        selected_topics = []
        
        for i, topic in enumerate(st.session_state.niche_topics):
            # 각 주제를 체크박스로 표시
            is_selected = st.checkbox(
                f"**주제 {i+1}:** {topic}",
                key=f"niche_topic_{i}",
                help="이 주제를 선택하여 논문에 포함합니다"
            )
            
            if is_selected:
                selected_topics.append(topic)
        
        # 선택된 주제 개수 확인
        if selected_topics:
            if len(selected_topics) < 2:
                st.warning("⚠️ 최소 2개의 주제를 선택해주세요.")
            elif len(selected_topics) > 3:
                st.warning("⚠️ 최대 3개의 주제만 선택할 수 있습니다.")
            else:
                st.success(f"✅ {len(selected_topics)}개 주제가 선택되었습니다.")
                
                # 논문 생성 버튼
                if st.button("📝 선택한 주제로 논문 형식 작성하기", type="primary"):
                    st.session_state.selected_niche_topics = selected_topics
                    
                    # 논문 생성
                    with st.spinner("🤖 AI가 체계적인 논문을 작성 중입니다..."):
                        st.session_state.generated_paper = generate_research_paper(
                            selected_topics, topic
                        )
                    
                    if st.session_state.generated_paper:
                        st.rerun()
    
    # ========== 논문 형식 표시 섹션 ==========
    if st.session_state.generated_paper:
        st.markdown("---")
        st.markdown('<div class="paper-section">', unsafe_allow_html=True)
        st.subheader("📄 생성된 연구 논문")
        st.markdown("선택한 틈새주제들을 바탕으로 체계적인 논문 형식을 생성했습니다.")
        
        # 생성된 논문 표시
        st.markdown(st.session_state.generated_paper)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # PDF용 텍스트에 논문 내용 추가
        st.session_state.full_text += f"\n\n## 📄 생성된 연구 논문\n\n{st.session_state.generated_paper}\n\n"
        
        # 다시 선택 버튼
        if st.button("🔄 다른 주제로 다시 작성하기"):
            st.session_state.generated_paper = ""
            st.session_state.selected_niche_topics = []
            st.rerun()
    
    # ========== PDF 저장 버튼 (기존 위치 유지) ==========
    if st.session_state.full_text:
        st.markdown("---")
        if st.button("📥 이 내용 PDF로 저장하기", type="secondary"):
            path = generate_pdf(st.session_state.full_text)
            with open(path, "rb") as f:
                st.download_button(
                    "📄 PDF 다운로드", 
                    f, 
                    file_name="little_science_ai.pdf",
                    mime="application/pdf"
                )
