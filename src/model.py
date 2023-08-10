from __future__ import annotations

import datetime
import os
from typing import Literal, TypeAlias

import pandas
from pandas import Series
from pykrx import stock as pykrx_stock

Market: TypeAlias = Literal["KOSPI", "KOSDAQ"]  # no KONEX
MARKETS = ["KOSPI", "KOSDAQ"]  # no KONEX


class Stock:
    ticker: str
    name: str
    market: Market
    prices: Prices

    def __init__(
        self,
        ticker: str,
        name: str,
        market: Market,
        price_dates: list[datetime.date],
    ) -> None:
        self.ticker = ticker
        self.name = name
        self.market = market
        self.prices = Prices(ticker=self.ticker, dates=price_dates)

    def is_condition_1(self, *, to_: datetime.date) -> bool:
        _1 = self.prices.is_gap_rate_over(over=4.0)
        _2 = self.prices.has_rate_and_trade_volume_over_in_days(
            rate_over=15, volume_over=50_000_000_000, days=30
        ) or self.prices.has_rate_and_trade_volume_over_in_days(
            rate_over=30, volume_over=20_000_000_000, days=30
        )
        return _1 and _2

    def is_condition_2(self, *, to_: datetime.date) -> bool:
        _1 = self.prices.is_gap_rate_over(over=3.0)
        _2 = self.prices.has_trade_volume_over_in_days(over=20_000_000_000, days=30)
        _3 = self.prices.is_in_regular_arrangement()
        return _1 and _2 and _3

    def row(self, date: str) -> list:
        return [
            date,
            self.ticker,
            self.name,
            self.market,
            self.prices.previous_last.close if self.prices.previous_last else None,
            self.prices.last.open if self.prices.last else None,
            self.prices.last_gap_rate,
            self.prices.last.high if self.prices.last else None,
            self.prices.last_high_rate,
            self.prices.last.low if self.prices.last else None,
            self.prices.last_low_rate,
        ]

    def __str__(self) -> str:
        return f"{self.ticker} {self.name} {self.market}"


class Prices:
    ticker: str
    dates: list[datetime.date]
    prices: list[Price]

    def __init__(self, *, ticker: str, dates: list[datetime.date]) -> None:
        self.ticker = ticker
        self.dates = dates

        filename = f"tickers/prices/{ticker}.csv"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if os.path.exists(filename):
            df = pandas.read_csv(filename, index_col=0)
        else:
            df = pykrx_stock.get_market_ohlcv(
                self.first_date.strftime("%Y%m%d"),
                self.last_date.strftime("%Y%m%d"),
                ticker,
            )
            df.to_csv(filename)

        self.prices = []
        for date in self.dates:
            try:
                price = Price(date, df.loc[date.strftime("%Y-%m-%d")])
            except KeyError:
                print(f"{ticker}의 날짜 {date}에 가격이 없습니다.")
            else:
                self.prices.append(price)

    @property
    def first_date(self) -> datetime.date:
        return self.dates[-1]

    @property
    def last_date(self) -> datetime.date:
        return self.dates[0]

    def dates_from(self, from_: datetime.date) -> list[datetime.date]:
        return [date for date in self.dates if date >= from_]

    def date_before(self, date: datetime.date, days: int) -> datetime.date:
        return self.dates[self.dates.index(date) + days]

    @property
    def last(self) -> Price | None:
        return self._get_by_date(self.last_date)

    @property
    def last_high_rate(self) -> float | None:
        if self.last is None:
            return None
        return round((self.last.high - self.last.open) / self.last.open * 100, 2)

    @property
    def last_low_rate(self) -> float | None:
        if self.last is None:
            return None
        return round((self.last.low - self.last.open) / self.last.open * 100, 2)

    @property
    def previous_last(self) -> Price | None:
        previous_date = self.dates[1]
        return self._get_by_date(previous_date)

    @property
    def last_gap_rate(self) -> float | None:
        return self._get_gap_rate_by_date(date=self.last_date)

    def is_gap_rate_over(self, *, over: float) -> bool:
        if self.last_gap_rate is None:
            return False
        return over <= self.last_gap_rate

    def has_trade_volume_over_in_days(self, *, over: int, days: int) -> bool:
        from_ = self.date_before(self.last_date, days)
        prices = self._get_all_by_from(from_)
        for price in prices:
            if price.trade_volume >= over:
                return True
        return False

    def has_rate_and_trade_volume_over_in_days(
        self, *, rate_over: float, volume_over: int, days: int
    ) -> bool:
        from_ = self.date_before(self.last_date, days)
        for date in self.dates_from(from_):
            rate = self._get_rate_by_date(date=date)
            price = self._get_by_date(date=date)
            if rate is None or price is None:
                continue
            if rate >= rate_over and price.trade_volume >= volume_over:
                return True
        return False

    def is_in_regular_arrangement(self) -> bool:
        if len(self.prices) < 120:
            return False
        _5 = self._get_moving_average(day=5)
        _20 = self._get_moving_average(day=20)
        _60 = self._get_moving_average(day=60)
        _120 = self._get_moving_average(day=120)
        return _5 > _20 > _60 > _120

    def _get_by_date(self, date: datetime.date) -> Price | None:
        for price in self.prices:
            if price.date == date:
                return price
        return None

    def _get_rate_by_date(self, *, date: datetime.date) -> float | None:
        price = self._get_by_date(date)
        previous_price = self._get_by_date(self.date_before(date, 1))
        if price is None or previous_price is None:
            return None
        return round(
            (price.close - previous_price.close) / previous_price.close * 100, 2
        )

    def _get_gap_rate_by_date(self, *, date: datetime.date) -> float | None:
        price = self._get_by_date(date)
        previous_price = self._get_by_date(self.date_before(date, 1))
        if price is None or previous_price is None:
            return None
        return round(
            (price.open - previous_price.close) / previous_price.close * 100, 2
        )

    def _get_all_by_from(self, from_: datetime.date) -> list[Price]:
        return self._get_all_by_from_and_to(from_, self.last_date)

    def _get_all_by_from_and_to(
        self, from_: datetime.date, to_: datetime.date
    ) -> list[Price]:
        return [price for price in self.prices if from_ <= price.date <= to_]

    def _get_moving_average(self, *, day: int) -> float:
        from_ = self.date_before(self.last_date, day)
        prices = self._get_all_by_from(from_)
        prices = prices[1:]  # remove today
        return round(sum([price.close for price in prices]) / day, 2)


class Price:
    date: datetime.date
    df: Series

    def __init__(self, date: datetime.date, df: Series) -> None:
        self.date = date
        self.df = df

    @property
    def open(self) -> int:
        return self.df["시가"]

    @property
    def close(self) -> int:
        return self.df["종가"]

    @property
    def high(self) -> int:
        return self.df["고가"]

    @property
    def low(self) -> int:
        return self.df["저가"]

    @property
    def volume(self) -> int:
        return self.df["거래량"]

    @property
    def trade_volume(self) -> int:
        return self.df["거래대금"]

    @property
    def rate(self) -> float:
        return self.df["등락률"]

    def __repr__(self) -> str:
        return f"{self.date} {self.df}"
