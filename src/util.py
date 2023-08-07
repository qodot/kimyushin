import datetime

from pykrx import stock as pykrx_stock


def get_previous_business_days(to_: datetime.date, count: int) -> list[datetime.date]:
    from_ = to_ - datetime.timedelta(days=count * 2)
    dates = pykrx_stock.get_previous_business_days(
        fromdate=from_.strftime("%Y%m%d"), todate=to_.strftime("%Y%m%d")
    )
    dates = [date.date() for date in dates]
    dates.reverse()
    return dates[:count]
