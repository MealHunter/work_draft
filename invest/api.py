from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import pandas as pd
import numpy as np

app = FastAPI()


# 从独立模块导入
from eastmoney_page import stock_zh_a_spot_em_self



class StockItem(BaseModel):
    code: str
    name: str
    price: str
    amount: str

class BuyRequest(BaseModel):
    data: list[StockItem]
    benjin: float

def handling_fee(transaction_amount, type_name):
    formalities_fee = 4.5                           # 净手续费
    transfer_fee = transaction_amount * 0.00001     # 过户费
    handling_cost = transaction_amount * 0.0000341  # 经手费
    management_fee = transaction_amount * 0.00002   # 证管费
    if type_name == 'sell':
        stamp_duty = transaction_amount * 0.0005    # 印花税
    else:
        stamp_duty = 0                              # 买入不收印花税
    total_fee = formalities_fee + transfer_fee + handling_cost + management_fee + stamp_duty
    if total_fee < 5:
        total_fee = 5
    print(f'手续费明细：净手续费：{formalities_fee}元，过户费：{transfer_fee:.2f}元，经手费：{handling_cost:.2f}元，证管费：{management_fee:.2f}元，印花税：{stamp_duty:.2f}元，总共：{total_fee:.2f}元')
    return total_fee


# ------------------------------早上9点 sell -------------------------------------
@app.post("/sell")
async def sell_item(req: BuyRequest):
    # 解析昨天买入的股票信息和资金
    benjin = req.benjin
    holdings = req.data
    holdings_df = pd.DataFrame([
        {
            "代码": item.code,
            "昨天价格": float(item.price),
            "买入数量": int(item.amount)
        }
        for item in holdings
    ])
    # 获取当前股票数据
    ten_df = stock_zh_a_spot_em_self()
    ten_df = ten_df.dropna()

    # 排除创业板
    ten_df = ten_df[~ten_df['代码'].str.startswith(('300', '301', '688'))]
    
    # 保存上午的数据，用于统计股票当天的涨幅
    ten_df.to_csv('D:/yyb/github/draft/invest/shangwu.csv', index=False)

    # 如果没有持仓直接返回
    if holdings_df.empty:
        return {
            "data": [],
            "benjin": benjin
        }

    # 删除删除当前包含任何NaN值的行
    current_df = ten_df.dropna()
    current_df = current_df[['代码', '名称', '最新价', '量比', '涨跌幅', '换手率', '总市值']]

    # 按代码 merge（核心）
    current_df = current_df.merge(
        holdings_df,
        on="代码",
        how="inner"   # 只保留昨天买入过的股票
    )

    # 计算每只股票的卖出金额和手续费
    current_df['卖出金额'] = current_df['最新价'] * current_df['买入数量']
    current_df['手续费'] = current_df['卖出金额'].apply(lambda x: handling_fee(x, 'sell'))
    current_df['收益'] = (current_df['最新价'] - current_df['昨天价格']) * current_df['买入数量'] - current_df['手续费']
    current_df.to_csv('D:/yyb/github/draft/invest/sell_results.csv', index=False)
    print(current_df)

    # 本金 = 原本金 + 卖出金额 - 手续费
    new_benjin = benjin + current_df['卖出金额'].sum() - current_df['手续费'].sum()
    new_benjin = round(new_benjin, 2)

    return {
        "data": [],
        "benjin": new_benjin
    }


# ------------------------------ 下午2点半 buy -------------------------------------------------------------------
# 集中资金买入函数
def round_down_to_hundreds(ben, price):
    """向下取到百位的整数倍"""
    max_quantity = ben // price
    return (max_quantity // 100) * 100


def allocate_capital_with_units(buy_df, benjin):
    df = buy_df.copy()
    actual_amounts = []
    count_list = []

    for latest_price in df['最新价']:
        if benjin // latest_price >= 100:
            count = round_down_to_hundreds(benjin, latest_price)
            count_list.append(count)
            actual_amounts.append(latest_price*count)
            benjin = benjin - latest_price * count
        else:
            actual_amounts.append(np.nan)
            count_list.append(np.nan)
    df['买入数量'] = count_list
    df['实际买入'] = actual_amounts
    df = df.dropna()
    
    # 打印买入信息
    for idx, row in df.iterrows():
        print(f"买入股票：代码={row['代码']}, 名称={row['名称']}, 价格={row['最新价']}, 数量={row['买入数量']}, 金额={row['实际买入']:.2f}元")
    
    # 每只股票单独计算手续费
    df['手续费'] = df['实际买入'].apply(lambda x: handling_fee(x, 'buy'))
    total_handling_fees = df['手续费'].sum()
    benjin = benjin - total_handling_fees
    benjin = round(benjin, 2)
    print(f'结余：{benjin}元')
    return df, benjin


@app.post("/buy")
async def buy_item(req: BuyRequest):
    benjin = req.benjin
    # 获取股票数据，akshare失败时使用备用方案
    df_zh = stock_zh_a_spot_em_self()

    shangwu_df = pd.read_csv('D:/yyb/github/draft/invest/shangwu.csv')

    # 重命名列
    shangwu_df = shangwu_df[['代码', '最新价']].rename(columns={'最新价': '早上价格'})

    shangwu_df['代码'] = shangwu_df['代码'].astype(str).str.zfill(6)

    # 去重：同一股票代码只保留第一条记录
    shangwu_df = shangwu_df.drop_duplicates(subset=['代码'], keep='first')

    # 只保留需要的列
    df_keep = df_zh[['代码', '名称', '最新价', '量比', '涨跌幅', '换手率', '总市值']]

    # 删除包含任何NaN值的行
    df_cleaned = df_keep.dropna()

    # 排除掉创业板块的股票
    no_cyb = df_cleaned[~df_cleaned['代码'].str.startswith(('300', '301'))]

    no_cyb.sort_values('换手率', ascending=False, inplace=True)

    # 将两个表做链接
    no_cyb = no_cyb.merge(shangwu_df, on='代码', how='left')
    # 计算当日涨幅（百分比）
    no_cyb['当日涨幅'] = ((no_cyb['最新价'] - no_cyb['早上价格']) / no_cyb['早上价格'] * 100)


    # -----------------------------------------筛选条件---------------------------------------------------
    df_filtered = no_cyb[
        (no_cyb['总市值'] < 20000000000) &  # 市值小于两百亿
        (no_cyb['换手率'] > 5) & (no_cyb['换手率'] < 10) & # 换手率在5-10之间
        (no_cyb['量比'] > 1) &                # 量比大于1
        (no_cyb['涨跌幅'] > 3) & (no_cyb['涨跌幅'] < 5) &   # 涨幅在3%-5%之间
        (no_cyb['当日涨幅'] > 0)    # 当天是上涨趋势
    ].copy()
    # -----------------------------------------筛选条件---------------------------------------------------

    print(df_filtered)
    # 将这个表格保存到本地
    # df_filtered.to_csv('D:/yyb/github/draft/invest/jvji.csv', index=False)
    print("----------------------------------------------")
    if df_filtered.empty:
        return {"data": [], "benjin": benjin}
    

    # 资金分配
    df, last_money = allocate_capital_with_units(df_filtered, benjin)

    if df.empty:
        return {"data": [], "benjin": benjin}
    
    # ===== 生成返回结构 =====
    result = []

    for _, row in df.iterrows():
        result.append({
            "code": str(row["代码"]).zfill(6),
            "name": row["名称"],
            "price": str(row["最新价"]),
            "amount": str(int(row["买入数量"]))
        })

    return {
        "data": result,
        "benjin": last_money
    }



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
