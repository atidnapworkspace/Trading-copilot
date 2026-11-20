# Spike de fuentes — 2026-11-20 16:23 UTC

Ejecutado desde la PC del owner (IP residencial). **Los resultados desde GitHub Actions pueden diferir (IPs de datacenter/EE.UU.)**: repetir allí.

| Fuente | Estado | Seg | Detalle |
|---|---|---|---|
| US: Nasdaq Trader universo | ✅ | 2.5 | nasdaqlisted=5608 otherlisted=7692 filas (incluye ETFs/warrants/etc, a filtrar) |
| US: SEC EDGAR companyfacts | ✅ | 0.7 | AAPL companyfacts 3769KB; conceptos clave presentes: ['EarningsPerShareDiluted', 'StockholdersEquity', 'NetIncomeLoss', 'WeightedAverageNumberOfDilutedSharesOutstanding'] |
| US: SEC ticker->CIK | ✅ | 0.7 | 10398 tickers->CIK |
| US: Stooq CSV diario | ❌ | 1.1 | HTTP 200; inicio: '<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="robots" content="no' |
| US: Yahoo precios (yfinance) | ✅ | 6.3 | filas cierre 1 mes: {'AAPL': 24, 'QQQ': 24, 'GGAL.BA': 23, 'BTC-USD': 32} |
| US: Yahoo fundamentales | ✅ | 0.9 | {'trailingPE': 38.74722, 'forwardPE': 32.910137, 'priceToBook': 45.112152, 'returnOnEquity': 1.42257} |
| US: Yahoo histórico 10y QQQ | ✅ | 1.2 | QQQ 10y diario: 2514 filas |
| CRYPTO: OKX funding/OI/ticker | ✅ | 1.8 | funding=0.0000238360137516 oiUsd=2051323432.250410846044 |
| CRYPTO: CoinGecko markets | ✅ | 0.6 | 50 monedas, top=btc, campos=['market_cap', 'ath', 'ath_change_percentage', 'total_volume'] |
| CRYPTO: CoinGecko global | ✅ | 0.5 | btc.d=57.9% |
| CRYPTO: Binance futures (geo?) | ✅ | 0.7 | HTTP 200 '{"symbol":"BTCUSDT","markPrice":"59375.40000000","indexPrice":"59384.90652174","estimatedS' |
| CRYPTO: Binance spot público | ✅ | 1.7 | HTTP 200 '{"symbol":"BTCUSDT","price":"59374.69000000"}' |
| CRYPTO: Bybit linear | ✅ | 0.7 | HTTP 200 '{"retCode":0,"retMsg":"OK","result":{"category":"linear","list":[{"symbol":"BTCUSDT","last' |
| AR: data912 acciones | ✅ | 0.7 | acciones: 96 items; ej={"symbol": "A3", "q_bid": 75.0, "px_bid": 2580.0, "px_ask": 2595.0, "q_ask": 3228.0, "v": 13281.0, "q_op": 22.0, "c": 2590.0, "pct_change": 0.0} |
| AR: data912 cedears | ✅ | 0.3 | cedears: 1049 items; ej={"symbol": "AAL", "q_bid": 5853.0, "px_bid": 10910.0, "px_ask": 10950.0, "q_ask": 6018.0, "v": 8587.0, "q_op": 69.0, "c": 10890.0, "pct_change": -1.98} |
| AR: data912 bonos | ✅ | 0.4 | bonos: 202 items; ej={"symbol": "AE38", "q_bid": 7227.0, "px_bid": 106710.0, "px_ask": 106790.0, "q_ask": 1253.0, "v": 1990072.0, "q_op": 1723.0, "c": 106790.0, "pct_change": -1.52} |
| AR: data912 histórico GGAL | ✅ | 0.4 | GGAL hist: 6327 filas; ej={"date": "2026-11-19", "o": 4720.0, "h": 4900.0, "l": 4527.5, "c": 4545.0, "v": 2650514.0, "dr": -0.0472, "sa": 0.4372} |
| AR: BYMA líderes | ❌ | 21.1 | EXC ConnectTimeout: HTTPSConnectionPool(host='open.bymadata.com.ar', port=443): Max retries exceeded with url: /vanoms-be-core/rest/api/bymadata/free/leading-equity (Caused by Conn |
| AR: BYMA bonos públicos | ❌ | 21.0 | EXC ConnectTimeout: HTTPSConnectionPool(host='open.bymadata.com.ar', port=443): Max retries exceeded with url: /vanoms-be-core/rest/api/bymadata/free/public-bonds (Caused by Connec |
| AR: dolarapi CCL/MEP | ✅ | 0.4 | ['Oficial', 'Blue', 'Bolsa', 'Contado con liquidación', 'Mayorista', 'Cripto', 'Tarjeta'] |

Pendientes por falta de key (no probadas): Polygon/Massive free, Finnhub free, CoinGecko demo key.