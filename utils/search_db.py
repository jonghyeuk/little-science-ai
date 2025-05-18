# utils/search_db.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import streamlit as st
from deep_translator import GoogleTranslator

# 📁 DB 엑셀 파일 경로
DB_PATH = os.path.join("data", "ISEF Final DB.xlsx")

# 열 이름 매핑 (영문 → 한글)
COLUMN_MAP = {
    'project title': '제목',
    'year': '연도',
    'category': '분야'
}

def load_internal_db():
    """내부 DB 엑셀 파일 로드 및 컬럼명 변환"""
    try:
        df = pd.read_excel(DB_PATH)
    except Exception as e:
        st.error(f"❌ 내부 DB 파일 로드 오류: {e}")
        st.stop()

    df.columns = [col.strip().lower() for col in df.columns]
    df.rename(columns=lambda c: COLUMN_MAP.get(c, c), inplace=True)

    df['제목'] = df.get('제목', pd.Series(["제목 없음"] * len(df))).fillna("제목 없음").astype(str)
    df['요약'] = df.get('요약', pd.Series(["요약 없음"] * len(df))).fillna("요약 없음").astype(str)
    df['분야'] = df.get('분야', pd.Series(["분야 없음"] * len(df))).fillna("분야 없음").astype(str)
    df['연도'] = df.get('연도', pd.Series(["연도 없음"] * len(df))).fillna("연도 없음").astype(str)

    return df

def translate_to_english(text):
    """한글 주제를 영어로 번역 (arxiv, TF-IDF용)"""
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception:
        return text  # 실패 시 원문 그대로 사용

def search_similar_titles(user_input, max_results=5):
    """입력 주제에 대한 내부 DB 유사 논문 검색"""
    df = load_internal_db()

    # ✅ 한글 입력 → 영어 번역
    translated_input = translate_to_english(user_input)

    corpus = df['제목'].tolist() + [translated_input]

    try:
        vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(3, 5),
            lowercase=True
        )
        tfidf_matrix = vectorizer.fit_transform(corpus)
        cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    except Exception as e:
        st.error(f"❌ 유사도 계산 오류: {e}")
        st.stop()

    df['score'] = cosine_sim
    df = df[df['score'] > 0]  # 0점 제외

    results = df.sort_values(by='score', ascending=False).head(max_results)

    return results[['제목', '요약', '연도', '분야', 'score']].to_dict(orient='records')
