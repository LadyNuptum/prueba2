"""Descarga de precios diarios desde Alpaca (o desde un CSV)."""
from datetime import datetime, timedelta, timezone

import pandas as pd


def descargar_diarios(simbolos, dias, api_key, secret_key):
    """
    Devuelve {simbolo: DataFrame con columnas open, high, low, close, volume}
    usando el feed gratuito IEX de Alpaca. Precios ajustados por splits/dividendos.
    """
    from alpaca.data.enums import Adjustment, DataFeed
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    cliente = StockHistoricalDataClient(api_key, secret_key)
    peticion = StockBarsRequest(
        symbol_or_symbols=list(simbolos),
        timeframe=TimeFrame.Day,
        start=datetime.now(timezone.utc) - timedelta(days=dias),
        adjustment=Adjustment.ALL,
        feed=DataFeed.IEX,
    )
    barras = cliente.get_stock_bars(peticion).df
    if barras.empty:
        return {}

    resultado = {}
    for simbolo in simbolos:
        if simbolo in barras.index.get_level_values("symbol"):
            df = barras.xs(simbolo, level="symbol")
            resultado[simbolo] = df[["open", "high", "low", "close", "volume"]].sort_index()
    return resultado


def leer_csv(ruta):
    """
    Lee un CSV con columnas: date, open, high, low, close (volume opcional).
    Útil para probar el backtest con datos descargados de otro sitio.
    """
    df = pd.read_csv(ruta)
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()
