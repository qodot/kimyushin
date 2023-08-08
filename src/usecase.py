import csv
import datetime
import os

from pykrx import stock as pykrx_stock

from src.model import MARKETS, Stock


def get_all_stocks(*, dates: list[datetime.date]) -> list[Stock]:
    filename = f"tickers/list/{dates[0].strftime('%Y%m%d')}.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if not os.path.exists(filename):
        csv_writer = csv.writer(open(filename, "w"))
        csv_writer.writerow(["ticker", "name", "market"])
        for market in MARKETS:
            tickers = pykrx_stock.get_market_ticker_list(market=market)
            for ticker in tickers:
                name = pykrx_stock.get_market_ticker_name(ticker)
                csv_writer.writerow([ticker, name, market])

    csv_reader = csv.reader(open(filename, "r"))
    _header = next(csv_reader)
    stocks = []
    for idx, row in enumerate(csv_reader):
        ticker = row[0]
        name = row[1]
        market = row[2]
        print(f"가격 정보 조회 중: {idx + 1} {ticker} {name} {market}")
        stocks.append(Stock(ticker=ticker, name=name, market=market, price_dates=dates))

    return stocks
