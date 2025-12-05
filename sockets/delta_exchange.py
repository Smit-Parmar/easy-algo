import websocket
import json
from datetime import datetime


# production websocket base url
WEBSOCKET_URL = "wss://socket.india.delta.exchange"

def on_error(ws, error):
    print(f"Socket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"Socket closed with status: {close_status_code} and message: {close_msg}")

def on_open(ws):
  print(f"Socket opened")
  # subscribe tickers of perpetual futures - BTCUSD & ETHUSD, call option C-BTC-95200-200225 and put option - P-BTC-95200-200225
#   subscribe(ws, "v2/ticker", ["BTCUSD", "ETHUSD", "C-BTC-95200-200225", "P-BTC-95200-200225"])
#   subscribe(ws, "v2/ticker", ["ETHUSD"])

  # subscribe 1 minute ohlc candlestick of perpetual futures - MARK:BTCUSD(mark price) & ETHUSD(ltp), call option C-BTC-95200-200225(ltp) and put option - P-BTC-95200-200225(ltp).
#   subscribe(ws, "candlestick_1m", ["MARK:BTCUSD", "ETHUSD", "C-BTC-95200-200225", "P-BTC-95200-200225"])
  subscribe(ws, "candlestick_1m", ["ETHUSD"])

def subscribe(ws, channel, symbols):
    payload = {
        "type": "subscribe",
        "payload": {
            "channels": [
                {
                    "name": channel,
                    "symbols": symbols
                }
            ]
        }
    }
    ws.send(json.dumps(payload))

def on_message(ws, message):
    # print json response
    data = json.loads(message)
    # print(data)
    if data.get("type") == "v2/ticker":
        symbol = data.get("symbol")
        ltp = data.get("close")
        iso_time = data.get("time")   # already human readable

        print(f"{symbol} | LTP: {ltp} | Time: {iso_time}")
    elif data.get("type") == "candlestick_1m":
        symbol = data["symbol"]
        ltp = data["close"]

        # convert microsecond timestamp to readable time
        ts_micro = data["timestamp"]
        ts = datetime.fromtimestamp(ts_micro / 1e6)
        time_str = ts.strftime("%Y-%m-%d %H:%M:%S.%f")

        print(f"{symbol} | LTP: {ltp} | Time: {time_str}")


if __name__ == "__main__":
  ws = websocket.WebSocketApp(WEBSOCKET_URL, on_message=on_message, on_error=on_error, on_close=on_close)
  ws.on_open = on_open
  ws.run_forever() # runs indefinitely