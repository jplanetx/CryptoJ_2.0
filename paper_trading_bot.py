import time
import pandas as pd
import requests
import curses

class MarketDataHandler:
    """Fetch real-time market data from Coinbase Advanced API"""
    def __init__(self, trading_pair="BTC-USD"):
        self.trading_pair = trading_pair
        self.api_url = f"https://api.coinbase.com/v2/prices/{trading_pair}/spot"

    def get_price(self):
        """Fetch current market price"""
        try:
            response = requests.get(self.api_url)
            data = response.json()
            return float(data["data"]["amount"])
        except Exception as e:
            print(f"❌ Error fetching price: {e}")
            return None


class TradeEngine:
    """Generates trading signals using EMA logic"""
    def __init__(self):
        self.prices = []
        self.last_buy_price = None  # Track last buy price to prevent repeat buys

    def update_price(self, price):
        """Add new price data and maintain rolling window"""
        self.prices.append(price)
        if len(self.prices) > 50:
            self.prices.pop(0)

    def generate_signal(self):
        """Determine buy/sell signals based on EMA logic"""
        if len(self.prices) < 16:
            print("⏳ Waiting for more price data (Need 16+ price points)")
            return "HOLD"

        short_ema = sum(self.prices[-8:]) / 8  # Short-term EMA (Increased for better filtering)
        long_ema = sum(self.prices[-16:]) / 16  # Long-term EMA (Increased for better filtering)

        print(f"📊 Short EMA: {short_ema:.2f}, Long EMA: {long_ema:.2f}")

        # Prevent repeat buys at the same price (Require 0.1% increase before re-buying)
        if short_ema > long_ema and (self.last_buy_price is None or self.prices[-1] > self.last_buy_price * 1.001):
            self.last_buy_price = self.prices[-1]  # Store last buy price
            print("✅ BUY Signal Generated")
            return "BUY"
        elif short_ema < long_ema:
            print("❌ SELL Signal Generated")
            return "SELL"
        else:
            print("⚖️ HOLD Signal (No Trade)")
            return "HOLD"


class PaperTradeSimulator:
    """Handles simulated trades and maintains virtual balance"""
    def __init__(self, initial_balance=230):
        self.balance = initial_balance
        self.holdings = 0
        self.trade_history = []
        self.wins = 0
        self.losses = 0

    def execute_trade(self, signal, price):
        """Simulate trade execution"""
        print(f"🔍 Checking Trade Execution: Signal={signal}, Price={price}")

        if signal == "BUY" and self.balance > 0:
            allocation = self.balance * 0.75  # Use 75% of balance per trade
            self.holdings = allocation / price
            self.balance -= allocation
            self.trade_history.append(("BUY", price, self.holdings, self.balance))
            print(f"✅ BUY @ {price:.2f} | Holdings: {self.holdings:.6f} BTC | New Balance: ${self.balance:.2f}")
            return f"BUY executed at {price:.2f}"

        elif signal == "SELL" and self.holdings > 0:
            proceeds = self.holdings * price
            buy_price = self.trade_history[-1][1]  # Get last buy price
            profit = proceeds - (buy_price * self.holdings)
            profit_percent = (price - buy_price) / buy_price * 100  

            # Only sell if profit is over 1% OR price starts strongly dropping
            if profit_percent > 1 or short_ema < long_ema * 0.999:
                self.balance += proceeds
                self.holdings = 0
                self.trade_history.append(("SELL", price, proceeds, self.balance, profit))

                if profit > 0:
                    self.wins += 1
                else:
                    self.losses += 1

                print(f"✅ SELL @ {price:.2f} | Profit: ${profit:.2f} ({profit_percent:.2f}%) | New Balance: ${self.balance:.2f}")
                return f"SELL executed at {price:.2f}"

        print("⚠️ No trade executed (Conditions Not Met)")
        return "No trade executed"

    def get_balance(self):
        """Return virtual balance"""
        return self.balance

    def get_trade_summary(self):
        """Return win/loss statistics"""
        return self.wins, self.losses, len(self.trade_history)


def trade_dashboard(stdscr, market, strategy, simulator):
    """Terminal UI to track trading performance"""
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(1000)

    while True:
        stdscr.clear()
        price = market.get_price()
        if price:
            strategy.update_price(price)
            signal = strategy.generate_signal()
            trade_message = simulator.execute_trade(signal, price)

        # Draw UI
        stdscr.addstr(1, 2, "🚀 Crypto Paper Trading Bot", curses.A_BOLD)
        stdscr.addstr(3, 2, f"💰 Current Price: ${price:.2f}")
        stdscr.addstr(4, 2, f"💵 Balance: ${simulator.get_balance():.2f}")
        stdscr.addstr(5, 2, f"🔹 Holdings: {simulator.holdings:.6f} BTC")
        
        # Performance Summary
        wins, losses, total_trades = simulator.get_trade_summary()
        stdscr.addstr(7, 2, "📊 Performance Summary:")
        stdscr.addstr(8, 2, f"📈 Total Trades: {total_trades}")
        stdscr.addstr(9, 2, f"✅ Wins: {wins} | ❌ Losses: {losses}")
        if total_trades > 0:
            win_rate = (wins / total_trades) * 100
            stdscr.addstr(10, 2, f"🏆 Win Rate: {win_rate:.2f}%")
        
        # Recent Trades
        stdscr.addstr(12, 2, "📝 Last 5 Trades:")
        for idx, trade in enumerate(simulator.trade_history[-5:]):
            stdscr.addstr(13 + idx, 2, f"{trade[0]} @ {trade[1]:.2f} | Balance: ${trade[3]:.2f}")

        # Trade Status
        stdscr.addstr(19, 2, f"🛠️ Last Trade: {trade_message}")

        stdscr.refresh()
        time.sleep(5)

        if stdscr.getch() == ord("q"):  # Press 'q' to quit
            break


# Initialize bot components
market = MarketDataHandler()
strategy = TradeEngine()
simulator = PaperTradeSimulator()

# Start Terminal UI
curses.wrapper(trade_dashboard, market, strategy, simulator)
