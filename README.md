# SpikeTrade Performance Dashboard

A professional Streamlit-based dashboard for tracking and analyzing trading performance in real-time.

## Features

✅ **Live Trade Ticker** - CNN-style ticker display showing latest trades with symbol, time, entry/exit prices, P&L, and status

✅ **Performance Metrics** - Win rate, total P&L, best/worst trades, and profit factor

✅ **Trade History** - Searchable database of all trades with filtering by symbol, status, and date

✅ **Advanced Analytics** - Charts, cumulative P&L, and performance by symbol

✅ **Simple Trade Recording** - Add trades directly via web interface

## Setup

### Local Installation
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Streamlit Cloud Deployment
1. Push this `website` folder to GitHub
2. Go to [streamlit.io](https://streamlit.io)
3. Click "New app" and select this repository
4. Set main file path to `website/app.py`
5. Deploy!

## Usage

### Adding Trades
1. Navigate to "Add Trade" tab
2. Enter symbol, entry/exit prices, times, type (BUY/SELL), and status
3. Click "Record Trade"
4. Trade automatically appears in dashboard and history

### Viewing Dashboard
- **Dashboard** - Overview with key metrics and live 15-trade ticker
- **Trade History** - Full historical records with advanced filtering
- **Analytics** - Performance charts and statistical analysis

## Data Storage

Trades are stored in `data/trades.json` as local JSON file. For production Streamlit Cloud deployment, you may want to configure database integration (PostgreSQL, Supabase, etc.).

## File Structure
```
website/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── data/              # Trade data storage
    └── trades.json    # Trade records (auto-generated)
```

## Integration with SpikeTrade

The SpikeTrade trading application can post trades to this dashboard via:

1. **JSON API** - POST requests to add trades
2. **Direct JSON** - Write directly to `data/trades.json`
3. **Scheduled Imports** - Periodically sync trade logs

Example Python integration:
```python
import requests

trade_data = {
    "symbol": "AAPL",
    "entry_price": 150.25,
    "exit_price": 151.50,
    "entry_time": "2024-01-15 09:30:00",
    "exit_time": "2024-01-15 10:15:00",
    "type": "BUY",
    "status": "CLOSED",
    "notes": "Signal confidence 85%"
}

# Direct JSON file method (local)
import json
with open('data/trades.json', 'a') as f:
    json.dump(trade_data, f)
    f.write('\n')
```

## Live Ticker Features

The main dashboard displays a CNN-style ticker showing:
- **TIME** - When trade was executed
- **SYMBOL** - Stock ticker (e.g., AAPL, TSLA)
- **TYPE** - BUY or SELL
- **ENTRY → EXIT** - Price range
- **P&L** - Dollar amount and percentage (color-coded)
- **STATUS** - OPEN/CLOSED with visual indicator

Green highlights winners, red highlights losses, yellow for neutral.

## Performance Metrics Explained

- **Win Rate** - Percentage of profitable trades
- **Best/Worst Trade** - Largest gain and loss
- **Profit Factor** - Ratio of wins to losses
- **Cumulative P&L** - Running total over time

## Notes

- Trades are stored locally; move to `data/trades.json` for backup
- Compatible with SpikeTrade Java application exports
- Real-time dashboard updates on page refresh
- No external API keys required

---

Built for SpikeTrade trading system | Streamlit Dashboard
