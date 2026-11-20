# Fuentes de datos — decisiones tras el spike (Fase 1.1)

Base: `docs/spike-results.md` (corrido desde PC residencial el 2026-11-20). **Falta repetirlo desde GitHub Actions** (IPs de datacenter).

| Necesidad | Decisión | Estado |
|---|---|---|
| Universo EE.UU. | Nasdaq Trader (`nasdaqlisted` 5.608 + `otherlisted` 7.692 filas brutas, a filtrar) | ✅ |
| Mapa ticker→CIK | SEC `company_tickers.json` (10.398) | ✅ |
| Fundamentales EE.UU. | SEC EDGAR companyfacts (EPS diluido, patrimonio, resultado neto presentes en AAPL) | ✅ |
| Histórico EE.UU. (watchlist, 10y) | Yahoo/yfinance (QQQ 10y = 2.514 filas) | ✅ |
| Forward P/E (watchlist) | Yahoo `forwardPE` | ✅ (no oficial) |
| Cruce de precios EE.UU. | **Stooq descartado** (devuelve HTML, ahora exige captcha/key). Reemplazo: Polygon/Massive o Finnhub cuando haya key | ⚠️ pendiente key |
| EOD todo el mercado | Polygon/Massive free | ⏳ sin probar (falta key) |
| Cripto ranking/mcap/ATH/dominancia | CoinGecko sin key anduvo (50 monedas, campos ATH y volumen) | ✅ |
| Cripto funding/OI/precio | OKX público | ✅ |
| Cripto respaldo | Binance futures/spot y Bybit respondieron desde esta IP; **no garantizado en GitHub Actions** | ⚠️ re-test |
| Argentina cotizaciones | **data912**: acciones (96), cedears (1.049 líneas), bonos (202) | ✅ |
| Argentina histórico | data912 `/historical/stocks/GGAL` (6.327 filas con OHLCV) | ✅ |
| Argentina BYMA Open Data | Timeout de conexión en ambos endpoints → **descartado como primaria** | ❌ |
| Dólar CCL/MEP | dolarapi.com (Oficial, Bolsa=MEP, CCL, Mayorista, Cripto, ...) | ✅ |

## Resultado desde GitHub Actions (`docs/spike-results-actions.md`, 2026-11-20)
- ✅ Igual que en la PC: Nasdaq Trader, Yahoo (precios, fundamentales, 10y), OKX, CoinGecko, data912 (acciones, cedears, bonos, histórico), dolarapi, Binance spot público.
- ❌ **Binance futures: HTTP 451** (ubicación restringida) y **Bybit: HTTP 403** (bloquea EE.UU.) => **OKX es la única fuente de derivados cripto en producción**. Binance spot (`data-api.binance.vision`) sirve como respaldo de precio.
- ❌ BYMA y Stooq: mismo fallo que en la PC (descartados).
- ⚠️ SEC EDGAR: no se pudo probar desde Actions; el secreto `SEC_CONTACT_EMAIL` llegó vacío (ticker->CIK dio 403 por falta de User-Agent identificado). Re-probar al corregir el secreto.

## Implicancias de diseño
- data912 pasa a ser la fuente primaria de Argentina (en vivo e histórico). Es no oficial: Yahoo `.BA` queda de respaldo y de cruce.
- Las 1.049 líneas de cedears incluyen variantes por moneda (ARS/USD/CCL del mismo subyacente): hay que normalizar a un instrumento + alias.
- Sin Stooq, la validación cruzada EE.UU. depende de conseguir la key de Polygon/Massive o Finnhub (sub-etapa 2).
- Riesgo abierto: ninguna fuente de Argentina es oficial; el criterio de fallo es "data912 caído => datos STALE visibles, no inventados".
