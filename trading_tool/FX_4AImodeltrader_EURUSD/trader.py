import MetaTrader5 as mt5
import pandas as pd
import joblib
import numpy as np
import time
from datetime import datetime

# ===== 設定 =====
SYMBOL = "EURUSD"
LOT = 0.1          # ロット数（デモ口座は0.1～1.0推奨）
RISK_PER_TRADE = 0.01  # 1%リスク（口座残高の1%まで損切り）
LEVERAGE = 1000    # あなたの設定

# MT5接続
if not mt5.initialize():
    print("MT5初期化失敗")
    exit()

# 最新モデル読み込み
model_name = max([f for f in os.listdir("models") if f.endswith(".pkl") and "RandomForest" in f or "XGBoost" in f])
model = joblib.load(f"models/{model_name}")
print(f"✅ 使用モデル：{model_name}")

# 特徴量の名前（feature_engineer.pyと一致させる）
FEATURES = ['ma_5', 'ma_20', 'ma_100', 'rsi', 'bb_upper', 'bb_lower',
            'macd', 'macd_signal', 'atr', 'price_change_pct']

def get_latest_data():
    rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M5, 0, 200)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

    # 指標追加（feature_engineer.pyと同じ処理）
    df['ma_5'] = df['close'].rolling(5).mean()
    df['ma_20'] = df['close'].rolling(20).mean()
    df['ma_100'] = df['close'].rolling(100).mean()

    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    bb_middle = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = bb_middle + (bb_std * 2)
    df['bb_lower'] = bb_middle - (bb_std * 2)

    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9).mean()

    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    tr = ranges.max(axis=1)
    df['atr'] = tr.rolling(14).mean()

    df['price_change_pct'] = df['close'].pct_change()
    df.dropna(inplace=True)

    return df.tail(1)[FEATURES]

def place_order(signal):
    point = mt5.symbol_info(SYMBOL).point
    price = mt5.symbol_info_tick(SYMBOL).ask if signal == 1 else mt5.symbol_info_tick(SYMBOL).bid

    # 損切り・利益確定（ATRベース）
    atr = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M5, 0, 20)[-1]['high'] - mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M5, 0, 20)[-1]['low']
    sl = price - (atr * 3) if signal == 1 else price + (atr * 3)
    tp = price + (atr * 6) if signal == 1 else price - (atr * 6)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT,
        "type": mt5.ORDER_TYPE_BUY if signal == 1 else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 234000,
        "comment": "AI-Trader",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("注文失敗：", result.comment)
    else:
        print(f"✅ 注文成功：{'買い' if signal == 1 else '売り'} @ {price}")

# メインループ
print("🤖 AIトレーダー起動中...（5分ごとに判定）")
while True:
    try:
        latest = get_latest_data()
        if len(latest) > 0:
            X_pred = latest.values.reshape(1, -1)
            signal = model.predict(X_pred)[0]
            print(f"[{datetime.now()}] モデル予測：{'買い' if signal == 1 else '売り'}")

            # 現在のポジション確認（重複注文防止）
            positions = mt5.positions_get(symbol=SYMBOL)
            if len(positions) == 0:
                place_order(signal)
            elif len(positions) > 0 and positions[0].type != (mt5.ORDER_TYPE_BUY if signal == 1 else mt5.ORDER_TYPE_SELL):
                # 反対方向ならクローズして新規
                mt5.PositionClose(SYMBOL)
                time.sleep(1)
                place_order(signal)

        time.sleep(300)  # 5分待機（M5足に同期）
    except Exception as e:
        print("エラー：", str(e))
        time.sleep(60)
