import threading
import tushare


class Debt(object):
    _instance_lock = threading.Lock()

    def __init__(self, token, previous_trade_date):
        tushare.set_token(token)
        pro = tushare.pro_api()

        self.debtinfo = pro.margin_detail(trade_date=previous_trade_date)

    def __new__(cls, *args, **kwargs):
        if not hasattr(Debt, "_instance"):
            with Debt._instance_lock:
                if not hasattr(Debt, "_instance"):
                    Debt._instance = object.__new__(cls)

        return Debt._instance

    # 这个地方的symbol要注意，要切到tushare模式下面来
    def get_debt_amount(self, symbol):
        detail = self.debtinfo[self.debtinfo["ts_code"] == symbol]

        if detail is None or len(detail) == 0:
            return 0

        return detail.iloc[0]["rzye"]
