"""
直接从页面JavaScript变量中提取数据
"""

import json
import pandas as pd
import numpy as np
import re
import random
from DrissionPage import ChromiumPage
from tqdm import tqdm


def stock_zh_a_spot_em_self() -> pd.DataFrame:
    """
    直接从页面的JavaScript变量中提取数据
    """
    driver = ChromiumPage()
    driver.listen.start("/api/qt/clist/get")
    url = "https://quote.eastmoney.com/center/gridlist.html"
    print(f"正在访问: {url}")
    driver.get(url)
    
    # ===== 点击页面位置（左下角） =====
    # 先移动到页面，再偏移点击
    driver.actions.move(200, 800).click()
    print("已点击页面位置 (200, 800) - 左下角")

    # ===== 切换到总市值 =====
    select_tag = driver.ele("x://select")
    select_tag.select("总市值")

    # 清空之前监听到的请求
    driver.listen.clear()

    all_diff = []  # 收集所有页数据
    page = 0
    total = 0  # 总数据条数
    pbar = None  # 进度条

    while True:
        page += 1
        resp = driver.listen.wait(timeout=10)

        body = resp.response.body
        # ===== 去掉 JSONP 包裹 =====
        match = re.search(r'\((.*)\)', body)
        if not match:
            continue
        json_str = match.group(1)

        data_json = json.loads(json_str)
        data = data_json.get("data", {})
        
        # 第一次获取总数，初始化进度条
        if page == 1:
            total = data.get("total", 0)
            pbar = tqdm(total=total, desc="加载进度", unit="条")

        diff = data.get("diff", [])

        if diff:
            all_diff.extend(diff)
            # 更新进度条
            if pbar:
                pbar.update(len(diff))
        else:
            break

        next_btn = driver.ele("@title=下一页")
        if not next_btn:
            break
        next_btn.click()

    # 关闭进度条
    if pbar:
        pbar.close()

    if not all_diff:
        return pd.DataFrame()

    # ===== 转 DataFrame =====
    df = pd.DataFrame(all_diff)

    # ===== 重命名字段 =====
    df = df.rename(columns={
        "f12": "代码",
        "f14": "名称",
        "f2": "最新价",
        "f3": "涨跌幅",
        "f4": "涨跌额",
        "f5": "成交量",
        "f6": "成交额",
        "f7": "振幅",
        "f8": "换手率",
        "f9": "市盈率",
        "f10": "量比",
        "f15": "最高",
        "f16": "最低",
        "f17": "今开",
        "f18": "昨收",
        "f20": "总市值",
    })
    # ===== 只保留需要字段 =====
    df = df[[
        "代码", "名称",
        "最新价", "涨跌幅", "涨跌额",
        "成交量", "成交额",
        "振幅", "换手率",
        "市盈率", "量比",
        "最高", "最低",
        "今开", "昨收", "总市值"
    ]]

    # ===== 价格字段除以100 =====
    price_cols = [
        "最新价", 
        "涨跌幅", 
        "涨跌额", 
        "振幅", 
        "换手率", 
        "最高", 
        "最低", 
        "今开", 
        "昨收", 
        "市盈率", 
        "总市值"]
    for col in price_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce") / 100

    # ===== 量比字段处理：将非数值转换为 np.nan =====
    df["量比"] = pd.to_numeric(df["量比"], errors="coerce")

    # # 成交额保持原始（单位：元）
    # df["成交额"] = pd.to_numeric(df["成交额"], errors="coerce")

    # print("\n===== DataFrame预览 =====")
    # print(f"总数据量: {len(df)} 条")

    driver.close()

    return df


if __name__ == "__main__":
    df = stock_zh_a_spot_em_self()
    if not df.empty:
        print(f"\n数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}")
        print("\n前5行:")
        print(df.head())
    else:
        print("获取数据失败")


