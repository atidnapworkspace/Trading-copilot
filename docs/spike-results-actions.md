# Spike de fuentes — 2026-11-20 16:56 UTC

Ejecutado desde: GitHub Actions (ubuntu-latest, IP de datacenter).

| Fuente | Estado | Seg | Detalle |
|---|---|---|---|
| US: Nasdaq Trader universo | ✅ | 0.7 | nasdaqlisted=5608 otherlisted=7692 filas (incluye ETFs/warrants/etc, a filtrar) |
| US: SEC EDGAR companyfacts | ❌ | 0.0 | falta SEC_CONTACT_EMAIL |
| US: SEC ticker->CIK | ❌ | 0.1 | HTTP 403 |
| US: Stooq CSV diario | ❌ | 0.8 | HTTP 200; inicio: '<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="robots" content="no' |
| US: Yahoo precios (yfinance) | ✅ | 2.1 | filas cierre 1 mes: {'AAPL': 24, 'QQQ': 24, 'GGAL.BA': 23, 'BTC-USD': 32} |
| US: Yahoo fundamentales | ✅ | 0.2 | {'trailingPE': 38.53852, 'forwardPE': 32.73288, 'priceToBook': 44.86917, 'returnOnEquity': 1.42257} |
| US: Yahoo histórico 10y QQQ | ✅ | 0.1 | QQQ 10y diario: 2514 filas |
| CRYPTO: OKX funding/OI/ticker | ✅ | 0.5 | funding=0.0000175810420726 oiUsd=2062354849.1776095205376 |
| CRYPTO: CoinGecko markets | ✅ | 0.1 | 50 monedas, top=btc, campos=['market_cap', 'ath', 'ath_change_percentage', 'total_volume'] |
| CRYPTO: CoinGecko global | ✅ | 0.1 | btc.d=57.9% |
| CRYPTO: Binance futures (geo?) | ❌ | 0.2 | HTTP 451 '{\n  "code": 0,\n  "msg": "Service unavailable from a restricted location according to \'b. E' |
| CRYPTO: Binance spot público | ✅ | 0.5 | HTTP 200 '{"symbol":"BTCUSDT","price":"59408.35000000"}' |
| CRYPTO: Bybit linear | ❌ | 1.6 | HTTP 403 '{\n    error:The Amazon CloudFront distribution is configured to block access from your cou' |
| AR: data912 acciones | ✅ | 0.3 | acciones: 96 items; ej={"symbol": "A3", "q_bid": 1402.0, "px_bid": 2520.0, "px_ask": 2580.0, "q_ask": 2958.0, "v": 21210.0, "q_op": 32.0, "c": 2580.0, "pct_change": -0.38} |
| AR: data912 cedears | ✅ | 0.1 | cedears: 1049 items; ej={"symbol": "AAL", "q_bid": 9.0, "px_bid": 10840.0, "px_ask": 10870.0, "q_ask": 6000.0, "v": 10708.0, "q_op": 81.0, "c": 10870.0, "pct_change": -2.16} |
| AR: data912 bonos | ✅ | 0.5 | bonos: 202 items; ej={"symbol": "AE38", "q_bid": 205861.0, "px_bid": 106970.0, "px_ask": 107050.0, "q_ask": 1412.0, "v": 2611926.0, "q_op": 2144.0, "c": 106970.0, "pct_change": -1.35} |
| AR: data912 histórico GGAL | ✅ | 0.1 | GGAL hist: 6327 filas; ej={"date": "2026-11-19", "o": 4720.0, "h": 4900.0, "l": 4527.5, "c": 4545.0, "v": 2650514.0, "dr": -0.0472, "sa": 0.4372} |
| AR: BYMA líderes | ❌ | 25.2 | EXC ConnectTimeout: HTTPSConnectionPool(host='open.bymadata.com.ar', port=443): Max retries exceeded with url: /vanoms-be-core/rest/api/bymadata/free/leading-equity (Caused by Conn |
| AR: BYMA bonos públicos | ❌ | 25.2 | EXC ConnectTimeout: HTTPSConnectionPool(host='open.bymadata.com.ar', port=443): Max retries exceeded with url: /vanoms-be-core/rest/api/bymadata/free/public-bonds (Caused by Connec |
| AR: dolarapi CCL/MEP | ✅ | 0.2 | ['Oficial', 'Blue', 'Bolsa', 'Contado con liquidación', 'Mayorista', 'Cripto', 'Tarjeta'] |

Pendientes por falta de key (no probadas): Polygon/Massive free, Finnhub free, CoinGecko demo key.