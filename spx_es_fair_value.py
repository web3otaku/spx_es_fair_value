import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI

app = FastAPI()

def fetch_fair_value_data():
    """ 爬取 IndexArb 網站的最新 SPX 與 ES 期貨數據 """
    url = "https://indexarb.com/fairValueDecomposition.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": "無法取得資料，請稍後再試"}

    soup = BeautifulSoup(response.text, "html.parser")

    # **列印所有表格內容**
    tables = soup.find_all("table")
    print(f"找到 {len(tables)} 個表格")

    # **列印每個表格的內容，幫助 Debug**
    for i, table in enumerate(tables):
        print(f"表格 {i}: {table.text[:200]}")  # 只列印前 200 個字，避免 log 太長

    # **確認是否有目標表格**
    if len(tables) < 2:
        return {"error": "找不到正確的數據表格，網站可能已經變更結構"}

    # **嘗試抓取正確的表格**
    data_table = tables[1]  # 假設目標表格是第二個，這裡可能需要調整

    rows = data_table.find_all("tr")

    if len(rows) < 6:
        return {"error": "表格數據異常，可能是網站更新導致的變更"}

    def safe_float(value):
        """ 轉換數值，遇到空值時回傳 0.0，避免 API 崩潰 """
        try:
            clean_value = value.strip().replace("%", "").replace(",", "")
            return float(clean_value) if clean_value else 0.0
        except ValueError:
            return 0.0

    # **列印所有行內容**
    for i, row in enumerate(rows):
        print(f"Row {i}: {[td.text.strip() for td in row.find_all('td')]}")

    spx_price = safe_float(rows[1].find_all("td")[1].text)
    es_price = safe_float(rows[2].find_all("td")[1].text)
    interest_rate = safe_float(rows[3].find_all("td")[1].text) / 100
    expected_dividends = safe_float(rows[4].find_all("td")[1].text)
    days_to_expiry_text = rows[5].find_all("td")[1].text.strip()
    days_to_expiry = int(days_to_expiry_text) if days_to_expiry_text.isdigit() else 0

    return {
        "spx_price": spx_price,
        "es_price": es_price,
        "interest_rate": interest_rate,
        "expected_dividends": expected_dividends,
        "days_to_expiry": days_to_expiry
    }

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
