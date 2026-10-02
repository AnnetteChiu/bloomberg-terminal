from fastapi import APIRouter, HTTPException
from functools import lru_cache
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("ALPHA_VANTAGE_KEY")
BASE = "https://www.alphavantage.co/query"

router = APIRouter()

# 簡單 TTL 快取
_cache = {}

def get_cached(key, fn, ttl=60):
    now = time.time()
    if key in _cache and now - _cache[key]["ts"] < ttl:
        return _cache[key]["data"]
    data = fn()
    _cache[key] = {"data": data, "ts": now}
    return data

@router.get("/{symbol}")
def get_stock(symbol: str):
    symbol = symbol.upper()
    def fetch():
        r = requests.get(BASE, params={
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": KEY,
        }, timeout=10)
        data = r.json().get("Global Quote", {})
        if not data:
            raise HTTPException(status_code=404, detail="Symbol not found")
        return {
            "symbol": symbol,
            "name": symbol,
            "price": float(data["05. price"]),
            "change": float(data["09. change"]),
            "change_pct": float(data["10. change percent"].replace("%", "")),
            "volume": int(data["06. volume"]),
        }
    return get_cached(f"quote_{symbol}", fetch, ttl=60)

@router.get("/{symbol}/history")
def get_history(symbol: str, period: str = "1mo"):
    symbol = symbol.upper()
    def fetch():
        outputsize = "compact" if period in ["5d", "1mo"] else "full"
        r = requests.get(BASE, params={
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize,
            "apikey": KEY,
        }, timeout=10)
        ts = r.json().get("Time Series (Daily)", {})
        if not ts:
            raise HTTPException(status_code=404, detail="No data found")

        from datetime import date, timedelta
        period_days = {"5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}
        days = period_days.get(period, 30)
        cutoff = date.today() - timedelta(days=days)

        return [
            {"time": d, "open": float(v["1. open"]), "high": float(v["2. high"]),
             "low": float(v["3. low"]), "close": float(v["4. close"]), "volume": int(v["5. volume"])}
            for d, v in sorted(ts.items()) if date.fromisoformat(d) >= cutoff
        ]
    return get_cached(f"history_{symbol}_{period}", fetch, ttl=300)
