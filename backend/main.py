from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests, time
from datetime import date, timedelta, datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "https://*.vercel.app", "https://bloomberg-terminal-1-622z.onrender.com"], allow_methods=["*"], allow_headers=["*"])

FINNHUB_KEY = "dahso4hr01qvl9br4mq0dahso4hr01qvl9br4mqg"
FINNHUB = "https://finnhub.io/api/v1"
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart"
HEADERS = {"User-Agent": "Mozilla/5.0"}
_cache = {}

# 監控股票清單：科技、金融、醫療、能源、消費、ETF
WATCHLIST = [
    # 科技
    'AAPL','MSFT','GOOGL','AMZN','META','NVDA','AMD','INTC','ORCL','CRM',
    'TSLA','NFLX','UBER','SPOT','COIN','PLTR','SNOW','SHOP','SQ','PYPL',
    # 金融
    'JPM','BAC','GS','MS','V','MA','BRK-B','AXP','C','WFC',
    # 醫療
    'JNJ','PFE','UNH','ABBV','MRK','LLY','TMO','ABT','AMGN','GILD',
    # 能源
    'XOM','CVX','COP','SLB','EOG','OXY','MPC','PSX',
    # 消費 / 零售
    'WMT','TGT','COST','HD','NKE','SBUX','MCD','DIS','AMZN',
    # ETF
    'SPY','QQQ','IWM','DIA','GLD','SLV','TLT','XLF','XLE','XLK',
]
# 去重
WATCHLIST = list(dict.fromkeys(WATCHLIST))

# 台股監控清單
TW_WATCHLIST = [
    # 半導體
    '2330.TW','2303.TW','2308.TW','2317.TW','2354.TW','2379.TW','2344.TW','3711.TW',
    # 電子/科技
    '2382.TW','2357.TW','2376.TW','2395.TW','3045.TW','2409.TW','2337.TW','2301.TW',
    # 金融
    '2882.TW','2881.TW','2886.TW','2884.TW','2891.TW','2892.TW','2883.TW','2880.TW',
    # 傳產/製造
    '1301.TW','1303.TW','1326.TW','2002.TW','1101.TW','2912.TW','2207.TW','2105.TW',
    # ETF
    '0050.TW','0056.TW','00878.TW','00881.TW','006208.TW',
]

TW_SECTORS = {
    "半導體": ['2330.TW','2303.TW','2308.TW','2354.TW','2379.TW','2344.TW','3711.TW'],
    "電子製造": ['2317.TW','2382.TW','2357.TW','2376.TW','2395.TW','2409.TW','2301.TW'],
    "金融": ['2882.TW','2881.TW','2886.TW','2884.TW','2891.TW','2892.TW','2883.TW'],
    "傳產": ['1301.TW','1303.TW','1326.TW','2002.TW','1101.TW','2207.TW'],
    "ETF": ['0050.TW','0056.TW','00878.TW','00881.TW','006208.TW'],
}

def cached(key, fn, ttl=60):
    now = time.time()
    if key in _cache and now - _cache[key]["ts"] < ttl:
        return _cache[key]["data"]
    data = fn()
    _cache[key] = {"data": data, "ts": now}
    return data

@app.get("/tw/stocks/{symbol}")
def get_tw_stock(symbol: str):
    symbol = symbol.upper()
    tw_sym = symbol if symbol.endswith('.TW') else f"{symbol}.TW"
    r = requests.get(f"{YAHOO}/{tw_sym}", params={"interval": "1d", "range": "5d"}, headers=HEADERS, timeout=10)
    data = r.json()
    result = data.get("chart", {}).get("result")
    if not result:
        raise HTTPException(status_code=404, detail="Symbol not found")
    meta = result[0].get("meta", {})
    price = meta.get("regularMarketPrice", 0)
    prev = meta.get("chartPreviousClose") or meta.get("previousClose") or price
    change = round(price - prev, 2)
    change_pct = round((price - prev) / prev * 100, 2) if prev else 0
    name = meta.get("shortName") or meta.get("symbol") or symbol
    return {
        "symbol": symbol,
        "name": name,
        "price": price,
        "change": change,
        "change_pct": change_pct,
        "currency": "TWD",
        "volume": meta.get("regularMarketVolume", 0),
    }

@app.get("/tw/stocks/{symbol}/history")
def get_tw_history(symbol: str, period: str = "1mo"):
    symbol = symbol.upper()
    tw_sym = symbol if symbol.endswith('.TW') else f"{symbol}.TW"
    range_map = {"5d": "5d", "1mo": "1mo", "3mo": "3mo", "6mo": "6mo", "1y": "1y"}
    yrange = range_map.get(period, "1mo")
    def fetch():
        r = requests.get(f"{YAHOO}/{tw_sym}", params={"interval": "1d", "range": yrange}, headers=HEADERS, timeout=10)
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
    return cached(f"tw_hist_{symbol}_{period}", fetch, ttl=300)

@app.get("/tw/stocks/{symbol}/indicators")
def get_tw_indicators(symbol: str, period: str = "1mo"):
    history = get_tw_history(symbol, period)
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

@app.get("/tw/stocks/{symbol}/signal")
def get_tw_signal(symbol: str):
    return get_tw_signal_logic(symbol)

def get_tw_signal_logic(symbol: str):
    symbol = symbol.upper()
    try:
        history = get_tw_history(symbol, "1mo")
        closes = [d["close"] for d in history]
        if len(closes) < 20:
            return {"signal": "WAIT", "reason": "數據不足", "score": 0}
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        changes = [closes[i]-closes[i-1] for i in range(1, len(closes))]
        gains = sum(c for c in changes[-14:] if c > 0)
        losses = sum(-c for c in changes[-14:] if c < 0)
        rsi = 100.0 if losses == 0 else round(100-(100/(1+gains/losses)), 2)
        trend = "up" if closes[-1] > closes[-5] else "down"
        score = 0; reasons = []
        if ma5 > ma20: score += 2; reasons.append("MA5 > MA20 ✓")
        else: score -= 2; reasons.append("MA5 < MA20 ✗")
        if rsi < 70: score += 1; reasons.append(f"RSI={rsi:.1f} 未超買 ✓")
        else: score -= 2; reasons.append(f"RSI={rsi:.1f} 超買 ✗")
        if rsi > 30: score += 1
        else: score -= 1; reasons.append(f"RSI={rsi:.1f} 超賣")
        if trend == "up": score += 1; reasons.append("近5日上漲趨勢 ✓")
        else: score -= 1; reasons.append("近5日下跌趨勢 ✗")
        signal = "BUY" if score >= 3 else "SELL" if score <= -2 else "HOLD"
        return {"signal": signal, "score": score, "ma5": round(ma5, 2), "ma20": round(ma20, 2),
                "rsi": rsi, "price": closes[-1], "reasons": reasons}
    except Exception as e:
        return {"signal": "ERROR", "reason": str(e), "score": 0}

@app.get("/tw/news/{symbol}")
def get_tw_news(symbol: str):
    # 用股票名稱搜尋 Finnhub 新聞（台股用英文代號搜尋）
    tw_sym = symbol.upper().replace('.TW', '')
    def fetch():
        r = requests.get(f"{FINNHUB}/company-news", params={
            "symbol": tw_sym, "from": (date.today()-timedelta(days=7)).isoformat(),
            "to": date.today().isoformat(), "token": FINNHUB_KEY}, timeout=10)
        items = r.json() if isinstance(r.json(), list) else []
        return [{"title": n.get("headline"), "url": n.get("url"),
                 "published": date.fromtimestamp(n.get("datetime", 0)).isoformat()} for n in items[:10]]
    return cached(f"tw_news_{symbol}", fetch, ttl=300)

def _tw_scan_helper(watchlist, period="1mo"):
    """共用台股歷史資料取得"""
    results = {}
    for symbol in watchlist:
        try:
            hist = get_tw_history(symbol, period)
            if hist:
                results[symbol] = hist
        except:
            pass
    return results

@app.get("/tw/scan/buy")
def scan_tw_buy():
    results = []
    for symbol in TW_WATCHLIST:
        try:
            hist = get_tw_history(symbol, "1mo")
            closes = [d["close"] for d in hist]
            if len(closes) < 20: continue
            ma5 = sum(closes[-5:]) / 5
            ma20 = sum(closes[-20:]) / 20
            changes = [closes[i]-closes[i-1] for i in range(1, len(closes))]
            gains = sum(c for c in changes[-14:] if c > 0)
            losses = sum(-c for c in changes[-14:] if c < 0)
            rsi = 100.0 if losses == 0 else round(100-(100/(1+gains/losses)), 2)
            if ma5 > ma20 and 40 <= rsi <= 65 and closes[-1] > closes[-5]:
                results.append({"symbol": symbol, "price": closes[-1], "rsi": rsi,
                                 "ma5": round(ma5,2), "ma20": round(ma20,2),
                                 "change_pct": round((closes[-1]-closes[-5])/closes[-5]*100, 2)})
        except: pass
    return sorted(results, key=lambda x: x["rsi"])

@app.get("/tw/scan/hot")
def scan_tw_hot():
    results = []
    for symbol in TW_WATCHLIST:
        try:
            hist = get_tw_history(symbol, "5d")
            if len(hist) < 2: continue
            closes = [d["close"] for d in hist]
            volumes = [d["volume"] for d in hist]
            price_change = (closes[-1] - closes[0]) / closes[0] * 100
            recent_vol = sum(volumes[-2:]) / 2
            prev_vol = sum(volumes[:-2]) / max(len(volumes)-2, 1)
            vol_ratio = recent_vol / prev_vol if prev_vol > 0 else 1
            changes = [closes[i]-closes[i-1] for i in range(1, len(closes))]
            gains = sum(c for c in changes if c > 0)
            losses = sum(-c for c in changes if c < 0)
            rsi = 100.0 if losses == 0 else round(100-(100/(1+gains/losses)), 2)
            score = min(price_change*10, 30) + min((vol_ratio-1)*20, 30)
            if 40 < rsi < 70: score += 20
            elif rsi >= 70: score -= 10
            results.append({"symbol": symbol, "price": closes[-1],
                             "price_change": round(price_change,2),
                             "vol_ratio": round(vol_ratio,2), "rsi": rsi, "score": round(score,1)})
        except: pass
    return sorted(results, key=lambda x: x["score"], reverse=True)[:8]

@app.get("/tw/scan/{mode}")
def scan_tw(mode: str):
    """台股版選股篩選：macd / bollinger / volume / drawdown / 52week / divergence / sector"""
    results = []
    period_map = {"macd":"3mo","bollinger":"1mo","volume":"1mo","drawdown":"6mo","52week":"1y","divergence":"3mo","sector":"1mo"}
    period = period_map.get(mode, "1mo")

    watchlist = TW_WATCHLIST
    sectors = TW_SECTORS

    for symbol in watchlist:
        try:
            hist = get_tw_history(symbol, period)
            closes = [d["close"] for d in hist]
            volumes = [d["volume"] for d in hist if d.get("volume",0) > 0]
            if len(closes) < 20: continue

            if mode == "52week":
                if len(closes) < 50: continue
                high_52 = max(closes); low_52 = min(closes); current = closes[-1]
                pct = (current - high_52) / high_52 * 100
                if current >= high_52 * 0.98:
                    results.append({"symbol": symbol, "price": current, "high_52": round(high_52,2),
                                     "low_52": round(low_52,2), "pct_from_high": round(pct,2),
                                     "type": "突破新高" if current >= high_52 else "接近新高"})

            elif mode == "divergence":
                def rsi_series(data, n=14):
                    out = [None]*n
                    for i in range(n, len(data)):
                        ch = [data[j]-data[j-1] for j in range(i-n+1,i+1)]
                        g = sum(c for c in ch if c>0); l = sum(-c for c in ch if c<0)
                        out.append(100.0 if l==0 else round(100-(100/(1+g/l)),2))
                    return out
                rs = rsi_series(closes)
                valid = [(c,r) for c,r in zip(closes,rs) if r is not None]
                if len(valid) < 20: continue
                mid = len(valid)//2
                pc=[v[0] for v in valid[:mid]]; cc=[v[0] for v in valid[mid:]]
                pr=[v[1] for v in valid[:mid]]; cr=[v[1] for v in valid[mid:]]
                dtype = None
                if max(cc)>max(pc) and max(cr)<=max(pr): dtype="頂背離"
                elif min(cc)<min(pc) and min(cr)>=min(pr): dtype="底背離"
                if dtype:
                    results.append({"symbol":symbol,"price":closes[-1],"rsi":valid[-1][1],
                                     "type":dtype,"signal":"SELL" if dtype=="頂背離" else "BUY"})

            elif mode == "macd":
                def ema(data,n):
                    k=2/(n+1); e=[data[0]]
                    for p in data[1:]: e.append(p*k+e[-1]*(1-k))
                    return e
                e12=ema(closes,12); e26=ema(closes,26)
                macd=[a-b for a,b in zip(e12,e26)]; sig=ema(macd,9)
                if len(macd)>=2:
                    cross = "金叉" if macd[-2]<sig[-2] and macd[-1]>sig[-1] else "死叉" if macd[-2]>sig[-2] and macd[-1]<sig[-1] else None
                    if cross:
                        results.append({"symbol":symbol,"price":closes[-1],"macd":round(macd[-1],3),
                                         "signal_val":round(sig[-1],3),"cross":cross,
                                         "signal":"BUY" if cross=="金叉" else "SELL"})

            elif mode == "bollinger":
                ma20=sum(closes[-20:])/20
                std=(sum((c-ma20)**2 for c in closes[-20:])/20)**0.5
                upper=ma20+2*std; lower=ma20-2*std; cur=closes[-1]; prev=closes[-2]
                status=None
                if prev<=lower and cur>lower: status="下軌反彈"
                elif prev>=upper and cur<upper: status="上軌回落"
                elif cur>upper: status="突破上軌"
                elif cur<lower: status="跌破下軌"
                if status:
                    results.append({"symbol":symbol,"price":round(cur,2),"upper":round(upper,2),
                                     "lower":round(lower,2),"ma20":round(ma20,2),
                                     "bandwidth":round((upper-lower)/ma20*100,2),"status":status,
                                     "signal":"BUY" if status=="下軌反彈" else "SELL" if status=="上軌回落" else "WATCH"})

            elif mode == "volume":
                if len(volumes)<10: continue
                avg_vol=sum(volumes[-20:])/min(len(volumes),20)
                vol_ratio=volumes[-1]/avg_vol if avg_vol>0 else 1
                if vol_ratio>=1.8:
                    change=(closes[-1]-closes[-2])/closes[-2]*100
                    results.append({"symbol":symbol,"price":closes[-1],"volume":volumes[-1],
                                     "avg_volume":round(avg_vol),"vol_ratio":round(vol_ratio,2),
                                     "change_pct":round(change,2),"signal":"BUY" if change>0 else "SELL"})

            elif mode == "drawdown":
                peak=closes[0]; max_dd=0
                for c in closes:
                    if c>peak: peak=c
                    dd=(c-peak)/peak*100
                    if dd<max_dd: max_dd=dd
                recent_peak=max(closes[-60:]) if len(closes)>=60 else max(closes)
                from_peak=(closes[-1]-recent_peak)/recent_peak*100
                changes=[closes[i]-closes[i-1] for i in range(1,len(closes))]
                gains=sum(c for c in changes[-14:] if c>0)
                losses_=sum(-c for c in changes[-14:] if c<0)
                rsi=100.0 if losses_==0 else round(100-(100/(1+gains/losses_)),2)
                if from_peak<=-15 and rsi<45:
                    results.append({"symbol":symbol,"price":closes[-1],"max_drawdown":round(max_dd,2),
                                     "from_peak":round(from_peak,2),"rsi":rsi,
                                     "recent_peak":round(recent_peak,2),"recovery_potential":round(-from_peak,2)})
        except: pass

    if mode == "sector":
        results = []
        for sname, syms in sectors.items():
            changes = []
            for symbol in syms:
                try:
                    hist = get_tw_history(symbol, "1mo")
                    closes = [d["close"] for d in hist]
                    if len(closes)<5: continue
                    c1w=round((closes[-1]-closes[-5])/closes[-5]*100,2)
                    c1m=round((closes[-1]-closes[0])/closes[0]*100,2)
                    changes.append({"symbol":symbol,"price":closes[-1],"change_1w":c1w,"change_1m":c1m})
                except: pass
            if changes:
                avg_1w=round(sum(c["change_1w"] for c in changes)/len(changes),2)
                avg_1m=round(sum(c["change_1m"] for c in changes)/len(changes),2)
                results.append({"sector":sname,"avg_1w":avg_1w,"avg_1m":avg_1m,
                                 "top":sorted(changes,key=lambda x:x["change_1w"],reverse=True)[:3],
                                 "count":len(changes)})
        return sorted(results, key=lambda x: x["avg_1w"], reverse=True)

    if mode in ["52week","divergence"]:
        return sorted(results, key=lambda x: x.get("pct_from_high", 0), reverse=True)
    if mode == "volume":
        return sorted(results, key=lambda x: x["vol_ratio"], reverse=True)
    if mode == "drawdown":
        return sorted(results, key=lambda x: x["rsi"])
    return results

@app.get("/tw/marquee")
def get_tw_marquee():
    """台股跑馬燈"""
    symbols = ['2330.TW','0050.TW','2317.TW','2382.TW','2882.TW','2303.TW','2308.TW','1301.TW','2002.TW','0056.TW']
    results = []
    for sym in symbols:
        try:
            info = get_tw_stock(sym)
            results.append(info)
        except: pass
    return results

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

@app.get("/scan/buy")
def scan_buy():
    """根據 MA 交叉 + RSI + 趨勢篩選今日建議買入股票"""
    watchlist = WATCHLIST
    results = []
    for symbol in watchlist:
        try:
            hist = get_history(symbol, "1mo")
            closes = [d["close"] for d in hist]
            if len(closes) < 20:
                continue

            ma5 = sum(closes[-5:]) / 5
            ma20 = sum(closes[-20:]) / 20

            changes = [closes[i]-closes[i-1] for i in range(1, len(closes))]
            gains = sum(c for c in changes[-14:] if c > 0)
            losses = sum(-c for c in changes[-14:] if c < 0)
            rsi = 100.0 if losses == 0 else round(100-(100/(1+gains/losses)), 2)

            # 買入條件：MA5 > MA20、RSI 在 40~65 健康區間、近5日上漲
            if ma5 > ma20 and 40 <= rsi <= 65 and closes[-1] > closes[-5]:
                results.append({
                    "symbol": symbol,
                    "price": closes[-1],
                    "rsi": rsi,
                    "ma5": round(ma5, 2),
                    "ma20": round(ma20, 2),
                    "change_pct": round((closes[-1] - closes[-5]) / closes[-5] * 100, 2),
                })
        except:
            pass
    results.sort(key=lambda x: x["rsi"])  # RSI 越低越優先
    return results

@app.get("/scan/hot")
def scan_hot():
    """根據成交量、價格動能、RSI 找出最熱門股票"""
    watchlist = WATCHLIST
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

SECTORS = {
    "科技": ['AAPL','MSFT','GOOGL','NVDA','AMD','INTC','ORCL','CRM','PLTR','SNOW','SHOP','SQ','PYPL','COIN','META'],
    "金融": ['JPM','BAC','GS','MS','V','MA','AXP','C','WFC'],
    "醫療": ['JNJ','PFE','UNH','ABBV','MRK','LLY','TMO','ABT','AMGN','GILD'],
    "能源": ['XOM','CVX','COP','SLB','EOG','OXY'],
    "消費": ['WMT','TGT','COST','HD','NKE','SBUX','MCD','DIS'],
}

@app.get("/scan/52week")
def scan_52week():
    """找出突破或接近52週高點的股票"""
    results = []
    for symbol in WATCHLIST:
        try:
            hist = get_history(symbol, "1y")
            if len(hist) < 50:
                continue
            closes = [d["close"] for d in hist]
            high_52 = max(closes)
            low_52 = min(closes)
            current = closes[-1]
            pct_from_high = (current - high_52) / high_52 * 100
            pct_from_low = (current - low_52) / low_52 * 100
            # 突破：現價在52週高點的98%以上
            if current >= high_52 * 0.98:
                results.append({
                    "symbol": symbol,
                    "price": current,
                    "high_52": round(high_52, 2),
                    "low_52": round(low_52, 2),
                    "pct_from_high": round(pct_from_high, 2),
                    "pct_from_low": round(pct_from_low, 2),
                    "type": "突破新高" if current >= high_52 else "接近新高",
                })
        except:
            pass
    results.sort(key=lambda x: x["pct_from_high"], reverse=True)
    return results

@app.get("/scan/divergence")
def scan_divergence():
    """偵測價格與RSI背離（價格創新高但RSI未跟上 → 預警反轉）"""
    results = []
    for symbol in WATCHLIST:
        try:
            hist = get_history(symbol, "3mo")
            closes = [d["close"] for d in hist]
            if len(closes) < 30:
                continue

            def calc_rsi_series(data, n=14):
                rsi_vals = [None] * n
                for i in range(n, len(data)):
                    ch = [data[j]-data[j-1] for j in range(i-n+1, i+1)]
                    g = sum(c for c in ch if c > 0)
                    l = sum(-c for c in ch if c < 0)
                    rsi_vals.append(100.0 if l == 0 else round(100-(100/(1+g/l)), 2))
                return rsi_vals

            rsi_series = calc_rsi_series(closes)
            valid = [(c, r) for c, r in zip(closes, rsi_series) if r is not None]
            if len(valid) < 20:
                continue

            # 比較最近10根 vs 前10根
            mid = len(valid) // 2
            prev_closes = [v[0] for v in valid[:mid]]
            curr_closes = [v[0] for v in valid[mid:]]
            prev_rsi = [v[1] for v in valid[:mid]]
            curr_rsi = [v[1] for v in valid[mid:]]

            price_up = max(curr_closes) > max(prev_closes)
            rsi_up = max(curr_rsi) > max(prev_rsi)
            price_down = min(curr_closes) < min(prev_closes)
            rsi_down = min(curr_rsi) < min(prev_rsi)

            divergence_type = None
            if price_up and not rsi_up:
                divergence_type = "頂背離"  # 看跌
            elif price_down and not rsi_down:
                divergence_type = "底背離"  # 看漲

            if divergence_type:
                current_rsi = valid[-1][1]
                results.append({
                    "symbol": symbol,
                    "price": closes[-1],
                    "rsi": current_rsi,
                    "type": divergence_type,
                    "signal": "SELL" if divergence_type == "頂背離" else "BUY",
                })
        except:
            pass
    return results

@app.get("/scan/macd")
def scan_macd():
    """MACD 金叉/死叉掃描"""
    results = []
    for symbol in WATCHLIST:
        try:
            hist = get_history(symbol, "3mo")
            closes = [d["close"] for d in hist]
            if len(closes) < 35:
                continue

            def ema(data, n):
                k = 2 / (n + 1)
                e = [data[0]]
                for p in data[1:]:
                    e.append(p * k + e[-1] * (1 - k))
                return e

            ema12 = ema(closes, 12)
            ema26 = ema(closes, 26)
            macd = [a - b for a, b in zip(ema12, ema26)]
            signal = ema(macd, 9)
            hist_macd = [m - s for m, s in zip(macd, signal)]

            # 金叉：前一根 MACD < Signal，現在 MACD > Signal
            if len(hist_macd) >= 2:
                cross = None
                if macd[-2] < signal[-2] and macd[-1] > signal[-1]:
                    cross = "金叉"
                elif macd[-2] > signal[-2] and macd[-1] < signal[-1]:
                    cross = "死叉"
                if cross:
                    results.append({
                        "symbol": symbol,
                        "price": closes[-1],
                        "macd": round(macd[-1], 3),
                        "signal_val": round(signal[-1], 3),
                        "histogram": round(hist_macd[-1], 3),
                        "cross": cross,
                        "signal": "BUY" if cross == "金叉" else "SELL",
                    })
        except:
            pass
    return sorted(results, key=lambda x: x["signal"])

@app.get("/scan/bollinger")
def scan_bollinger():
    """布林通道突破掃描"""
    results = []
    for symbol in WATCHLIST:
        try:
            hist = get_history(symbol, "1mo")
            closes = [d["close"] for d in hist]
            if len(closes) < 20:
                continue

            ma20 = sum(closes[-20:]) / 20
            std = (sum((c - ma20) ** 2 for c in closes[-20:]) / 20) ** 0.5
            upper = ma20 + 2 * std
            lower = ma20 - 2 * std
            current = closes[-1]
            prev = closes[-2]

            status = None
            if prev <= lower and current > lower:
                status = "下軌反彈"
            elif prev >= upper and current < upper:
                status = "上軌回落"
            elif current > upper:
                status = "突破上軌"
            elif current < lower:
                status = "跌破下軌"

            if status:
                bw = round((upper - lower) / ma20 * 100, 2)  # 帶寬
                results.append({
                    "symbol": symbol,
                    "price": round(current, 2),
                    "upper": round(upper, 2),
                    "lower": round(lower, 2),
                    "ma20": round(ma20, 2),
                    "bandwidth": bw,
                    "status": status,
                    "signal": "BUY" if status in ["下軌反彈"] else ("SELL" if status in ["上軌回落"] else "WATCH"),
                })
        except:
            pass
    return results

@app.get("/scan/volume")
def scan_volume():
    """成交量暴增掃描（量比 > 2x）"""
    results = []
    for symbol in WATCHLIST:
        try:
            hist = get_history(symbol, "1mo")
            if len(hist) < 10:
                continue
            volumes = [d["volume"] for d in hist if d["volume"] > 0]
            closes = [d["close"] for d in hist]
            if len(volumes) < 10:
                continue

            avg_vol = sum(volumes[-20:]) / min(len(volumes), 20)
            latest_vol = volumes[-1]
            vol_ratio = latest_vol / avg_vol if avg_vol > 0 else 1

            if vol_ratio >= 1.8:
                change = (closes[-1] - closes[-2]) / closes[-2] * 100
                results.append({
                    "symbol": symbol,
                    "price": closes[-1],
                    "volume": latest_vol,
                    "avg_volume": round(avg_vol),
                    "vol_ratio": round(vol_ratio, 2),
                    "change_pct": round(change, 2),
                    "signal": "BUY" if change > 0 else "SELL",
                })
        except:
            pass
    return sorted(results, key=lambda x: x["vol_ratio"], reverse=True)

@app.get("/scan/drawdown")
def scan_drawdown():
    """最大回撤掃描 — 找出回撤後可能反彈的股票"""
    results = []
    for symbol in WATCHLIST:
        try:
            hist = get_history(symbol, "6mo")
            closes = [d["close"] for d in hist]
            if len(closes) < 20:
                continue

            peak = closes[0]
            max_dd = 0
            for c in closes:
                if c > peak:
                    peak = c
                dd = (c - peak) / peak * 100
                if dd < max_dd:
                    max_dd = dd

            current = closes[-1]
            recent_peak = max(closes[-60:]) if len(closes) >= 60 else max(closes)
            from_peak = (current - recent_peak) / recent_peak * 100

            # 找大幅回撤後 RSI 低位，可能是反彈機會
            changes = [closes[i]-closes[i-1] for i in range(1, len(closes))]
            gains = sum(c for c in changes[-14:] if c > 0)
            losses = sum(-c for c in changes[-14:] if c < 0)
            rsi = 100.0 if losses == 0 else round(100-(100/(1+gains/losses)), 2)

            if from_peak <= -15 and rsi < 45:
                results.append({
                    "symbol": symbol,
                    "price": current,
                    "max_drawdown": round(max_dd, 2),
                    "from_peak": round(from_peak, 2),
                    "rsi": rsi,
                    "recent_peak": round(recent_peak, 2),
                    "recovery_potential": round(-from_peak, 2),
                })
        except:
            pass
    return sorted(results, key=lambda x: x["rsi"])

@app.get("/scan/sector")
def scan_sector():
    """板塊輪動：計算各板塊近期平均漲跌幅"""
    results = []
    for sector_name, symbols in SECTORS.items():
        changes = []
        for symbol in symbols:
            try:
                hist = get_history(symbol, "1mo")
                if len(hist) < 5:
                    continue
                closes = [d["close"] for d in hist]
                change_1w = (closes[-1] - closes[-5]) / closes[-5] * 100
                change_1m = (closes[-1] - closes[0]) / closes[0] * 100
                changes.append({"symbol": symbol, "price": closes[-1],
                                 "change_1w": round(change_1w, 2),
                                 "change_1m": round(change_1m, 2)})
            except:
                pass
        if changes:
            avg_1w = round(sum(c["change_1w"] for c in changes) / len(changes), 2)
            avg_1m = round(sum(c["change_1m"] for c in changes) / len(changes), 2)
            results.append({
                "sector": sector_name,
                "avg_1w": avg_1w,
                "avg_1m": avg_1m,
                "top": sorted(changes, key=lambda x: x["change_1w"], reverse=True)[:3],
                "count": len(changes),
            })
    results.sort(key=lambda x: x["avg_1w"], reverse=True)
    return results

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
