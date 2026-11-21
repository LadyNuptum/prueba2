"""
Backtest: simula la estrategia con datos históricos.

Reglas de la simulación (para no engañarnos):
- La señal se calcula con el cierre de un día y se ejecuta en la APERTURA
  del día siguiente (no se usa información del futuro).
- Cada compra o venta paga un slippage (peor precio que el teórico).
- Se compara siempre con "comprar y mantener" la misma acción.

Uso:
    python backtest.py                    # descarga datos de Alpaca (necesita .env)
    python backtest.py --csv precios.csv  # usa un CSV propio
"""
import argparse
from pathlib import Path

import pandas as pd

import config
from datos import descargar_diarios, leer_csv
from estrategia import COMPRAR, VENDER, calcular_senales


def simular(precios: pd.DataFrame, rapida=config.SMA_RAPIDA, lenta=config.SMA_LENTA,
            capital=config.CAPITAL_INICIAL, slippage=config.SLIPPAGE,
            stop_loss=config.STOP_LOSS, dias_validez_cruce=config.DIAS_VALIDEZ_CRUCE):
    """Simula una sola acción. Devuelve un diccionario con resultados."""
    senales = calcular_senales(precios["close"], rapida, lenta, dias_validez_cruce)

    efectivo = float(capital)
    acciones = 0
    precio_entrada = 0.0
    orden_pendiente = None  # "COMPRAR" / "VENDER" para la apertura de mañana
    operaciones = []        # rentabilidad de cada operación cerrada
    curva = []

    for fecha, fila in precios.iterrows():
        # 1) Ejecutar en la apertura lo que se decidió ayer
        if orden_pendiente == COMPRAR and acciones == 0:
            precio = fila["open"] * (1 + slippage)
            cantidad = int(efectivo // precio)
            if cantidad > 0:
                acciones = cantidad
                efectivo -= cantidad * precio
                precio_entrada = precio
        elif orden_pendiente == VENDER and acciones > 0:
            precio = fila["open"] * (1 - slippage)
            efectivo += acciones * precio
            operaciones.append(precio / precio_entrada - 1)
            acciones = 0
        orden_pendiente = None

        # 2) Al cierre, decidir qué hacer mañana
        senal = senales.at[fecha, "senal"]
        if acciones > 0:
            perdida = fila["close"] / precio_entrada - 1
            if perdida <= -stop_loss or senal == VENDER:
                orden_pendiente = VENDER
        elif senal == COMPRAR:
            orden_pendiente = COMPRAR

        curva.append(efectivo + acciones * fila["close"])

    curva = pd.Series(curva, index=precios.index)
    comprar_y_mantener = capital * precios["close"] / precios["open"].iloc[0]
    return {
        "curva": curva,
        "rentabilidad": curva.iloc[-1] / capital - 1,
        "rentabilidad_mantener": comprar_y_mantener.iloc[-1] / capital - 1,
        "caida_maxima": _caida_maxima(curva),
        "caida_maxima_mantener": _caida_maxima(comprar_y_mantener),
        "anual": _anualizada(curva, capital),
        "anual_mantener": _anualizada(comprar_y_mantener, capital),
        "operaciones": len(operaciones),
        "aciertos": sum(1 for r in operaciones if r > 0) / len(operaciones) if operaciones else 0.0,
        "posicion_abierta": acciones > 0,
    }


def _caida_maxima(curva: pd.Series) -> float:
    return float((curva / curva.cummax() - 1).min())


def _anualizada(curva: pd.Series, capital: float) -> float:
    dias = (curva.index[-1] - curva.index[0]).days
    if dias <= 0 or curva.iloc[-1] <= 0:
        return 0.0
    return (curva.iloc[-1] / capital) ** (365.25 / dias) - 1


def imprimir(simbolo, r):
    print(f"\n=== {simbolo} ===")
    print(f"{'':28}{'Bot':>10}{'Comprar y mantener':>22}")
    print(f"{'Rentabilidad total':28}{r['rentabilidad']:>10.1%}{r['rentabilidad_mantener']:>22.1%}")
    print(f"{'Rentabilidad anual':28}{r['anual']:>10.1%}{r['anual_mantener']:>22.1%}")
    print(f"{'Caída máxima':28}{r['caida_maxima']:>10.1%}{r['caida_maxima_mantener']:>22.1%}")
    print(f"Operaciones cerradas: {r['operaciones']}   "
          f"Ganadoras: {r['aciertos']:.0%}   "
          f"{'(posición abierta al final)' if r['posicion_abierta'] else ''}")


def main():
    parser = argparse.ArgumentParser(description="Backtest de la estrategia de medias móviles")
    parser.add_argument("--csv", help="CSV con columnas date,open,high,low,close")
    parser.add_argument("--simbolos", nargs="+", help="Acciones a probar (por defecto las de config.py)")
    args = parser.parse_args()

    if args.csv:
        datos = {Path(args.csv).stem: leer_csv(args.csv)}
    else:
        if not config.ALPACA_API_KEY:
            raise SystemExit("Faltan las claves de Alpaca. Copia .env.example a .env y rellénalo.")
        simbolos = args.simbolos or config.SIMBOLOS
        datos = descargar_diarios(simbolos, config.DIAS_HISTORICO_BACKTEST,
                                  config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY)

    print(f"Estrategia: SMA {config.SMA_RAPIDA}/{config.SMA_LENTA}, "
          f"stop-loss {config.STOP_LOSS:.0%}, slippage {config.SLIPPAGE:.2%}")
    for simbolo, precios in datos.items():
        if len(precios) <= config.SMA_LENTA:
            print(f"\n{simbolo}: datos insuficientes ({len(precios)} días)")
            continue
        imprimir(simbolo, simular(precios))

    print("\nRecuerda: un buen resultado pasado NO garantiza resultados futuros.")


if __name__ == "__main__":
    main()
