# utils/search_arxiv.py

import requests
import feedparser

def search_arxiv(query, max_results=5):
    base_url = "http://export.arxiv.org/api/query"
    query_url = f"{base_url}?search_query=all:{query}&start=0&max_results={max_results}"

    feed = feedparser.parse(query_url)
    results = []

    for entry in feed.entries:
        results.append({
            "title": entry.title,
            "summary": entry.summary,
            "link": entry.link,
            "source": "arXiv"
        })

    return results
