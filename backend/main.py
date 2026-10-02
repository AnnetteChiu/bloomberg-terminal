from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests, time
from datetime import date, timedelta, datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "https://*.vercel.app"], allow_methods=["*"], allow_headers=["*"])

FINNHUB_KEY = "dahso4hr01qvl9br4mq0dahso4hr01qvl9br4mqg"
FINNHUB = "https://finnhub.io/api/v1"
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart"
HEADERS = {"User-Agent": "Mozilla/5.0"}
_cache = {}

def cached(key, fn, ttl=60):
    now = time.time()
    if key in _cache and now - _cache[key]["ts"] < ttl:
        return _cache[key]["data"]
    data = fn()
    _cache[key] = {"data": data, "ts": now}
    return data

@app.get("/stocks/{symbol}")
def get_stock(symbol: str):
    symbol = symbol.upper()
    r = requests.get(f"{FINNHUB}/quote", params={"symbol": symbol, "token": FINNHUB_KEY}, timeout=10)
    d = r.json()
    if not d or "c" not in d or d["c"] == 0:
        raise HTTPException(status_code=404, detail="Symbol not found")
    return {"symbol": symbol, "name": symbol, "price": d["c"], "change": d["d"], "change_pct": d["dp"], "volume": 0}

@app.get("/stocks/{symbol}/history")
def get_history(symbol: str, period: str = "1mo"):
    symbol = symbol.upper()
    range_map = {"5d": "5d", "1mo": "1mo", "3mo": "3mo", "6mo": "6mo", "1y": "1y"}
    yrange = range_map.get(period, "1mo")
    def fetch():
        r = requests.get(f"{YAHOO}/{symbol}", params={"interval": "1d", "range": yrange}, headers=HEADERS, timeout=10)
        data = r.json()
        result = data.get("chart", {}).get("result")
        if not result:
            raise HTTPException(status_code=404, detail="No data found")
        res = result[0]
        timestamps = res["timestamp"]
        ohlcv = res["indicators"]["quote"][0]
        return [
            {"time": date.fromtimestamp(t).isoformat(),
             "open": round(o, 2), "high": round(h, 2), "low": round(l, 2), "close": round(c, 2), "volume": int(v or 0)}
            for t, o, h, l, c, v in zip(timestamps, ohlcv["open"], ohlcv["high"], ohlcv["low"], ohlcv["close"], ohlcv["volume"])
            if o and h and l and c
        ]
    return cached(f"hist_{symbol}_{period}", fetch, ttl=300)

@app.get("/stocks/{symbol}/indicators")
def get_indicators(symbol: str, period: str = "1mo"):
    history = get_history(symbol, period)
    closes = [d["close"] for d in history]
    times = [d["time"] for d in history]
    def ma(data, n):
        return [round(sum(data[i-n:i])/n, 2) if i >= n else None for i in range(1, len(data)+1)]
    def rsi(data, n=14):
        result = [None] * n
        for i in range(n, len(data)):
            ch = [data[j]-data[j-1] for j in range(i-n+1, i+1)]
            g = sum(c for c in ch if c > 0)
            l = sum(-c for c in ch if c < 0)
            result.append(100.0 if l == 0 else round(100-(100/(1+g/l)), 2))
        return result
    return [{"time": t, "ma5": m5, "ma20": m20, "rsi": r}
            for t, m5, m20, r in zip(times, ma(closes, 5), ma(closes, 20), rsi(closes))]

@app.get("/news/{symbol}")
def get_news(symbol: str):
    def fetch():
        r = requests.get(f"{FINNHUB}/company-news", params={"symbol": symbol.upper(), "from": (date.today()-timedelta(days=7)).isoformat(), "to": date.today().isoformat(), "token": FINNHUB_KEY}, timeout=10)
        return [{"title": n.get("headline"), "url": n.get("url"), "published": date.fromtimestamp(n.get("datetime", 0)).isoformat()} for n in r.json()[:10]]
    return cached(f"news_{symbol}", fetch, ttl=300)

@app.get("/forex/")
def get_forex():
    pairs = [("USD","TWD"),("USD","JPY"),("EUR","USD"),("USD","CNY"),("GBP","USD")]
    results = []
    for f, t in pairs:
        def fetch(fc=f, tc=t):
            r = requests.get(f"{FINNHUB}/forex/rates", params={"base": fc, "token": FINNHUB_KEY}, timeout=10)
            rate = r.json().get("quote", {}).get(tc)
            return {"pair": f"{fc}/{tc}", "rate": rate} if rate else None
        res = cached(f"fx_{f}_{t}", fetch, ttl=120)
        if res:
            results.append(res)
    return results

# ── 算法交易 ──────────────────────────────────────────
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import threading

ALPACA_KEY = "PKZ2CETAO2ZREQ64YTUHC3YDAE"
ALPACA_SECRET = "Ec46PELq6cWpYakqVuWVqACrcTHFHLykuZUtskxqFuUU"
alpaca = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)

strategy_state = {"running": False, "symbol": "AAPL", "qty": 1, "logs": []}

def log(msg):
    entry = {"time": datetime.now().strftime("%H:%M:%S"), "msg": msg}
    strategy_state["logs"].insert(0, entry)
    strategy_state["logs"] = strategy_state["logs"][:50]

def run_strategy():
    symbol = strategy_state["symbol"]
    qty = strategy_state["qty"]
    prices = []
    log(f"策略啟動 {symbol} (MA交叉 + RSI過濾)")

    def calc_rsi(data, n=14):
        if len(data) < n + 1:
            return None
        changes = [data[i] - data[i-1] for i in range(1, len(data))]
        gains = sum(c for c in changes[-n:] if c > 0)
        losses = sum(-c for c in changes[-n:] if c < 0)
        if losses == 0:
            return 100.0
        return round(100 - (100 / (1 + gains / losses)), 2)

    while strategy_state["running"]:
        try:
            r = requests.get(f"{FINNHUB}/quote", params={"symbol": symbol, "token": FINNHUB_KEY}, timeout=5)
            price = r.json().get("c", 0)
            if price:
                prices.append(price)
                if len(prices) > 30:
                    prices.pop(0)
                if len(prices) >= 20:
                    ma5 = sum(prices[-5:]) / 5
                    ma20 = sum(prices) / 20
                    rsi = calc_rsi(prices)
                    rsi_str = f"RSI={rsi:.1f}" if rsi else "RSI=n/a"
                    if ma5 > ma20 * 1.001 and rsi and rsi < 70:
                        order = MarketOrderRequest(symbol=symbol, qty=qty, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
                        alpaca.submit_order(order)
                        log(f"BUY {qty} {symbol} @ ${price:.2f} MA5={ma5:.2f} {rsi_str}")
                    elif ma5 < ma20 * 0.999 and rsi and rsi > 30:
                        order = MarketOrderRequest(symbol=symbol, qty=qty, side=OrderSide.SELL, time_in_force=TimeInForce.DAY)
                        alpaca.submit_order(order)
                        log(f"SELL {qty} {symbol} @ ${price:.2f} MA5={ma5:.2f} {rsi_str}")
                    else:
                        log(f"HOLD {symbol} @ ${price:.2f} MA5={ma5:.2f} MA20={ma20:.2f} {rsi_str}")
                else:
                    log(f"收集數據中 {len(prices)}/20")
        except Exception as e:
            log(f"ERROR: {e}")
        time.sleep(60)
    log("策略停止")

@app.get("/stocks/{symbol}/signal")
def get_signal(symbol: str):
    symbol = symbol.upper()
    try:
        history = get_history(symbol, "1mo")
        closes = [d["close"] for d in history]
        if len(closes) < 20:
            return {"signal": "WAIT", "reason": "數據不足", "score": 0}

        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20

        # RSI
        changes = [closes[i]-closes[i-1] for i in range(1, len(closes))]
        gains = sum(c for c in changes[-14:] if c > 0)
        losses = sum(-c for c in changes[-14:] if c < 0)
        rsi = 100.0 if losses == 0 else round(100-(100/(1+gains/losses)), 2)

        # 趨勢
        trend = "up" if closes[-1] > closes[-5] else "down"
        score = 0
        reasons = []

        if ma5 > ma20:
            score += 2
            reasons.append("MA5 > MA20 ✓")
        else:
            score -= 2
            reasons.append("MA5 < MA20 ✗")

        if rsi < 70:
            score += 1
            reasons.append(f"RSI={rsi:.1f} 未超買 ✓")
        else:
            score -= 2
            reasons.append(f"RSI={rsi:.1f} 超買 ✗")

        if rsi > 30:
            score += 1
        else:
            score -= 1
            reasons.append(f"RSI={rsi:.1f} 超賣")

        if trend == "up":
            score += 1
            reasons.append("近5日上漲趨勢 ✓")
        else:
            score -= 1
            reasons.append("近5日下跌趨勢 ✗")

        if score >= 3:
            signal = "BUY"
        elif score <= -2:
            signal = "SELL"
        else:
            signal = "HOLD"

        return {
            "signal": signal,
            "score": score,
            "ma5": round(ma5, 2),
            "ma20": round(ma20, 2),
            "rsi": rsi,
            "price": closes[-1],
            "reasons": reasons,
        }
    except Exception as e:
        return {"signal": "ERROR", "reason": str(e), "score": 0}
def get_account():
    acc = alpaca.get_account()
    pnl = float(acc.equity) - float(acc.last_equity) if acc.equity and acc.last_equity else 0.0
    return {"cash": float(acc.cash), "portfolio": float(acc.portfolio_value), "pnl": round(pnl, 2)}

@app.get("/scan/hot")
def scan_hot():
    """根據成交量、價格動能、RSI 找出最熱門股票"""
    watchlist = ['AAPL','GOOGL','MSFT','TSLA','AMZN','META','NVDA','NFLX','AMD','INTC','ORCL','CRM','UBER','SPOT','COIN']
    results = []
    for symbol in watchlist:
        try:
            hist = get_history(symbol, "5d")
            if len(hist) < 2:
                continue
            closes = [d["close"] for d in hist]
            volumes = [d["volume"] for d in hist]

            # 價格動能：近5日漲幅
            price_change = (closes[-1] - closes[0]) / closes[0] * 100

            # 成交量動能：近2日 vs 前3日均量
            recent_vol = sum(volumes[-2:]) / 2
            prev_vol = sum(volumes[:-2]) / max(len(volumes)-2, 1)
            vol_ratio = recent_vol / prev_vol if prev_vol > 0 else 1

            # RSI
            changes = [closes[i]-closes[i-1] for i in range(1, len(closes))]
            gains = sum(c for c in changes if c > 0)
            losses = sum(-c for c in changes if c < 0)
            rsi = 100.0 if losses == 0 else round(100-(100/(1+gains/losses)), 2)

            # 綜合評分
            score = 0
            score += min(price_change * 10, 30)   # 漲幅最多30分
            score += min((vol_ratio - 1) * 20, 30) # 量能最多30分
            if 40 < rsi < 70:
                score += 20  # RSI 健康區間加分
            elif rsi >= 70:
                score -= 10  # 超買扣分

            results.append({
                "symbol": symbol,
                "price": closes[-1],
                "price_change": round(price_change, 2),
                "vol_ratio": round(vol_ratio, 2),
                "rsi": rsi,
                "score": round(score, 1),
            })
        except:
            pass
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:8]

@app.post("/algo/start")
def start_strategy(symbol: str = "AAPL", qty: int = 1):
    if strategy_state["running"]:
        return {"status": "already running"}
    strategy_state["running"] = True
    strategy_state["symbol"] = symbol.upper()
    strategy_state["qty"] = qty
    t = threading.Thread(target=run_strategy, daemon=True)
    t.start()
    return {"status": "started", "symbol": symbol, "qty": qty}

@app.post("/algo/stop")
def stop_strategy():
    strategy_state["running"] = False
    return {"status": "stopped"}

@app.get("/algo/logs")
def get_logs():
    return {"running": strategy_state["running"], "symbol": strategy_state["symbol"], "logs": strategy_state["logs"]}
