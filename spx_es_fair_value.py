from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup

app = FastAPI()

def fetch_fair_value_data():
    """ 爬取 IndexArb 網站的最新 SPX 與 ES 期貨數據 """
    url = "https://indexarb.com/fairValueDecomposition.html"
    headers = {"User-Agent": "Mozilla/5.0"}  # 避免被網站封鎖
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return {"error": "無法取得資料，請稍後再試"}
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    try:
        data_table = soup.find_all("table")[1]  # 找到第二個表格 (Fair Value Decomposition)
        rows = data_table.find_all("tr")
        
        spx_price = float(rows[1].find_all("td")[1].text.strip())
        es_price = float(rows[2].find_all("td")[1].text.strip())
        interest_rate = float(rows[3].find_all("td")[1].text.strip().replace("%", "")) / 100
        expected_dividends = float(rows[4].find_all("td")[1].text.strip())
        days_to_expiry = int(rows[5].find_all("td")[1].text.strip())
        
        return {
            "spx_price": spx_price,
            "es_price": es_price,
            "interest_rate": interest_rate,
            "expected_dividends": expected_dividends,
            "days_to_expiry": days_to_expiry
        }
    except Exception as e:
        return {"error": f"解析數據時發生錯誤: {e}"}

@app.get("/")
def home():
    return {"message": "FastAPI is running!"}

@app.get("/fetch-data")
def get_fair_value_data():
    """ API 端點：自動從 IndexArb 獲取數據 """
    return fetch_fair_value_data()

@app.get("/calculate-fair-value")
def calculate_fair_value():
    """ 使用自動爬取的數據來計算 SPX 與 ES 的合理價差 """
    data = fetch_fair_value_data()
    
    if "error" in data:
        return data
    
    spx_price = data["spx_price"]
    interest_rate = data["interest_rate"]
    days_to_expiry = data["days_to_expiry"]
    expected_dividends = data["expected_dividends"]
    
    interest_component = spx_price * ((1 + interest_rate) ** (days_to_expiry / 365) - 1)
    dividend_component = expected_dividends
    fair_value = interest_component - dividend_component
    fair_value_es = spx_price + fair_value
    
    return {
        "spx_price": spx_price,
        "fair_value": round(fair_value, 2),
        "fair_es_price": round(fair_value_es, 2),
        "arbitrage_advice": "做空 ES" if data["es_price"] > fair_value_es else "買入 ES"
    }
