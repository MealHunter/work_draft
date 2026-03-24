import os

for k in [
    "HTTP_PROXY", "HTTPS_PROXY",
    "http_proxy", "https_proxy",
    "ALL_PROXY", "all_proxy"
]:
    os.environ.pop(k, None)



import akshare as ak

ten_df = ak.stock_zh_a_spot_em()
print(ten_df.head())


# import os
# for k in [
#     "HTTP_PROXY", "HTTPS_PROXY",
#     "http_proxy", "https_proxy",
#     "ALL_PROXY", "all_proxy"
# ]:
#     os.environ.pop(k, None)

# import akshare as ak

# df = ak.stock_zh_a_hist(symbol="600000", period="daily")
# print(df.tail())
