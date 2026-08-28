# Project Context: Fragrance Aggregator & Dupe Mapper

### 1. The Core Objective
The system is a high-performance fragrance aggregator designed to automate price tracking and clone matching. It replaces manual spreadsheet tracking to quickly identify dupe relationships across 17 target e-commerce sites. This automated data pipeline directly supports content creation and clone comparisons for O.C. Decant.

### 2. The Tech Stack
*   **Frontend:** Next.js (App Router), Tailwind CSS, TypeScript. Key UI elements include `FragranceCard` and `GlassCard` for rendering "Inspired by" tags.
*   **Backend:** Python via FastAPI.
*   **Data Pipeline:** Crawl4AI for asynchronous markdown extraction, falling back to direct `/products.json` fetches for Shopify storefronts.
*   **Database & Search:** Elasticsearch configured with an `edge_ngram` tokenizer for fuzzy matching, alongside Redis for caching.

### 3. AI & Hardware Specifications
*   **Local Inference:** All unstructured markdown parsing and dupe identification is routed through local AI endpoints (via LiteLLM/LM Studio). 
*   **Hardware:** The extraction pipeline is optimized to run entirely on an RTX 5070 Ti, eliminating cloud API costs.
*   **Target Logic:** The extraction models are tuned to handle complex naming conventions from clone houses such as Bujairami, Lattafa, French Avenue, Divain, and Armaf.

### 4. Agent Tooling
The workspace is governed by custom standalone skills located in `~/.agents/skills/`. The coding agent is instructed to prioritize strict schema extraction and database synchronization when expanding the scraping engine.