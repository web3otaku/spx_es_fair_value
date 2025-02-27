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

    # 解析 HTML 內容，找出 SPX、ES、利率與股息
    try:
        data_table = soup.find_all("table")[1]  # 找到第二個表格 (Fair Value Decomposition)
        rows = data_table.find_all("tr")

        # 取得 SPX 現貨價格
        spx_price = float(rows[1].find_all("td")[1].text.strip())

        # 取得 ES 期貨價格
        es_price = float(rows[2].find_all("td")[1].text.strip())

        # 取得無風險利率
        interest_rate = float(rows[3].find_all("td")[1].text.strip().replace("%", "")) / 100  # 轉換成小數

        # 取得預期股息
        expected_dividends = float(rows[4].find_all("td")[1].text.strip())

        # 取得期貨到期日
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


@app.get("/fetch-data")
def get_fair_value_data():
    """ API 端點：自動從 IndexArb 獲取數據 """
    return fetch_fair_value_data()
