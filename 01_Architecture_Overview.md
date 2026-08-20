```markdown
# Outline a highly scalable system architecture utilizing a Next.js frontend and a FastAPI backend to track real-time grey market prices for over 150,000 global fragrances. Detail the implementation of PostgreSQL for relational data mapping, Redis for caching trending clones, and Elasticsearch for ultra-fast, typo-tolerant full-text search across international name variations.

A scalable design should treat PostgreSQL as the source of truth, Elasticsearch as the discovery index, and Redis as the low-latency serving and real-time coordination layer. FastAPI exposes read/write and streaming APIs, while Next.js provides a globally cached, SEO-friendly application shell and subscribes only to the price updates relevant to the active view. FastAPI supports WebSocket endpoints with dependency-based authentication, but cross-instance fan-out should use a shared broker rather than in-process connection lists.

## System topology

```text
                         ┌────────────────────────────┐
                         │          Next.js            │
                         │ App Router / SSR / Edge CDN │
                         └──────────────┬─────────────┘
                          HTTPS REST    │    WebSocket/SSE
                                        │
                    ┌───────────────────▼───────────────────┐
                    │ API Gateway / WAF / Rate Limiting      │
                    └───────────────┬───────────────┬────────┘
                                    │               │
                    ┌───────────────▼───┐     ┌─────▼────────────────┐
                    │ FastAPI Read APIs │     │ Realtime Gateway      │
                    │ Search / Catalog  │     │ Subscription Manager  │
                    └─────┬──────┬──────┘     └────────┬──────────────┘
                          │      │                      │
                  ┌───────▼─┐ ┌──▼──────────┐      ┌────▼─────┐
                  │ Redis   │ │ Elasticsearch│      │ Redis    │
                  │ cache   │ │ search index │      │ Pub/Sub  │
                  └─────────┘ └──────────────┘      │ Streams  │
                                                     └────┬─────┘
                                                          │
       ┌─────────────────────────────── Event bus / stream ────────────────┐
       │                                                                     │
┌──────▼────────┐   ┌───────────────┐  ┌────────────────┐    ┌─────────────▼──┐
│ Source adapters│   │ Normalization │  │ Price evaluator │    │ Indexer / cache│
│ retailer, resale│→ │ & identity     │→ │ & anomaly rules │ → │ projection     │
└────────────────┘   └───────────────┘  └────────────────┘    └───────┬────────┘
                                                                        │
                                                   ┌────────────────────▼──┐
                                                   │ PostgreSQL primary +   │
                                                   │ read replicas / backup │
                                                   └───────────────────────┘
```

Use asynchronous workers for source collection, normalization, price calculation, index projection, and notifications; the customer-facing FastAPI service should never wait on scraping or bulk indexing. The architecture also avoids direct dual writes: persist a price event and an outbox record in one PostgreSQL transaction, then publish the outbox event to the stream; consumers update Elasticsearch, Redis, aggregates, and client subscriptions idempotently.

## Ingestion and identity

Each connector should be isolated by marketplace or retailer, with its own rate limits, credentials, parser version, proxy policy, and circuit breaker. Normalize every offer into a canonical currency, volume in milliliters, concentration, condition, seller region, observed time, source URL, and source-specific listing ID.

Use an identity-resolution service to map listings to the canonical fragrance:

1. Exact rules: GTIN/UPC/EAN, brand-supplied SKU, verified source mapping.
2. Strong match: normalized brand, scent name, concentration, bottle size, and edition.
3. Probabilistic match: multilingual aliases, transliteration, token similarity, and image/manual-review confidence.
4. Quarantine: retain uncertain listings without updating a published price until reviewed or confidence exceeds a threshold.

Do not equate a “clone” with the original fragrance. Model clone/dupe relationships explicitly and assign them a confidence score plus provenance, so users can see that “inspired by,” “similar to,” and confirmed alternative are materially different relationships.

## PostgreSQL model

PostgreSQL holds transactional relationships, provenance, editorial corrections, user alerts, and the immutable price-history record. Keep commonly filtered attributes relational, while retaining source-specific and irregular metadata in `jsonb`; PostgreSQL supports GIN indexes for efficient key and key/value searches within `jsonb` documents.


| Table | Purpose | Important indexes / constraints |
| :-- | :-- | :-- |
| `brand` | Canonical house/brand, parent company, country | Unique normalized brand key |
| `fragrance` | Canonical product family, brand, launch year, status | `(brand_id, canonical_slug)` unique |
| `fragrance_variant` | Concentration, edition, gender marketing, bottle/volume variant | Unique `(fragrance_id, concentration, edition_key, size_ml)` |
| `fragrance_name` | International names, aliases, scripts, transliterations | `(locale, normalized_name)` plus canonical variant FK |
| `relationship` | Clone/dupe, flankers, reformulations, equivalents | `(from_variant_id, relationship_type, to_variant_id)` unique; confidence and source |
| `marketplace` | Source, market, trust tier, fees and rules | Unique marketplace key |
| `listing` | Current identity and availability of a marketplace offer | Unique `(marketplace_id, external_listing_id)` |
| `price_observation` | Append-only observed price, stock, shipping, condition, currency | Partition by `observed_at`; index `(variant_id, region, observed_at DESC)` |
| `price_snapshot` | Latest and calculated price per variant, region, condition, size | Unique `(variant_id, region, condition, size_ml)```<|END_OF_TURN_TOKEN|>

I've rewritten the text to improve readability and clarity, while retaining all the original content: 

### Partitioning Strategy

Partition the `price_observation` table by time initially monthly, with subpartitions based on a stable hash of `fragrance_variant_id`. This approach ensures manageable retention, backfills, and time-window queries without fragmenting core catalog tables. With 150,000 fragrances, storage and throughput concerns are primarily driven by price observations. 

### Price Semantics

Store various price components separately: source price, shipping costs, taxes (if known), fees, currency, foreign exchange rate/version, and a normalized landed price. Present market prices as robust statistics like medians or trimmed medians filtered by region, bottle size, condition, and trusted-source policy, rather than just the lowest listing observed. 

Flag outliers but don't discard them silently. A useful publish rule could be: require a minimum of independent listings or corroboration from another source; reject impossible combinations of sizes/prices; and provide a confidence score with quotes. 

## Redis for Hot Reads & Clones

Use Redis to store data that's cheap to recompute but expensive to fetch repeatedly, such as product-page snapshots, trending rankings, autocomplete suggestions, user alert state, API rate limits, and real-time subscription routing. Here is a recommended key layout: 

```text
fragrance:{variant_id}:snapshot:{region}       JSON, TTL 30–120 seconds
search:suggest:{locale}:{normalized_prefix}     JSON, TTL 5–30 minutes
trending:clones:{region}:{window}               Sorted set, refreshed every minute
clone:{variant_id}:top:{region}                 JSON, TTL 5–15 minutes
pricechart:{variant_id}:{region}:{range}        JSON/compressed, TTL 1–5 minutes
ws:topic:{variant_id}                           Pub/Sub channel
rate:{actor}:{minute_bucket}                    Counter with expiry
```

Define "trending clones" using a decaying score, not just total views. Combine clone-page views, searches, watchlist additions, alert creation, and price movement; weigh these by event recency and deduplicate them per user/session. Store the ranking in a Redis sorted set and have FastAPI return the top N directly without joining large sets at request time. 

Use cache-aside for catalog and aggregate reads: read from Redis first, then fallback to PostgreSQL or Elasticsearch; populate with bounded TTLs and some jitter. On price updates, publish an invalidation/update event but don't assume that's enough for real-time client delivery. 

## Elasticsearch Search

Index one document per `fragrance_variant`, denormalized with canonical fields, all international names, aliases, brand aliases, clone relations, search popularity, and current regional price summaries. Elasticsearch fuzzy queries can handle inserted, removed, changed, or transposed characters using Levenshtein edit distance. 

Example document: 

```json
{
  "variant_id": "uuid",
  "brand": {"canonical": "Maison Example", "aliases": ["Example Maison"]},
  "names": [
    {"text": "Noir Édition", "locale": "fr-FR", "type": "canonical"},
    {"text": "ノワール エディション", "locale": "ja-JP", "type": "localized"},
    {"text": "Noir Edition", "locale": "und", "type": "transliteration"}
  ],
  "attributes": {"concentration": "EDP", "size_ml": 100, "launch_year": 2021},
  "clone_of": [{"variant_id": "uuid", "confidence": 0.91}],
  "markets": [{"region": "US", "median_price": 87.5, "currency": "USD"}],
  "popularity": 0.78
}
```

### Mapping & Analyzers 

Use multifields instead of a generic text field: 

- `keyword` normalizer for exact filters, IDs, brand facets, canonical slugs, and locale codes.
- `text` field with Unicode folding, lowercase, punctuation normalization, and language-aware analyzers where needed.
- `search_as_you_type` or edge-ngram subfields for prefix autocomplete.
- Transliteration subfields (Cyrillic/Arabic/Greek to Latin) so native and Latin script queries match. 
- A synonym graph from curated brand/name aliases, historical names, common abbreviations, and verified regional variants. 

Use a two-stage query: first run boosted exact/prefix matching; then constrained fuzzy matching only if recall is insufficient. Set `fuzziness` to `AUTO`, a nonzero `prefix_length`, and conservative expansion caps as Elasticsearch cautions high expansions can harm performance, especially with zero prefix length. 

```json
{
  "size": 20,
  "query": {
    "bool": {
      "should": [
        {"multi_match": {
          "query": "bacarrat rouge",
          "type": "bool_prefix",
          "fields": ["brand.search", "names.text.search_as_you_type"]
        }},
        {"multi_match": {
          "query": "bacarrat rouge",
          "fields": ["brand.text^5", "names.text^8", "names.aliases^4"],
          "fuzziness": "AUTO",
          "prefix_length": 2,
          "max_expansions": 25
        }}
      ],
      "minimum_should_match": 1,
      "filter": [{"term": {"status": "active"}}]
    }
  }
}
```

Reindex through versioned aliases: write to `fragrances_v12`, validate it, then atomically move the read alias. This supports evolution of analyzers and mappings without search downtime. 

## FastAPI Services

Deploy stateless FastAPI pods behind a load balancer with separate read/ingestion-control/realtime workloads. Expose versioned APIs like: 

```text
GET  /v1/search?q=&locale=&market=
GET  /v1/fragrances/{slug}?market=US
GET  /v1/fragrances/{id}/prices?range=90d&region=US
GET  /v1/fragrances/{id}/clones?region=US
POST /v1/alerts
GET  /v1/trending/clones?region=US
WS   /v1/stream?topics=price:{variant_id},trending:US
```

For reads, FastAPI resolves Redis first, then Elasticsearch for search or PostgreSQL. Use async drivers, bounded pools, timeouts, pagination, cursor pagination for histories, and response-size limits per route. 

For streaming: authenticate at connection setup; authorize each topic; subscribe clients only to visible/watchlisted product IDs. FastAPI supports text/binary/JSON data but its own docs note in-memory connections work within one process, so use Redis Pub/Sub or a durable stream-backed broadcaster for multi-replica fan-out. 

Send compact deltas: 

```json
{
  "type": "price.updated",
  "variant_id": "uuid",
  "region": "US",
  "median_price": 87.50,
  "currency": "USD",
  "change_24h_pct": -4.1,
  "as_of": "2026-08-18T21:54:00Z",
  "sequence": 918283
}
```

Include a monotonically increasing sequence/version so the client can ignore stale/duplicate updates and request REST resync after reconnecting. 

## Next.js Frontend

Use Next.js App Router for server-rendered catalog, brand, fragrance pages with CDN caching for anonymous pages/metadata. Cache controls fit immutable catalog details and short-lived market summary pages: 

- Render canonical fragrance pages on the server for SEO, social previews, locale awareness, and fast first paint. 
- Hydrate only interactive islands post-rendering: price chart, marketplace filters, watchlist, live price badge.
- Fetch initial snapshots via FastAPI with short revalidation; after hydration, attach a WebSocket only to visible/watched variants.
- Keep global trending clones on a 30–60 second polling/revalidation cadence without opening sockets for every visitor. 

## Reliability & Operations

Run PostgreSQL with multi-zone primary/standby replication, point-in-time recovery, tested restores, and read replicas for noncritical history queries. Use Elasticsearch shards based on measured index volume/query rate rather than pre-sharding; scale primarily for aliases, price projections, traffic, not canonical fragrances' count. 

Monitor: 

- Ingestion freshness by source, parser failures, mapping confidence distribution, missing listing rates. 
- PostgreSQL replication lag, slow queries, partition growth, lock waits, outbox backlog. 
- Redis memory usage, eviction rate, hit ratio, hot key rates, stream consumer lags, Pub/Sub fan-out pressure. 
- Elasticsearch p95/p99 latencies, rejected requests, shard balance, indexing lag, zero result rates, search-to-click success ratios. 
- User outcomes: quote freshness, chart load latency, alert delivery latency, incorrect match reports. 

## Security & Governance

Keep marketplace credentials in encrypted secrets managers; use short-lived user tokens; enforce RBAC for source management and editorial corrections. Apply WAF rules, endpoint rate limits, never expose unredacted payloads/credentials to browsers, log mapping changes, price overrides. 

Compliance should be a first-class ingestion constraint: each adapter should encode permitted access methods, data retention rules, attribution requirements, market pricing/tax disclosures. Grey-market data is especially sensitive; make source trust, condition, authenticity signals, quote confidence visible attributes instead of hidden details.<|END_OF_TURN_TOKEN|>
