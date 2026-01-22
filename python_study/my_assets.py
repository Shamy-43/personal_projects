#まずは全体の流れ
# APIでビットコインの価格を取ってくる
# 自分の持っている「枚数」を変数で作る
# 「価格 × 枚数」で仮想通貨の時価を出す
# 銀行残高などと足して、合計を表示する

import requests

# 1. 最新価格の取得
url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=jpy"
response = requests.get(url)
data = response.json()
btc_price = data["bitcoin"]["jpy"]

# 2. 自分の資産データ
btc_owned = 0.085  # 例：0.085枚持っているとします
bank_balance = 300000 # 銀行口座残高
stock_assets = 500000 # 証券口座残高

# 3. 計算
#仮想通貨の計算と、銀行口座+証券残高合計の計算
crypto_total = btc_price * btc_owned
total_assets = bank_balance + crypto_total + stock_assets

# 4. 表示（カンマ区切りでプロ仕様に！）
print("--- 現在の資産状況 ---")
print(f"ビットコイン時価: {btc_price:,} 円")
print(f"仮想通貨資産額  : {int(crypto_total):,} 円")
print(f"銀行・証券残高  : {bank_balance + stock_assets:,} 円")
print("-----------------------")
print(f"総資産額        : {int(total_assets):,} 円")