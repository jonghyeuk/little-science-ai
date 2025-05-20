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
@st.cache_data(show_spinner=False)
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

# 프로젝트 내용 추론 함수 (캐싱 적용)
@st.cache_data(show_spinner=False, ttl=3600)
def infer_project_content(title, category=None):
    try:
        prompt = title
        if category:
            prompt = f"{title} (연구 분야: {category})"
            
        explanation = explain_topic(prompt)[0]
        return explanation
    except Exception as e:
        return f"이 프로젝트는 '{title}'에 관한 연구입니다."

# 내부 DB 로드 및 정제
@st.cache_data(ttl=3600)
def load_internal_db():
    try:
        df = pd.read_excel(DB_PATH)
        return df
    except Exception as e:
        st.error(f"❌ 내부 DB 로드 실패: {e}")
        return pd.DataFrame()

# 유사 프로젝트 검색 함수
def search_similar_titles(user_input, max_results=5):
    df = load_internal_db()
    
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
    
    # 3. 영어 제목으로 검색
    title_field = 'Project Title'
    if title_field not in df.columns:
        return []
    
    corpus = df[title_field].fillna("").astype(str).tolist()
    corpus.append(search_query)
    
    try:
        vectorizer = TfidfVectorizer(
            analyzer='word', 
            ngram_range=(1, 2),
            lowercase=True
        )
        
        tfidf_matrix = vectorizer.fit_transform(corpus)
        cosine_sim = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
    except Exception as e:
        return []
    
    # 4. 결과 정렬
    result_df = df.copy()
    result_df['score'] = cosine_sim
    filtered_df = result_df[result_df['score'] > 0.05].copy()
    
    if filtered_df.empty:
        return []
    
    # 5. 상위 결과 선택
    top_df = filtered_df.sort_values(by='score', ascending=False).head(max_results)
    
    # 6. 결과 구성 (파이널리스트 정보 제외)
    results = []
    for _, row in top_df.iterrows():
        project_title = row.get('Project Title', '')
        category = row.get('Category', '')
        
        result_item = {
            '제목': project_title,  # 영어 제목 사용
            '연도': str(row.get('Year', '')),
            '분야': category,
            '국가': row.get('Fair Country', ''),
            '지역': row.get('Fair State', ''),
            '수상': row.get('Awards', ''),
            '요약': infer_project_content(project_title, category),  # 필요할 때만 추론
            'score': float(row.get('score', 0))
        }
        
        results.append(result_item)
    
    return results
