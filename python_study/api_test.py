import requests

# CoinGeckoというサイトのAPI（窓口）のURL
url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=jpy"

# お願いを送る（リクエスト）
response = requests.get(url)

# 返ってきたデータを解析する
data = response.json()

# ビットコインの価格（jpy）を取り出す
price = data["bitcoin"]["jpy"]

# {price:,} と書くだけで、自動でカンマを入れてくれます
print(f"現在のビットコイン価格は {price:,} 円です！")