# utils/search_arxiv.py

import requests
import feedparser
import urllib.parse
import streamlit as st

def search_arxiv(query, max_results=5):
    base_url = "http://export.arxiv.org/api/query"
    encoded_query = urllib.parse.quote(query)

    query_url = f"{base_url}?search_query=all:{encoded_query}&start=0&max_results={max_results}"

    try:
        feed = feedparser.parse(query_url)

        if not feed.entries:
            return [{"title": "검색 결과 없음", "summary": "", "link": "", "source": "arXiv"}]

        results = []
        for entry in feed.entries:
            results.append({
                "title": entry.title,
                "summary": entry.get("summary", ""),
                "link": entry.link,
                "source": "arXiv"
            })

        return results

    except Exception as e:
        st.error(f"❌ arXiv 검색 중 오류가 발생했습니다: {e}")
        return [{"title": "arXiv 검색 실패", "summary": "", "link": "", "source": "arXiv"}]
