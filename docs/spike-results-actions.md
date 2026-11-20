# Spike de fuentes — 2026-11-20 20:23 UTC

Ejecutado desde: GitHub Actions (ubuntu-latest, IP de datacenter).

| Fuente | Estado | Seg | Detalle |
|---|---|---|---|
| US: Nasdaq Trader universo | ✅ | 1.6 | nasdaqlisted=5608 otherlisted=7692 filas (incluye ETFs/warrants/etc, a filtrar) |
| US: SEC EDGAR companyfacts | ✅ | 0.4 | AAPL companyfacts 3769KB; conceptos clave presentes: ['EarningsPerShareDiluted', 'StockholdersEquity', 'NetIncomeLoss', 'WeightedAverageNumberOfDilutedSharesOutstanding'] |
| US: SEC ticker->CIK | ✅ | 0.1 | 10398 tickers->CIK |
| US: Stooq CSV diario | ❌ | 50.0 | EXC ConnectTimeout: HTTPSConnectionPool(host='stooq.com', port=443): Max retries exceeded with url: /q/d/l/?s=aapl.us&i=d (Caused by ConnectTimeoutError(<HTTPSConnection(host='stoo |
| US: Yahoo precios (yfinance) | ✅ | 1.4 | filas cierre 1 mes: {'AAPL': 24, 'QQQ': 24, 'GGAL.BA': 23, 'BTC-USD': 32} |
| US: Yahoo fundamentales | ✅ | 0.1 | {'trailingPE': 38.428173, 'forwardPE': 32.639156, 'priceToBook': 44.740696, 'returnOnEquity': 1.42257} |
| US: Yahoo histórico 10y QQQ | ✅ | 0.2 | QQQ 10y diario: 2514 filas |
| CRYPTO: OKX funding/OI/ticker | ✅ | 0.4 | funding=-0.0000153198540488 oiUsd=1979064025.2607898402808 |
| CRYPTO: CoinGecko markets | ✅ | 0.1 | 50 monedas, top=btc, campos=['market_cap', 'ath', 'ath_change_percentage', 'total_volume'] |
| CRYPTO: CoinGecko global | ✅ | 0.1 | btc.d=57.7% |
| CRYPTO: Binance futures (geo?) | ❌ | 0.1 | HTTP 451 '{\n  "code": 0,\n  "msg": "Service unavailable from a restricted location according to \'b. E' |
| CRYPTO: Binance spot público | ✅ | 0.4 | HTTP 200 '{"symbol":"BTCUSDT","price":"58556.41000000"}' |
| CRYPTO: Bybit linear | ❌ | 0.1 | HTTP 403 '{\n    error:The Amazon CloudFront distribution is configured to block access from your cou' |
| AR: data912 acciones | ✅ | 0.3 | acciones: 96 items; ej={"symbol": "A3", "q_bid": 85.0, "px_bid": 2565.0, "px_ask": 2570.0, "q_ask": 3620.0, "v": 41963.0, "q_op": 79.0, "c": 2570.0, "pct_change": -0.77} |
| AR: data912 cedears | ✅ | 0.1 | cedears: 1051 items; ej={"symbol": "AAL", "q_bid": 7169.0, "px_bid": 10780.0, "px_ask": 10830.0, "q_ask": 7661.0, "v": 19185.0, "q_op": 175.0, "c": 10780.0, "pct_change": -2.97} |
| AR: data912 bonos | ✅ | 0.1 | bonos: 203 items; ej={"symbol": "AE38", "q_bid": 86.0, "px_bid": 108350.0, "px_ask": 109000.0, "q_ask": 5000.0, "v": 6304315.0, "q_op": 4275.0, "c": 108350.0, "pct_change": -0.08} |
| AR: data912 histórico GGAL | ✅ | 0.1 | GGAL hist: 6327 filas; ej={"date": "2026-11-19", "o": 4720.0, "h": 4900.0, "l": 4527.5, "c": 4545.0, "v": 2650514.0, "dr": -0.0472, "sa": 0.4372} |
| AR: BYMA líderes | ❌ | 25.0 | EXC ConnectTimeout: HTTPSConnectionPool(host='open.bymadata.com.ar', port=443): Max retries exceeded with url: /vanoms-be-core/rest/api/bymadata/free/leading-equity (Caused by Conn |
| AR: BYMA bonos públicos | ❌ | 25.0 | EXC ConnectTimeout: HTTPSConnectionPool(host='open.bymadata.com.ar', port=443): Max retries exceeded with url: /vanoms-be-core/rest/api/bymadata/free/public-bonds (Caused by Connec |
| AR: dolarapi CCL/MEP | ✅ | 0.1 | ['Oficial', 'Blue', 'Bolsa', 'Contado con liquidación', 'Mayorista', 'Cripto', 'Tarjeta'] |

Pendientes por falta de key (no probadas): Polygon/Massive free, Finnhub free, CoinGecko demo key.