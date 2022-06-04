class Trader:
    def __init__(self, trader, accountid, accounttype) -> None:
        self.trader = trader
        self.accountid = accountid
        self.accounttype = accounttype

    def get_account(self):
        return self.trader.get_account(self.accountid, self.accounttype)

    def get_deal(self, stock, direction):
        return self.get_deal(self.accountid, self.accounttype, stock, direction)

    def get_order(self, stock, direction):
        return self.get_order(self, self.accountid, self.accounttype, stock, direction)

    def order(self, bar, symbol, price, quanty):
        self.order(bar, symbol, price, quanty, self.accounttype, self.accountid)
