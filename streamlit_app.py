import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pytz
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Spiketrade", layout="wide")

CALIBRATED_WEIGHTS = {
    "price_roc": 0.44, "vwap": 0.25, "volume_spike": 0.49,
    "rsi_oversold": 0.85, "rvol_high": 0.44, "obv_roc": 0.51,
    "mfi": 0.67, "spike_quality": 0.48, "ema_downtrend": 0.46, "stoch_oversold": 0.47
}

TRADING_SETTINGS = {
    "buyPeriodMinutes": 48, "bbLengthMinutes": 24, "rsiLengthMinutes": 14,
    "priceRocPeriodMinutes": 20, "obvRocPeriodMinutes": 20, "mfiPeriodMinutes": 14,
    "vwapPeriodMinutes": 10, "spikePriceRocZThreshold": 1.0,
    "spikeRsiRocZThreshold": 0.5, "spikeObvRocZThreshold": 0.5, "spikeMfiRocZThreshold": 0.6,
    "spikePercentBRocZThreshold": 0.5, "spikeVwapRocZThreshold": 0.5, "spikeVolumeRocZThreshold": 0.5,
    "regularPriceRocThreshold": 2.0, "regularRsiRocThreshold": 5.0, "regularObvRocThreshold": 10.0,
    "regularMfiRocThreshold": 5.0, "regularPercentBRocThreshold": 15.0, "regularVwapRocThreshold": 1.5,
    "regularVolumeRocThreshold": 20.0, "comboSignalThreshold": 0.76, "highProbThreshold": 0.8,
    "stopLossPct": 0.02, "targetGainPercent": 2.0, "macdHistogramRocThreshold": 0.5,
    "stochasticOversoldThreshold": 30, "rvolThreshold": 1.2
}

class PennyBreakoutStrategy:
    def __init__(self):
        self.settings = TRADING_SETTINGS
        self.weights = CALIBRATED_WEIGHTS
    
    def calculate_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def calculate_ema(self, prices, period):
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        return macd_line, signal_line, macd_line - signal_line
    
    def calculate_signals(self, df):
        df = df.copy()
        df['RSI'] = self.calculate_rsi(df['Close'], self.settings['rsiLengthMinutes'])
        df['EMA_9'] = self.calculate_ema(df['Close'], 9)
        df['EMA_20'] = self.calculate_ema(df['Close'], 20)
        df['EMA_50'] = self.calculate_ema(df['Close'], 50)
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = self.calculate_macd(df['Close'])
        return df

def fetch_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1d", interval="1m", prepost=True)
        if df.empty:
            return None, "No data available"
        return df, None
    except Exception as e:
        return None, str(e)

def get_market_status():
    et_tz = pytz.timezone('US/Eastern')
    now = datetime.now(et_tz)
    current_time = now.time()
    weekday = now.weekday()
    
    if weekday >= 5:
        return "closed", "🚫 Weekend - Market Closed"
    
    from datetime import time
    if current_time < time(4, 0):
        return "closed", "🚫 Market Closed"
    elif current_time < time(9, 30):
        return "prepost", "🌅 Pre-Market"
    elif current_time < time(16, 0):
        return "open", "📈 Market Open"
    elif current_time < time(20, 0):
        return "prepost", "🌙 After-Hours"
    else:
        return "closed", "🚫 Market Closed"

# Header
st.markdown("<h1 style='text-align: center; color: #00D9FF;'>Spiketrade</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #999;'>Real-time buy/sell signals with 1-minute data</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📊 Market Status")
    status, status_text = get_market_status()
    et_tz = pytz.timezone('US/Eastern')
    current_time = datetime.now(et_tz).strftime('%H:%M ET')
    
    status_color = "🟢" if status == "open" else "🟡" if status == "prepost" else "🔴"
    st.markdown(f"**{status_color} {status_text}**")
    st.markdown(f"Current Time: **{current_time}**")
    
    st.divider()
    
    st.markdown("### ⚡ Quick Tickers")
    cols = st.columns(3)
    quick_tickers = ["MULN", "SNDL", "BBIG", "CLOV", "SOFI", "PLTR"]
    for i, ticker in enumerate(quick_tickers):
        with cols[i % 3]:
            if st.button(ticker, use_container_width=True):
                st.session_state.selected_ticker = ticker
    
    st.divider()
    
    st.markdown("### ⚙️ Strategy Settings")
    st.metric("Signal Threshold", f"{int(TRADING_SETTINGS['comboSignalThreshold']*100)}%")
    st.metric("High Probability", f"{int(TRADING_SETTINGS['highProbThreshold']*100)}%")
    st.metric("Stop Loss", f"{TRADING_SETTINGS['stopLossPct']*100}%")
    st.metric("Target Gain", f"{TRADING_SETTINGS['targetGainPercent']}%")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    ticker_input = st.text_input("Enter stock ticker (e.g., AAPL, TSLA):", 
                                  value=st.session_state.get('selected_ticker', ''),
                                  placeholder="MULN").upper()
    
    if st.button("Search", use_container_width=True):
        if ticker_input:
            st.session_state.selected_ticker = ticker_input
        else:
            st.warning("Please enter a ticker symbol")

if st.session_state.get('selected_ticker'):
    ticker = st.session_state['selected_ticker']
    
    with st.spinner(f"Loading {ticker} data..."):
        df, error = fetch_stock_data(ticker)
        
        if error:
            st.error(f"Error: {error}")
        elif df is not None:
            strategy = PennyBreakoutStrategy()
            df = strategy.calculate_signals(df)
            
            latest = df.iloc[-1]
            current_price = float(latest['Close'])
            open_price = float(df['Open'].iloc[0])
            day_change = ((current_price - open_price) / open_price * 100)
            
            # Display metrics
            with col2:
                st.metric("Current Price", f"${current_price:.2f}", f"{day_change:+.2f}%")
                st.metric("RSI", f"{latest['RSI']:.1f}")
                st.metric("MACD", f"{latest['MACD']:.4f}")
            
            # Candlestick chart
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               row_heights=[0.7, 0.3],
                               subplot_titles=("Price Action", "Volume"))
            
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name="Price",
                increasing_line_color='#00FF00',
                decreasing_line_color='#FF0000'
            ), row=1, col=1)
            
            fig.add_trace(go.Bar(
                x=df.index,
                y=df['Volume'],
                name="Volume",
                marker_color='rgba(100, 100, 255, 0.5)'
            ), row=2, col=1)
            
            # Add EMAs
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['EMA_9'],
                name="EMA 9",
                line=dict(color='#FFA500', width=1)
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['EMA_20'],
                name="EMA 20",
                line=dict(color='#0099FF', width=1)
            ), row=1, col=1)
            
            fig.update_layout(height=600, hovermode='x unified', 
                            template='plotly_dark', showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Technical indicators
            col_rsi, col_macd, col_ema = st.columns(3)
            
            with col_rsi:
                st.markdown("### RSI")
                rsi_level = "Oversold" if latest['RSI'] < 30 else "Neutral" if latest['RSI'] < 70 else "Overbought"
                st.info(f"{latest['RSI']:.1f} - {rsi_level}")
            
            with col_macd:
                st.markdown("### MACD")
                macd_signal = "Bullish" if latest['MACD'] > latest['MACD_Signal'] else "Bearish"
                st.info(f"{latest['MACD']:.4f}\n{macd_signal}")
            
            with col_ema:
                st.markdown("### EMA Trend")
                trend = "Uptrend" if latest['EMA_9'] > latest['EMA_20'] else "Downtrend"
                st.info(f"{trend}\n9:{latest['EMA_9']:.2f}")
else:
    st.info("👈 Enter a stock ticker to get started")
