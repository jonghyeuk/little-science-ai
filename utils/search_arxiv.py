import urllib.parse
import feedparser
import streamlit as st
from deep_translator import GoogleTranslator

# ✅ 캐시된 번역기
@st.cache_data(show_spinner=False)
def translate_once(text, src="en", tgt="ko"):
    try:
        return GoogleTranslator(source=src, target=tgt).translate(text)
    except:
        return text

def search_arxiv(query, max_results=5):
    base_url = "http://export.arxiv.org/api/query"

    # ✅ Step 1: 입력 쿼리 한영 번역
    try:
        translated_query = translate_once(query, src='auto', tgt='en')
    except Exception as e:
        st.error(f"❌ 검색어 번역 실패: {e}")
        translated_query = query

    encoded_query = urllib.parse.quote(translated_query)
    query_url = f"{base_url}?search_query=all:{encoded_query}&start=0&max_results={max_results}"

    try:
        feed = feedparser.parse(query_url)
        entries = feed.entries

        if not entries:
            return [{
                "title": "검색 결과 없음",
                "summary": "해당 주제와 관련된 arXiv 논문을 찾을 수 없습니다.",
                "link": "",
                "source": "arXiv"
            }]

        # ✅ 중복 방지 병렬 번역 (제목, 요약)
        titles = list(set(e.title for e in entries))
        summaries = list(set(e.get("summary", "") for e in entries))

        title_map = {t: translate_once(t) for t in titles}
        summary_map = {s: translate_once(s) for s in summaries}

        results = []
        for entry in entries:
            title_en = entry.title
            summary_en = entry.get("summary", "")
            link = entry.link

            title_ko = title_map.get(title_en, title_en)
            summary_ko = summary_map.get(summary_en, summary_en)

            results.append({
                "title": f"**{title_ko}**\n`{title_en}`",
                "summary": summary_ko,
                "link": link,
                "source": "arXiv"
            })

        return results

    except Exception as e:
        st.error(f"❌ arXiv 검색 중 오류 발생: {e}")
        return [{
            "title": "arXiv 검색 실패",
            "summary": "",
            "link": "",
            "source": "arXiv"
        }]
