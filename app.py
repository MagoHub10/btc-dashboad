import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.subplots as sp

# ✅ Fetch Bitcoin OHLC Data
@st.cache_data(ttl=1800)
def get_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc"
    params = {'vs_currency': 'usd', 'days': 365}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index("timestamp", inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching Bitcoin data: {e}")
        return None

# ✅ Fetch RSI & EMA from AlphaVantage API
@st.cache_data(ttl=1800)
def get_technical_indicators():
    API_KEY = "0RZD71ZFRAWYN55"
    base_url = "https://www.alphavantage.co/query"

    rsi_url = f"{base_url}?function=RSI&symbol=BTCUSD&interval=daily&time_period=14&series_type=close&apikey={API_KEY}"
    rsi_response = requests.get(rsi_url).json()
    rsi_data = rsi_response.get("Technical Analysis: RSI", {})

    ema_urls = {
        "EMA_7": f"{base_url}?function=EMA&symbol=BTCUSD&interval=daily&time_period=7&series_type=close&apikey={API_KEY}",
        "EMA_30": f"{base_url}?function=EMA&symbol=BTCUSD&interval=daily&time_period=30&series_type=close&apikey={API_KEY}",
        "EMA_60": f"{base_url}?function=EMA&symbol=BTCUSD&interval=daily&time_period=60&series_type=close&apikey={API_KEY}",
        "EMA_200": f"{base_url}?function=EMA&symbol=BTCUSD&interval=daily&time_period=200&series_type=close&apikey={API_KEY}"
    }

    ema_data = {}
    for key, url in ema_urls.items():
        response = requests.get(url).json()
        ema_data[key] = response.get("Technical Analysis: EMA", {})

    return {"RSI": rsi_data, **ema_data}

# ✅ AI Insights Function
def generate_ai_insights(selected_kpis):
    crypto_df = get_crypto_data()
    indicators = get_technical_indicators()

    if crypto_df is None or not indicators:
        return "❌ Error fetching market data."

    latest_price = crypto_df["close"].iloc[-1]
    
    latest_rsi = "N/A"
    if "RSI" in selected_kpis and "RSI" in indicators and indicators["RSI"]:
        rsi_values = [float(value) for value in indicators["RSI"].values() if value.replace('.', '', 1).isdigit()]
        latest_rsi = rsi_values[0] if rsi_values else "N/A"

    latest_ema = {key: float(list(value.values())[0]) for key, value in indicators.items() if key != "RSI" and key in selected_kpis}

    kpi_summary = f"RSI: {latest_rsi:.2f}\n" + "\n".join([f"{k}: {v:.2f}" for k, v in latest_ema.items()])

    return f"**Latest BTC Price:** ${latest_price:,.2f}\n\n🔹 **Key Indicators:**\n{kpi_summary}"

# ✅ Streamlit UI
st.set_page_config(layout="wide")
st.title("📊 Bitcoin Market Dashboard with AI Insights")

# ✅ Sidebar KPI Selection
st.sidebar.header("🔹 Select KPIs to Display")
kpi_options = ["RSI", "EMA_7", "EMA_30", "EMA_60", "EMA_200"]
selected_kpis = st.sidebar.multiselect("Choose indicators:", kpi_options, default=["EMA_30", "EMA_200"])

st.sidebar.subheader("📌 Selected KPIs")
st.sidebar.write(", ".join(selected_kpis))

# ✅ AI Insights Section
st.subheader("🤖 AI Market Insights")
insights_placeholder = st.empty()
if st.button("Generate Insights"):
    with st.spinner("Generating insights..."):
        insights = generate_ai_insights(selected_kpis)
        insights_placeholder.write(insights)

# ✅ Candlestick Chart & RSI (if selected)
crypto_df = get_crypto_data()
indicators = get_technical_indicators()

if crypto_df is not None:
    rows = 2 if "RSI" in selected_kpis else 1
    fig = sp.make_subplots(rows=rows, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3] if rows == 2 else [1], vertical_spacing=0.1)

    # ✅ Candlestick Chart
    fig.add_trace(go.Candlestick(x=crypto_df.index, open=crypto_df['open'], high=crypto_df['high'], low=crypto_df['low'], close=crypto_df['close'], increasing_line_color='green', decreasing_line_color='red', name="BTC Price"), row=1, col=1)

    # ✅ Separate RSI Subplot
    if "RSI" in selected_kpis:
        fig.add_trace(go.Scatter(x=rsi_dates, y=rsi_values, mode='lines', line=dict(color='blue'), name="RSI"), row=2, col=1)

    fig.update_layout(xaxis_rangeslider_visible=False)
    st.plotly_chart(fig)
else:
    st.error("❌ Error fetching Bitcoin price data.")
