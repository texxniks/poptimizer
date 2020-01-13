"""Формирование примеров для обучения в формате PyTorch."""
from typing import Optional, Dict

import pandas as pd
import torch
from torch.utils import data

from poptimizer.ml.feature.std import LOW_STD


def price_feature(price: pd.Series, item: int, params: dict) -> torch.Tensor:
    """Динамика изменения цены нормированная на первоначальную цену."""
    history_days = params["history_days"]
    price = price.iloc[item + 1 : item + history_days] / price.iloc[item] - 1
    return torch.tensor(price)


def div_feature(
    price: pd.Series, div: pd.Series, item: int, params: dict
) -> torch.Tensor:
    """Динамика накопленных дивидендов нормированная на первоначальную цену."""
    history_days = params["history_days"]
    div = div.iloc[item + 1 : item + history_days].cumsum()
    div = div / price.iloc[item]
    return torch.tensor(div)


def weight_feature(
    price: pd.Series, div: pd.Series, item: int, params: dict
) -> torch.Tensor:
    """Обратная величина СКО полной доходности обрезанная для низких значений."""
    history_days = params["history_days"]
    price = price.iloc[item : item + history_days]
    div = div.iloc[item + 1 : item + history_days]
    price0 = price.shift(1)
    returns = (price + div) / price0
    returns = returns.iloc[1:]
    std = max(returns.std(), LOW_STD)
    weight = 1 / std ** 2
    return torch.tensor(weight)


def label_feature(
    price: pd.Series, div: pd.Series, item: int, params: dict
) -> torch.Tensor:
    """Линейная комбинация полной и дивидендной доходности после окончания периода."""
    history_days = params["history_days"]
    last_history_price = price.iloc[item + history_days - 1]
    forecast_days = params["forecast_days"]
    last_forecast_price = price.iloc[item + history_days - 1 + forecast_days]
    all_div = div.iloc[item + history_days : item + history_days + forecast_days]
    all_div = all_div.sum()
    label = (last_forecast_price - last_history_price) * (1 - params["div_share"])
    label = label + all_div
    label = label / last_history_price
    return torch.tensor(label)


class OneTickerDataset(data.Dataset):
    """Готовит обучающие примеры для одного тикера.

    Признаки:
    - Прирост цены акции в течении периода нормированный на цену акции в начале периода.
    - Дивиденды рассчитываются нарастающим итогом в течении периода и нормируются на цену акции в начале
    периода.

    Метки:
    - Доходность в течении нескольких дней после окончания исторического периода. Может быть
    произвольной пропорцией между дивидендной или полной доходностью.

    Вес обучающих примеров:
    - Обратный квадрату СКО доходности - для имитации метода максимального
    правдоподобия. Низкое СКО обрезается, для избежания деления на 0.

    Каждая составляющая помещается в словарь в виде torch.Tensor.
    """

    def __init__(
        self,
        price: pd.Series,
        div: pd.Series,
        params: dict,
        dataset_end: Optional[pd.Timestamp],
    ):
        start = price.first_valid_index()
        self.price = price[start:]
        self.div = div[start:]
        self.params = params
        self.dataset_end = dataset_end or price.index[-1]

    def __getitem__(self, item) -> Dict[str, torch.Tensor]:
        price = self.price
        div = self.div
        params = self.params

        rez = dict(
            price=price_feature(price, item, params),
            div=div_feature(price, div, item, params),
            weight=weight_feature(price, div, item, params),
        )

        if self.dataset_end != price.index[-1]:
            rez["label"] = label_feature(price, div, item, params)
        return rez

    def __len__(self) -> int:
        return (
            self.price.index.get_loc(self.dataset_end) + 2 - self.params["history_days"]
        )


def get_dataset(
    price: pd.DataFrame,
    div: pd.DataFrame,
    params: dict,
    dataset_start: Optional[pd.Timestamp] = None,
    dataset_end: Optional[pd.Timestamp] = None,
) -> data.Dataset:
    """Сформировать набор обучающих примеров для заданных тикеров.

    :param price:
        Данные по ценам акций.
    :param div:
        Данные по дивидендам акций.
    :param params:
        Параметры формирования обучающих примеров.
    :param dataset_start:
        Первая дата для формирования х-ов обучающих примеров. Если отсутствует, то будут
        использоваться дынные с начала статистики.
    :param dataset_end:
        Последняя дата для формирования х-ов обучающих примеров. Если отсутствует, то будет
        использована last_date.
    :return:
        Искомый набор примеров для сети.
    """
    div = div.loc[dataset_start:]
    price = price.loc[dataset_start:]
    tickers = price.columns
    return data.ConcatDataset(
        [
            OneTickerDataset(price[ticker], div[ticker], params, dataset_end)
            for ticker in tickers
        ]
    )
