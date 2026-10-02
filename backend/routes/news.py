from fastapi import APIRouter
import requests
import os
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("ALPHA_VANTAGE_KEY")
BASE = "https://www.alphavantage.co/query"

router = APIRouter()

@router.get("/{symbol}")
def get_news(symbol: str):
    r = requests.get(BASE, params={
        "function": "NEWS_SENTIMENT",
        "tickers": symbol,
        "limit": 10,
        "apikey": KEY,
    })
    items = r.json().get("feed", [])
    return [
        {
            "title": n.get("title"),
            "url": n.get("url"),
            "published": n.get("time_published", "")[:10],
        }
        for n in items[:10]
    ]
