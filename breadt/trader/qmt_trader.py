from loguru import logger
from ..base import *
import datetime


class QMTTrader:
    def __init__(self, get_trade_detail_data) -> None:
        self.get_trade_detail_data = get_trade_detail_data

    def parse_direction(self, direction):
        if direction == 48:
            return BreadtSignalDirect.BUY

        if direction == 49:
            return BreadtSignalDirect.SELL

    def get_account(self, accountid, accounttype):
        acct_info = self.get_trade_detail_data(accountid, accounttype, "account")

        if acct_info is None or len(acct_info) == 0:
            logger.error("未获取账号信息")
            return None

        account = BreadtAccount(acct_info[0].m_dEnableBailBalance)

        return account

    def get_deal(self, accountid, accounttype, stock, direction):
        deal_info = self.get_trade_detail_data(accountid, accounttype, "deal")
        code = stock["symbol"].split(".")[0]

        contracts = []
        for deal in deal_info:
            if deal.m_strInstrumentID == code and deal.m_nDirection == direction:
                odeal = BreadtTradeOrder(
                    deal.m_strInstrumentID,
                    self.parse_direction(deal.m_nDirection),
                    deal.m_dPrice,
                    deal.m_nVolume,
                    datetime.datetime.strptime(
                        deal.m_strTradeDate + " " + deal.m_strTradeTime,
                        "%Y%m%d %H:%M:%S",
                    ),
                )
                contracts.append(odeal)

        return contracts

    def get_order(self, accountid, accounttype, stock, direction):
        order_info = self.get_trade_detail_data(accountid, accounttype, "order")
        code = stock["symbol"].split(".")[0]

        orders = []
        for order in order_info:

            if (
                order.m_strInstrumentID == code
                and order.m_nDirection == direction
                and order.m_nOrderStatus in [50, 51, 52, 53, 54, 55, 56]
            ):
                ocontract = BreadtTradeContract(
                    order.m_strOrderSysID,
                    order.m_strInstrumentID,
                    self.parse_direction(order.m_nDirection),
                    order.m_dTradedPrice,
                    order.m_nVolumeTraded,
                    order.m_nVolumeTotalOriginal,
                    datetime.datetime.strptime(
                        order.m_strInsertDate + " " + order.m_strInsertTime,
                        "%Y%m%d %H:%M:%S",
                    ),
                )
                orders.append(ocontract)

        return orders
