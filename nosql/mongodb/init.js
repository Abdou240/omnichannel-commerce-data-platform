// ============================================================================
// MongoDB-Initialisierung: Raw-Document-Store
// Wird beim ersten Start des MongoDB-Containers ausgefuehrt
// (via docker-entrypoint-initdb.d).
// Erstellt 4 Collections mit passenden Indexes fuer die Batch/Streaming-Pipeline.
// ============================================================================

// Datenbank: commerce_raw (optionaler JSON-Speicher fuer Roh-Payloads)
db = db.getSiblingDB("commerce_raw");

// 4 Collections fuer die 4 Datenquellen
db.createCollection("retailrocket_events_raw");
db.createCollection("open_food_facts_products_raw");
db.createCollection("open_meteo_weather_raw");
db.createCollection("frankfurter_fx_raw");

// Indexes fuer schnelle Abfragen und Deduplizierung
db.retailrocket_events_raw.createIndex({ event_id: 1 }, { unique: true });
db.retailrocket_events_raw.createIndex({ event_type: 1, event_ts: -1 });
db.open_food_facts_products_raw.createIndex({ product_code: 1 });
db.open_meteo_weather_raw.createIndex({ weather_date: 1, city: 1 });
db.frankfurter_fx_raw.createIndex({ rate_date: 1, base_currency: 1, quote_currency: 1 });
