# Manager selection: which slots of the portfolio are implemented by a
# manager instead of the passive ETF / proxy.
#
# Slot (UNIVERSE label) -> manager. port_con still decides the weight of the
# slot; the manager is what we actually hold in it, from the day the manager
# has prices. Before that the slot keeps the passive ETF.
#
#   symbol     Yahoo symbol of the manager
#   leverage   the manager's leverage (1 = none)
#   unlevered  Yahoo symbol of an unlevered ETF of what the manager invests in.
#              Attribution shows (leverage - 1) x (unlevered - cash) as
#              "Manager leverage"; everything else vs the slot's passive ETF
#              (region, stock picking, fees) is "Manager".

MANAGERS = {
    "ZXLF": {
        "symbol": "HFIN.TO",   # Hamilton Enhanced Canadian Financials ETF, from 2022-01
        "leverage": 1.25,
        "unlevered": "XFN.TO",  # iShares S&P/TSX Capped Financials
    },
}
