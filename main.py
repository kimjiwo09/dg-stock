import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(
    page_title="한·미 주요 주식 수익률 비교기",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 웹앱 제목 및 설명
st.title("📈 한·미 주요 주식 수익률 비교 웹앱")
st.markdown("""
이 앱은 한국과 미국의 주요 주식들의 수익률을 같은 시점에서 공정하게 비교할 수 있도록 도와줍니다.
선택한 기간 동안의 **누적 수익률(%)**을 계산하여 차트로 시각화합니다.
""")

# 2. 사이드바 설정 (사용자 입력)
st.sidebar.header("⚙️ 분석 설정")

# 주식 목록 정의 (yfinance 티커 기준)
us_stocks = {
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Google (GOOGL)": "GOOGL",
    "Tesla (TSLA)": "TSLA",
    "NVIDIA (NVDA)": "NVDA",
    "Amazon (AMZN)": "AMZN"
}

kr_stocks = {
    "삼성전자 (005930.KS)": "005930.KS",
    "SK하이닉스 (000660.KS)": "000660.KS",
    "현대차 (005380.KS)": "005380.KS",
    "NAVER (035420.KS)": "035420.KS",
    "카카오 (035720.KS)": "035720.KS"
}

# 주식 선택 UI
st.sidebar.subheader("1. 비교할 주식 선택")
selected_us = st.sidebar.multiselect(
    "🇺🇸 미국 주식 선택", 
    list(us_stocks.keys()), 
    default=["Apple (AAPL)", "NVIDIA (NVDA)"]
)
selected_kr = st.sidebar.multiselect(
    "🇰🇷 한국 주식 선택", 
    list(kr_stocks.keys()), 
    default=["삼성전자 (005930.KS)"]
)

# 기간 선택 UI
st.sidebar.subheader("2. 분석 기간 설정")
default_start = datetime.today() - timedelta(days=365) # 기본값: 최근 1년
start_date = st.sidebar.date_input("시작일", default_start)
end_date = st.sidebar.date_input("종료일", datetime.today())

# 선택된 주식들을 하나의 리스트로 통합 및 이름 매핑
tickers = []
ticker_names = {}

for name in selected_us:
    ticker = us_stocks[name]
    tickers.append(ticker)
    ticker_names[ticker] = name

for name in selected_kr:
    ticker = kr_stocks[name]
    tickers.append(ticker)
    ticker_names[ticker] = name

# 3. 데이터 로드 및 시각화 처리
if not tickers:
    st.warning("⚠️ 왼쪽 사이드바에서 비교할 주식을 최소 하나 이상 선택해 주세요!")
else:
    st.subheader("📊 누적 수익률 비교 차트")
    
    with st.spinner("야후 파이낸스(yfinance)로부터 데이터를 불러오는 중입니다..."):
        try:
            # yfinance를 통해 수정종가(Adj Close) 다운로드
            data = yf.download(tickers, start=start_date, end=end_date)['Adj Close']
            
            # 주식이 1개만 선택되었을 경우 DataFrame 형태를 유지하기 위한 처리
            if len(tickers) == 1:
                data = pd.DataFrame({tickers[0]: data})
            
            if data.empty:
                st.error("❌ 선택한 기간에 해당하는 데이터가 없습니다. 다른 기간을 선택해 주세요.")
            else:
                # 💡 다른 휴장일 처리: 한국과 미국의 휴장일이 다르므로 결측치(NaN)를 직전 값으로 채움(Forward Fill)
                data_cleaned = data.ffill().bfill()
                
                # 누적 수익률 계산: (현재가 / 시작일 가격 - 1) * 100
                cum_returns = (data_cleaned / data_cleaned.iloc[0] - 1) * 100
                
                # Plotly를 이용한 동적 선 그래프 그리기
                fig = go.Figure()
                
                for ticker in tickers:
                    fig.add_trace(go.Scatter(
                        x=cum_returns.index,
                        y=cum_returns[ticker],
                        mode='lines',
                        name=ticker_names[ticker]
                    ))
                
                fig.update_layout(
                    xaxis_title="날짜",
                    yaxis_title="누적 수익률 (%)",
                    hovermode="x unified",
                    template="plotly_dark", # 깔끔하고 현대적인 다크 테마 적용
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                    margin=dict(l=20, r=20, t=30, b=20)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 4. 상세 성과 데이터 테이블 제공
                st.subheader("📋 상세 성과 요약")
                metrics = []
                for ticker in tickers:
                    start_val = data_cleaned[ticker].iloc[0]
                    end_val = data_cleaned[ticker].iloc[-1]
                    tot_return = ((end_val / start_val) - 1) * 100
                    
                    metrics.append({
                        "주식명": ticker_names[ticker],
                        "티커(Ticker)": ticker,
                        "시작일 가격": f"{start_val:,.2f}",
                        "종료일 가격": f"{end_val:,.2f}",
                        "누적 수익률 (%)": f"{tot_return:+.2f}%"
                    })
                
                st.table(pd.DataFrame(metrics))
                
        except Exception as e:
            st.error(f"데이터를 가져오는 중 문제가 발생했습니다: {e}")

# 5. 스스로 탐구해볼 수 있는 질문 던지기 (학습용)
st.markdown("---")
st.info("""
**💡 한 걸음 더 나아가는 탐구 질문 (스스로 생각해보기!)**
1. **누적 수익률 계산의 장점**: 단순히 주가 금액 자체를 비교하지 않고, 왜 **누적 수익률(%)**로 변환하여 비교했을까요? (힌트: 삼성전자 주가와 엔비디아 주가의 절대적인 금액 차이를 생각해 보세요!)
2. **환율 효과(Currency Effect)**: 미국 주식은 달러(USD) 기준이고 한국 주식은 원화(KRW) 기준입니다. 원-달러 환율 변동을 이 코드에 반영하려면 어떻게 계산식을 고쳐야 할까요?
3. **결측치 처리**: 한국과 미국은 명절이나 휴일이 달라 한쪽 시장만 열리는 날이 있습니다. 코드 안에서 `.ffill().bfill()`을 사용해 이 문제를 해결했는데, 이것이 의미하는 바는 무엇일까요?
""")
