"""
Bot de trading para Alpaca.

Se ejecuta UNA vez al día (por ejemplo a las 10:00 hora de Nueva York):
revisa cada acción de config.SIMBOLOS, decide si comprar, vender o no hacer
nada, y envía las órdenes.

Uso:
    python bot.py --simular   # solo muestra lo que haría, no envía órdenes
    python bot.py             # envía órdenes (a la cuenta de PAPEL por defecto)
"""
import argparse
import logging
import math
from pathlib import Path
from zoneinfo import ZoneInfo

import config
from estrategia import COMPRAR, VENDER, senal_de_hoy

log = logging.getLogger("bot")
ZONA_NY = ZoneInfo("America/New_York")


def configurar_registro():
    archivo = Path(__file__).with_name("registro.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(archivo, encoding="utf-8")],
    )


def crear_cliente():
    from alpaca.trading.client import TradingClient

    if not config.ALPACA_API_KEY or not config.ALPACA_SECRET_KEY:
        raise SystemExit("Faltan las claves de Alpaca. Copia .env.example a .env y rellénalo.")
    if not config.ALPACA_PAPER and not config.CONFIRMO_DINERO_REAL:
        raise SystemExit("ALPACA_PAPER=false pero no has puesto CONFIRMO_DINERO_REAL=SI. "
                         "Por seguridad no se opera con dinero real.")
    return TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY, paper=config.ALPACA_PAPER)


def simbolos_con_ordenes_abiertas(cliente):
    from alpaca.trading.enums import QueryOrderStatus
    from alpaca.trading.requests import GetOrdersRequest

    ordenes = cliente.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN))
    return {o.symbol for o in ordenes}


def comprar(cliente, simbolo, cantidad):
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import MarketOrderRequest

    cliente.submit_order(MarketOrderRequest(
        symbol=simbolo, qty=cantidad, side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
    ))


def vender(cliente, simbolo):
    cliente.close_position(simbolo)


def quitar_vela_de_hoy(precios, ahora):
    """
    Con el mercado abierto, la vela de hoy aún no ha cerrado. La quitamos para
    decidir con cierres completos, igual que en el backtest.
    """
    hoy = ahora.astimezone(ZONA_NY).date()
    resultado = {}
    for simbolo, df in precios.items():
        fechas = df.index.tz_convert(ZONA_NY).date if df.index.tz else df.index.date
        resultado[simbolo] = df[fechas < hoy]
    return resultado


def decidir(cuenta, posiciones, pendientes, precios):
    """
    Lógica pura (sin llamadas a Alpaca), para poder probarla.

    cuenta:     objeto con .equity, .last_equity, .buying_power, .trading_blocked
    posiciones: {simbolo: objeto con .qty y .unrealized_plpc}
    pendientes: conjunto de símbolos con órdenes todavía abiertas
    precios:    {simbolo: DataFrame con columna 'close'}

    Devuelve una lista de acciones: ("COMPRAR", simbolo, cantidad, motivo)
                                    ("VENDER", simbolo, None, motivo)
    """
    if cuenta.trading_blocked:
        log.warning("La cuenta tiene el trading bloqueado. No se hace nada.")
        return []

    capital = float(cuenta.equity)
    capital_ayer = float(cuenta.last_equity)
    if capital_ayer > 0 and capital / capital_ayer - 1 <= -config.PERDIDA_DIARIA_MAX:
        log.warning("La cuenta ha caído %.1f%% hoy (límite %.0f%%). No se opera más hoy.",
                    (capital / capital_ayer - 1) * 100, config.PERDIDA_DIARIA_MAX * 100)
        return []

    poder_compra = float(cuenta.buying_power)
    acciones = []

    for simbolo in config.SIMBOLOS:
        if simbolo in pendientes:
            log.info("%s: ya tiene una orden pendiente, se omite.", simbolo)
            continue
        df = precios.get(simbolo)
        if df is None or df.empty:
            log.warning("%s: sin datos de precios.", simbolo)
            continue

        senal = senal_de_hoy(df["close"], config.SMA_RAPIDA, config.SMA_LENTA,
                             config.DIAS_VALIDEZ_CRUCE)
        ultimo = float(df["close"].iloc[-1])
        posicion = posiciones.get(simbolo)

        if posicion is not None:
            resultado = float(posicion.unrealized_plpc)
            if resultado <= -config.STOP_LOSS:
                acciones.append((VENDER, simbolo, None, f"stop-loss ({resultado:.1%})"))
            elif senal == VENDER:
                acciones.append((VENDER, simbolo, None, f"cruce bajista (resultado {resultado:+.1%})"))
            else:
                log.info("%s: mantener posición (%s acciones, %+.1f%%).",
                         simbolo, posicion.qty, resultado * 100)
        elif senal == COMPRAR:
            presupuesto = min(capital * config.PORCENTAJE_POR_POSICION, poder_compra)
            cantidad = math.floor(presupuesto / ultimo)
            if cantidad < 1:
                log.info("%s: señal de compra pero no alcanza el dinero (precio %.2f).", simbolo, ultimo)
                continue
            poder_compra -= cantidad * ultimo
            acciones.append((COMPRAR, simbolo, cantidad, f"cruce alcista, ~{cantidad * ultimo:,.0f} USD"))
        else:
            log.info("%s: sin señal (%s).", simbolo, senal)

    return acciones


def main():
    parser = argparse.ArgumentParser(description="Bot de cruce de medias móviles para Alpaca")
    parser.add_argument("--simular", action="store_true",
                        help="Muestra lo que haría sin enviar ninguna orden")
    args = parser.parse_args()
    configurar_registro()

    from datos import descargar_diarios

    cliente = crear_cliente()
    modo = "PAPEL (dinero ficticio)" if config.ALPACA_PAPER else "*** DINERO REAL ***"
    log.info("Inicio del bot. Cuenta: %s%s", modo, "  [SIMULACIÓN]" if args.simular else "")

    reloj = cliente.get_clock()
    if not reloj.is_open:
        log.info("El mercado está cerrado: las órdenes se ejecutarán en la próxima apertura.")

    cuenta = cliente.get_account()
    log.info("Capital: %s USD  |  Poder de compra: %s USD", cuenta.equity, cuenta.buying_power)

    posiciones = {p.symbol: p for p in cliente.get_all_positions()}
    pendientes = simbolos_con_ordenes_abiertas(cliente)
    # Pedimos suficientes días para calcular la media lenta (en días naturales).
    precios = descargar_diarios(config.SIMBOLOS, config.SMA_LENTA * 3,
                                config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY)
    if reloj.is_open:
        precios = quitar_vela_de_hoy(precios, reloj.timestamp)

    for tipo, simbolo, cantidad, motivo in decidir(cuenta, posiciones, pendientes, precios):
        texto = f"{tipo} {simbolo}" + (f" x{cantidad}" if cantidad else " (toda la posición)")
        if args.simular:
            log.info("[SIMULACIÓN] %s — %s", texto, motivo)
            continue
        try:
            if tipo == COMPRAR:
                comprar(cliente, simbolo, cantidad)
            else:
                vender(cliente, simbolo)
            log.info("Orden enviada: %s — %s", texto, motivo)
        except Exception as error:  # una orden fallida no debe detener las demás
            log.error("No se pudo enviar %s: %s", texto, error)

    log.info("Fin del bot.")


if __name__ == "__main__":
    main()
