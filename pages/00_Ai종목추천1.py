import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(
    page_title="AI 밸류체인 핵심 기업 분석기",
    layout="wide"
)

st.title("🤖 글로벌 AI 핵심 관련주 비교 분석기")
st.markdown("""
이 웹앱은 글로벌 AI 트렌드를 주도하는 핵심 기업들을 세 가지 밸류체인(하드웨어, 플랫폼/클라우드, 소프트웨어)으로 분류하여, 
각 분야가 시장에서 어떻게 성장하고 있는지 비교 탐구할 수 있는 대시보드입니다.
""")

# 2. AI 밸류체인 기업 데이터베이스 정의
ai_sectors = {
    "💾 AI 하드웨어 (반도체/인프라)": {
        "NVIDIA (NVDA)": "NVDA",
        "TSMC (TSM)": "TSM",
        "Broadcom (AVGO)": "AVGO",
        "한미반도체 (042700.KS)": "042700.KS"
    },
    "☁️ AI 클라우드 & 거대모델 (빅테크)": {
        "Microsoft (MSFT)": "MSFT",
        "Alphabet/Google (GOOGL)": "GOOGL",
        "Amazon (AMZN)": "AMZN",
        "Meta (META)": "META"
    },
    "💻 AI 소프트웨어 & 서비스": {
        "Palantir (PLTR)": "PLTR",
        "Adobe (ADBE)": "ADBE",
        "ServiceNow (NOW)": "NOW"
    }
}

# 3. 사이드바 UI 구성
st.sidebar.header("⚙️ 탐구 및 분석 설정")

# 섹터 선택
selected_sector = st.sidebar.selectbox(
    "1. 분석할 AI 분야(Sektor)를 선택하세요",
    list(ai_sectors.keys())
)

# 선택된 섹터 내 기업들 목록
available_stocks = ai_sectors[selected_sector]

# 분석할 기업 선택 (기본값으로 모두 선택)
selected_stocks = st.sidebar.multiselect(
    "2. 분석할 기업을 선택하세요 (다중 선택 가능)",
    list(available_stocks.keys()),
    default=list(available_stocks.keys())
)

# 분석 기간 설정
st.sidebar.subheader("3. 분석 기간 설정")
default_start = datetime.today() - timedelta(days=365) # 기본 1년
start_date = st.sidebar.date_input("시작일", default_start)
end_date = st.sidebar.date_input("종료일", datetime.today())

# 4. 데이터 로드 및 처리
if not selected_stocks:
    st.warning("⚠️ 왼쪽 사이드바에서 최소 하나 이상의 기업을 선택해주세요!")
else:
    st.subheader(f"📊 {selected_sector} 대표 기업 분석 결과")
    
    with st.spinner("AI 기업들의 데이터를 불러오는 중입니다..."):
        ticker_data = {}
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # 선택된 주식 데이터 가져오기 (시간대 오류 해결 기법 적용)
        for name in selected_stocks:
            ticker = available_stocks[name]
            try:
                t = yf.Ticker(ticker)
                df = t.history(start=start_str, end=end_str)
                if not df.empty:
                    # 시간대 정보 통일 및 제거
                    if df.index.tz is not None:
                        df.index = df.index.tz_localize(None)
                    ticker_data[name] = df['Close']
            except Exception as e:
                st.error(f"⚠️ {name} 데이터를 가져오는 중 오류 발생: {e}")
        
        if ticker_data:
            data = pd.DataFrame(ticker_data)
            # 다른 개장일 차이 보완하기 위해 앞/뒤 값으로 결측치 채우기
            data_cleaned = data.ffill().bfill()
            
            # 누적 수익률 계산
            cum_returns = (data_cleaned / data_cleaned.iloc[0] - 1) * 100
            
            # 시각화 (Plotly 선 그래프)
            fig = go.Figure()
            for col in cum_returns.columns:
                fig.add_trace(go.Scatter(
                    x=cum_returns.index,
                    y=cum_returns[col],
                    mode='lines',
                    name=col
                ))
            
            fig.update_layout(
                title=f"{selected_sector} 내 기업들의 누적 수익률 (%) 비교",
                xaxis_title="날짜",
                yaxis_title="누적 수익률 (%)",
                hovermode="x unified",
                template="plotly_dark",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 상세 성과 테이블 제공
            st.subheader("📋 성과 데이터 요약")
            metrics = []
            for col in data_cleaned.columns:
                start_val = data_cleaned[col].iloc[0]
                end_val = data_cleaned[col].iloc[-1]
                tot_return = ((end_val / start_val) - 1) * 100
                
                metrics.append({
                    "기업명": col,
                    "시작 가격": f"{start_val:,.2f}",
                    "종료 가격": f"{end_val:,.2f}",
                    "기간 내 누적 수익률": f"{tot_return:+.2f}%"
                })
                
            st.table(pd.DataFrame(metrics))
            
        else:
            st.error("데이터를 가져오는 데 실패했습니다. 올바른 날짜 범위를 선택했는지 확인해주세요.")

# 5. 스스로 탐구해볼 수 있는 질문 던지기 (학습용)
st.markdown("---")
st.info("""
**💡 AI 관련주 탐구를 위한 심층 질문 (수행평가/탐구 보고서 주제 추천)**
1. **성장의 순서(시차 효과)**: AI 열풍이 불었을 때, 하드웨어 기업(예: NVIDIA)의 주가 상승 시점과 소프트웨어 기업(예: Adobe)의 상승 시점에 차이가 있었을까요? 왜 그런 현상이 나타났을지 공급망 관점에서 탐구해 보세요.
2. **밸류에이션(Valuation)**: 주가수익비율(PER) 등 다양한 재무 지표를 찾아보고, 현재 AI 핵심주들의 주가가 기업의 실제 실적(이익)에 비해 고평가(버블)인지, 혹은 정당한 상승인지 친구들의 생각을 정리해보세요.
3. **국내와 글로벌의 연동**: 한미반도체(한국)와 NVIDIA/TSMC(글로벌)의 주가 흐름을 비교해 보세요. 글로벌 AI 반도체 동맹(HBM 공급망)이 주가에 어떤 커플링(동조화) 효과를 주는지 분석해 보세요!
""")
