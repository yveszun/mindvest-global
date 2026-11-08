# BehaviorGPT integration plan (not yet activated)

Documentation reviewed:
- https://portal.unboxai.com/llms.txt
- https://raw.githubusercontent.com/Unbox-AI/behaviorgpt/main/README.md
- https://raw.githubusercontent.com/Unbox-AI/behaviorgpt/main/docs/catalog-format.md
- https://raw.githubusercontent.com/Unbox-AI/behaviorgpt/main/.claude/skills/embed-catalog/SKILL.md

## Experimental mapping

- Decision unit: which funding opportunity theme an institution might support next.
- Item unit: stable opportunity theme ID, NOT a grant award ID; one item per theme. Awards map to themes only after human-reviewed classification.
- History: chronologically ordered documented awards, tentatively `Order([theme_item_id])` events. Do not fabricate `View` or `Search` events.
- Ranking catalog: theme/opportunity items. Source metadata stays in the local relational layer, not a replacement for evidence.
- Evaluate: chronological train/test split per funder; Recall@5, MRR, novel-theme recall, eligibility compliance, and coverage; compare with overlap/frequency/recency baselines.

## SDK catalog columns

`id`, `name`, `brand`, `categories`, `image_url`, `event_type`, `group`, `sales_since`, `timestamp`, `frequency`, `market`, `price`, `currency`, `search_keywords`, `keywords`.

`id` and `name` required; `event_type` and `group` must be `product`; other columns nullable. For this text-heavy institutional catalog, image hosting and upload behavior must be tested against the official format requirements. Leave unknown popularity values null, never invent them.

## Permission checkpoint

Before conversion or upload of an actual source dataset: review mappings, confirm source rights and public status, confirm which catalog is being created/refreshed, and obtain explicit approval. Only then call `client.embed` and record `catalog_id`. Keep `UNBOXAI_API_KEY` server-side. Until then, the prototype operates without an API key.
