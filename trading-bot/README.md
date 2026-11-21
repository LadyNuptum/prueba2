# Bot de trading de acciones (Alpaca)

Bot sencillo en Python que opera acciones en Alpaca con una estrategia de
**cruce de medias móviles**. Está pensado para aprender y probar con dinero ficticio.

> ⚠️ **Este bot no garantiza ganancias.** La mayoría de las estrategias
> automáticas pierden dinero o rinden menos que simplemente comprar un índice.
> Úsalo primero en la cuenta de **papel** (dinero ficticio) durante semanas.

## Cómo funciona la estrategia

- **SMA 20** = precio medio de los últimos 20 días. **SMA 50** = de los últimos 50.
- **Compra** cuando la SMA 20 cruza por encima de la SMA 50 (la tendencia empieza a subir).
- **Vende** cuando la SMA 20 vuelve a quedar por debajo de la SMA 50,
  o si la posición pierde un 8 % (*stop-loss*).
- Cada compra usa como máximo el **10 %** del capital.
- Si la cuenta cae un **3 %** en el día, el bot no hace nada más ese día.
- Solo toca las acciones de la lista `SIMBOLOS`; no vende nada más que tengas.

Todo esto se cambia en [`config.py`](config.py).

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `config.py` | Acciones, parámetros de la estrategia y límites de riesgo |
| `estrategia.py` | Calcula las señales COMPRAR / VENDER / MANTENER |
| `backtest.py` | Prueba la estrategia con datos históricos |
| `bot.py` | Revisa la cuenta y envía las órdenes a Alpaca |
| `datos.py` | Descarga precios diarios de Alpaca |
| `tests/` | Pruebas automáticas (no necesitan conexión) |

## Paso 1: Crear la cuenta y las claves

1. Regístrate en <https://alpaca.markets> (es gratis).
2. En el panel, cambia a **Paper Trading** (arriba a la izquierda).
3. Ve a **API Keys**, pulsa **Generate New Key** y copia la *Key* y el *Secret*.
   El *Secret* solo se muestra una vez.

## Paso 2: Instalar

Necesitas Python 3.10 o más reciente.

```bash
cd trading-bot
python -m venv .venv
# Windows:      .venv\Scripts\activate
# Mac / Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

Copia `.env.example` como `.env` y pega tus claves dentro.
El archivo `.env` está en `.gitignore`: **nunca lo subas a GitHub.**

## Paso 3: Backtest (probar con el pasado)

```bash
python backtest.py
```

Muestra, para cada acción, la rentabilidad del bot comparada con simplemente
comprar y mantener, junto con la caída máxima (lo peor que llegó a ir).
Si el bot no supera a "comprar y mantener", conviene replantear la estrategia.

Para probar otras acciones: `python backtest.py --simbolos NVDA AMZN`

Cuidado al ajustar parámetros: si los cambias hasta que el backtest salga
perfecto, casi seguro estás sobreajustando al pasado y no funcionará igual en el futuro.

## Paso 4: Ejecutar el bot en modo simulación

```bash
python bot.py --simular
```

Muestra qué compraría o vendería **sin enviar ninguna orden**.

## Paso 5: Paper trading (dinero ficticio)

```bash
python bot.py
```

Envía órdenes reales a tu cuenta **de papel**. Ejecútalo **una vez al día**,
idealmente con el mercado abierto (por ejemplo a las 10:00 de Nueva York).
Todo queda registrado en `registro.log`.

Para que se ejecute solo cada día:

- **Mac / Linux** (`crontab -e`), de lunes a viernes a las 10:00 de Nueva York:
  ```
  CRON_TZ=America/New_York
  0 10 * * 1-5 cd /ruta/a/trading-bot && .venv/bin/python bot.py
  ```
- **Windows**: usa el *Programador de tareas* para lanzar
  `.venv\Scripts\python.exe bot.py` dentro de la carpeta `trading-bot`.

Déjalo funcionando **varias semanas** y compara los resultados con el backtest.

## Paso 6 (opcional): Dinero real

Solo si después de semanas en papel los resultados son buenos, y con una
cantidad que puedas permitirte perder. En `.env`:

```
ALPACA_PAPER=false
CONFIRMO_DINERO_REAL=SI
```

(Necesitas además claves de la cuenta real, que son distintas a las de papel.)

## Pruebas

```bash
python -m unittest discover tests
```

## Limitaciones que debes conocer

- Usa el feed gratuito **IEX** de Alpaca, que es suficiente para precios diarios.
- El stop-loss se revisa solo cuando se ejecuta el bot (una vez al día), así que
  la pérdida real puede ser mayor que el 8 % si el precio cae de golpe.
- Las órdenes son "a mercado": se ejecutan al precio que haya en ese momento.
- El cruce de medias funciona en mercados con tendencia y pierde en mercados
  laterales (muchas compras y ventas pequeñas con pérdidas).
