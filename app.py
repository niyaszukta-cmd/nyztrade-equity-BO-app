"""
NYZTrade Equity Screener — Multi-Timeframe Swing & Breakout Screener
Author: NYZTrade Analytics | Dr. Niyas N
Version: 1.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import json
import os
import time
import pickle
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NYZTrade Equity Screener",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Dark Trading Terminal Theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

.stApp {
    background: #0a0e1a;
    color: #e2e8f0;
}

.main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px 30px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 60%);
}
.main-header h1 {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2rem;
    background: linear-gradient(90deg, #818cf8, #c084fc, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.main-header p {
    color: #64748b;
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    margin: 4px 0 0 0;
}

.metric-card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #6366f1; }
.metric-card .value {
    font-size: 1.8rem;
    font-weight: 800;
    color: #a5b4fc;
    font-family: 'Space Mono', monospace;
}
.metric-card .label {
    font-size: 0.7rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}

.breakout-badge {
    background: linear-gradient(90deg, #7c3aed, #db2777);
    color: white;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
}
.bullish-badge {
    background: #064e3b;
    color: #34d399;
    border: 1px solid #065f46;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
}
.bearish-badge {
    background: #450a0a;
    color: #f87171;
    border: 1px solid #7f1d1d;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
}
.neutral-badge {
    background: #1c1917;
    color: #a8a29e;
    border: 1px solid #44403c;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
}

.fii-positive { color: #34d399; font-weight: 700; font-family: 'Space Mono', monospace; }
.fii-negative { color: #f87171; font-weight: 700; font-family: 'Space Mono', monospace; }

.stDataFrame { font-size: 0.82rem; }
[data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid #1f2937;
}
.stTab [data-baseweb="tab"] {
    font-family: 'Syne', sans-serif;
    font-weight: 600;
}
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    border-radius: 8px;
    padding: 8px 20px;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #818cf8, #a78bfa);
    transform: translateY(-1px);
}
.status-bar {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 8px;
    padding: 10px 16px;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    color: #6366f1;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
CACHE_DIR = ".nyztrade_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

NIFTY_50 = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
    "HINDUNILVR.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","KOTAKBANK.NS",
    "LT.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS",
    "TITAN.NS","WIPRO.NS","ULTRACEMCO.NS","BAJFINANCE.NS","NESTLEIND.NS",
    "POWERGRID.NS","NTPC.NS","HCLTECH.NS","M&M.NS","ONGC.NS",
    "TATAMOTORS.NS","ADANIENT.NS","JSWSTEEL.NS","TATASTEEL.NS","BAJAJFINSV.NS",
    "TECHM.NS","DIVISLAB.NS","CIPLA.NS","DRREDDY.NS","EICHERMOT.NS",
    "BPCL.NS","COALINDIA.NS","HEROMOTOCO.NS","GRASIM.NS","BRITANNIA.NS",
    "INDUSINDBK.NS","SHREECEM.NS","HINDALCO.NS","SBILIFE.NS","HDFCLIFE.NS",
    "ADANIPORTS.NS","TATACONSUM.NS","APOLLOHOSP.NS","UPL.NS","BAJAJ-AUTO.NS"
]

NIFTY_NEXT50 = [
    "AMBUJACEM.NS","AUROPHARMA.NS","BANDHANBNK.NS","BERGEPAINT.NS","BIOCON.NS",
    "BOSCHLTD.NS","CHOLAFIN.NS","COLPAL.NS","DABUR.NS","DMART.NS",
    "GAIL.NS","GODREJCP.NS","HAVELLS.NS","ICICIPRULI.NS","ICICIGI.NS",
    "INDUSTOWER.NS","JINDALSTEL.NS","JUBLFOOD.NS","LUPIN.NS","MCDOWELL-N.NS",
    "MFSL.NS","MOTHERSON.NS","MPHASIS.NS","MRF.NS","NAUKRI.NS",
    "NMDC.NS","OBEROIRLTY.NS","PAGEIND.NS","PEL.NS","PERSISTENT.NS",
    "PETRONET.NS","PFC.NS","PIDILITIND.NS","PNB.NS","RECLTD.NS",
    "SAIL.NS","SIEMENS.NS","SRF.NS","TORNTPHARM.NS","TRENT.NS",
    "TVSMOTOR.NS","UBL.NS","VEDL.NS","VOLTAS.NS","WHIRLPOOL.NS",
    "YESBANK.NS","ZYDUSLIFE.NS","IDFCFIRSTB.NS","POLICYBZR.NS","NYKAA.NS"
]

MIDCAP_SAMPLE = [
    "AAPL","ABCAPITAL.NS","ACC.NS","AFFLE.NS","ANGELONE.NS",
    "ASHOKLEY.NS","ASTRAL.NS","ATUL.NS","AUBANK.NS","BALRAMCHIN.NS",
    "BATAINDIA.NS","BHARATFORG.NS","BHEL.NS","BLUESTARCO.NS","CANBK.NS",
    "CANFINHOME.NS","CESC.NS","CHAMBLFERT.NS","COFORGE.NS","CONCOR.NS",
    "CROMPTON.NS","CUMMINSIND.NS","DEEPAKNITR.NS","DELTACORP.NS","DIXON.NS",
    "EDELWEISS.NS","EMAMILTD.NS","ESCORTS.NS","EXIDEIND.NS","FEDERALBNK.NS",
    "FINOLEXIND.NS","FORCEMOT.NS","FORTIS.NS","GLENMARK.NS","GNFC.NS",
    "GODREJIND.NS","GRANULES.NS","GRAPHITE.NS","GRINDWELL.NS","GSPL.NS",
    "GULFOILLUB.NS","HAL.NS","HFCL.NS","HINDZINC.NS","HONAUT.NS",
    "IEX.NS","IFBIND.NS","IPCALAB.NS","IRB.NS","IRCTC.NS"
]

# ─────────────────────────────────────────────
# TECHNICAL INDICATORS
# ─────────────────────────────────────────────
def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def compute_atr(high, low, close, period=14):
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(com=period - 1, min_periods=period).mean()

def compute_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def compute_macd(series: pd.Series):
    ema12 = compute_ema(series, 12)
    ema26 = compute_ema(series, 26)
    macd = ema12 - ema26
    signal = compute_ema(macd, 9)
    hist = macd - signal
    return macd, signal, hist

def compute_bbands(series: pd.Series, period=20, std=2):
    sma = series.rolling(period).mean()
    sd = series.rolling(period).std()
    upper = sma + std * sd
    lower = sma - std * sd
    return upper, sma, lower

def compute_stochastic(high, low, close, k=14, d=3):
    lowest_low = low.rolling(k).min()
    highest_high = high.rolling(k).max()
    pct_k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    pct_d = pct_k.rolling(d).mean()
    return pct_k, pct_d

def compute_adx(high, low, close, period=14):
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    up_move = high.diff()
    down_move = -low.diff()
    pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr = tr.ewm(com=period - 1, min_periods=period).mean()
    di_pos = 100 * pd.Series(pos_dm, index=high.index).ewm(com=period-1, min_periods=period).mean() / atr
    di_neg = 100 * pd.Series(neg_dm, index=high.index).ewm(com=period-1, min_periods=period).mean() / atr
    dx = 100 * (di_pos - di_neg).abs() / (di_pos + di_neg).replace(0, np.nan)
    adx = dx.ewm(com=period-1, min_periods=period).mean()
    return adx

def add_volume_ma(df: pd.DataFrame, period=20) -> pd.DataFrame:
    df["vol_ma"] = df["Volume"].rolling(period).mean()
    df["vol_ratio"] = df["Volume"] / df["vol_ma"].replace(0, np.nan)
    return df

# ─────────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def fetch_ohlcv(ticker: str, interval: str = "1d", period: str = "1y") -> Optional[pd.DataFrame]:
    try:
        df = yf.download(ticker, interval=interval, period=period,
                         auto_adjust=True, progress=False, timeout=10)
        if df is None or len(df) < 30:
            return None
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df.dropna(inplace=True)
        return df
    except Exception:
        return None

def fetch_batch(tickers: list, interval: str, period: str, max_workers: int = 10):
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(fetch_ohlcv, t, interval, period): t for t in tickers}
        for future in as_completed(future_map):
            ticker = future_map[future]
            try:
                data = future.result()
                if data is not None and len(data) > 30:
                    results[ticker] = data
            except Exception:
                pass
    return results

# ─────────────────────────────────────────────
# FII / DII DATA (NSE India)
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fii_dii_nse() -> Optional[pd.DataFrame]:
    """
    Fetches FII/DII cash market activity from NSE India.
    Uses session + headers to pass NSE anti-bot checks.
    """
    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.nseindia.com/",
        }
        # Warm up cookies
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        time.sleep(1)
        url = "https://www.nseindia.com/api/fiidiiTradeReact"
        resp = session.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fii_dii_moneycontrol() -> Optional[pd.DataFrame]:
    """Fallback: scrape Moneycontrol FII/DII table."""
    try:
        url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        tables = pd.read_html(resp.text)
        if tables:
            df = tables[0]
            return df
    except Exception:
        pass
    return None

def get_fii_dii_data() -> Optional[pd.DataFrame]:
    df = fetch_fii_dii_nse()
    if df is not None and len(df) > 0:
        return df, "NSE India"
    df = fetch_fii_dii_moneycontrol()
    if df is not None:
        return df, "Moneycontrol"
    return None, None

# ─────────────────────────────────────────────
# GROQ AI RATINGS
# ─────────────────────────────────────────────
def get_groq_rating(ticker: str, df: pd.DataFrame, api_key: str) -> dict:
    """
    Uses Groq API with llama3-70b to generate a structured analyst-style rating.
    """
    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        # Prepare summary stats
        last = df.iloc[-1]
        prev = df.iloc[-2]
        sma50 = df["Close"].rolling(50).mean().iloc[-1]
        sma200 = df["Close"].rolling(200).mean().iloc[-1] if len(df) > 200 else None
        rsi = compute_rsi(df["Close"]).iloc[-1]
        vol_ratio = df["Volume"].iloc[-1] / df["Volume"].rolling(20).mean().iloc[-1]
        chg_1d = (last["Close"] - prev["Close"]) / prev["Close"] * 100
        chg_5d = (last["Close"] - df["Close"].iloc[-6]) / df["Close"].iloc[-6] * 100 if len(df) > 6 else 0
        high_52w = df["High"].tail(252).max()
        low_52w = df["Low"].tail(252).min()
        from_high = (last["Close"] - high_52w) / high_52w * 100

        sma200_text = f"{sma200:.2f}" if sma200 is not None else "N/A"

        prompt = f"""You are a senior equity analyst. Analyze this NSE/BSE stock and give a structured rating.

Ticker: {ticker}
Current Price: ₹{last['Close']:.2f}
1-Day Change: {chg_1d:.2f}%
5-Day Change: {chg_5d:.2f}%
RSI(14): {rsi:.1f}
Volume Ratio (vs 20d avg): {vol_ratio:.2f}x
SMA50: {sma50:.2f} | SMA200: {sma200_text}
52W High: {high_52w:.2f} | 52W Low: {low_52w:.2f}
Distance from 52W High: {from_high:.1f}%

Respond ONLY in this exact JSON format:
{{
  "rating": "Strong Buy / Buy / Hold / Sell / Strong Sell",
  "score": <integer 1-10>,
  "target_1m": <price>,
  "stop_loss": <price>,
  "key_reason": "<one line reason>",
  "risk": "Low / Medium / High"
}}"""

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        text = response.choices[0].message.content.strip()
        # Extract JSON
        start = text.find("{")
        end = text.rfind("}") + 1
        result = json.loads(text[start:end])
        result["ticker"] = ticker
        return result
    except Exception as e:
        return {"ticker": ticker, "rating": "N/A", "score": 0,
                "target_1m": 0, "stop_loss": 0, "key_reason": str(e), "risk": "N/A"}

# ─────────────────────────────────────────────
# BREAKOUT SCREENER — CORE ENGINE
# ─────────────────────────────────────────────
def breakout_score(df: pd.DataFrame) -> dict:
    """
    Multi-condition breakout scoring. Returns score 0-10 and individual flags.
    Each condition adds points. Score >= 6 = actionable breakout.
    """
    if df is None or len(df) < 55:
        return None

    c = df["Close"]
    h = df["High"]
    l = df["Low"]
    v = df["Volume"]

    # Indicators
    ema9 = compute_ema(c, 9).iloc[-1]
    ema21 = compute_ema(c, 21).iloc[-1]
    ema50 = compute_ema(c, 50).iloc[-1]
    rsi = compute_rsi(c).iloc[-1]
    atr = compute_atr(h, l, c).iloc[-1]
    adx = compute_adx(h, l, c).iloc[-1]
    vol_avg20 = v.rolling(20).mean().iloc[-1]
    vol_ratio = v.iloc[-1] / vol_avg20 if vol_avg20 > 0 else 0

    price = c.iloc[-1]
    prev_close = c.iloc[-2]
    price_move = abs(price - prev_close)

    # 52-week high breakout
    high_52w = h.tail(252).max() if len(df) >= 252 else h.max()
    # Donchian 20-day high
    don_high_20 = h.tail(20).max()
    don_high_55 = h.tail(55).max()

    # Body quality
    candle_range = h.iloc[-1] - l.iloc[-1]
    candle_body = abs(c.iloc[-1] - df["Open"].iloc[-1])
    body_ratio = candle_body / candle_range if candle_range > 0 else 0

    # Score conditions (max 10 pts)
    conditions = {
        "ema_stack":        ema9 > ema21 > ema50,          # 2 pts — EMA bullish alignment
        "rsi_momentum":     55 <= rsi <= 78,                # 1.5 pts — momentum zone
        "volume_surge":     vol_ratio >= 1.8,               # 2 pts — volume expansion
        "price_breakout":   price >= don_high_55 * 0.999,  # 2 pts — 55-day breakout
        "atr_expansion":    price_move >= 1.2 * atr,        # 1 pt — ATR-significant move
        "adx_trend":        adx >= 22,                      # 1 pt — trending market
        "candle_quality":   body_ratio >= 0.55,             # 0.5 pt — strong candle
    }

    weights = {
        "ema_stack": 2.0,
        "rsi_momentum": 1.5,
        "volume_surge": 2.0,
        "price_breakout": 2.0,
        "atr_expansion": 1.0,
        "adx_trend": 1.0,
        "candle_quality": 0.5,
    }

    score = sum(weights[k] for k, v in conditions.items() if v)

    # Near 52W high bonus
    near_high = price >= high_52w * 0.97
    if near_high:
        score = min(10, score + 0.5)

    return {
        "score": round(score, 1),
        "price": round(price, 2),
        "ema9": round(ema9, 2),
        "ema21": round(ema21, 2),
        "ema50": round(ema50, 2),
        "rsi": round(rsi, 1),
        "vol_ratio": round(vol_ratio, 2),
        "atr": round(atr, 2),
        "adx": round(adx, 1),
        "body_ratio": round(body_ratio, 2),
        "high_52w": round(high_52w, 2),
        "don_high_55": round(don_high_55, 2),
        "near_52w_high": near_high,
        "signal": "🔥 BREAKOUT" if score >= 7 else ("⚡ WATCH" if score >= 5 else "—"),
        **{k: v for k, v in conditions.items()}
    }

# ─────────────────────────────────────────────
# SWING SCREENER — MULTI-TIMEFRAME
# ─────────────────────────────────────────────
def swing_analyze(ticker: str, df: pd.DataFrame, timeframe: str) -> Optional[dict]:
    if df is None or len(df) < 30:
        return None

    c = df["Close"]
    h = df["High"]
    l = df["Low"]
    v = df["Volume"]

    ema9 = compute_ema(c, 9).iloc[-1]
    ema21 = compute_ema(c, 21).iloc[-1]
    ema50 = compute_ema(c, 50).iloc[-1] if len(c) >= 50 else np.nan
    rsi = compute_rsi(c).iloc[-1]
    macd, signal, hist = compute_macd(c)
    bb_up, bb_mid, bb_low = compute_bbands(c)
    stoch_k, stoch_d = compute_stochastic(h, l, c)
    vol_ratio = v.iloc[-1] / v.rolling(20).mean().iloc[-1] if v.rolling(20).mean().iloc[-1] > 0 else 0

    price = c.iloc[-1]
    chg_pct = (price - c.iloc[-2]) / c.iloc[-2] * 100

    # Swing signal logic
    bullish = 0
    bearish = 0

    if ema9 > ema21:        bullish += 1
    else:                   bearish += 1
    if not np.isnan(ema50):
        if price > ema50:   bullish += 1
        else:               bearish += 1
    if rsi > 55:            bullish += 1
    elif rsi < 45:          bearish += 1
    if hist.iloc[-1] > 0:   bullish += 1
    else:                   bearish += 1
    if stoch_k.iloc[-1] > stoch_d.iloc[-1] and stoch_k.iloc[-1] < 80: bullish += 1
    if vol_ratio > 1.5:     bullish += 1

    if bullish >= 4:
        bias = "BULLISH"
    elif bearish >= 4:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    return {
        "Ticker": ticker,
        "Price": round(price, 2),
        "Chg%": round(chg_pct, 2),
        "RSI": round(rsi, 1),
        "EMA9": round(ema9, 2),
        "EMA21": round(ema21, 2),
        "MACD_Hist": round(hist.iloc[-1], 3),
        "Stoch_K": round(stoch_k.iloc[-1], 1),
        "Vol_Ratio": round(vol_ratio, 2),
        "BB_Pos%": round((price - bb_low.iloc[-1]) / (bb_up.iloc[-1] - bb_low.iloc[-1]) * 100, 1) if bb_up.iloc[-1] != bb_low.iloc[-1] else 50,
        "Bias": bias,
        "Score": bullish,
    }

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:16px 0;">
        <div style="font-family:'Syne',sans-serif; font-weight:800; font-size:1.4rem;
             background:linear-gradient(90deg,#818cf8,#c084fc); -webkit-background-clip:text;
             -webkit-text-fill-color:transparent;">📡 NYZTrade</div>
        <div style="font-size:0.65rem; color:#475569; font-family:'Space Mono',monospace;">
            EQUITY SCREENER v1.0</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎯 Universe")
    universe_choice = st.selectbox("Select Universe", [
        "Nifty 50",
        "Nifty 50 + Next 50",
        "Nifty 50 + Next 50 + Midcap",
        "Custom Tickers",
    ])

    custom_tickers = []
    if universe_choice == "Custom Tickers":
        custom_input = st.text_area(
            "Enter tickers (comma-separated, add .NS for NSE)",
            "RELIANCE.NS,TCS.NS,INFY.NS",
            height=100
        )
        custom_tickers = [t.strip().upper() for t in custom_input.split(",") if t.strip()]

    if universe_choice == "Nifty 50":
        UNIVERSE = NIFTY_50
    elif universe_choice == "Nifty 50 + Next 50":
        UNIVERSE = NIFTY_50 + NIFTY_NEXT50
    elif universe_choice == "Nifty 50 + Next 50 + Midcap":
        UNIVERSE = NIFTY_50 + NIFTY_NEXT50 + MIDCAP_SAMPLE
    else:
        UNIVERSE = custom_tickers if custom_tickers else NIFTY_50

    # Load from uploaded CSV
    uploaded_file = st.file_uploader("📂 Upload Ticker CSV (column: ticker)", type=["csv"])
    if uploaded_file:
        try:
            df_tickers = pd.read_csv(uploaded_file)
            col = df_tickers.columns[0]
            UNIVERSE = df_tickers[col].dropna().str.strip().str.upper().tolist()
            st.success(f"✅ Loaded {len(UNIVERSE)} tickers")
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown(f"**Universe size:** `{len(UNIVERSE)}` tickers")

    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    max_workers = st.slider("Parallel threads", 5, 20, 10)
    min_breakout_score = st.slider("Min Breakout Score", 4.0, 9.0, 6.0, 0.5)
    min_vol_ratio = st.slider("Min Volume Ratio", 1.0, 5.0, 1.5, 0.25)

    st.markdown("---")
    st.markdown("### 🤖 Groq AI Ratings")
    groq_api_key = st.text_input("Groq API Key", type="password",
                                  placeholder="gsk_...")
    groq_tickers_input = st.text_input("Tickers for AI Rating (comma-sep)",
                                        "RELIANCE.NS,TCS.NS,INFY.NS")

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.65rem; color:#374151; text-align:center; font-family:'Space Mono',monospace;">
    © 2025 NYZTrade Analytics<br>Dr. Niyas N | Kerala, India
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📡 NYZTrade Equity Screener</h1>
    <p>Multi-Timeframe Swing & Breakout Analytics | FII/DII Flow | AI Ratings</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔥 Breakout Screener",
    "📈 Swing Screener",
    "🏦 FII / DII Flow",
    "🤖 AI Broker Ratings",
    "🔬 Stock Deep Dive"
])

# ════════════════════════════════════════════════
# TAB 1 — BREAKOUT SCREENER
# ════════════════════════════════════════════════
with tab1:
    st.markdown("### 🔥 Breakout Screener")
    st.markdown("""
    <div class="status-bar">
    STRATEGY: EMA Stack + Volume Surge (≥1.8x) + 55-Day Donchian Breakout + RSI Momentum Zone + ADX Trend Confirmation + ATR Expansion + Candle Quality
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        tf_breakout = st.selectbox("Timeframe", ["Daily", "1 Hour", "15 Min"], key="tf_break")
    with col2:
        period_map = {"Daily": "1y", "1 Hour": "60d", "15 Min": "5d"}
        interval_map = {"Daily": "1d", "1 Hour": "1h", "15 Min": "15m"}
        st.metric("Universe", f"{len(UNIVERSE)} stocks")

    run_breakout = st.button("🚀 Run Breakout Scan", use_container_width=True)

    if run_breakout:
        interval = interval_map[tf_breakout]
        period = period_map[tf_breakout]

        progress = st.progress(0, text="Initializing scan...")
        status_box = st.empty()

        results = []
        batch_size = 50
        batches = [UNIVERSE[i:i+batch_size] for i in range(0, len(UNIVERSE), batch_size)]

        for i, batch in enumerate(batches):
            status_box.markdown(f"<div class='status-bar'>Scanning batch {i+1}/{len(batches)}: {batch[0]} → {batch[-1]}</div>", unsafe_allow_html=True)
            data = fetch_batch(batch, interval, period, max_workers)
            for ticker, df in data.items():
                res = breakout_score(df)
                if res and res["score"] >= min_breakout_score:
                    res["ticker"] = ticker
                    results.append(res)
            progress.progress((i + 1) / len(batches), text=f"Scanned {min((i+1)*batch_size, len(UNIVERSE))}/{len(UNIVERSE)}")

        progress.empty()
        status_box.empty()

        if results:
            results.sort(key=lambda x: x["score"], reverse=True)

            # Summary metrics
            strong_breaks = sum(1 for r in results if r["score"] >= 7)
            watch = sum(1 for r in results if 5 <= r["score"] < 7)

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f'<div class="metric-card"><div class="value">{len(results)}</div><div class="label">Setups Found</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-card"><div class="value" style="color:#f472b6">{strong_breaks}</div><div class="label">🔥 Breakouts</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="metric-card"><div class="value" style="color:#fbbf24">{watch}</div><div class="label">⚡ Watch List</div></div>', unsafe_allow_html=True)
            with m4:
                st.markdown(f'<div class="metric-card"><div class="value">{len(UNIVERSE)}</div><div class="label">Stocks Scanned</div></div>', unsafe_allow_html=True)

            st.markdown("")

            # Results table
            display_cols = ["ticker", "signal", "score", "price", "rsi", "vol_ratio",
                            "adx", "ema9", "ema21", "ema50", "body_ratio", "high_52w"]

            df_results = pd.DataFrame(results)[display_cols]
            df_results.columns = ["Ticker", "Signal", "Score", "Price", "RSI",
                                   "Vol Ratio", "ADX", "EMA9", "EMA21", "EMA50",
                                   "Body Ratio", "52W High"]

            def color_signal(val):
                if "BREAKOUT" in str(val):
                    return "background-color:#2d1b4e; color:#c084fc; font-weight:bold"
                elif "WATCH" in str(val):
                    return "background-color:#1c1a00; color:#fbbf24"
                return ""

            def color_score(val):
                if val >= 7: return "color:#f472b6; font-weight:bold"
                if val >= 5: return "color:#fbbf24"
                return ""

            styled = df_results.style\
                .map(color_signal, subset=["Signal"])\
                .map(color_score, subset=["Score"])\
                .format({"Price": "₹{:.2f}", "Score": "{:.1f}", "RSI": "{:.1f}",
                         "Vol Ratio": "{:.2f}x", "ADX": "{:.1f}",
                         "Body Ratio": "{:.2f}", "52W High": "₹{:.2f}"})\
                .set_properties(**{"background-color": "#111827", "color": "#e2e8f0"})

            st.dataframe(styled, use_container_width=True, height=500)

            # Download
            csv = df_results.to_csv(index=False)
            st.download_button("⬇️ Download Breakout List CSV", csv,
                               f"nyztrade_breakout_{tf_breakout.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                               "text/csv")

            # Condition heatmap
            st.markdown("#### 🔍 Condition Breakdown (Top 20)")
            cond_cols = ["ticker", "ema_stack", "rsi_momentum", "volume_surge",
                         "price_breakout", "atr_expansion", "adx_trend", "candle_quality"]
            df_cond = pd.DataFrame(results[:20])[cond_cols]
            df_cond.columns = ["Ticker", "EMA Stack", "RSI Zone", "Vol Surge",
                                "Price BRK", "ATR Expand", "ADX Trend", "Candle"]
            df_cond_display = df_cond.set_index("Ticker")
            st.dataframe(
                df_cond_display.style.map(
                    lambda v: "background-color:#064e3b;color:#34d399" if v else "background-color:#450a0a;color:#f87171"
                ).set_properties(**{"background-color": "#111827", "color": "#e2e8f0", "font-family": "Space Mono"}),
                use_container_width=True
            )
        else:
            st.info(f"No breakouts found with score ≥ {min_breakout_score}. Try lowering the minimum score or expanding the universe.")

# ════════════════════════════════════════════════
# TAB 2 — SWING SCREENER
# ════════════════════════════════════════════════
with tab2:
    st.markdown("### 📈 Multi-Timeframe Swing Screener")

    col1, col2 = st.columns(2)
    with col1:
        swing_tf = st.selectbox("Timeframe", ["Daily (1d)", "1 Hour (1h)", "15 Min (15m)"], key="swing_tf")
        tf_to_interval = {"Daily (1d)": ("1d", "1y"), "1 Hour (1h)": ("1h", "60d"), "15 Min (15m)": ("15m", "5d")}
        sw_interval, sw_period = tf_to_interval[swing_tf]
    with col2:
        bias_filter = st.multiselect("Filter Bias", ["BULLISH", "NEUTRAL", "BEARISH"],
                                      default=["BULLISH"])

    run_swing = st.button("📊 Run Swing Scan", use_container_width=True)

    if run_swing:
        prog = st.progress(0)
        results_sw = []
        batch_size = 50
        batches = [UNIVERSE[i:i+batch_size] for i in range(0, len(UNIVERSE), batch_size)]

        for i, batch in enumerate(batches):
            data = fetch_batch(batch, sw_interval, sw_period, max_workers)
            for ticker, df in data.items():
                res = swing_analyze(ticker, df, swing_tf)
                if res and res["Bias"] in bias_filter:
                    results_sw.append(res)
            prog.progress((i + 1) / len(batches))

        prog.empty()

        if results_sw:
            df_sw = pd.DataFrame(results_sw).sort_values("Score", ascending=False)

            # Badge rendering
            def bias_badge(val):
                if val == "BULLISH": return "background-color:#064e3b; color:#34d399; font-weight:bold"
                if val == "BEARISH": return "background-color:#450a0a; color:#f87171; font-weight:bold"
                return "color:#a8a29e"

            m1, m2, m3 = st.columns(3)
            bullish_cnt = len(df_sw[df_sw["Bias"]=="BULLISH"])
            bearish_cnt = len(df_sw[df_sw["Bias"]=="BEARISH"])
            neutral_cnt = len(df_sw[df_sw["Bias"]=="NEUTRAL"])
            with m1: st.markdown(f'<div class="metric-card"><div class="value fii-positive">{bullish_cnt}</div><div class="label">Bullish</div></div>', unsafe_allow_html=True)
            with m2: st.markdown(f'<div class="metric-card"><div class="value fii-negative">{bearish_cnt}</div><div class="label">Bearish</div></div>', unsafe_allow_html=True)
            with m3: st.markdown(f'<div class="metric-card"><div class="value">{neutral_cnt}</div><div class="label">Neutral</div></div>', unsafe_allow_html=True)

            st.markdown("")
            styled_sw = df_sw.style\
                .map(bias_badge, subset=["Bias"])\
                .format({"Price": "₹{:.2f}", "Chg%": "{:.2f}%", "RSI": "{:.1f}",
                         "Vol_Ratio": "{:.2f}x", "BB_Pos%": "{:.1f}%",
                         "MACD_Hist": "{:.4f}", "Stoch_K": "{:.1f}"})\
                .set_properties(**{"background-color": "#111827", "color": "#e2e8f0"})

            st.dataframe(styled_sw, use_container_width=True, height=500)
            csv = df_sw.to_csv(index=False)
            st.download_button("⬇️ Download Swing Scan CSV", csv,
                               f"nyztrade_swing_{sw_interval}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
        else:
            st.info("No results. Try changing the bias filter or timeframe.")

# ════════════════════════════════════════════════
# TAB 3 — FII / DII FLOW
# ════════════════════════════════════════════════
with tab3:
    st.markdown("### 🏦 FII / DII Cash Market Flow")
    st.markdown("""
    <div class="status-bar">
    DATA SOURCE: NSE India API (primary) → Moneycontrol (fallback) | Refreshes every hour
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Fetch FII/DII Data", use_container_width=True):
        with st.spinner("Fetching institutional flow data..."):
            df_flow, source = get_fii_dii_data()

        if df_flow is not None and len(df_flow) > 0:
            st.success(f"✅ Data fetched from: **{source}**")
            st.dataframe(
                df_flow.style.set_properties(**{"background-color": "#111827", "color": "#e2e8f0"}),
                use_container_width=True,
                height=400
            )

            # Try to plot if columns exist
            try:
                # NSE API format: date, fiiNet, diiNet or similar
                col_candidates_fii = [c for c in df_flow.columns if "fii" in c.lower() or "FII" in c]
                col_candidates_dii = [c for c in df_flow.columns if "dii" in c.lower() or "DII" in c]
                date_col = [c for c in df_flow.columns if "date" in c.lower() or "Date" in c]

                if col_candidates_fii and date_col:
                    chart_df = df_flow[[date_col[0], col_candidates_fii[0]]].copy()
                    if col_candidates_dii:
                        chart_df[col_candidates_dii[0]] = df_flow[col_candidates_dii[0]]
                    chart_df = chart_df.set_index(date_col[0])
                    chart_df = chart_df.apply(pd.to_numeric, errors="coerce").dropna()

                    if len(chart_df) > 0:
                        st.markdown("#### Net FII / DII Activity (₹ Crore)")
                        st.bar_chart(chart_df, use_container_width=True)
            except Exception:
                pass

            csv_flow = df_flow.to_csv(index=False)
            st.download_button("⬇️ Download FII/DII CSV", csv_flow,
                               f"fii_dii_{datetime.now().strftime('%Y%m%d')}.csv")
        else:
            st.warning("""
            ⚠️ Could not fetch live FII/DII data. This usually happens because:
            - NSE India blocks automated requests (cookie/bot protection)
            - Network restrictions in your deployment environment

            **Solutions:**
            1. Run locally — NSE API works best from Indian IPs
            2. Use [NSE India website](https://www.nseindia.com/market-data/fii-dii-trade) directly
            3. Subscribe to a data vendor (Nifty Trader, Sensibull)
            """)

    st.markdown("---")
    st.markdown("#### 📌 FII/DII Interpretation Guide")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        **Bullish Signals:**
        - FII Net Buying > ₹500 Cr for 3+ consecutive days
        - DII net buying even when FII sells (retail + domestic strength)
        - Both FII & DII buying simultaneously = strong rally signal
        """)
    with col_b:
        st.markdown("""
        **Bearish Signals:**
        - FII Net Selling > ₹1000 Cr for 3+ days
        - FII selling + DII not buying = market weakness
        - Sudden spike in FII selling = possible macro event
        """)

# ════════════════════════════════════════════════
# TAB 4 — AI BROKER RATINGS
# ════════════════════════════════════════════════
with tab4:
    st.markdown("### 🤖 AI Broker Ratings (Groq LLaMA)")
    st.markdown("""
    <div class="status-bar">
    ENGINE: Groq llama3-70b-8192 | Generates analyst-style ratings with price targets and stop-loss levels
    </div>
    """, unsafe_allow_html=True)

    if not groq_api_key:
        st.info("🔑 Enter your Groq API key in the sidebar to enable AI ratings. Get a free key at console.groq.com")
    else:
        rating_tickers = [t.strip().upper() for t in groq_tickers_input.split(",") if t.strip()]
        st.markdown(f"**Tickers queued:** {', '.join(f'`{t}`' for t in rating_tickers)}")

        if st.button("🤖 Generate AI Ratings", use_container_width=True):
            ai_results = []
            prog_ai = st.progress(0)

            for i, ticker in enumerate(rating_tickers):
                with st.spinner(f"Analyzing {ticker}..."):
                    df_ai = fetch_ohlcv(ticker, "1d", "6mo")
                    if df_ai is not None and len(df_ai) > 30:
                        rating = get_groq_rating(ticker, df_ai, groq_api_key)
                        ai_results.append(rating)
                    else:
                        ai_results.append({"ticker": ticker, "rating": "NO DATA",
                                           "score": 0, "target_1m": 0,
                                           "stop_loss": 0, "key_reason": "Insufficient data", "risk": "N/A"})
                prog_ai.progress((i + 1) / len(rating_tickers))

            prog_ai.empty()

            df_ai_res = pd.DataFrame(ai_results)

            def rating_color(val):
                colors = {
                    "Strong Buy": "background-color:#064e3b;color:#34d399;font-weight:bold",
                    "Buy": "background-color:#065f46;color:#6ee7b7",
                    "Hold": "background-color:#1c1917;color:#a8a29e",
                    "Sell": "background-color:#7f1d1d;color:#fca5a5",
                    "Strong Sell": "background-color:#450a0a;color:#f87171;font-weight:bold",
                }
                for k, v in colors.items():
                    if k.lower() in str(val).lower():
                        return v
                return ""

            def risk_color(val):
                if val == "Low": return "color:#34d399"
                if val == "High": return "color:#f87171"
                return "color:#fbbf24"

            styled_ai = df_ai_res.style\
                .map(rating_color, subset=["rating"])\
                .map(risk_color, subset=["risk"])\
                .format({"target_1m": lambda x: f"₹{x:.2f}" if x else "N/A",
                         "stop_loss": lambda x: f"₹{x:.2f}" if x else "N/A"})\
                .set_properties(**{"background-color": "#111827", "color": "#e2e8f0"})

            st.dataframe(styled_ai, use_container_width=True)

            # Individual rating cards
            st.markdown("#### 📋 Rating Cards")
            cols = st.columns(min(len(ai_results), 3))
            for idx, r in enumerate(ai_results):
                with cols[idx % 3]:
                    score_color = "#34d399" if r.get("score", 0) >= 7 else ("#fbbf24" if r.get("score", 0) >= 5 else "#f87171")
                    st.markdown(f"""
                    <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;
                                padding:16px;margin-bottom:12px;">
                        <div style="font-family:'Space Mono';font-size:0.9rem;color:#818cf8;font-weight:700">
                            {r.get('ticker','')}</div>
                        <div style="font-size:1.1rem;font-weight:800;margin:6px 0">{r.get('rating','')}</div>
                        <div style="font-size:1.5rem;font-weight:800;color:{score_color};
                             font-family:'Space Mono'">{r.get('score',0)}/10</div>
                        <div style="font-size:0.72rem;color:#64748b;margin-top:8px">
                            Target: ₹{r.get('target_1m',0):.2f} | SL: ₹{r.get('stop_loss',0):.2f}</div>
                        <div style="font-size:0.72rem;color:#94a3b8;margin-top:4px;
                             border-top:1px solid #1f2937;padding-top:6px">
                            {r.get('key_reason','')}</div>
                    </div>
                    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════
# TAB 5 — STOCK DEEP DIVE
# ════════════════════════════════════════════════
with tab5:
    st.markdown("### 🔬 Individual Stock Deep Dive")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        dd_ticker = st.text_input("Ticker", "RELIANCE.NS", key="dd_ticker").upper().strip()
    with col2:
        dd_tf = st.selectbox("Timeframe", ["Daily", "1 Hour", "15 Min"], key="dd_tf")
    with col3:
        dd_period_map = {"Daily": "1y", "1 Hour": "60d", "15 Min": "5d"}
        dd_interval_map = {"Daily": "1d", "1 Hour": "1h", "15 Min": "15m"}

    load_dd = st.button("🔍 Analyze", use_container_width=True)

    if load_dd and dd_ticker:
        with st.spinner(f"Loading {dd_ticker}..."):
            df_dd = fetch_ohlcv(dd_ticker, dd_interval_map[dd_tf], dd_period_map[dd_tf])

        if df_dd is not None and len(df_dd) > 30:
            c = df_dd["Close"]
            h = df_dd["High"]
            l = df_dd["Low"]
            v = df_dd["Volume"]

            # Compute all indicators
            ema9 = compute_ema(c, 9)
            ema21 = compute_ema(c, 21)
            ema50 = compute_ema(c, 50)
            rsi = compute_rsi(c)
            macd_line, sig_line, hist = compute_macd(c)
            bb_up, bb_mid, bb_low = compute_bbands(c)
            atr = compute_atr(h, l, c)
            adx = compute_adx(h, l, c)
            stoch_k, stoch_d = compute_stochastic(h, l, c)
            vol_ratio = v / v.rolling(20).mean()

            # Run breakout score
            brk = breakout_score(df_dd)

            # Metrics row
            price = c.iloc[-1]
            prev_price = c.iloc[-2]
            chg = (price - prev_price) / prev_price * 100
            high_52w = h.tail(252).max() if len(df_dd) >= 252 else h.max()
            low_52w = l.tail(252).min() if len(df_dd) >= 252 else l.min()

            m1, m2, m3, m4, m5, m6 = st.columns(6)
            with m1: st.metric("Price", f"₹{price:.2f}", f"{chg:+.2f}%")
            with m2: st.metric("RSI(14)", f"{rsi.iloc[-1]:.1f}")
            with m3: st.metric("ADX(14)", f"{adx.iloc[-1]:.1f}")
            with m4: st.metric("Vol Ratio", f"{vol_ratio.iloc[-1]:.2f}x")
            with m5: st.metric("52W High", f"₹{high_52w:.2f}")
            with m6: st.metric("ATR(14)", f"₹{atr.iloc[-1]:.2f}")

            # Breakout score display
            if brk:
                score_col = "#34d399" if brk["score"] >= 7 else ("#fbbf24" if brk["score"] >= 5 else "#94a3b8")
                st.markdown(f"""
                <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;
                            padding:16px;margin:12px 0;display:flex;align-items:center;gap:20px">
                    <div>
                        <div style="font-size:2rem;font-weight:800;color:{score_col};
                             font-family:'Space Mono'">{brk['score']}/10</div>
                        <div style="font-size:0.7rem;color:#64748b">BREAKOUT SCORE</div>
                    </div>
                    <div style="font-size:1.2rem;font-weight:700">{brk['signal']}</div>
                    <div style="font-size:0.8rem;color:#94a3b8">
                        EMA9 {'✅' if brk['ema_stack'] else '❌'} &nbsp;|&nbsp;
                        RSI {'✅' if brk['rsi_momentum'] else '❌'} &nbsp;|&nbsp;
                        Volume {'✅' if brk['volume_surge'] else '❌'} &nbsp;|&nbsp;
                        Breakout {'✅' if brk['price_breakout'] else '❌'} &nbsp;|&nbsp;
                        ATR {'✅' if brk['atr_expansion'] else '❌'} &nbsp;|&nbsp;
                        ADX {'✅' if brk['adx_trend'] else '❌'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Charts using Streamlit native
            st.markdown("#### Price + EMAs")
            chart_df = pd.DataFrame({
                "Close": c,
                "EMA9": ema9,
                "EMA21": ema21,
                "EMA50": ema50,
                "BB_Upper": bb_up,
                "BB_Lower": bb_low,
            }).tail(100)
            st.line_chart(chart_df, use_container_width=True, height=300)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### RSI(14)")
                rsi_chart = pd.DataFrame({"RSI": rsi}).tail(100)
                st.line_chart(rsi_chart, use_container_width=True, height=200)

            with col_b:
                st.markdown("#### MACD")
                macd_chart = pd.DataFrame({"MACD": macd_line, "Signal": sig_line, "Histogram": hist}).tail(100)
                st.line_chart(macd_chart, use_container_width=True, height=200)

            st.markdown("#### Volume Ratio")
            vol_chart = pd.DataFrame({"Vol_Ratio": vol_ratio}).tail(100)
            st.area_chart(vol_chart, use_container_width=True, height=150)

            # Raw data
            with st.expander("📋 Raw OHLCV Data"):
                st.dataframe(df_dd.tail(50).style.set_properties(**{"background-color": "#111827", "color": "#e2e8f0"}),
                             use_container_width=True)

        else:
            st.error(f"Could not load data for `{dd_ticker}`. Check the ticker symbol and try again.")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;font-size:0.7rem;color:#374151;font-family:'Space Mono',monospace;padding:10px">
    NYZTrade Analytics | Dr. Niyas N | Kerala, India | @NYZTrade<br>
    <span style="color:#1f2937">Disclaimer: For educational purposes only. Not financial advice.</span>
</div>
""", unsafe_allow_html=True)
