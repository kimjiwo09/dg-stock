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
    
    with st.spinner("야후 파이낸스(yfinance)로부터 데이터를 안전하게 불러오는 중입니다..."):
        # 안전한 개별 다운로드 및 시간대 정렬 방식 도입
        ticker_data = {}
        
        # Streamlit 날짜 포맷을 문자열로 변환
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        for ticker in tickers:
            try:
                # yf.Ticker를 사용하여 단일 종목씩 히스토리 가져오기 (오류 발생 확률 극소화)
                t = yf.Ticker(ticker)
                df = t.history(start=start_str, end=end_str)
                
                if not df.empty:
                    # 💡 시간대(Timezone) 정보 제거하여 한국/미국 주식 시간대 충돌 방지!
                    if df.index.tz is not None:
                        df.index = df.index.tz_localize(None)
                    
                    # history()의 'Close'는 기본적으로 배당/분할이 반영된 수정종가(Adjusted Close)입니다.
                    ticker_data[ticker] = df['Close']
                else:
                    st.warning(f"⚠️ {ticker_names[ticker]} ({ticker}) 데이터가 해당 기간에 존재하지 않습니다.")
            except Exception as e:
                st.warning(f"⚠️ {ticker_names[ticker]} ({ticker}) 데이터를 가져오는 데 실패했습니다: {e}")
        
        # 딕셔너리를 데이터프레임으로 변환
        if ticker_data:
            data = pd.DataFrame(ticker_data)
        else:
            data = pd.DataFrame()
            
        if data.empty:
            st.error("❌ 선택한 기간에 분석 가능한 주식 데이터가 없습니다. 다른 기간이나 주식을 선택해 주세요.")
        else:
            # 💡 한국/미국 휴장일 불일치 처리: 결측치를 직전 종가로 채우기
            data_cleaned = data.ffill().bfill()
            
            # 누적 수익률 계산: (현재가 / 시작일 가격 - 1) * 100
            cum_returns = (data_cleaned / data_cleaned.iloc[0] - 1) * 100
            
            # Plotly를 이용한 선 그래프 시각화
            fig = go.Figure()
            
            for ticker in tickers:
                if ticker in cum_returns.columns:
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
                template="plotly_dark", # 가독성 좋은 어두운 배경 테마
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                margin=dict(l=20, r=20, t=30, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 4. 상세 성과 데이터 테이블 제공
            st.subheader("📋 상세 성과 요약")
            metrics = []
            for ticker in tickers:
                if ticker in data_cleaned.columns:
                    start_val = data_cleaned[ticker].iloc[0]
                    end_val = data_cleaned[ticker].iloc[-1]
                    tot_return = ((end_val / start_val) - 1) * 100
                    
                    metrics.append({
                        "주식명": ticker_names[ticker],
                        "티커(Ticker)": ticker,
                        "시작 가격": f"{start_val:,.2f}",
                        "종료 가격": f"{end_val:,.2f}",
                        "누적 수익률 (%)": f"{tot_return:+.2f}%"
                    })
            
            st.table(pd.DataFrame(metrics))

# 5. 스스로 탐구해볼 수 있는 질문 던지기 (학습용)
st.markdown("---")
st.info("""
**💡 왜 이전 코드에서 오류가 났을까요? 함께 공부해보자!**
1. **라이브러리 버전 업데이트의 영향**: 오픈소스 라이브러리는 수시로 업데이트되며 데이터 구조(출력 형태)를 바꿉니다. 이전 코드에서는 여러 주식을 한 번에 다운받아 생기는 다중 인덱스(MultiIndex) 문제 때문에 오류가 발생했습니다.
2. **시간대(Timezone)의 충돌**: 미국 시장(미국 동부 시간 기준)과 한국 시장(KST 기준)은 하루의 기준이 다릅니다. 이 코드에서는 어떤 방법으로 두 국가의 주식 날짜를 하나로 묶었는지 생각해보세요!
""")
