import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import os

# ===== 設定 =====
SYMBOL = "EURUSD"      # 取引通貨ペア（変更可）
TIMEFRAME = mt5.TIMEFRAME_M5  # 5分足
DAYS_BACK = 730        # ✅ 2年分（730日）を取得

# MT5接続
if not mt5.initialize():
    print("MT5初期化失敗")
    exit()

# 現在時刻から過去2年分の範囲を計算
end_time = datetime.now()
start_time = end_time - timedelta(days=DAYS_BACK)

# データ取得（1回で最大30,000本まで）
rates = mt5.copy_rates_range(SYMBOL, TIMEFRAME, start_time, end_time)
mt5.shutdown()

if rates is None or len(rates) == 0:
    print("データが取得できませんでした。通貨ペア名を確認してください。")
else:
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

    # ファイル保存
    filename = f"data/{SYMBOL}_{DAYS_BACK}days_M5.csv"
    os.makedirs("data", exist_ok=True)
    df.to_csv(filename)
    print(f"✅ {len(df)}本のデータを保存しました：{filename}")
