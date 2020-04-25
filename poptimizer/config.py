"""Основные настраиваемые параметры"""
import logging
import pathlib

import pandas as pd
import torch


class POptimizerError(Exception):
    """Базовое исключение."""


# Воспроизводиломость https://pytorch.org/docs/stable/notes/randomness.html
torch.manual_seed(0)

# Конфигурация логгера
logging.basicConfig(level=logging.INFO)

# Количество колонок в распечатках без переноса на несколько страниц
pd.set_option("display.max_columns", 20)
pd.set_option("display.max_rows", 100)
pd.set_option("display.width", None)

# Путь к директории с отчетам
REPORTS_PATH = pathlib.Path(__file__).parents[1] / "reports"

# Путь к MongoDB и dump с данными по дивидендам
MONGO_PATH = pathlib.Path(__file__).parents[1] / "db"
MONGO_DUMP = pathlib.Path(__file__).parents[1] / "dump"

# Количество торговых дней в году
YEAR_IN_TRADING_DAYS = 12 * 21

# Множитель, для переходя к после налоговым значениям
AFTER_TAX = 1 - 0.13

# Параметр для доверительных интервалов
T_SCORE = 2.0

# База дивидендов содержит данные с начала 2010 года
# Постепенно срок будет сдвигаться к началу режима TQBR для корректного учета сдвига T+2
STATS_START = pd.Timestamp("2010-12-01")

# Максимальный объем одной торговой операции в долях портфеля
MAX_TRADE = 1 / 100

# Параметры ML-модели
ML_PARAMS = {
    "data": (
        ("Label", {"days": 190, "div_share": 0.7, "on_off": True}),
        ("Scaler", {"days": 205, "on_off": True}),
        ("Ticker", {"on_off": True}),
        ("Mom12m", {"days": 181, "on_off": True, "periods": 3}),
        ("DivYield", {"days": 187, "on_off": True, "periods": 2}),
        ("Mom1m", {"days": 23, "on_off": True}),
        ("RetMax", {"days": 44, "on_off": True}),
        ("ChMom6m", {"days": 112, "on_off": True}),
        ("STD", {"days": 30, "on_off": True}),
        ("DayOfYear", {"on_off": False}),
        ("TurnOver", {"days": 269, "normalize": True, "on_off": True}),
        ("TurnOverVar", {"days": 173, "on_off": True}),
    ),
    "model": {
        "bagging_temperature": 0.5599793040266028,
        "depth": 16,
        "l2_leaf_reg": 0.8412478754428343,
        "learning_rate": 0.0045726516089600626,
        "one_hot_max_size": 2,
        "random_strength": 0.3322703074678968,
    },
}
