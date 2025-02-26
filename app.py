
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ✅ Load Bitcoin price data
def get_crypto_data(crypto_id="bitcoin", days=180):
    url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
    params = {'vs_currency': 'usd', 'days': days, 'interval': 'daily'}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    else:
        st.error(f"❌ Error fetching data: {response.json()}")
        return pd.DataFrame()

# ✅ Load AI Insights
API_KEY = "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"
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"

def generate_ai_insights(prompt):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})

    if response.status_code != 200:
        st.error(f"❌ AI API Error: HTTP {response.status_code}")
        return "Error generating insights."

    try:
        result = response.json()
        return result[0]['generated_text']
    except Exception as e:
        st.error(f"❌ JSON Parsing Error: {e}")
        return "Error processing AI response."

# 🔹 Streamlit UI
st.title("📊 Bitcoin Dashboard with AI Insights")

# ✅ Load BTC Data
crypto_df = get_crypto_data()

if crypto_df.empty:
    st.error("❌ No data available.")
else:
    # 🔹 Display Bitcoin Price Trend
    st.subheader("🔹 Bitcoin Price Trend (Last 6 Months)")
    st.line_chart(crypto_df.set_index('timestamp')['price'])

    # 🔹 AI Insights Section
    st.subheader("🤖 AI-Generated Insights")
    user_question = st.text_input("Ask AI about Bitcoin trends", "What are the latest Bitcoin trends?")
    
    if st.button("Generate Insights"):
        with st.spinner("Generating insights..."):
            insights = generate_ai_insights(user_question)
            st.write(insights)
