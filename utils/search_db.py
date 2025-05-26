import pandas as pd
import os
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.explain_topic import explain_topic
import anthropic  # OpenAI 대신 anthropic 사용
import re

# 📁 내부 DB 경로
DB_PATH = os.path.join("data", "ISEF Final DB.xlsx")

# 🔤 ISEF DB 열 매핑
COLUMN_MAP = {
    'Project Title': '제목',
    'Year': '연도',
    'Category': '분야',
    'Fair Country': '국가',
    'Fair State': '지역',
    'Awards': '수상'
}

# 전역 변수 - 사전 처리된 데이터 저장
_DB_INITIALIZED = False
_PROCESSED_DB = None
_VECTORIZER = None
_TFIDF_MATRIX = None

# 초기화 함수 - 앱 시작 시 한 번만 실행
@st.cache_data(ttl=86400, show_spinner=False)  # 캐시 24시간 유지
def initialize_db():
    """데이터베이스와 벡터라이저 초기화"""
    global _DB_INITIALIZED, _PROCESSED_DB, _VECTORIZER, _TFIDF_MATRIX
    
    try:
        # Excel 파일 로드
        df = pd.read_excel(DB_PATH)
        _PROCESSED_DB = df
        
        # 벡터화 미리 수행
        title_field = 'Project Title'
        corpus = df[title_field].fillna("").astype(str).tolist()
        
        _VECTORIZER = TfidfVectorizer(
            analyzer='word', 
            ngram_range=(1, 2),
            lowercase=True
        )
        
        _TFIDF_MATRIX = _VECTORIZER.fit_transform(corpus)
        _DB_INITIALIZED = True
        
        print(f"✅ 내부 DB 초기화 완료: {len(df)} 개 논문 로드됨")
        return True
    except Exception as e:
        print(f"❌ 내부 DB 초기화 실패: {e}")
        return False

# 키워드 추출 함수 - 개선됨
def extract_keywords(text, top_n=5):
    # 텍스트 정제 강화
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # 한국어 조사/어미 제거 강화
    stopwords = [
        # 한국어 조사/어미
        '이', '가', '을', '를', '에', '에서', '로', '으로', '의', '는', '은', '도', '만', '부터', '까지', '와', '과', '하고',
        '에게', '한테', '께', '아', '야', '이야', '라', '이라', '에요', '예요', '습니다', '입니다',
        '하다', '있다', '되다', '같다', '이다', '아니다',
        # 기타 불용어
        '그', '저', '것', '및', '등', '들', '때', '곳', '중', '간', '내', '외', '전', '후', '상', '하', '좌', '우',
        # 영어 불용어
        'the', 'of', 'and', 'a', 'to', 'in', 'is', 'that', 'for', 'on', 'with', 'as', 'be', 'by', 'from', 'at', 'or'
    ]
    
    # 단어 분리 및 필터링
    words = []
    for word in text.split():
        # 길이 2 이상, 불용어 제외, 숫자만으로 구성된 단어 제외
        if len(word) >= 2 and word not in stopwords and not word.isdigit():
            # 한국어는 어간 추출 (간단한 방법)
            if any('\uAC00' <= char <= '\uD7A3' for char in word):  # 한글 포함
                # 조사 제거 (간단한 규칙)
                if word.endswith(('이', '가', '을', '를', '에', '로', '의', '는', '은')):
                    word = word[:-1]
                elif word.endswith(('에서', '으로', '에게', '한테', '에요', '예요')):
                    word = word[:-2]
                elif word.endswith(('습니다', '입니다')):
                    word = word[:-3]
            words.append(word)
    
    # 단어 빈도 계산
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # 빈도순 정렬
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    # 상위 키워드 반환
    top_keywords = [word for word, _ in sorted_words[:top_n]]
    
    return top_keywords

# 효율적인 Claude 번역 함수 - 키워드만 번역
@st.cache_data(show_spinner=False, ttl=3600)
def claude_translate_keywords(keywords, tgt_lang="en") -> list:
    if not keywords:
        return []
        
    try:
        client = anthropic.Anthropic(api_key=st.secrets["api"]["claude_key"])
        keyword_text = ", ".join(keywords)
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,  # 키워드 번역은 짧으니 적은 토큰
            system=f"다음 키워드들을 {tgt_lang}로 번역해주세요. 번역된 키워드만 쉼표로 구분하여 알려주세요.",
            messages=[
                {"role": "user", "content": keyword_text}
            ]
        )
        
        translated = response.content[0].text.strip()
        return [k.strip() for k in translated.split(',')]
    except Exception as e:
        st.warning(f"키워드 번역 중 오류: {e}")
        return keywords

# 일괄 처리 함수 - 여러 프로젝트 제목 한 번에 처리 (Claude 버전)
@st.cache_data(show_spinner=False, ttl=3600)
def batch_infer_content(titles, categories=None):
    """여러 프로젝트 제목을 한 번에 처리하여 Claude API 호출 최소화"""
    if not titles:
        return []
        
    try:
        client = anthropic.Anthropic(api_key=st.secrets["api"]["claude_key"])
        
        # 범주 정보 추가
        prompts = []
        for i, title in enumerate(titles):
            category = categories[i] if categories and i < len(categories) else None
            if category:
                prompts.append(f"{i+1}. '{title}' (연구 분야: {category})")
            else:
                prompts.append(f"{i+1}. '{title}'")
        
        # 시스템 프롬프트 작성
        system_prompt = """
        당신은 과학 논문 제목만으로 내용을 추론하는 도우미입니다. 중요한 규칙:
        
        1. 제목만 있고 실제 논문을 보지 못했다는 것을 명확히 언급할 것
        2. 제목에 없는 구체적 방법론이나 결과는 추론하지 말 것  
        3. 서술은 먼저 제목을 자연스럽게 번역하고, 그 내용을 바탕으로 내용을 추론한다. 설명하는 모든 서술은 "~을 다루었을 것으로 예상됩니다" 같은 추측형으로 작성할 것
        4. 각 논문에 대해 4-6문장의 알기쉬운 구체적인 설명을 제공하고 예를 드는 설명을 보강할 할 것
        5. 각 응답 시작에 번호를 유지할 것 (1., 2., 등)
        
        다음 형식으로 각 논문을 설명하세요:
        "X. 이 연구는 [주제]에 관한 것으로 추정됩니다. 제목에서 유추하면, [예상 목적/방법]을 다루었을 것으로 보입니다. (주의: 이는 제목만을 기반으로 한 추론으로, 실제 연구 내용과 다를 수 있습니다.)"
        나쁜 예: "전자기 유도의 특성을 활용하여 효율적인 전기 생산 방법을..."
        좋은 예: "잎의 생체모방학과 전자기 유도를 활용한 전기 생산 연구입니다."
        """
        
        # 사용자 프롬프트 작성
        user_prompt = "다음 과학 논문 제목들의 내용을 추론해주세요:\n\n" + "\n".join(prompts)
        
        # Claude API 호출
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,  # 여러 프로젝트 일괄 처리를 위한 충분한 토큰
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        full_response = response.content[0].text.strip()
        
        # 응답 파싱
        summaries = []
        current_summary = ""
        current_index = 0
        
        lines = full_response.split('\n')
        for line in lines:
            # 새로운 항목 시작 감지 (1., 2., 등)
            match = re.match(r'^(\d+)\.', line)
            if match:
                # 이전 요약 저장
                if current_summary and current_index > 0:
                    summaries.append(current_summary.strip())
                    
                # 새 요약 시작
                index = int(match.group(1))
                current_index = index
                current_summary = line
            elif current_summary:  # 현재 요약에 라인 추가
                current_summary += " " + line
        
        # 마지막 요약 저장
        if current_summary:
            summaries.append(current_summary.strip())
        
        # 요약 개수 확인 및 조정 
        if len(summaries) < len(titles):
            # 부족한 요약 추가
            for i in range(len(summaries), len(titles)):
                title = titles[i]
                summaries.append(f"{i+1}. 이 프로젝트는 '{title}'에 관한 연구로 추정됩니다. (요약 생성 실패)")
        
        return summaries
    
    except Exception as e:
        print(f"일괄 추론 오류: {e}")
        # 에러 발생시 기본 요약 반환
        return [f"이 프로젝트는 '{title}'에 관한 연구로 추정됩니다. (추론 오류)" for title in titles]

# 개별 프로젝트 내용 추론 함수 (Claude 버전)
@st.cache_data(show_spinner=False, ttl=3600)
def infer_project_content(title, category=None):
    try:
        client = anthropic.Anthropic(api_key=st.secrets["api"]["claude_key"])
        
        system_prompt = """
        당신은 과학 논문 제목만으로 내용을 추론하는 도우미입니다. 중요한 규칙:
        
        1. 제목만 있고 실제 논문을 보지 못했다는 것을 명확히 언급할 것
        2. 모든 서술은 "~로 추측됩니다", "~을 다루었을 것으로 예상됩니다" 같은 추측형으로 작성할 것
        3. 구체적인 방법론과 결과는 완전히 추측이라는 것을 명시할 것
        4. 제목에서 유추할 수 있는 연구 주제와 예상되는 접근법 중심으로 설명할 것
        
        다음 형식으로 답변하세요:
        "이 연구는 [주제]에 관한 것으로 추정됩니다. 제목에서 유추하면, [예상 목적]을 위해 [예상 방법]을 사용했을 것으로 보입니다. 이 연구는 [예상 분야]에 기여할 가능성이 있으며, [잠재적 의의]를 가질 것으로 예상됩니다. (주의: 이는 제목만을 기반으로 한 추론으로, 실제 연구 내용과 다를 수 있습니다.)"
        """
        
        user_prompt = title
        if category:
            user_prompt = f"{title} (연구 분야: {category})"
            
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,  # 개별 프로젝트 추론을 위한 적절한 토큰
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response.content[0].text.strip()
    except Exception as e:
        return f"이 프로젝트는 '{title}'에 관한 연구로 추정됩니다. (추론 과정에서 오류가 발생했습니다.)"

# 내부 DB 로드 및 정제 (기존 함수 보존)
@st.cache_data(ttl=3600)
def load_internal_db():
    try:
        df = pd.read_excel(DB_PATH)
        return df
    except Exception as e:
        st.error(f"❌ 내부 DB 로드 실패: {e}")
        return pd.DataFrame()

# 주제 관련성 검증 함수 추가
def is_topic_relevant(title, category, search_keywords, min_match_score=0.3):
    """검색 주제와 논문의 관련성을 검증"""
    title_lower = title.lower()
    category_lower = category.lower() if category else ""
    
    # 직접 키워드 매칭 점수 계산
    match_score = 0
    total_keywords = len(search_keywords)
    
    for keyword in search_keywords:
        keyword_lower = keyword.lower()
        # 제목에서 키워드 부분 매칭
        if keyword_lower in title_lower:
            match_score += 1.0  # 완전 매칭
        elif any(k in keyword_lower for k in title_lower.split() if len(k) > 2):
            match_score += 0.5  # 부분 매칭
        
        # 카테고리에서 키워드 매칭
        if keyword_lower in category_lower:
            match_score += 0.3
    
    relevance_score = match_score / total_keywords if total_keywords > 0 else 0
    
    print(f"   관련성 검증: '{title[:40]}...' = {relevance_score:.3f}")
    return relevance_score >= min_match_score

# 키워드 확장 함수 추가
def expand_search_keywords(keywords):
    """검색 키워드를 확장하여 관련 용어 추가"""
    keyword_expansions = {
        'microplastic': ['microplastic', 'plastic', 'polymer', 'pollution', 'marine', 'ocean'],
        'plastic': ['plastic', 'polymer', 'microplastic', 'pollution', 'waste'],
        '미세플라스틱': ['plastic', 'microplastic', 'polymer', 'pollution'],
        'environment': ['environmental', 'ecology', 'pollution', 'marine', 'ocean'],
        '환경': ['environmental', 'ecology', 'pollution'],
        'pollution': ['pollution', 'contamination', 'waste', 'environmental'],
        '오염': ['pollution', 'contamination', 'environmental'],
        'marine': ['marine', 'ocean', 'sea', 'water', 'aquatic'],
        '해양': ['marine', 'ocean', 'sea', 'water'],
        'health': ['health', 'medical', 'human', 'body', 'toxicity'],
        '건강': ['health', 'medical', 'human'],
        'water': ['water', 'aquatic', 'marine', 'ocean', 'sea'],
        '물': ['water', 'aquatic', 'marine']
    }
    
    expanded = set(keywords)  # 원본 키워드 유지
    
    for keyword in keywords:
        if keyword.lower() in keyword_expansions:
            expanded.update(keyword_expansions[keyword.lower()])
    
    return list(expanded)

# 메인 검색 함수 - 누락되었던 함수 추가
def search_similar_titles(user_input: str, max_results: int = 10):
    """메인 검색 함수 - 사용자 입력으로 유사한 논문 제목들을 검색"""
    global _DB_INITIALIZED, _PROCESSED_DB, _VECTORIZER, _TFIDF_MATRIX
    
    print(f"🔍 검색 시작: '{user_input}'")
    
    # DB 초기화 확인 및 수행
    if not _DB_INITIALIZED:
        initialize_db()
    
    # 기본 DB 사용 (초기화 실패 시)
    if _PROCESSED_DB is None:
        df = load_internal_db()
    else:
        df = _PROCESSED_DB
    
    if df.empty:
        print("   ❌ DB가 비어있음")
        return []
    
    # 1. 키워드 추출 - 디버깅 로그 추가
    print("📝 1단계: 키워드 추출")
    keywords = extract_keywords(user_input)
    print(f"   추출된 키워드: {keywords}")
    
    if not keywords:
        print("   ❌ 키워드 추출 실패")
        return []
    
    # 2. 키워드 번역 (Claude API 호출 1회) - 디버깅 로그 추가
    print("🌐 2단계: 키워드 번역")
    translated_keywords = claude_translate_keywords(keywords)
    print(f"   번역된 키워드: {translated_keywords}")
    
    if not translated_keywords:
        translated_keywords = keywords
        print("   ⚠️ 번역 실패, 원본 키워드 사용")
    
    search_query = " ".join(translated_keywords)
    print(f"   최종 검색어: '{search_query}'")
    
    # 3. 영어 제목으로 검색 (초기화된 벡터라이저 사용) - 오류 수정
    print("🔢 3단계: 유사도 계산")
    try:
        if _VECTORIZER is not None and _TFIDF_MATRIX is not None:  # 수정: is not None 명시적 비교
            # 사전 처리된 벡터라이저와 매트릭스 사용
            search_vector = _VECTORIZER.transform([search_query])
            cosine_sim = cosine_similarity(search_vector, _TFIDF_MATRIX)[0]
            print(f"   벡터화 성공, 총 {len(cosine_sim)}개 문서와 비교")
        else:
            # 초기화 실패 시 기존 방식으로 폴백
            print("   ⚠️ 사전 처리된 벡터 없음, 새로 계산")
            title_field = 'Project Title'
            corpus = df[title_field].fillna("").astype(str).tolist()
            corpus.append(search_query)
            
            vectorizer = TfidfVectorizer(
                analyzer='word', 
                ngram_range=(1, 2),
                lowercase=True
            )
            
            tfidf_matrix = vectorizer.fit_transform(corpus)
            cosine_sim = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
            print(f"   새로 벡터화 완료, 총 {len(cosine_sim)}개 문서와 비교")
    except Exception as e:
        print(f"   ❌ 검색 벡터화 오류: {e}")
        return []
    
    # 4. 결과 정렬 - 디버깅 로그 추가
    print("📊 4단계: 결과 분석")
    result_df = df.copy()
    result_df['score'] = cosine_sim
    
    # 상위 10개 점수와 제목 출력
    top_10_scores = result_df.nlargest(10, 'score')[['Project Title', 'Category', 'score']]
    print("   상위 10개 유사도 점수:")
    for idx, row in top_10_scores.iterrows():
        print(f"     {row['score']:.6f}: [{row.get('Category', 'N/A')}] {row['Project Title'][:60]}...")
    
    # 임계값 테스트
    thresholds = [0.1, 0.05, 0.01, 0.005]
    selected_threshold = 0.005  # 기본값
    for threshold in thresholds:
        filtered_count = len(result_df[result_df['score'] > threshold])
        print(f"   임계값 {threshold} 이상: {filtered_count}개")
        if filtered_count > 0 and filtered_count <= max_results * 3:  # 적당한 수의 결과
            selected_threshold = threshold
            break
    
    # 선택된 임계값으로 필터링
    filtered_df = result_df[result_df['score'] > selected_threshold].copy()
    print(f"   선택된 임계값: {selected_threshold}")
    
    if filtered_df.empty:
        print("   ❌ 관련 프로젝트를 찾을 수 없음")
        return []
    
    # 5. 상위 결과 선택
    top_df = filtered_df.sort_values(by='score', ascending=False).head(max_results)
    print(f"   최종 선택: {len(top_df)}개")
    
    print("📋 선택된 논문들:")
    for idx, row in top_df.iterrows():
        print(f"     {row['score']:.6f}: [{row.get('Category', 'N/A')}] {row['Project Title']}")
    
    # 6. 결과를 위한 제목과 카테고리 수집
    titles = []
    categories = []
    for _, row in top_df.iterrows():
        titles.append(row.get('Project Title', ''))
        categories.append(row.get('Category', ''))
    
    # 7. 일괄 처리로 모든 요약 한 번에 생성
    if titles:
        print("🤖 5단계: AI 요약 생성")
        summaries = batch_infer_content(titles, categories)
        print(f"   생성된 요약: {len(summaries)}개")
    else:
        summaries = []
    
    # 8. 결과 구성
    results = []
    for i, (_, row) in enumerate(top_df.iterrows()):
        project_title = row.get('Project Title', '')
        category = row.get('Category', '')
        
        # 요약 가져오기
        summary = ""
        if i < len(summaries):
            # 요약에서 번호 제거
            summary_text = summaries[i]
            summary = re.sub(r'^\d+\.\s*', '', summary_text)
        else:
            summary = f"이 프로젝트는 '{project_title}'에 관한 연구로 추정됩니다."
        
        result_item = {
            '제목': project_title,  # 영어 제목 사용
            '연도': str(row.get('Year', '')),
            '분야': category,
            '국가': row.get('Fair Country', ''),
            '지역': row.get('Fair State', ''),
            '수상': row.get('Awards', ''),
            '요약': summary,
            'score': float(row.get('score', 0))
        }
        
        results.append(result_item)
    
    print(f"✅ 검색 완료: {len(results)}개 결과 반환")
    return results
