import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px

# Configure Streamlit page
st.set_page_config(
    page_title="SpikeTrade Performance",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for authentication
if 'owner_authenticated' not in st.session_state:
    st.session_state.owner_authenticated = False

# Display logo and header
col1, col2 = st.columns([1, 4])
with col1:
    try:
        st.image("website/static/logo2.jpg", width=80)
    except:
        st.image("static/logo2.jpg", width=80)

with col2:
    st.title("SpikeTrade Performance")
    st.markdown("*Real-time trading performance and historical trade analysis*")

st.divider()

# Custom CSS for professional styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 14px;
        opacity: 0.9;
    }
    .win-trade {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0;
    }
    .loss-trade {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0;
    }
    .neutral-trade {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# Data management
DATA_DIR = Path("website/data")
DATA_DIR.mkdir(exist_ok=True)
TRADES_FILE = DATA_DIR / "trades.json"

def load_trades():
    """Load trades from JSON file"""
    if TRADES_FILE.exists():
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_trades(trades):
    """Save trades to JSON file"""
    with open(TRADES_FILE, 'w') as f:
        json.dump(trades, f, indent=2, default=str)

def add_trade(symbol, entry_price, exit_price, entry_time, exit_time, trade_type, status, notes=""):
    """Add a new trade"""
    trades = load_trades()
    
    pnl = (exit_price - entry_price) if exit_price else 0
    pnl_percent = (pnl / entry_price * 100) if entry_price else 0
    
    trade = {
        "id": len(trades) + 1,
        "symbol": symbol.upper(),
        "entry_price": float(entry_price),
        "exit_price": float(exit_price) if exit_price else None,
        "entry_time": entry_time.isoformat() if isinstance(entry_time, datetime) else entry_time,
        "exit_time": exit_time.isoformat() if isinstance(exit_time, datetime) else exit_time,
        "type": trade_type,  # BUY or SELL
        "status": status,     # OPEN or CLOSED
        "pnl": pnl,
        "pnl_percent": pnl_percent,
        "notes": notes,
        "recorded_at": datetime.now().isoformat()
    }
    
    trades.append(trade)
    save_trades(trades)
    return trade

def get_performance_metrics(trades_df):
    """Calculate performance metrics"""
    if trades_df.empty:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "avg_pnl": 0,
            "best_trade": 0,
            "worst_trade": 0
        }
    
    closed_trades = trades_df[trades_df['status'] == 'CLOSED']
    
    if closed_trades.empty:
        closed_trades = trades_df
    
    winning = (closed_trades['pnl'] > 0).sum()
    losing = (closed_trades['pnl'] < 0).sum()
    total = len(closed_trades)
    
    return {
        "total_trades": len(trades_df),
        "winning_trades": winning,
        "losing_trades": losing,
        "win_rate": (winning / total * 100) if total > 0 else 0,
        "total_pnl": closed_trades['pnl'].sum(),
        "avg_pnl": closed_trades['pnl'].mean(),
        "best_trade": closed_trades['pnl'].max(),
        "worst_trade": closed_trades['pnl'].min()
    }

# Sidebar - Owner login
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔒 Owner Access")

if not st.session_state.owner_authenticated:
    password = st.sidebar.text_input("Owner Password", type="password", key="owner_pwd_input")
    if password:
        try:
            correct_password = st.secrets.get("owner_password", "")
            if password == correct_password:
                st.session_state.owner_authenticated = True
                st.sidebar.success("✅ Authenticated!")
                st.rerun()
            else:
                st.sidebar.error("❌ Incorrect password")
        except:
            st.sidebar.warning("⚠️ Password not configured")
else:
    if st.sidebar.button("🔓 Logout"):
        st.session_state.owner_authenticated = False
        st.rerun()
    st.sidebar.success("✅ You're logged in as owner")

st.sidebar.markdown("---")

# Main app navigation
page = st.sidebar.radio("Navigation", ["Dashboard", "Trade History", "Add Trade", "Analytics"])

# Load trades
trades_data = load_trades()
trades_df = pd.DataFrame(trades_data) if trades_data else pd.DataFrame()

if not trades_df.empty:
    trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
    trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])

# Dashboard page
if page == "Dashboard":
    st.header("Performance Summary")
    
    if trades_data:
        metrics = get_performance_metrics(trades_df)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Trades", int(metrics['total_trades']), 
                     delta=f"{metrics['win_rate']:.1f}% Win Rate")
        
        with col2:
            color = "🟢" if metrics['winning_trades'] > metrics['losing_trades'] else "🔴"
            st.metric(f"{color} Winning / Losing", 
                     f"{int(metrics['winning_trades'])} / {int(metrics['losing_trades'])}")
        
        with col3:
            pnl_color = "green" if metrics['total_pnl'] > 0 else "red"
            st.metric("Total P&L", f"${metrics['total_pnl']:.2f}", 
                     delta_color=pnl_color if metrics['total_pnl'] > 0 else "red")
        
        with col4:
            st.metric("Avg P&L per Trade", f"${metrics['avg_pnl']:.2f}")
        
        # Recent trades - Live Ticker Style
        st.subheader("📺 Live Trade Ticker")
        recent = trades_df.tail(15).sort_values('entry_time', ascending=False)
        
        # Create columns for ticker display
        ticker_cols = st.columns([1, 2, 2, 2, 2])
        with ticker_cols[0]:
            st.markdown("**TIME**")
        with ticker_cols[1]:
            st.markdown("**SYMBOL / TYPE**")
        with ticker_cols[2]:
            st.markdown("**ENTRY → EXIT**")
        with ticker_cols[3]:
            st.markdown("**P&L**")
        with ticker_cols[4]:
            st.markdown("**STATUS**")
        
        st.divider()
        
        for _, trade in recent.iterrows():
            color_class = "win-trade" if trade['pnl'] > 0 else "loss-trade" if trade['pnl'] < 0 else "neutral-trade"
            pnl_sign = "+" if trade['pnl'] > 0 else ""
            status_badge = "✅ CLOSED" if trade['status'] == 'CLOSED' else "⏳ OPEN"
            status_color = "green" if trade['status'] == 'CLOSED' else "blue"
            pnl_color = "green" if trade['pnl'] > 0 else "red" if trade['pnl'] < 0 else "gray"
            
            ticker_cols = st.columns([1, 2, 2, 2, 2])
            
            with ticker_cols[0]:
                st.caption(trade['entry_time'].strftime("%H:%M:%S"))
            
            with ticker_cols[1]:
                st.markdown(f"**{trade['symbol']}** \n{trade['type']}")
            
            with ticker_cols[2]:
                st.caption(f"${trade['entry_price']:.2f} → ${trade['exit_price']:.2f}")
            
            with ticker_cols[3]:
                st.markdown(f"<span style='color:{pnl_color}'><b>{pnl_sign}${trade['pnl']:.2f}</b></span> \n({pnl_sign}{trade['pnl_percent']:.2f}%)", 
                           unsafe_allow_html=True)
            
            with ticker_cols[4]:
                st.markdown(f"<span style='color:{status_color}'>{status_badge}</span>", 
                           unsafe_allow_html=True)
    else:
        st.info("No trades recorded yet. Use 'Add Trade' to record your first trade.")

# Trade History page
elif page == "Trade History":
    st.header("Trade History")
    
    if trades_data:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            symbol_filter = st.multiselect("Filter by Symbol", 
                                          options=trades_df['symbol'].unique(),
                                          default=trades_df['symbol'].unique())
        
        with col2:
            status_filter = st.multiselect("Filter by Status",
                                          options=trades_df['status'].unique(),
                                          default=trades_df['status'].unique())
        
        with col3:
            date_filter = st.date_input("From Date", value=trades_df['entry_time'].min())
        
        # Apply filters
        filtered_df = trades_df[
            (trades_df['symbol'].isin(symbol_filter)) &
            (trades_df['status'].isin(status_filter)) &
            (trades_df['entry_time'] >= pd.Timestamp(date_filter))
        ].sort_values('entry_time', ascending=False)
        
        if not filtered_df.empty:
            # Display table
            display_df = filtered_df[[
                'symbol', 'type', 'entry_price', 'exit_price', 
                'pnl', 'pnl_percent', 'status', 'entry_time'
            ]].copy()
            
            display_df.columns = ['Symbol', 'Type', 'Entry', 'Exit', 'P&L', 'P&L %', 'Status', 'Date']
            
            # Format numbers
            display_df['Entry'] = display_df['Entry'].apply(lambda x: f"${x:.2f}")
            display_df['Exit'] = display_df['Exit'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "-")
            display_df['P&L'] = display_df['P&L'].apply(lambda x: f"${x:.2f}")
            display_df['P&L %'] = display_df['P&L %'].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Summary statistics for filtered data
            st.subheader("Filtered Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Trades", len(filtered_df))
            
            with col2:
                total_pnl = filtered_df['pnl'].sum()
                st.metric("Total P&L", f"${total_pnl:.2f}")
            
            with col3:
                win_rate = (filtered_df['pnl'] > 0).sum() / len(filtered_df) * 100
                st.metric("Win Rate", f"{win_rate:.1f}%")
        else:
            st.info("No trades match the selected filters.")
    else:
        st.info("No trade history available.")

# Add Trade page
elif page == "Add Trade":
    if not st.session_state.owner_authenticated:
        st.error("🔒 **Owner authentication required to add trades**")
        st.info("Please enter your owner password in the left sidebar to unlock trade recording.")
    else:
        st.header("Record a New Trade")
        st.success("✅ You are authenticated as owner")
        
        with st.form("trade_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                symbol = st.text_input("Symbol (e.g., AAPL)", "")
                trade_type = st.selectbox("Trade Type", ["BUY", "SELL"])
                entry_price = st.number_input("Entry Price ($)", min_value=0.01, step=0.01)
                entry_time = st.datetime_input("Entry Time", value=datetime.now())
            
            with col2:
                exit_price = st.number_input("Exit Price ($)", min_value=0.01, step=0.01)
                status = st.selectbox("Status", ["CLOSED", "OPEN"])
                exit_time = st.datetime_input("Exit Time", value=datetime.now())
                notes = st.text_area("Notes (optional)")
            
            submitted = st.form_submit_button("✅ Record Trade")
            
            if submitted:
                if symbol and entry_price and exit_price:
                    trade = add_trade(symbol, entry_price, exit_price, entry_time, exit_time, 
                                     trade_type, status, notes)
                    st.success(f"✅ Trade recorded! P&L: ${trade['pnl']:.2f} ({trade['pnl_percent']:.2f}%)")
                    st.balloons()
                else:
                    st.error("Please fill in all required fields")

# Analytics page
elif page == "Analytics":
    st.header("Performance Analytics")
    
    if trades_data and not trades_df.empty:
        metrics = get_performance_metrics(trades_df)
        
        # Performance overview
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
        with col2:
            st.metric("Best Trade", f"${metrics['best_trade']:.2f}")
        with col3:
            st.metric("Worst Trade", f"${metrics['worst_trade']:.2f}")
        with col4:
            # Safe profit factor calculation
            try:
                if metrics['losing_trades'] > 0 and metrics['worst_trade'] != 0:
                    pf = (metrics['best_trade'] * metrics['winning_trades']) / abs(metrics['worst_trade'] * metrics['losing_trades'])
                    st.metric("Profit Factor", f"{pf:.2f}")
                else:
                    st.metric("Profit Factor", "N/A")
            except:
                st.metric("Profit Factor", "N/A")
        
        # Charts - with error handling
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                # P&L by trade
                if len(trades_df) > 0:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        y=trades_df['symbol'],
                        x=trades_df['pnl'],
                        marker_color=['green' if x > 0 else 'red' for x in trades_df['pnl']],
                        orientation='h'
                    ))
                    fig.update_layout(title="P&L by Trade", xaxis_title="P&L ($)", height=400)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Win vs Loss distribution
                if metrics['winning_trades'] > 0 or metrics['losing_trades'] > 0:
                    win_loss = pd.Series({
                        'Winning Trades': max(1, int(metrics['winning_trades'])),
                        'Losing Trades': max(1, int(metrics['losing_trades']))
                    })
                    fig = go.Figure(data=[go.Pie(
                        labels=win_loss.index,
                        values=win_loss.values,
                        marker=dict(colors=['green', 'red'])
                    )])
                    fig.update_layout(title="Win/Loss Distribution", height=400)
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not generate charts: {str(e)}")
        
        # Cumulative P&L
        try:
            if len(trades_df) > 0:
                trades_df_sorted = trades_df.sort_values('entry_time')
                trades_df_sorted['cumulative_pnl'] = trades_df_sorted['pnl'].cumsum()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=trades_df_sorted['entry_time'],
                    y=trades_df_sorted['cumulative_pnl'],
                    mode='lines+markers',
                    name='Cumulative P&L',
                    line=dict(color='blue', width=2),
                    fill='tozeroy'
                ))
                fig.update_layout(
                    title="Cumulative P&L Over Time",
                    xaxis_title="Date",
                    yaxis_title="Cumulative P&L ($)",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not generate cumulative chart: {str(e)}")
        
        # Trades by symbol
        try:
            if len(trades_df) > 0:
                symbol_summary = trades_df.groupby('symbol').agg({
                    'pnl': ['sum', 'count', 'mean']
                }).round(2)
                symbol_summary.columns = ['Total P&L', 'Trades', 'Avg P&L']
                
                st.subheader("Performance by Symbol")
                st.dataframe(symbol_summary, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not generate symbol summary: {str(e)}")
    else:
        st.info("📊 No analytics available yet. Add some trades to see performance metrics!")

# Footer
st.markdown("---")
st.markdown("🚀 SpikeTrade | Real-time Trading Performance Dashboard")
