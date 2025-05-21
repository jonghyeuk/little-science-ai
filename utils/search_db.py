import pandas as pd
import os
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.explain_topic import explain_topic
from openai import OpenAI
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

# 키워드 추출 함수
def extract_keywords(text, top_n=5):
    text = re.sub(r'[^\w\s]', '', text.lower())
    stopwords = ['이', '그', '저', '것', '및', '등', '를', '을', '에', '에서', '의', '으로', '로', '에게', '하다', '있다', '되다',
                'the', 'of', 'and', 'a', 'to', 'in', 'is', 'that', 'for', 'on', 'with']
    
    words = [word for word in text.split() if word not in stopwords and len(word) > 1]
    
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_n]]

# 효율적인 GPT 번역 함수 - 키워드만 번역
@st.cache_data(show_spinner=False, ttl=3600)
def gpt_translate_keywords(keywords, tgt_lang="en") -> list:
    if not keywords:
        return []
        
    try:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])
        keyword_text = ", ".join(keywords)
        prompt = f"다음 키워드들을 {tgt_lang}로 번역해주세요. 번역된 키워드만 쉼표로 구분하여 알려주세요: {keyword_text}"
        
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        translated = res.choices[0].message.content.strip()
        return [k.strip() for k in translated.split(',')]
    except Exception as e:
        st.warning(f"키워드 번역 중 오류: {e}")
        return keywords

# 일괄 처리 함수 - 여러 프로젝트 제목 한 번에 처리
@st.cache_data(show_spinner=False, ttl=3600)
def batch_infer_content(titles, categories=None):
    """여러 프로젝트 제목을 한 번에 처리하여 GPT API 호출 최소화"""
    if not titles:
        return []
        
    try:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])
        
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
        2. 모든 서술은 "~로 추측됩니다", "~을 다루었을 것으로 예상됩니다" 같은 추측형으로 작성할 것
        3. 각 논문에 대해 2-3문장의 간결한 설명 제공
        4. 각 응답 시작에 번호를 유지할 것 (1., 2., 등)
        
        다음 형식으로 각 논문을 설명하세요:
        "X. 이 연구는 [주제]에 관한 것으로 추정됩니다. 제목에서 유추하면, [예상 목적/방법]을 다루었을 것으로 보입니다. (주의: 이는 제목만을 기반으로 한 추론으로, 실제 연구 내용과 다를 수 있습니다.)"
        """
        
        # 사용자 프롬프트 작성
        user_prompt = "다음 과학 논문 제목들의 내용을 추론해주세요:\n\n" + "\n".join(prompts)
        
        # API 호출
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        full_response = res.choices[0].message.content.strip()
        
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

# 개별 프로젝트 내용 추론 함수 (기존 함수 보존)
@st.cache_data(show_spinner=False, ttl=3600)
def infer_project_content(title, category=None):
    try:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])
        
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
            
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        return res.choices[0].message.content.strip()
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

# 최적화된 유사 프로젝트 검색 함수
def search_similar_titles(user_input, max_results=5):
    global _DB_INITIALIZED, _PROCESSED_DB, _VECTORIZER, _TFIDF_MATRIX
    
    # DB 초기화 확인 및 수행
    if not _DB_INITIALIZED:
        initialize_db()
    
    # 기본 DB 사용 (초기화 실패 시)
    if _PROCESSED_DB is None:
        df = load_internal_db()
    else:
        df = _PROCESSED_DB
    
    if df.empty:
        return []
    
    # 1. 키워드 추출
    keywords = extract_keywords(user_input)
    if not keywords:
        return []
    
    # 2. 키워드 번역 (API 호출 1회)
    translated_keywords = gpt_translate_keywords(keywords)
    if not translated_keywords:
        translated_keywords = keywords
    
    search_query = " ".join(translated_keywords)
    
    # 3. 영어 제목으로 검색 (초기화된 벡터라이저 사용)
    try:
        if _VECTORIZER and _TFIDF_MATRIX:
            # 사전 처리된 벡터라이저와 매트릭스 사용
            search_vector = _VECTORIZER.transform([search_query])
            cosine_sim = cosine_similarity(search_vector, _TFIDF_MATRIX)[0]
        else:
            # 초기화 실패 시 기존 방식으로 폴백
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
    except Exception as e:
        print(f"검색 벡터화 오류: {e}")
        return []
    
    # 4. 결과 정렬
    result_df = df.copy()
    result_df['score'] = cosine_sim
    filtered_df = result_df[result_df['score'] > 0.05].copy()
    
    if filtered_df.empty:
        return []
    
    # 5. 상위 결과 선택
    top_df = filtered_df.sort_values(by='score', ascending=False).head(max_results)
    
    # 6. 결과를 위한 제목과 카테고리 수집
    titles = []
    categories = []
    for _, row in top_df.iterrows():
        titles.append(row.get('Project Title', ''))
        categories.append(row.get('Category', ''))
    
    # 7. 일괄 처리로 모든 요약 한 번에 생성
    if titles:
        summaries = batch_infer_content(titles, categories)
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
    
    return results
