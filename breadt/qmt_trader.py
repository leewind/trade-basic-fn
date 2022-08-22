from loguru import logger
from .trading_system_basic import *
import datetime
from enum import Enum
from .threadlock import SharedCounter

_fetch_lock = SharedCounter()


class QMTSignalDirect(Enum):
    BUY = 48
    SELL = 49


class QMTStockTrade(Enum):
    BUY = 23  # 股票买入，或沪港通、深港通股票买入
    SELL = 24  # 股票卖出，或沪港通、深港通股票卖出


class QMTCreditTrade(Enum):
    CREDICT_BUY = 27  # 融资买入
    CREDICT_SELL = 28  # 融券卖出
    BUY_FOR_RETURN_STOCK = 29  # 买券还券
    DIRECT_FOR_RETURN_STOCK = 30  # 直接还券
    SELL_FOR_RETURN_MONEY = 31  # 卖券还款
    DIRECT_FOR_RETURN_MONEY = 32  # 直接还款
    CREDICT_CASH_BUY = 33  # 信用账号股票买入
    CREDICT_SIMPLY_SELL = 34  # 信用账号股票卖出


class QMTTrader:
    def __init__(
        self,
        ContextInfo,
        get_trade_detail_data,
        passorder,
        cancel_order=None,
        name="qmt",
    ) -> None:
        self.get_trade_detail_data = get_trade_detail_data
        self.passorder = passorder
        self.cancel = cancel_order
        self.ct = ContextInfo
        self.name = name

    def order(
        self, bar, symbol, price, quanty, account_type, account_id, is_debt_buy=False
    ):
        _fetch_lock.incr()
        logger.info("QMTTrader 接收到下单信息 {}".format(account_type))
        if account_type.upper() == "STOCK":
            self.order_impl(bar, symbol, price, quanty, account_id)
        elif account_type.upper() == "CREDIT":
            self.credit_order_impl(bar, symbol, price, quanty, account_id, is_debt_buy)
        _fetch_lock.decr()

    def order_impl(self, bar, symbol, price, quanty, account_id):
        logger.info(
            "交易提交: {} price:{}, quanty:{}, symbol:{}, accountid:{}".format(
                symbol, price, quanty, symbol, account_id
            )
        )

        opType = QMTStockTrade.BUY
        if quanty < 0:
            opType = QMTStockTrade.SELL

        self.passorder(
            opType.value,
            1101,
            account_id,
            symbol,
            14,
            -1,
            abs(quanty),
            self.name,
            1,
            self.ct,
        )
        logger.info("stock单次交易提交完成，已被接收")

    def credit_order_impl(self, bar, symbol, price, quanty, account_id, is_debt_buy):
        logger.info(
            "交易提交: {} price:{}, quanty:{}, symbol:{}, accountid:{}".format(
                symbol, price, quanty, symbol, account_id
            )
        )

        opType = (
            QMTCreditTrade.CREDICT_CASH_BUY
            if not is_debt_buy
            else QMTCreditTrade.CREDICT_BUY
        )

        if quanty < 0:
            opType = QMTCreditTrade.CREDICT_SIMPLY_SELL

        self.passorder(
            opType.value,
            1101,
            account_id,
            symbol,
            14,
            -1,
            abs(quanty),
            self.name,
            1,
            self.ct,
        )
        logger.info("credit单次交易提交完成，已被接收")

    def cancel_order(self, orderId, account_id, accountType):
        if self.cancel is None:
            logger.error("cancel对象没有传入")
            return

        _fetch_lock.incr()
        self.cancel(orderId, account_id, accountType, self.ct)
        _fetch_lock.decr()

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

        account = BreadtAccount(acct_info[0].m_dAvailable)

        return account

    def get_deal(self, accountid, accounttype, symbol, direction):
        deal_info = self.get_trade_detail_data(
            accountid, accounttype, "deal", self.name
        )
        code = symbol.split(".")[0]

        contracts = []
        for deal in deal_info:
            if deal.m_strInstrumentID == code and deal.m_nOffsetFlag == direction:
                odeal = BreadtTradeOrder(
                    deal.m_strInstrumentID,
                    self.parse_direction(deal.m_nOffsetFlag),
                    deal.m_dPrice,
                    deal.m_nVolume,
                    datetime.datetime.strptime(
                        deal.m_strTradeDate + " " + deal.m_strTradeTime,
                        "%Y%m%d %H%M%S",
                    ),
                )
                contracts.append(odeal)

        return contracts

    def get_all_orders(self, accountid, accounttype):
        order_info = self.get_trade_detail_data(
            accountid, accounttype, "order", self.name
        )

        orders = []
        for order in order_info:
            ocontract = BreadtTradeContract(
                order.m_strOrderSysID,
                order.m_strInstrumentID,
                self.parse_direction(order.m_nOffsetFlag),
                order.m_dTradedPrice,
                order.m_nVolumeTraded,
                order.m_nVolumeTotalOriginal,
                datetime.datetime.strptime(
                    order.m_strInsertDate + " " + order.m_strInsertTime,
                    "%Y%m%d %H%M%S",
                ),
                order.m_nOrderStatus,
            )
            orders.append(ocontract)

        return orders

    def get_order(self, accountid, accounttype, symbol, direction):
        order_info = self.get_trade_detail_data(
            accountid, accounttype, "order", self.name
        )
        code = symbol.split(".")[0]

        orders = []
        for order in order_info:

            if (
                order.m_strInstrumentID == code
                and order.m_nOffsetFlag == direction
                and order.m_nOrderStatus in [50, 51, 52, 53, 54, 55, 56]
            ):
                ocontract = BreadtTradeContract(
                    order.m_strOrderSysID,
                    order.m_strInstrumentID,
                    self.parse_direction(order.m_nOffsetFlag),
                    order.m_dTradedPrice,
                    order.m_nVolumeTraded,
                    order.m_nVolumeTotalOriginal,
                    datetime.datetime.strptime(
                        order.m_strInsertDate + " " + order.m_strInsertTime,
                        "%Y%m%d %H%M%S",
                    ),
                    order.m_nOrderStatus,
                )
                orders.append(ocontract)

        return orders

    def get_avaliable(self, accountid, accounttype):
        result = 0
        resultlist = self.get_trade_detail_data(accountid, accounttype, "ACCOUNT")
        for obj in resultlist:
            result = obj.m_dAvailable
        return result

    def get_balance(self, accountid, accounttype):
        result = 0
        resultlist = self.get_trade_detail_data(accountid, accounttype, "ACCOUNT")
        for obj in resultlist:
            # result = obj.m_dBalance
            result = obj.m_dAssureAsset
        return result

    def get_holdings(self, accountid, accounttype):
        holdinglist = {}
        resultlist = self.get_trade_detail_data(accountid, accounttype, "POSITION")
        for obj in resultlist:
            holdinglist[
                obj.m_strInstrumentID + "." + obj.m_strExchangeID
            ] = obj.m_nCanUseVolume
        return holdinglist

    def get_position(self, accountid, accounttype, symbol):
        resultlist = self.get_trade_detail_data(accountid, accounttype, "position")
        code = symbol.split(".")[0]

        for position in resultlist:
            if position.m_strInstrumentID == code:
                return position.m_nCanUseVolume

        return 0
