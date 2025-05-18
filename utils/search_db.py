import pandas as pd
import os
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from deep_translator import GoogleTranslator

DB_PATH = os.path.join("data", "ISEF Final DB.xlsx")
COLUMN_MAP = {
    'project title': '제목',
    'year': '연도',
    'category': '분야'
}

# ✅ 캐싱된 번역기
@st.cache_data(show_spinner=False)
def translate_once(text, src='auto', tgt='en'):
    try:
        return GoogleTranslator(source=src, target=tgt).translate(text)
    except:
        return text

# ✅ 요약 추론 생성기
def get_summary(title):
    try:
        return GoogleTranslator(source='en', target='ko').translate(
            f"This paper studies a science fair topic titled: {title}. It may be related to STEM education or science research."
        )
    except:
        return "요약 없음"

def load_internal_db():
    try:
        df = pd.read_excel(DB_PATH)
    except Exception as e:
        st.error(f"❌ 내부 DB 파일 로드 오류: {e}")
        st.stop()

    df.columns = [col.strip().lower() for col in df.columns]
    df.rename(columns=lambda c: COLUMN_MAP.get(c, c), inplace=True)

    df['제목'] = df.get('제목', pd.Series(["제목 없음"] * len(df))).fillna("제목 없음").astype(str)
    df['요약'] = df.get('요약', pd.Series([""] * len(df))).fillna("").astype(str)
    df['분야'] = df.get('분야', pd.Series(["분야 없음"] * len(df))).fillna("분야 없음").astype(str)
    df['연도'] = df.get('연도', pd.Series(["연도 없음"] * len(df))).fillna("연도 없음").astype(str)

    return df

def search_similar_titles(user_input, max_results=5):
    df = load_internal_db()

    # ✅ 번역 (입력 + 전체 제목)
    translated_input = translate_once(user_input)
    unique_titles = list(set(df['제목'].tolist()))
    translated_map = {t: translate_once(t) for t in unique_titles}
    df['제목_번역'] = df['제목'].map(translated_map)

    corpus = df['제목_번역'].tolist() + [translated_input]

    try:
        vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), lowercase=True)
        tfidf_matrix = vectorizer.fit_transform(corpus)
        cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    except Exception as e:
        st.error(f"❌ 유사도 계산 오류: {e}")
        st.stop()

    df['score'] = cosine_sim
    df = df[df['score'] > 0]

    top = df.sort_values(by='score', ascending=False).head(max_results)

    # ✅ 요약 없는 항목 처리
    top['요약'] = top.apply(lambda row: row['요약'] if row['요약'] != "" else get_summary(row['제목']), axis=1)

    return top[['제목', '요약', '연도', '분야', 'score']].to_dict(orient='records')
