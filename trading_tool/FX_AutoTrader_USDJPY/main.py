
# ---

# ## 📄 4. `main.py` —— **あなたのAI自動売買システムの核（完全実装）**

# ```python
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import configparser
from datetime import datetime, timedelta
import pytz
import time
import os

# ===== 設定読み込み =====
config = configparser.ConfigParser()
with open('config.ini', 'r', encoding='utf-8') as f:
    config.read_file(f)
config.read('config.ini',encoding='UTF-8')
SYMBOL = config['TRADING']['SYMBOL']
LOT_SIZE = float(config['TRADING']['LOT_SIZE'])
LEVERAGE = int(config['TRADING']['LEVERAGE'])
RISK_REWARD_RATIO = int(config['TRADING']['RISK_REWARD_RATIO'])
START_HOUR = int(config['TIME']['START_HOUR'])
END_HOUR = int(config['TIME']['END_HOUR'])
TIMEZONE = config['TIME']['TIMEZONE']
DEMO_MODE = config.getboolean('MODE', 'DEMO_MODE')
LOG_FILE = config['MODE']['LOG_FILE']
DAYS_TO_LOG = int(config['MODE']['DAYS_TO_LOG'])
ENTRY_THRESHOLD = float(config['AI']['ENTRY_THRESHOLD'])

# ===== ログファイル初期化 =====
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
        f.write("DateTime,Signal,Price,SL,TP,Result,Balance\n")

# ===== MT5接続 =====
def connect_mt5():
    if not mt5.initialize():
        print("MT5初期化失敗")
        exit()
    print(f"MT5接続成功：{mt5.version()}")


connect_mt5()

# ===== 現在時刻（日本時間）を取得 =====
def get_jst_time():
    return datetime.now(pytz.timezone(TIMEZONE))

# ===== 取引可能時間かチェック =====
def is_trading_hours():
    now = get_jst_time()
    hour = now.hour
    if START_HOUR <= hour < END_HOUR:
        return True
    else:
        print(f"[{now.strftime('%Y-%m-%d %H:%M')}] 取引時間外：{START_HOUR}:00～{END_HOUR}:00の間のみ取引可能")
        return False

# ===== 技術指標（AIロジック）：EMA + RSI交差判定 =====
def get_signal():
    rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M15, 0, 100)
    if rates is None:
        return None

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    # EMA
    df['ema_fast'] = df['close'].ewm(span=9).mean()
    df['ema_slow'] = df['close'].ewm(span=21).mean()

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # シグナル判定（最新足）
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # ロングシグナル：EMAが上向き、RSIが30以下から復活
    long_condition = (
        prev['ema_fast'] <= prev['ema_slow'] and
        last['ema_fast'] > last['ema_slow'] and
        prev['rsi'] < 30 and
        last['rsi'] > 30
    )

    # ショートシグナル：EMAが下向き、RSIが70以上から下落
    short_condition = (
        prev['ema_fast'] >= prev['ema_slow'] and
        last['ema_fast'] < last['ema_slow'] and
        prev['rsi'] > 70 and
        last['rsi'] < 70
    )

    if long_condition:
        return 'BUY', float(last['close'])
    elif short_condition:
        return 'SELL', float(last['close'])
    else:
        return None, None

# ===== 注文処理（デモモード対応）=====
def place_order(order_type, price):
    sl = 0
    tp = 0
    if order_type == 'BUY':
        sl = price - (price * 0.001)   # 損切り：10pips（USDJPY）
        tp = price + (price * 0.002)   # 利確：20pips
    elif order_type == 'SELL':
        sl = price + (price * 0.001)
        tp = price - (price * 0.002)

    if DEMO_MODE:
        print(f"[DEMO] {order_type} 注文：価格={price:.3f}, SL={sl:.3f}, TP={tp:.3f}")
        log_trade(order_type, price, sl, tp, "DEMO")
        return True
    else:
        # 本番注文（実際のMT5注文）
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": SYMBOL,
            "volume": LOT_SIZE,
            "type": mt5.ORDER_TYPE_BUY if order_type == 'BUY' else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": "AI Trader",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"[本番] {order_type} 注文成功：価格={price:.3f}")
            log_trade(order_type, price, sl, tp, "LIVE")
            return True
        else:
            print(f"注文失敗：{result.comment}")
            return False

# ===== 取引履歴をCSVに保存 =====
def log_trade(signal, price, sl, tp, status):
    now = get_jst_time().strftime('%Y-%m-%d %H:%M:%S')
    balance = mt5.account_info().balance if mt5.initialize() else 0
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        f.write(f"{now},{signal},{price:.5f},{sl:.5f},{tp:.5f},{status},{balance}\n")

# ===== メインループ =====
def main():
    print("=== FX自動売買システム「USDJPY AI Trader」起動 ===")
    print(f"モード: {'デモ（検証）' if DEMO_MODE else '本番'} | ロット: {LOT_SIZE} | レバレッジ: {LEVERAGE}")
    print(f"取引時間: {START_HOUR}:00～{END_HOUR}:00 (日本時間)")
    print("起動中... 毎15分ごとにシグナルをチェックします\n")

    last_check = None

    while True:
        now = get_jst_time()

        # 15分ごとにチェック（MT5負荷軽減）
        if last_check and (now - last_check).seconds < 900:
            time.sleep(60)
            continue
        last_check = now

        # 取引時間外ならスキップ
        if not is_trading_hours():
            time.sleep(3600)  # 1時間待機
            continue

        # シグナル取得
        signal, price = get_signal()
        if signal and price:
            print(f"[{now.strftime('%H:%M')}] シグナル発生：{signal} @ {price:.3f}")
            place_order(signal, price)
        else:
            print(f"[{now.strftime('%H:%M')}] シグナルなし")

        # 1分待機
        time.sleep(60)

if __name__ == "__main__":
    main()
