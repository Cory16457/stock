import os
import streamlit as st
import streamlit.components.v1 as components
import requests
from cerebras.cloud.sdk import Cerebras
from datetime import datetime, timedelta


os.environ["CEREBRAS_API_KEY"] = "csk-n552ehwetvcnykdcwc3wyffn33kw8yfcwddj6vw9cdvyxkpr"
FINNHUB_API_KEY = "cvm7r6hr01qnndmcn1kgcvm7r6hr01qnndmcn1l0"

client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY"))

st.set_page_config(page_title="Dashboard", page_icon="📈", layout="wide")
st.markdown(
    "<h1 style='text-align: left;'>📈 Essential Stock Dashboard <span style='font-size: 18px;'>(Cerebras-powered)</span></h1>",
    unsafe_allow_html=True
)




col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("#### 🏛️ Select Exchange")
    exchange = st.selectbox("Choose exchange:", ["NASDAQ", "NYSE"], index=0)

    ticker = st.text_input("Enter a stock ticker:", "AAPL", key="ticker_input_main")

    # Analyze button
    if st.button("Analyze"):
        st.markdown(f"🔍 **Fetching news for `{ticker.upper()}`...**")

        today = datetime.today().date()
        week_ago = today - timedelta(days=7)
        url = f"https://finnhub.io/api/v1/company-news?symbol={ticker.upper()}&from={week_ago}&to={today}&token={FINNHUB_API_KEY}"
        res = requests.get(url)

        if res.status_code != 200:
            st.error("❌ Failed to fetch news from Finnhub.")
            st.stop()

        news_data = res.json()
        if not news_data:
            st.warning("⚠️ No recent news found for this ticker.")
            st.stop()

        headlines = [(item['headline'], item['url']) for item in news_data[:5]]
        combined_news = "\n".join([title for title, url in headlines])

        st.session_state["headlines"] = headlines
        st.session_state["combined_news"] = combined_news
        st.session_state["ticker"] = ticker.upper()
        st.session_state["exchange"] = exchange

        prompt = [{
            "role": "user",
            "content": f"""
You're a financial LLM that analyzes stock news. Based on the news below, give a sentiment score from -100 (very bearish) to +100 (very bullish) and explain briefly why.

News:
{combined_news}

Respond in this format only:
Score: [number]
Explanation: [text]
"""
        }]

        with st.spinner("🧠 Cerebras LLM analyzing sentiment..."):
            try:
                response = client.chat.completions.create(
                    messages=prompt,
                    model="llama-4-scout-17b-16e-instruct",
                )
                output = response.choices[0].message.content
                st.session_state["sentiment_output"] = output
            except Exception as e:
                st.session_state["sentiment_output"] = f"❌ Cerebras error: {e}"

    # Show sentiment output if available
    if "sentiment_output" in st.session_state:
        st.markdown("### 📊 Sentiment Analysis Output:")
        st.markdown(
            f"<div style='background-color:#262730; padding: 15px; border-radius: 10px; color: white;'>{st.session_state['sentiment_output']}</div>",
            unsafe_allow_html=True
        )

    # Show headlines if available
    if "headlines" in st.session_state:
        st.markdown("### 📰 News Headlines Used:")
        for idx, (title, url) in enumerate(st.session_state["headlines"], 1):
            st.markdown(f"{idx}. [{title}]({url})")

    # Chatbox – always available once news is fetched
    if "combined_news" in st.session_state:
        st.markdown("---")
        st.markdown("### 💬 Ask About This Stock")

        user_question = st.text_input("Ask a question about this stock:", key="user_question_input")

        if user_question:
            chat_prompt = [{
                "role": "user",
                "content": f"""
You're a financial assistant. A user asked a question about {st.session_state['ticker']}. Use the following recent news as context.

News:
{st.session_state['combined_news']}

Question:
{user_question}

Answer clearly and concisely, like you're advising an investor.
"""
            }]

            with st.spinner("💬 Thinking..."):
                try:
                    chat_response = client.chat.completions.create(
                        messages=chat_prompt,
                        model="llama-4-scout-17b-16e-instruct",
                    )
                    chat_answer = chat_response.choices[0].message.content
                    st.success("✅ Response:")
                    st.markdown(
                        f"<div style='background-color:#20262E; padding: 15px; border-radius: 10px; color: white;'>{chat_answer}</div>",
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"❌ Chat error: {e}")

# ========================
# CHART
# ========================
with col2:
    st.markdown("### 📈 Stock Chart")

    # Show chart only if ticker selected
    if "ticker" in st.session_state and "exchange" in st.session_state:
        tv_code = f"""
        <iframe src="https://s.tradingview.com/widgetembed/?symbol={st.session_state['exchange']}%3A{st.session_state['ticker']}&interval=D&theme=dark&style=1&locale=en"
            width="100%" height="400" frameborder="0" allowtransparency="true" scrolling="no">
        </iframe>
        """
        components.html(tv_code, height=400)

st.markdown("---")
st.markdown("### 🧠 Compare Two Stocks")

col3, col4 = st.columns(2)
ticker1_input = col3.text_input("First stock ticker:", st.session_state.get("compare_ticker1", "AAPL"), key="compare_ticker1_value")
ticker2_input = col4.text_input("Second stock ticker:", st.session_state.get("compare_ticker2", "MSFT"), key="compare_ticker2_value")

def fetch_news(ticker):
    today = datetime.today().date()
    week_ago = today - timedelta(days=7)
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker.upper()}&from={week_ago}&to={today}&token={FINNHUB_API_KEY}"
    res = requests.get(url)
    if res.status_code == 200:
        news_data = res.json()
        return [(item["headline"], item["url"]) for item in news_data[:5]]
    return []

def format_news_for_prompt(news_list):
    return "\n".join([f"- {title} ({url})" for title, url in news_list]) if isinstance(news_list, list) else "No news."

if st.button("Compare Stocks"):
    with st.spinner("🧠 Fetching news and analyzing with Cerebras..."):
        news1 = fetch_news(ticker1_input)
        news2 = fetch_news(ticker2_input)

        st.session_state["compare_news1"] = news1
        st.session_state["compare_news2"] = news2
        st.session_state["compare_ticker1"] = ticker1_input
        st.session_state["compare_ticker2"] = ticker2_input

        compare_prompt = [{
            "role": "user",
            "content": f"""
Compare the following two stocks based on their recent news.

📦 {ticker1_input.upper()}:
{format_news_for_prompt(news1)}

🖥 {ticker2_input.upper()}:
{format_news_for_prompt(news2)}

Your task:
1. Provide a one-paragraph analysis comparing investor sentiment.
2. Recommend which stock looks stronger and why."""
        }]
        try:
            compare_response = client.chat.completions.create(
                messages=compare_prompt,
                model="llama-4-scout-17b-16e-instruct",
            )
            st.session_state["compare_result"] = compare_response.choices[0].message.content
        except Exception as e:
            st.session_state["compare_result"] = f"❌ Cerebras comparison error: {e}"

# ✅ Render comparison
if "compare_result" in st.session_state:
    st.success(f"📊 Comparison: {st.session_state['compare_ticker1'].upper()} vs. {st.session_state['compare_ticker2'].upper()}")
    st.markdown(
        f"<div style='background-color:#0F1117; padding: 15px; border-radius: 10px; color: white;'>{st.session_state['compare_result']}</div>",
        unsafe_allow_html=True
    )

# Add clickable source links for both stocks
st.markdown("### 🔗 Sources for Comparison")

if "compare_news1" in st.session_state:
    st.markdown(f"**Sources for {st.session_state['compare_ticker1'].upper()}**")
    for i, (headline, url) in enumerate(st.session_state["compare_news1"], 1):
        st.markdown(f"{i}. [{headline}]({url})")

if "compare_news2" in st.session_state:
    st.markdown(f"**Sources for {st.session_state['compare_ticker2'].upper()}**")
    for i, (headline, url) in enumerate(st.session_state["compare_news2"], 1):
        st.markdown(f"{i}. [{headline}]({url})")


    

st.markdown("---")
st.markdown("### 🏆 Leaderboard: Top MAG7 Stocks (Past 7 Days)")

# Tickers to analyze
leaderboard_tickers = ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN", "GOOGL", "META",]

# Run only once and cache results
if "leaderboard_data" not in st.session_state:
    st.session_state.leaderboard_data = []
    for t in leaderboard_tickers:
        with st.spinner(f"🔍 Analyzing {t}..."):
            try:
                # News fetch
                today = datetime.today().date()
                week_ago = today - timedelta(days=7)
                url = f"https://finnhub.io/api/v1/company-news?symbol={t}&from={week_ago}&to={today}&token={FINNHUB_API_KEY}"
                res = requests.get(url)
                data = res.json()[:5]
                headlines = "\n".join([article["headline"] for article in data])

                if not headlines.strip():
                    continue

                # Cerebras prompt
                prompt = [{
                    "role": "user",
                    "content": f"""
You're a financial LLM that analyzes stock news. Based on the news below, give a sentiment score from -100 (very bearish) to +100 (very bullish) and explain briefly why.

News:
{headlines}

Respond in this format only:
Score: [number]
Explanation: [text]
"""
                }]

                response = client.chat.completions.create(
                    messages=prompt,
                    model="llama-4-scout-17b-16e-instruct",
                )
                output = response.choices[0].message.content

                score_line = [line for line in output.splitlines() if "Score:" in line]
                if score_line:
                    score = int(score_line[0].replace("Score:", "").strip())
                    st.session_state.leaderboard_data.append((t, score))
            except Exception as e:
                st.warning(f"{t}: failed – {e}")

if st.session_state.leaderboard_data:
    sorted_data = sorted(st.session_state.leaderboard_data, key=lambda x: x[1], reverse=True)

    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("#### 🥇 Top 5 Bullish Stocks:")
        for rank, (t, score) in enumerate(sorted_data[:5], 1):
            st.markdown(f"{rank}. **{t}** – Score: `{score}`")

    with col_right:
        st.image("image.png", caption="Microsoft Featured", use_container_width=True)
else:
    st.warning("No leaderboard results yet.")


st.markdown("---")
st.markdown("### 🧠 TL;DR Summary of the Week")

summary_tickers = ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN"]
summary_headlines = []

today = datetime.today().date()
week_ago = today - timedelta(days=7)

for t in summary_tickers:
    url = f"https://finnhub.io/api/v1/company-news?symbol={t}&from={week_ago}&to={today}&token={FINNHUB_API_KEY}"
    res = requests.get(url)
    data = res.json()[:3]
    summary_headlines.extend([f"{t}: {article['headline']}" for article in data])

if summary_headlines:
    summary_prompt = [{
        "role": "user",
        "content": f"""
You are a financial news summarizer. Here's a list of major headlines from this week across the market:

{chr(10).join(summary_headlines)}

Write a 4–5 sentence TL;DR summary of what happened in the stock market this week. Include overall market tone and key events.
"""
    }]

    with st.spinner("📚 Analyzing the week..."):
        try:
            response = client.chat.completions.create(
                messages=summary_prompt,
                model="llama-4-scout-17b-16e-instruct",
            )
            summary_output = response.choices[0].message.content
            st.success("✅ TL;DR Ready!")
            st.markdown(
                f"<div style='background-color:#1e2127; padding: 15px; border-radius: 10px; color: white;'>{summary_output}</div>",
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"❌ TL;DR error: {e}")
else:
    st.warning("Could not fetch enough headlines to generate a summary.")

try:
    data = res.json()
    if isinstance(data, list):
        data = data[:3]
    else:
        st.warning(f"Unexpected response for {t}: {data}")
        data = []
except Exception as e:
    st.warning(f"Could not parse news for {t}: {e}")
    data = []
