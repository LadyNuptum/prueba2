"""
Configuración del bot. Este es el archivo que normalmente vas a modificar.

Las claves de Alpaca NO van aquí: van en el archivo .env (ver .env.example).
"""
import os

from dotenv import load_dotenv

load_dotenv()

# --- Acciones que el bot vigila y opera -------------------------------------
# El bot SOLO toca estas acciones; nunca vende otras posiciones que tengas.
SIMBOLOS = ["SPY", "QQQ", "AAPL", "MSFT"]

# --- Estrategia: cruce de medias móviles -----------------------------------
# Se compra cuando la media rápida cruza por encima de la lenta
# y se vende cuando vuelve a quedar por debajo.
SMA_RAPIDA = 20   # días
SMA_LENTA = 50    # días
# Si el cruce ocurrió hace como mucho estos días, todavía se acepta la compra
# (por si un día no ejecutaste el bot).
DIAS_VALIDEZ_CRUCE = 3

# --- Gestión de riesgo ------------------------------------------------------
PORCENTAJE_POR_POSICION = 0.10  # cada compra usa como máximo el 10 % del capital
STOP_LOSS = 0.08                # vende si una posición pierde un 8 %
PERDIDA_DIARIA_MAX = 0.03       # si la cuenta cae un 3 % en el día, no opera más hoy

# --- Backtest ---------------------------------------------------------------
CAPITAL_INICIAL = 10_000
SLIPPAGE = 0.0005  # 0,05 % de peor precio en cada operación (estimación realista)
DIAS_HISTORICO_BACKTEST = 365 * 5

# --- Credenciales (desde .env) ---------------------------------------------
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
# Por seguridad, por defecto SIEMPRE se usa la cuenta de papel (dinero ficticio).
ALPACA_PAPER = os.getenv("ALPACA_PAPER", "true").strip().lower() != "false"
# Para usar dinero real hay que poner ALPACA_PAPER=false Y CONFIRMO_DINERO_REAL=SI
CONFIRMO_DINERO_REAL = os.getenv("CONFIRMO_DINERO_REAL", "").strip().upper() == "SI"
