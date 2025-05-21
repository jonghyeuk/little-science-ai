# api_utils.py 예시 시작점
import requests
import urllib.parse
import feedparser
import os

def search_arxiv(query, max_results=5):
    # 기존 코드 이동...

def search_crossref(query, max_results=5, email=None):
    email = email or os.getenv("CROSSREF_EMAIL", "")
    url = "https://api.crossref.org/works"
    params = {
        "query": query,
        "rows": max_results,
        "sort": "relevance"
    }
    headers = {}
    if email:
        headers["mailto"] = email
        
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return []
        
    data = response.json()
    results = []
    for item in data.get("message", {}).get("items", []):
        # 결과 파싱...
    return results
