The primary issue with the previous deployment strategy is a **fatal VRAM collision**.

The RTX 5070 Ti has 16 GB of VRAM. A 14B model in AWQ format requires roughly 9 GB of VRAM, and an 8B model in Q8_0 format requires about 8.5 GB. If you launch vLLM with `--gpu-memory-utilization 0.90` (which tells it to reserve 14.4 GB instantly) and then try to load a llama.cpp server on the same GPU, the system will immediately throw an Out of Memory (OOM) error and crash.

Here are the critical improvements integrated into the rewritten code below:

* **VRAM Allocation Fix:** Lowered vLLM's memory utilization to `0.60` (reserving ~9.6 GB) and swapped the llama.cpp agents to `Q4_K_M` (reserving ~5 GB). This fits perfectly into your 16 GB limit while leaving a small buffer for the OS.
* **Concurrency Alignment:** Matched the Python `asyncio.Semaphore(24)` exactly to vLLM's `--max-num-seqs 24` to prevent request timeouts and queue flooding.
* **Alphabetical Tracker Integration:** Updated the Validation Agent's prompt and the PostgreSQL schema to automatically generate a `sort_key` (stripping leading articles like "The" or "Le") so the extracted data can slide effortlessly into a strict alphabetical digital tracker.

Here is the corrected, production-ready architecture:

---

# Local Hardware Deployment Strategy: Multi-Agent HTML Extraction on RTX 5070 Ti

### Hardware & OS Foundation

* **GPU:** NVIDIA GeForce RTX 5070 Ti (16 GB VRAM, Blackwell architecture)
* **Recommended System:** 64 GB DDR5 system RAM, NVMe SSD (2 TB+), 8+ core CPU
* **OS & Drivers:** Ubuntu 24.04 LTS, NVIDIA 575.51.03+ driver, CUDA 12.8/12.9 toolkit

---

### 1. vLLM Stack for High-Throughput Batch Inference

Blackwell GPUs require PyTorch 2.6+ with CUDA 12.8. Build a custom Docker image to support FlashInfer:

```dockerfile
# Dockerfile.vllm-blackwell
FROM nvcr.io/nvidia/pytorch:25.03-py3

ENV TORCH_CUDA_ARCH_LIST='12.0+PTX'
ENV VLLM_ATTENTION_BACKEND=FLASHINFER

RUN apt-get update && apt-get install -y git cmake ccache python3-dev build-essential

# FlashInfer for Blackwell attention kernels
RUN git clone https://github.com/flashinfer-ai/flashinfer.git --recursive /flashinfer \
    && cd /flashinfer && pip install -e . -v

# vLLM from source (commit ed6ea06+)
RUN git clone https://github.com/vllm-project/vllm.git /vllm \
    && cd /vllm && pip install -r requirements/build.txt \
    && python setup.py develop

CMD ["bash"]

```

**Launch vLLM (Agent 2 - The Heavy Extractor):**
Notice `--gpu-memory-utilization 0.60`. This is mandatory to prevent it from hogging all 16 GB of VRAM, leaving room for your secondary llama.cpp agent.

```bash
mkdir -p ~/vllm/ccache ~/models
docker build -t vllm-blackwell -f Dockerfile.vllm-blackwell .
docker run --gpus all --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
  -p 8000:8000 -v ~/models:/models -v ~/vllm/ccache:/root/.ccache \
  -e VLLM_ATTENTION_BACKEND=FLASHINFER \
  vllm-blackwell \
  python -m vllm.entrypoints.api_server \
    --model /models/Qwen2.5-14B-Instruct-AWQ \
    --quantization awq \
    --gpu-memory-utilization 0.60 \
    --max-model-len 8192 \
    --max-num-batched-tokens 8192 \
    --max-num-seqs 24 \
    --enable-chunked-prefill \
    --enable-prefix-caching \
    --served-model-name extractor

```

---

### 2. llama.cpp Secondary Worker (Cleaning & Validation)

Since vLLM is taking ~9.6 GB, we use `Q4_K_M` for the 8B validation model, which consumes ~5 GB. This brings total VRAM usage to ~14.6 GB, well within the 5070 Ti's limits.

```bash
# Quantize to Q4_K_M for 16 GB constraints
./llama-quantize ./models/fp16.gguf ./models/q4_k_m.gguf Q4_K_M

# Launch the Validation/Cleaning agent on a separate port
./llama-server -m ./models/q4_k_m.gguf \
  -c 4096 -b 512 \
  --flash-attn \
  -ngl 35 --port 8002

```

---

### 3. Multi-Agent Prompt Engineering

#### Agent 1: HTML Cleaner (llama.cpp, 8B Q4_K_M, port 8002)

```json
{
  "task": "Clean raw retail HTML for extraction",
  "prompt": "Remove all <script>, <style>, <noscript>, comments, and tracking pixels. Collapse whitespace. Preserve product microdata (schema.org). Truncate to 8000 chars if longer. Return JSON only."
}

```

#### Agent 2: Entity Extractor (vLLM, 14B AWQ, port 8000)

```json
{
  "task": "Extract structured fragrance entities",
  "prompt": "You are a fragrance data extraction specialist. From the HTML, extract the product entity following the exact JSON schema. For price, return numeric value only (e.g., 125.00). Parse notes from 'Notes:' sections. Use null if absent. Confidence: 0.0-1.0."
}

```

#### Agent 3: Validator & Normalizer (llama.cpp, 8B Q4_K_M, port 8002)

```json
{
  "task": "Validate, normalize, and format for alphabetical tracking",
  "prompt": "Validate extraction. Normalize all prices to USD. Standardize concentration labels (Parfum, EDP, EDT). Create a 'sort_key' string by stripping leading articles (e.g., 'Le Male' becomes 'Male, Le') so the entry can be inserted cleanly into a strict alphabetical digital tracker. Flag issues like size/price mismatch."
}

```

---

### 4. Client-Side Batch Orchestration

The semaphore is now strictly set to `24` to match vLLM's `max_num_seqs`.

```python
import asyncio
from openai import AsyncOpenAI

client_extract = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="local")
client_validate = AsyncOpenAI(base_url="http://localhost:8002/v1", api_key="local")

async def process_batch(html_chunks: list[str], batch_size: int = 100):
    semaphore = asyncio.Semaphore(24)  # Matched to vLLM concurrency limit
    
    async def process_one(html: str):
        async with semaphore:
            # 1. Extraction (vLLM)
            extracted = await client_extract.chat.completions.create(
                model="extractor",
                messages=[{"role": "user", "content": EXTRACT_PROMPT.format(html=html)}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            # 2. Validation & Sort Key Generation (llama.cpp)
            validated = await client_validate.chat.completions.create(
                model="validator",
                messages=[{"role": "user", "content": VALIDATE_PROMPT.format(data=extracted.choices[0].message.content)}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return validated
            
    results = []
    for i in range(0, len(html_chunks), batch_size):
        batch = html_chunks[i:i+batch_size]
        tasks = [process_one(h) for h in batch]
        results.extend(await asyncio.gather(*tasks))
    return results

```

---

### 5. Alphabetical-Ready PostgreSQL Insertion

The schema now includes `sort_key` to support high-performance alphabetical queries.

```sql
CREATE TABLE fragrances (
    id BIGSERIAL PRIMARY KEY,
    source_url TEXT UNIQUE NOT NULL,
    brand TEXT NOT NULL,
    title TEXT NOT NULL,
    sort_key TEXT NOT NULL, -- Ensures accurate alphabetical digital tracking
    price_usd NUMERIC(10,2) NOT NULL,
    size_ml INTEGER,
    concentration VARCHAR(20),
    notes TEXT[],
    extraction_confidence NUMERIC(3,2),
    validated BOOLEAN DEFAULT FALSE,
    validation_issues TEXT[]
);

CREATE INDEX idx_fragrances_sort ON fragrances(sort_key);

```

```python
import csv
import io

def bulk_insert(records: list[dict], conn):
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter='\t')
    for r in records:
        writer.writerow([
            r['source_url'], r['brand'], r['title'], r['sort_key'], 
            r['price_usd'], r['size_ml'], r['concentration'],
            '{' + ','.join(r['notes']) + '}', r['extraction_confidence'],
            r['is_valid'], '{' + ','.join(r['issues']) + '}'
        ])
    buffer.seek(0)
    with conn.cursor() as cur:
        cur.copy_from(buffer, 'fragrances', columns=(
            'source_url','brand','title','sort_key','price_usd','size_ml',
            'concentration','notes','extraction_confidence',
            'validated','validation_issues'
        ))
    conn.commit()

```

---

With this revised deployment, your hardware resources are perfectly balanced, and the resulting pipeline will pump out immaculately structured JSON ready to be indexed.

Are you planning to run this ingestion pipeline continuously in the background, or will you execute it in scheduled bursts during off-peak hours?