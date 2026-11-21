# Chequeo de secretos (sin valores)

| Chequeo | Estado | Detalle |
|---|---|---|
| POLYGON_API_KEY presente | ✅ | longitud=32 |
| FINNHUB_API_KEY presente | ✅ | longitud=40 |
| SUPABASE_URL presente | ✅ | longitud=40 |
| SUPABASE_SERVICE_KEY presente | ✅ | longitud=46 |
| SEC_CONTACT_EMAIL presente | ✅ | longitud=27 |
| POLYGON_API_KEY funciona | ✅ | HTTP 200, resultsCount=12564 (grouped daily, todo el mercado en 1 llamada) |
| FINNHUB_API_KEY funciona | ✅ | HTTP 200, precio presente=True |
| Forma de SUPABASE_* | ✅ | empieza con https://=False, termina en .supabase.co=False, tiene espacios=False; tipo=sb_publishable_ (NO sirve: es la clave publica) |
| SUPABASE_* funciona | ❌ | error de red/tipo MissingSchema |
