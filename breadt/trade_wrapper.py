from loguru import logger


class Trader:
    def __init__(self, trader, accountid, accounttype) -> None:
        self.trader = trader
        self.accountid = accountid
        self.accounttype = accounttype

    def get_account(self):
        return self.trader.get_account(self.accountid, self.accounttype)

    def get_deal(self, stock, direction):
        return self.trader.get_deal(self.accountid, self.accounttype, stock, direction)

    def get_order(self, stock, direction):
        return self.trader.get_order(self.accountid, self.accounttype, stock, direction)

    def get_all_orders(self):
        return self.trader.get_all_orders(self.accountid, self.accounttype)

    def order(self, bar, symbol, price, quanty, is_debt_buy=False):
        logger.info("TraderWrapp接收到下单请求")
        self.trader.order(
            bar,
            symbol,
            price,
            quanty,
            self.accounttype,
            self.accountid,
            is_debt_buy=is_debt_buy,
        )

    def cancel(self, order_id):
        self.trader.cancel_order(str(order_id), self.accountid, self.accounttype)

    def get_avaliable(self):
        return self.trader.get_avaliable(self.accountid, self.accounttype)

    def get_balance(self):
        return self.trader.get_balance(self.accountid, self.accounttype)

    def get_holdings(self):
        return self.trader.get_holdings(self.accountid, self.accounttype)

    def get_position(self, symbol):
        return self.trader.get_position(self.accountid, self.accounttype, symbol)
