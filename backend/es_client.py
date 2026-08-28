import os
from elasticsearch import AsyncElasticsearch

ES_URL = os.getenv("ES_URL", "http://localhost:9200")

es_client = AsyncElasticsearch(ES_URL)

async def get_es():
    yield es_client

async def init_es_index():
    index_name = "fragrances"
    
    # Define mapping with fuzzy search capabilities
    mapping = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "autocomplete": {
                        "type": "custom",
                        "tokenizer": "autocomplete_tokenizer",
                        "filter": ["lowercase"]
                    }
                },
                "tokenizer": {
                    "autocomplete_tokenizer": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 20,
                        "token_chars": ["letter", "digit"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "dna_id": {"type": "keyword"},
                "brand_name": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "standard"},
                "canonical_name": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "standard"},
                "market_segment": {"type": "keyword"},
                "is_dupe": {"type": "boolean"},
                "inspired_by": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "standard"}
            }
        }
    }
    
    exists = await es_client.indices.exists(index=index_name)
    if exists:
        await es_client.indices.delete(index=index_name)
        print(f"Deleted old Elasticsearch index: {index_name}")
        
    await es_client.indices.create(index=index_name, body=mapping)
    print(f"Created Elasticsearch index: {index_name}")
