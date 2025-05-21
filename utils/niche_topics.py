import streamlit as st
from openai import OpenAI
import re

@st.cache_data(show_spinner="🧠 틈새주제 분석 중...", ttl=3600)
def generate_niche_topics(paper_title, paper_abstract=None, field=None):
    """선택된 논문을 기반으로 틈새주제를 생성"""
    try:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])
        
        # 논문 초록이 있으면 함께 사용, 없으면 제목만 사용
        context = f"제목: {paper_title}"
        if paper_abstract:
            context += f"\n\n초록 또는 요약: {paper_abstract}"
        if field:
            context += f"\n\n연구 분야: {field}"
        
        system_prompt = """
        너는 고등학생 과학 연구 주제 개발 전문가입니다. 주어진 논문 정보를 바탕으로, 고등학생이 연구할 수 있는 확장 가능한 틈새주제를 제안해주세요.
        
        주어진 논문 정보를 바탕으로, 다음과 같은 틈새주제를 정확히 5개 제안해주세요:
        1. 기존 연구의 한계점을 개선할 수 있는 주제
        2. 다른 분야와 융합할 수 있는 주제
        3. 실용적인 응용이 가능한 주제
        4. 고등학생 수준에서 실험/연구 가능한 주제
        5. 사회적 영향력이 큰 주제
        
        각 틈새주제는 다음 구조로 제시해야 합니다:
        
        ```
        - 주제: [구체적인 연구 주제 제목]
          설명: [이 주제가 왜 중요하고 어떻게 접근할 수 있는지 설명]
          난이도: [초급/중급/고급]
          핵심어: [3-5개의 관련 키워드를 쉼표로 구분]
        ```
        
        모든 응답은 한국어로 작성해주세요. 각 주제는 충분히 구체적이어야 하며, 실제 고등학생이 연구할 수 있도록 범위가 적절해야 합니다.
        주제들은 서로 다른 방향성을 가져야 합니다. 즉, 다양한 각도에서 원래 주제를 확장할 수 있어야 합니다.
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            temperature=0.8
        )
        
        # 응답 파싱 및 구조화
        content = response.choices[0].message.content.strip()
        
        # 주제 분리 및 포맷팅
        topics = []
        
        # 정규식으로 각 주제 추출
        pattern = r'- 주제: (.*?)(?=\n- 주제:|$)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            lines = match.strip().split('\n')
            topic_data = {"title": "", "description": "", "difficulty": "중급", "keywords": []}
            
            # 첫 줄은 항상 주제
            topic_data["title"] = lines[0].strip()
            
            # 나머지 줄 처리
            for line in lines[1:]:
                line = line.strip()
                if line.startswith("설명:"):
                    topic_data["description"] = line[3:].strip()
                elif line.startswith("난이도:"):
                    topic_data["difficulty"] = line[4:].strip()
                elif line.startswith("핵심어:"):
                    keywords = line[4:].strip()
                    topic_data["keywords"] = [k.strip() for k in keywords.split(',')]
            
            topics.append(topic_data)
        
        # 주제가 5개 미만이면 자동으로 채움
        while len(topics) < 5:
            idx = len(topics) + 1
            topics.append({
                "title": f"틈새주제 {idx}",
                "description": "AI가 이 주제를 생성하지 못했습니다. 다른 주제를 선택해주세요.",
                "difficulty": "중급",
                "keywords": ["기타"]
            })
            
        return topics
    
    except Exception as e:
        st.error(f"❌ 틈새주제 생성 중 오류 발생: {e}")
        return []
        
# 카드 UI로 틈새주제 표시
def display_niche_topics(topics):
    """틈새주제를 세련된 카드 UI로 표시"""
    if not topics:
        st.warning("🤔 틈새주제를 생성할 수 없습니다.")
        return None
    
    st.markdown("## 🔍 연구 가능한 틈새주제")
    st.markdown("아래 주제 중 하나를 선택하여 논문 형식으로 확장해보세요.")
    
    # 카드 스타일 정의
    st.markdown("""
    <style>
    .niche-card {
        background-color: white;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        padding: 16px;
        margin: 10px 0;
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
        cursor: pointer;
    }
    .niche-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    .niche-title {
        font-size: 18px;
        font-weight: 600;
        color: #1565C0;
        margin-bottom: 8px;
    }
    .niche-description {
        font-size: 14px;
        color: #333;
        margin-bottom: 12px;
    }
    .niche-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 10px;
    }
    .niche-difficulty {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 12px;
        font-weight: 500;
    }
    .niche-keywords {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    .niche-keyword {
        background-color: #f1f3f4;
        color: #444;
        border-radius: 12px;
        padding: 3px 10px;
        font-size: 12px;
    }
    .difficulty-beginner {
        background-color: #e8f5e9;
        color: #2e7d32;
    }
    .difficulty-intermediate {
        background-color: #fff8e1;
        color: #f57f17;
    }
    .difficulty-advanced {
        background-color: #ffebee;
        color: #c62828;
    }
    .selected-card {
        border: 2px solid #1565C0;
        background-color: #f0f7ff;
    }
    .niche-select-btn {
        position: absolute;
        right: 16px;
        bottom: 16px;
        background-color: #1565C0;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px 12px;
        font-size: 13px;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .niche-select-btn:hover {
        background-color: #0d47a1;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 난이도 클래스 매핑
    difficulty_classes = {
        "초급": "difficulty-beginner",
        "중급": "difficulty-intermediate",
        "고급": "difficulty-advanced"
    }
    
    # 선택 상태 초기화
    if 'selected_topic_index' not in st.session_state:
        st.session_state.selected_topic_index = None
    
    # 2열 그리드로 주제 표시
    col1, col2 = st.columns(2)
    
    selected_topic = None
    
    for i, topic in enumerate(topics):
        # 짝수 인덱스는 왼쪽, 홀수 인덱스는 오른쪽 열에 배치
        col = col1 if i % 2 == 0 else col2
        
        with col:
            # 현재 주제가 선택되었는지 확인
            is_selected = st.session_state.selected_topic_index == i
            selected_class = "selected-card" if is_selected else ""
            
            difficulty = topic.get("difficulty", "중급")
            diff_class = difficulty_classes.get(difficulty, "difficulty-intermediate")
            
            # 키워드 목록 생성
            keywords_html = ""
            for kw in topic.get("keywords", []):
                keywords_html += f'<span class="niche-keyword">{kw}</span>'
            
            # 카드 HTML 생성
            card_html = f"""
            <div class="niche-card {selected_class}" id="topic-{i}">
                <div class="niche-title">{topic.get('title', '제목 없음')}</div>
                <div class="niche-description">{topic.get('description', '설명 없음')}</div>
                <div class="niche-meta">
                    <span class="niche-difficulty {diff_class}">{difficulty}</span>
                </div>
                <div class="niche-keywords">{keywords_html}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            # 숨겨진 버튼으로 선택 상태 관리
            if st.button(f"이 주제 선택", key=f"btn_select_{i}", help="이 틈새주제로 논문 형식의 내용을 생성합니다"):
                st.session_state.selected_topic_index = i
                selected_topic = topic
                st.experimental_rerun()
    
    # 선택된 주제가 있으면 확인 메시지 표시
    if st.session_state.selected_topic_index is not None:
        selected_idx = st.session_state.selected_topic_index
        if 0 <= selected_idx < len(topics):
            st.success(f"✅ '{topics[selected_idx]['title']}' 주제를 선택했습니다!")
            
            # 계속 진행 버튼
            if st.button("📝 이 주제로 논문 형식 작성하기", 
                       key="btn_continue", 
                       help="선택한 틈새주제로 논문 형식의 글을 작성합니다",
                       type="primary"):
                return topics[selected_idx]
    
    return selected_topic
