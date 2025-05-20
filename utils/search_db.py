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

# 🔤 열 이름 매핑
COLUMN_MAP = {
    'project title': '제목',
    'year': '연도',
    'category': '분야'
}

# 키워드 추출 함수 (NLTK 없이 구현)
def extract_keywords(text, top_n=5):
    """텍스트에서 중요 키워드 추출 - 간단한 버전"""
    # 특수문자 제거 및 소문자화
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # 한국어 불용어 (직접 정의)
    stopwords = ['이', '그', '저', '것', '및', '등', '를', '을', '에', '에서', '의', '으로', '로', '에게', '하다', '있다', '되다']
    
    # 단어 분리 및 불용어 제거
    words = []
    for word in text.split():
        if word not in stopwords and len(word) > 1:  # 2글자 이상만 포함
            words.append(word)
    
    # 빈도수 기반 키워드 추출
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # 빈도순 정렬 및 상위 키워드 반환
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_n]]

# ✅ GPT 번역 함수 (키워드만 번역)
@st.cache_data(show_spinner=False)
def gpt_translate_keywords(keywords, tgt_lang="en") -> list:
    """키워드 리스트만 번역 (API 호출 최소화)"""
    if not keywords:
        return []
        
    try:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])
        # 키워드를 한 번에 번역 요청
        keyword_text = ", ".join(keywords)
        prompt = f"다음 키워드들을 {tgt_lang}로 번역해주세요. 번역된 키워드만 쉼표로 구분하여 알려주세요: {keyword_text}"
        
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        # 번역된 키워드 파싱
        translated = res.choices[0].message.content.strip()
        return [k.strip() for k in translated.split(',')]
    except Exception as e:
        st.warning(f"키워드 번역 중 오류: {e}")
        return keywords  # 실패 시 원본 반환

# ✅ 요약 생성 함수
def get_summary(title):
    try:
        return explain_topic(title)[0]
    except:
        return "요약 없음"

# ✅ 내부 DB 로드 및 정제
def load_internal_db():
    try:
        df = pd.read_excel(DB_PATH)
    except Exception as e:
        st.error(f"❌ 내부 DB 로드 실패: {e}")
        st.stop()
        
    df.columns = [col.strip().lower() for col in df.columns]
    df.rename(columns=lambda c: COLUMN_MAP.get(c, c), inplace=True)
    df['제목'] = df.get('제목', pd.Series(["제목 없음"] * len(df))).fillna("제목 없음").astype(str)
    df['요약'] = df.get('요약', pd.Series([""] * len(df))).fillna("").astype(str)
    df['분야'] = df.get('분야', pd.Series(["분야 없음"] * len(df))).fillna("분야 없음").astype(str)
    df['연도'] = df.get('연도', pd.Series(["연도 없음"] * len(df))).fillna("연도 없음").astype(str)
    
    return df

# ✅ 새로운 유사 논문 검색 함수
def search_similar_titles(user_input, max_results=5):
    df = load_internal_db()
    
    # 1. 사용자 입력에서 키워드 추출
    keywords = extract_keywords(user_input)
    
    # 2. 키워드만 번역 (API 호출 최소화)
    translated_keywords = gpt_translate_keywords(keywords)
    
    # 3. 검색용 쿼리 생성
    search_query = " ".join(translated_keywords)
    
    # 4. 영문 제목에 대해 TF-IDF 유사도 분석
    # DB에 영문 제목 필드가 있다고 가정 (project title)
    if 'project title' in df.columns:
        corpus = df['project title'].fillna('').tolist() + [search_query]
    else:
        # 영문 제목 필드가 없는 경우 한글 제목 사용
        corpus = df['제목'].fillna('').tolist() + [search_query]
    
    try:
        # 단어 수준 및 문자 수준 혼합 분석
        vectorizer = TfidfVectorizer(
            analyzer='word', 
            ngram_range=(1, 2),
            lowercase=True,
            max_features=5000
        )
        tfidf_matrix = vectorizer.fit_transform(corpus)
        cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    except Exception as e:
        st.error(f"❌ 유사도 분석 오류: {e}")
        return []
    
    # 5. 유사도 점수 할당 및 필터링
    df['score'] = cosine_sim
    df = df[df['score'] > 0.1]  # 최소 유사도 임계값 설정
    
    # 6. 상위 결과 선택
    top = df.sort_values(by='score', ascending=False).head(max_results)
    
    # 7. 요약 정보 보완
    top['요약'] = top.apply(
        lambda row: row['요약'].strip() if row.get('요약') and row['요약'].strip() else get_summary(row['제목']),
        axis=1
    )
    
    return top[['제목', '요약', '연도', '분야', 'score']].to_dict(orient='records')
