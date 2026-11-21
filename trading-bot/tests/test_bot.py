"""Pruebas sin conexión a Alpaca. Ejecutar con:  python -m unittest discover tests"""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
from backtest import simular  # noqa: E402
from bot import decidir, quitar_vela_de_hoy  # noqa: E402
from estrategia import COMPRAR, MANTENER, VENDER, calcular_senales, senal_de_hoy  # noqa: E402


def serie(valores, inicio="2024-01-01"):
    fechas = pd.date_range(inicio, periods=len(valores), freq="B")
    return pd.Series(valores, index=fechas, dtype=float)


def velas(cierres):
    s = serie(cierres)
    return pd.DataFrame({"open": s.shift(1).fillna(s.iloc[0]), "high": s, "low": s,
                         "close": s, "volume": 1000})


# Baja 60 días y luego sube: produce un cruce alcista claro al final.
BAJA_Y_SUBE = list(np.linspace(100, 70, 60)) + list(np.linspace(70, 110, 40))


def cuenta(equity=10_000, last_equity=10_000, buying_power=10_000, bloqueada=False):
    return SimpleNamespace(equity=str(equity), last_equity=str(last_equity),
                           buying_power=str(buying_power), trading_blocked=bloqueada)


class PruebasEstrategia(unittest.TestCase):
    def test_sin_datos_suficientes_no_hace_nada(self):
        self.assertEqual(senal_de_hoy(serie([100] * 10), 5, 20), MANTENER)

    def test_tendencia_bajista_da_vender(self):
        self.assertEqual(senal_de_hoy(serie(np.linspace(200, 100, 80)), 5, 20), VENDER)

    def test_cruce_alcista_da_comprar_solo_unos_dias(self):
        senales = calcular_senales(serie(BAJA_Y_SUBE), 5, 20, dias_validez_cruce=3)["senal"]
        compras = senales[senales == COMPRAR]
        self.assertTrue(1 <= len(compras) <= 3)
        # Después de la ventana del cruce, ya no se recompra.
        self.assertEqual(senales.iloc[-1], MANTENER)

    def test_rapida_debe_ser_menor(self):
        with self.assertRaises(ValueError):
            calcular_senales(serie([1] * 100), 50, 20)


class PruebasBacktest(unittest.TestCase):
    def test_no_usa_informacion_del_futuro(self):
        precios = velas(BAJA_Y_SUBE)
        r = simular(precios, rapida=5, lenta=20, capital=10_000, slippage=0)
        senales = calcular_senales(precios["close"], 5, 20)["senal"]
        primer_compra = senales[senales == COMPRAR].index[0]
        dia = precios.index.get_loc(primer_compra)
        # El capital no cambia el día de la señal (se compra al día siguiente).
        self.assertAlmostEqual(r["curva"].iloc[dia], 10_000)
        self.assertTrue(r["posicion_abierta"])

    def test_stop_loss_cierra_la_operacion(self):
        cierres = BAJA_Y_SUBE[:70] + list(np.linspace(80, 40, 30))
        r = simular(velas(cierres), rapida=5, lenta=20, stop_loss=0.05, slippage=0)
        self.assertGreaterEqual(r["operaciones"], 1)
        self.assertGreater(r["caida_maxima"], -0.20)  # el stop limitó la caída


class PruebasBot(unittest.TestCase):
    def setUp(self):
        self._original = (config.SIMBOLOS, config.SMA_RAPIDA, config.SMA_LENTA)
        config.SIMBOLOS, config.SMA_RAPIDA, config.SMA_LENTA = ["AAA"], 5, 20
        self.precios_compra = {"AAA": velas(BAJA_Y_SUBE[:68])}  # justo tras el cruce

    def tearDown(self):
        config.SIMBOLOS, config.SMA_RAPIDA, config.SMA_LENTA = self._original

    def test_compra_con_limite_de_tamano(self):
        acciones = decidir(cuenta(), {}, set(), self.precios_compra)
        self.assertEqual(len(acciones), 1)
        tipo, simbolo, cantidad, _ = acciones[0]
        precio = self.precios_compra["AAA"]["close"].iloc[-1]
        self.assertEqual((tipo, simbolo), (COMPRAR, "AAA"))
        self.assertLessEqual(cantidad * precio, 10_000 * config.PORCENTAJE_POR_POSICION)

    def test_no_opera_tras_perdida_diaria(self):
        self.assertEqual(decidir(cuenta(equity=9_500), {}, set(), self.precios_compra), [])

    def test_no_opera_con_cuenta_bloqueada(self):
        self.assertEqual(decidir(cuenta(bloqueada=True), {}, set(), self.precios_compra), [])

    def test_no_duplica_si_hay_orden_pendiente(self):
        self.assertEqual(decidir(cuenta(), {}, {"AAA"}, self.precios_compra), [])

    def test_stop_loss_vende(self):
        pos = SimpleNamespace(qty="10", unrealized_plpc="-0.10")
        acciones = decidir(cuenta(), {"AAA": pos}, set(), self.precios_compra)
        self.assertEqual(acciones[0][0], VENDER)
        self.assertIn("stop-loss", acciones[0][3])

    def test_mantiene_posicion_ganadora(self):
        pos = SimpleNamespace(qty="10", unrealized_plpc="0.05")
        self.assertEqual(decidir(cuenta(), {"AAA": pos}, set(), self.precios_compra), [])

    def test_quita_vela_incompleta_de_hoy(self):
        fechas = pd.to_datetime(["2026-11-18 05:00", "2026-11-19 05:00", "2026-11-20 05:00"], utc=True)
        df = pd.DataFrame({"close": [1.0, 2.0, 3.0]}, index=fechas)
        ahora = datetime(2026, 11, 20, 15, 0, tzinfo=timezone.utc)  # 10:00 en Nueva York
        self.assertEqual(len(quitar_vela_de_hoy({"X": df}, ahora)["X"]), 2)


if __name__ == "__main__":
    unittest.main()
