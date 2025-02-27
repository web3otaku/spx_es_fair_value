from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict
from fastapi.staticfiles import StaticFiles

app = FastAPI()

class FairValueRequest(BaseModel):
    spx_price: float
    interest_rate: float
    days_to_expiry: int
    expected_dividends: float
    divisor: float
    current_es_price: float

def calculate_fair_value(spx_price, interest_rate, days_to_expiry, expected_dividends, divisor):
    interest_component = spx_price * ((1 + interest_rate) ** (days_to_expiry / 365) - 1)
    dividend_component = expected_dividends / divisor
    fair_value = interest_component - dividend_component
    fair_value_es = spx_price + fair_value
    return fair_value, fair_value_es

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head><title>SPX vs ES Fair Value Calculator</title></head>
        <body>
            <h2>SPX 與 ES 期貨合理價差計算器</h2>
            <form action="/calculate" method="post">
                <label>輸入當前 S&P 500 指數價格: <input type="number" step="0.01" name="spx_price" required></label><br>
                <label>輸入無風險利率 (如 SOFR, 以小數表示): <input type="number" step="0.0001" name="interest_rate" required></label><br>
                <label>輸入期貨到期日距今的天數: <input type="number" name="days_to_expiry" required></label><br>
                <label>輸入預期股息總額: <input type="number" step="0.01" name="expected_dividends" required></label><br>
                <label>輸入 S&P 500 指數的 Divisor: <input type="number" step="0.0001" name="divisor" required></label><br>
                <label>輸入當前 ES 期貨價格: <input type="number" step="0.01" name="current_es_price" required></label><br>
                <button type="submit">計算合理價差</button>
            </form>
        </body>
    </html>
    """

@app.post("/calculate")
def calculate(spx_price: float = Form(...), interest_rate: float = Form(...), days_to_expiry: int = Form(...), expected_dividends: float = Form(...), divisor: float = Form(...), current_es_price: float = Form(...)):
    fv, fair_es = calculate_fair_value(spx_price, interest_rate, days_to_expiry, expected_dividends, divisor)
    advice = "⚖ 目前 ES 期貨價格與合理價相符，沒有明顯的套利機會。"
    if current_es_price > fair_es:
        advice = "🚨 目前 ES 期貨價格高於合理價，可能存在套利機會 (做空期貨，買入 SPX)。"
    elif current_es_price < fair_es:
        advice = "✅ 目前 ES 期貨價格低於合理價，可能存在套利機會 (買入期貨，做空 SPX)。"
    
    return {
        "fair_value": round(fv, 2),
        "fair_es_price": round(fair_es, 2),
        "arbitrage_advice": advice
    }

# 啟動 FastAPI 伺服器：
# 1. 安裝 FastAPI 和 Uvicorn： `pip install fastapi uvicorn`
# 2. 執行伺服器： `uvicorn your_script:app --reload`
