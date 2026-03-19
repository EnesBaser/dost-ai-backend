# services/search.py
import re
import requests as req_lib
from config import TAVILY_API_KEY, SERPER_API_KEY


def fetch_page_content(url, max_chars=2000):
    try:
        resp = req_lib.get(url, timeout=6, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; DostAI/1.0)'
        })
        if resp.status_code != 200:
            return None
        text = resp.text
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:max_chars] if text else None
    except Exception as e:
        print(f"fetch_page_content error: {e}")
        return None


def serper_search(query, num=5):
    if not SERPER_API_KEY:
        return None
    try:
        response = req_lib.post(
            'https://google.serper.dev/search',
            headers={'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'},
            json={'q': query, 'num': num, 'gl': 'tr', 'hl': 'tr'},
            timeout=8
        )
        if response.status_code != 200:
            return None

        data = response.json()
        parts = []

        answer_box = data.get('answerBox', {})
        if answer_box.get('answer'):
            parts.append(f"Doğrudan yanıt: {answer_box['answer']}")
        elif answer_box.get('snippet'):
            parts.append(f"Özet: {answer_box['snippet']}")

        kg = data.get('knowledgeGraph', {})
        if kg.get('description'):
            parts.append(f"Bilgi: {kg['description'][:300]}")

        organic = data.get('organic', [])
        top_url = None
        for r in organic[:4]:
            title   = r.get('title', '')
            snippet = r.get('snippet', '')
            url     = r.get('link', '')
            if title and snippet:
                parts.append(f"- {title}: {snippet[:250]}")
            if not top_url and url:
                top_url = url

        if top_url and len(parts) < 3:
            full_content = fetch_page_content(top_url)
            if full_content:
                parts.append(f"\n[Tam içerik]:\n{full_content}")

        result = '\n'.join(parts)
        return result if result else None
    except Exception as e:
        print(f"Serper error: {e}")
        return None


def tavily_search(query, max_results=5):
    if not TAVILY_API_KEY:
        return None
    try:
        response = req_lib.post(
            'https://api.tavily.com/search',
            json={
                'api_key': TAVILY_API_KEY,
                'query': query,
                'max_results': max_results,
                'search_depth': 'basic',
                'include_answer': True,
                'language': 'tr',
            },
            timeout=8
        )
        if response.status_code != 200:
            return None

        data = response.json()
        parts = []

        answer = data.get('answer', '')
        if answer:
            parts.append(f"Özet: {answer}")

        for r in data.get('results', [])[:3]:
            title   = r.get('title', '')
            snippet = r.get('content', '')[:200]
            if title and snippet:
                parts.append(f"- {title}: {snippet}")

        result = '\n'.join(parts)
        return result if result else None
    except Exception as e:
        print(f"Tavily error: {e}")
        return None


def web_search(query):
    """Önce Serper, olmazsa Tavily."""
    return serper_search(query) or tavily_search(query)
