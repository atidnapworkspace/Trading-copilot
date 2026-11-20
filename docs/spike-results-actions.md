# Spike de fuentes — 2026-11-20 19:56 UTC

Ejecutado desde: GitHub Actions (ubuntu-latest, IP de datacenter).

| Fuente | Estado | Seg | Detalle |
|---|---|---|---|
| US: Nasdaq Trader universo | ✅ | 0.3 | nasdaqlisted=5608 otherlisted=7692 filas (incluye ETFs/warrants/etc, a filtrar) |
| US: SEC EDGAR companyfacts | ❌ | 0.0 | falta SEC_CONTACT_EMAIL |
| US: SEC ticker->CIK | ❌ | 0.1 | HTTP 403 |
| US: Stooq CSV diario | ❌ | 0.6 | HTTP 200; inicio: '<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="robots" content="no' |
| US: Yahoo precios (yfinance) | ✅ | 1.6 | filas cierre 1 mes: {'AAPL': 24, 'QQQ': 24, 'GGAL.BA': 23, 'BTC-USD': 32} |
| US: Yahoo fundamentales | ✅ | 0.2 | {'trailingPE': 38.426506, 'forwardPE': 32.63774, 'priceToBook': 44.738754, 'returnOnEquity': 1.42257} |
| US: Yahoo histórico 10y QQQ | ✅ | 0.2 | QQQ 10y diario: 2514 filas |
| CRYPTO: OKX funding/OI/ticker | ✅ | 0.6 | funding=-0.0000047994508113 oiUsd=1982068523.36204980775088 |
| CRYPTO: CoinGecko markets | ✅ | 0.1 | 50 monedas, top=btc, campos=['market_cap', 'ath', 'ath_change_percentage', 'total_volume'] |
| CRYPTO: CoinGecko global | ✅ | 0.1 | btc.d=57.8% |
| CRYPTO: Binance futures (geo?) | ❌ | 0.1 | HTTP 451 '{\n  "code": 0,\n  "msg": "Service unavailable from a restricted location according to \'b. E' |
| CRYPTO: Binance spot público | ✅ | 0.6 | HTTP 200 '{"symbol":"BTCUSDT","price":"58624.00000000"}' |
| CRYPTO: Bybit linear | ❌ | 0.1 | HTTP 403 '{\n    error:The Amazon CloudFront distribution is configured to block access from your cou' |
| AR: data912 acciones | ✅ | 0.2 | acciones: 96 items; ej={"symbol": "A3", "q_bid": 168.0, "px_bid": 2565.0, "px_ask": 2570.0, "q_ask": 4870.0, "v": 40630.0, "q_op": 77.0, "c": 2570.0, "pct_change": -0.77} |
| AR: data912 cedears | ✅ | 0.1 | cedears: 1049 items; ej={"symbol": "AAL", "q_bid": 7661.0, "px_bid": 10850.0, "px_ask": 10890.0, "q_ask": 6.0, "v": 17839.0, "q_op": 162.0, "c": 10870.0, "pct_change": -2.16} |
| AR: data912 bonos | ✅ | 0.2 | bonos: 203 items; ej={"symbol": "AE38", "q_bid": 4018.0, "px_bid": 107340.0, "px_ask": 108910.0, "q_ask": 20659.0, "v": 6296876.0, "q_op": 4263.0, "c": 108910.0, "pct_change": 0.43} |
| AR: data912 histórico GGAL | ✅ | 1.0 | GGAL hist: 6327 filas; ej={"date": "2026-11-19", "o": 4720.0, "h": 4900.0, "l": 4527.5, "c": 4545.0, "v": 2650514.0, "dr": -0.0472, "sa": 0.4372} |
| AR: BYMA líderes | ❌ | 25.4 | EXC ReadTimeout: HTTPSConnectionPool(host='open.bymadata.com.ar', port=443): Read timed out. (read timeout=25) |
| AR: BYMA bonos públicos | ❌ | 25.0 | EXC ConnectTimeout: HTTPSConnectionPool(host='open.bymadata.com.ar', port=443): Max retries exceeded with url: /vanoms-be-core/rest/api/bymadata/free/public-bonds (Caused by Connec |
| AR: dolarapi CCL/MEP | ✅ | 0.1 | ['Oficial', 'Blue', 'Bolsa', 'Contado con liquidación', 'Mayorista', 'Cripto', 'Tarjeta'] |

Pendientes por falta de key (no probadas): Polygon/Massive free, Finnhub free, CoinGecko demo key.