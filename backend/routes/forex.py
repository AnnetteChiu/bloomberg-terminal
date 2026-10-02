from fastapi import APIRouter
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("FINNHUB_KEY") or "dahso4hr01qvl9br4mq0dahso4hr01qvl9br4mqg"
BASE = "https://finnhub.io/api/v1"

router = APIRouter()
_cache = {}

PAIRS = [("USD","TWD"),("USD","JPY"),("EUR","USD"),("USD","CNY"),("GBP","USD")]

def get_cached(key, fn, ttl=120):
    now = time.time()
    if key in _cache and now - _cache[key]["ts"] < ttl:
        return _cache[key]["data"]
    data = fn()
    if data:
        _cache[key] = {"data": data, "ts": now}
    return data

@router.get("/")
def get_forex():
    results = []
    for from_c, to_c in PAIRS:
        def fetch(f=from_c, t=to_c):
            r = requests.get(f"{BASE}/forex/rates", params={"base": f, "token": KEY}, timeout=10)
            d = r.json()
            rate = d.get("quote", {}).get(t)
            if not rate:
                return None
            return {"pair": f"{f}/{t}", "rate": rate}
        result = get_cached(f"forex_{from_c}_{to_c}", fetch, ttl=120)
        if result:
            results.append(result)
    return results
