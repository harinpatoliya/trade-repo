import unittest
import os
from database import init_db, buy_stock, sell_stock, get_holdings, get_account, get_history, reset_account

class TestTradingApp(unittest.TestCase):
    def setUp(self):
        init_db()
        reset_account()

    def test_initial_balance(self):
        account = get_account()
        self.assertEqual(account['balance'], 300000)

    def test_buy_stock(self):
        success, msg = buy_stock("TATASTEEL", "NSE", 10, 100.0, "MARKET")
        self.assertTrue(success)

        account = get_account()
        self.assertEqual(account['balance'], 299000) # 300000 - 1000

        holdings = get_holdings()
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings.iloc[0]['symbol'], "TATASTEEL")
        self.assertEqual(holdings.iloc[0]['quantity'], 10)
        self.assertEqual(holdings.iloc[0]['average_price'], 100.0)

    def test_sell_stock(self):
        buy_stock("TATASTEEL", "NSE", 10, 100.0, "MARKET")

        success, msg = sell_stock("TATASTEEL", "NSE", 5, 110.0, "MARKET")
        self.assertTrue(success)

        account = get_account()
        # Spent 1000. Balance 299000.
        # Sold 5 * 110 = 550. Balance 299550.
        self.assertEqual(account['balance'], 299550)

        holdings = get_holdings()
        self.assertEqual(holdings.iloc[0]['quantity'], 5)

        history = get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history.iloc[0]['pnl'], 50.0) # (110-100)*5
        self.assertEqual(history.iloc[0]['pnl_percent'], 10.0)

    def test_insufficient_funds(self):
        success, msg = buy_stock("MRF", "NSE", 1, 400000.0, "MARKET")
        self.assertFalse(success)
        self.assertEqual(msg, "Insufficient funds")

    def test_insufficient_holdings(self):
        success, msg = sell_stock("RELIANCE", "NSE", 1, 2000.0, "MARKET")
        self.assertFalse(success)
        self.assertEqual(msg, "Insufficient holdings")

if __name__ == '__main__':
    unittest.main()
