# services/ai_service.py
from openai import OpenAI
from config import OPENAI_API_KEY

_client = None

def get_client():
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY bulunamadı!")
        _client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client başlatıldı!")
    return _client


def calculate_cost(tokens, model='gpt-4o-mini'):
    costs = {
        'gpt-4o-mini': 0.00015,
        'gpt-4o':      0.0025,
        'gpt-4.1':     0.008,
        'gpt-4.1-mini': 0.0004,
    }
    return (tokens / 1000) * costs.get(model, 0.00015)
