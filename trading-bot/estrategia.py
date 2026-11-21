"""
Estrategia de cruce de medias móviles (SMA).

- COMPRAR: la media rápida cruzó por encima de la lenta hace pocos días
           y sigue por encima.
- VENDER:  la media rápida está por debajo de la lenta.
- MANTENER: cualquier otro caso (no hacer nada).

Esta función la usan tanto el backtest como el bot real, así que lo que
pruebas en el backtest es exactamente lo que se opera.
"""
import pandas as pd

COMPRAR = "COMPRAR"
VENDER = "VENDER"
MANTENER = "MANTENER"


def calcular_senales(cierres: pd.Series, rapida: int, lenta: int,
                     dias_validez_cruce: int = 3) -> pd.DataFrame:
    """Devuelve un DataFrame con las medias y la señal de cada día."""
    if rapida >= lenta:
        raise ValueError("La media rápida debe tener menos días que la lenta")

    df = pd.DataFrame({"cierre": cierres.astype(float)})
    df["sma_rapida"] = df["cierre"].rolling(rapida).mean()
    df["sma_lenta"] = df["cierre"].rolling(lenta).mean()

    validas = df["sma_lenta"].notna()
    arriba = (df["sma_rapida"] > df["sma_lenta"]) & validas
    arriba_ayer = arriba.shift(1, fill_value=False)
    cruce_alcista = arriba & ~arriba_ayer & validas.shift(1, fill_value=False)

    # ¿Hubo un cruce alcista en los últimos N días?
    cruce_reciente = (
        cruce_alcista.astype(int)
        .rolling(dias_validez_cruce, min_periods=1)
        .max()
        .astype(bool)
    )

    df["senal"] = MANTENER
    df.loc[arriba & cruce_reciente, "senal"] = COMPRAR
    df.loc[validas & ~arriba, "senal"] = VENDER
    return df


def senal_de_hoy(cierres: pd.Series, rapida: int, lenta: int,
                 dias_validez_cruce: int = 3) -> str:
    """Señal correspondiente al último cierre disponible."""
    if len(cierres) < lenta + 1:
        return MANTENER  # no hay suficientes datos para decidir
    return calcular_senales(cierres, rapida, lenta, dias_validez_cruce)["senal"].iloc[-1]
