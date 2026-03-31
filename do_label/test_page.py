"""
从东方财富行情页面直接获取股票数据
https://quote.eastmoney.com/center/gridlist.html
"""

import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def get_stock_data_from_page() -> pd.DataFrame:
    """
    从东方财富行情页面直接获取股票数据
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,3000")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = None
    try:
        print("正在访问东方财富行情页面...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get("https://quote.eastmoney.com/center/gridlist.html")

        wait = WebDriverWait(driver, 30)
        print("等待页面加载...")
        
        # 等待页面完全加载
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        time.sleep(3)

        # 滚动页面加载更多数据
        print("滚动加载更多数据...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # 方法1: 尝试获取表格数据
        print("尝试提取表格数据...")
        table = driver.find_element(By.CSS_SELECTOR, "table")
        
        # 获取表头
        headers = []
        ths = table.find_elements(By.CSS_SELECTOR, "thead th")
        for th in ths:
            text = th.text.strip()
            if text:
                headers.append(text)
        print(f"表头: {headers}")

        # 获取数据行
        rows_data = []
        tbody = table.find_element(By.CSS_SELECTOR, "tbody")
        trs = tbody.find_elements(By.CSS_SELECTOR, "tr")
        print(f"找到 {len(trs)} 行")

        for tr in trs:
            cells = tr.find_elements(By.TAG_NAME, "td")
            row_data = []
            for cell in cells:
                text = cell.text.strip()
                row_data.append(text)
            if row_data:
                rows_data.append(row_data)

        if len(rows_data) > 10:
            print(f"成功获取 {len(rows_data)} 行数据")
            df = pd.DataFrame(rows_data)
            if len(df.columns) == len(headers):
                df.columns = headers
            return df

        # 方法2: 尝试获取JSON数据
        print("尝试提取JSON数据...")
        scripts = driver.find_elements(By.CSS_SELECTOR, "script")
        for script in scripts:
            content = script.get_attribute("textContent") or ""
            if "stockList" in content or "quotationData" in content or "data[" in content:
                # 提取JSON数据
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    try:
                        json_str = content[start:end]
                        data = json.loads(json_str)
                        print(f"找到JSON数据: {list(data.keys())[:5]}")
                        return pd.DataFrame(data)
                    except:
                        pass

        # 方法3: 尝试获取JavaScript变量
        print("尝试提取JS变量...")
        js_data = driver.execute_script("""
            if (typeof stockList !== 'undefined') return stockList;
            if (typeof quotationData !== 'undefined') return quotationData;
            if (typeof window.stockData !== 'undefined') return window.stockData;
            if (typeof window.dataList !== 'undefined') return window.dataList;
            return null;
        """)
        
        if js_data:
            print(f"找到JS数据: {type(js_data)}")
            if isinstance(js_data, list) and len(js_data) > 10:
                return pd.DataFrame(js_data)
            elif isinstance(js_data, dict):
                return pd.DataFrame(js_data)

        # 方法4: 获取页面中所有data-symbol的元素
        print("尝试备选提取方式...")
        all_data = []
        
        # 获取表格所有文本
        table_text = table.text
        lines = table_text.split('\n')
        for line in lines:
            if line.strip():
                all_data.append(line.split())

        if len(all_data) > 10:
            df = pd.DataFrame(all_data[1:], columns=all_data[0] if all_data[0] else None)
            return df

        print("未能获取足够数据")
        return pd.DataFrame()

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


if __name__ == "__main__":
    df = get_stock_data_from_page()
    if not df.empty:
        print(f"\n数据形状: {df.shape}")
        print(df.head())
    else:
        print("获取数据失败")
