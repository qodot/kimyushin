import csv
import datetime
import os

import typer

from src.usecase import get_all_stocks
from src.util import get_previous_business_days


def main(date: str) -> None:
    date_ = datetime.datetime.strptime(date, "%Y%m%d").date()

    filename_1 = f"results/{date_.strftime('%Y%m%d')}_condition_1.csv"
    filename_2 = f"results/{date_.strftime('%Y%m%d')}_condition_2.csv"
    os.makedirs(os.path.dirname(filename_1), exist_ok=True)
    os.makedirs(os.path.dirname(filename_2), exist_ok=True)
    csv_writer_1 = csv.writer(open(filename_1, "w"))
    csv_writer_2 = csv.writer(open(filename_2, "w"))
    header = [
        "날짜",
        "티커",
        "이름",
        "마켓",
        "전일종가",
        "당일시가",
        "갭상승률",
        "고가",
        "고가%",
        "저가",
        "저가%",
    ]
    csv_writer_1.writerow(header)
    csv_writer_2.writerow(header)

    dates = get_previous_business_days(to_=date_, count=121)
    stocks = get_all_stocks(dates=dates)
    print(f"총 종목 수: {len(stocks)}")
    for idx, stock in enumerate(stocks):
        print(f"조건 계산 중: {idx + 1}번째 {stock}")

        if stock.is_condition_1(to_=date_):
            csv_writer_1.writerow(stock.row(date))
        elif stock.is_condition_2(to_=date_):
            csv_writer_2.writerow(stock.row(date))


if __name__ == "__main__":
    typer.run(main)
