import pandas as pd
import os
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from deep_translator import GoogleTranslator

# 📁 내부 DB 파일 경로
DB_PATH = os.path.join("data", "ISEF Final DB.xlsx")

# 🔤 열 이름 매핑
COLUMN_MAP = {
    'project title': '제목',
    'year': '연도',
    'category': '분야'
}

# ✅ 번역 캐싱 함수
@st.cache_data(show_spinner=False)
def translate_once(text, src='auto', tgt='en'):
    try:
        return GoogleTranslator(source=src, target=tgt).translate(text)
    except Exception as e:
        st.warning(f"⚠️ 번역 실패 → {text}")
        return text

# ✅ 요약 추론 함수
def get_summary(title):
    try:
        return GoogleTranslator(source='en', target='ko').translate(
            f"This paper explores a science fair project titled: {title}. It may involve STEM education or scientific investigation."
        )
    except:
        return "요약 없음"

# ✅ 내부 DB 로드 및 정리
def load_internal_db():
    try:
        df = pd.read_excel(DB_PATH)
    except Exception as e:
        st.error(f"❌ 내부 DB 로드 오류: {e}")
        st.stop()

    # 열 정리 및 결측 채움
    df.columns = [col.strip().lower() for col in df.columns]
    df.rename(columns=lambda c: COLUMN_MAP.get(c, c), inplace=True)

    df['제목'] = df.get('제목', pd.Series(["제목 없음"] * len(df))).fillna("제목 없음").astype(str)
    df['요약'] = df.get('요약', pd.Series([""] * len(df))).fillna("").astype(str)
    df['분야'] = df.get('분야', pd.Series(["분야 없음"] * len(df))).fillna("분야 없음").astype(str)
    df['연도'] = df.get('연도', pd.Series(["연도 없음"] * len(df))).fillna("연도 없음").astype(str)

    return df

# ✅ 내부 유사 논문 검색
def search_similar_titles(user_input, max_results=5):
    df = load_internal_db()

    # 입력 번역
    translated_input = translate_once(user_input)

    # 전체 제목 번역 캐싱
    unique_titles = list(set(df['제목'].tolist()))
    translated_map = {t: translate_once(t) for t in unique_titles}
    df['제목_번역'] = df['제목'].map(translated_map)

    # 유사도 분석용 말뭉치
    corpus = df['제목_번역'].tolist() + [translated_input]

    try:
        vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), lowercase=True)
        tfidf_matrix = vectorizer.fit_transform(corpus)
        cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    except Exception as e:
        st.error(f"❌ 유사도 계산 실패: {e}")
        st.stop()

    df['score'] = cosine_sim
    df = df[df['score'] > 0]

    top = df.sort_values(by='score', ascending=False).head(max_results)

    # 요약 자동 생성
    top['요약'] = top.apply(
        lambda row: row['요약'] if row['요약'].strip() else get_summary(row['제목']),
        axis=1
    )

    return top[['제목', '요약', '연도', '분야', 'score']].to_dict(orient='records')
