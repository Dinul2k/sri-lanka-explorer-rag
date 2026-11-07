"""Generate a fixed query bank for cache-vs-RAG latency benchmarks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DISTRICTS = [
    "Colombo",
    "Gampaha",
    "Galle",
    "Matara",
    "Badulla",
    "Kalutara",
    "Hatton",
    "Rathnapura",
    "Kurunegala",
    "Matale",
    "Hambantota",
]

INTENTS = [
    {
        "id": "budget_food",
        "canonical": "Best budget food in {district}",
        "paraphrases": [
            "Cheap places to eat in {district}",
            "Affordable local food recommendations for {district}",
            "Where can I find inexpensive meals in {district}?",
            "Budget-friendly restaurants and street food in {district}",
        ],
    },
    {
        "id": "tuk_tuk",
        "canonical": "Tuk-tuk tips for getting around {district}",
        "paraphrases": [
            "How should I ride three-wheelers in {district}?",
            "Advice for tuk tuk fares in {district}",
            "Is Grab or PickMe better for tuk-tuks in {district}?",
            "Local transport tips using tuk-tuks in {district}",
        ],
    },
    {
        "id": "beaches",
        "canonical": "Quiet beaches near {district}",
        "paraphrases": [
            "Less crowded beach spots around {district}",
            "Calm swimming beaches close to {district}",
            "Where are peaceful coastal areas near {district}?",
            "Hidden beach recommendations near {district}",
        ],
    },
    {
        "id": "temples",
        "canonical": "Temple etiquette and must-see shrines in {district}",
        "paraphrases": [
            "What should tourists know before visiting temples in {district}?",
            "Dress code and customs for temples around {district}",
            "Best cultural and temple stops in {district}",
            "Religious sites worth visiting in {district}",
        ],
    },
    {
        "id": "stay",
        "canonical": "Good guest houses and homestays in {district}",
        "paraphrases": [
            "Affordable places to stay in {district}",
            "Family-run lodging recommendations for {district}",
            "Where should backpackers stay in {district}?",
            "Budget accommodation tips for {district}",
        ],
    },
    {
        "id": "day_trip",
        "canonical": "Best day trips from {district}",
        "paraphrases": [
            "What can I visit in one day starting from {district}?",
            "Nearby attractions for a day outing from {district}",
            "Recommended short excursions around {district}",
            "One-day itinerary ideas based in {district}",
        ],
    },
    {
        "id": "slang",
        "canonical": "Useful local slang for travellers in {district}",
        "paraphrases": [
            "Local words and phrases tourists should know in {district}",
            "Explain Sri Lankan slang useful around {district}",
            "Common tourism slang near {district}",
            "What local terms help when visiting {district}?",
        ],
    },
    {
        "id": "weather",
        "canonical": "When is the best weather to visit {district}?",
        "paraphrases": [
            "Monsoon timing advice for {district}",
            "Best season for travel to {district}",
            "Rainy season tips for visitors to {district}",
            "What months are ideal for {district} tourism?",
        ],
    },
    {
        "id": "nightlife",
        "canonical": "Safe evening activities and nightlife in {district}",
        "paraphrases": [
            "What to do at night in {district}",
            "Evening food and cafe spots in {district}",
            "Is nightlife tourist-friendly in {district}?",
            "Night-time travel tips for {district}",
        ],
    },
    {
        "id": "shopping",
        "canonical": "Local markets and souvenir shopping in {district}",
        "paraphrases": [
            "Where to buy handicrafts in {district}",
            "Best markets for travellers in {district}",
            "Souvenir tips and local products from {district}",
            "Shopping areas worth visiting in {district}",
        ],
    },
]


def build_cases(target: int, variants_per_family: int) -> list[dict]:
    families: list[tuple[str, str, list[str]]] = []
    for district in DISTRICTS:
        for intent in INTENTS:
            family = f"{district.lower()}-{intent['id']}"
            canon = intent["canonical"].format(district=district)
            paras = [p.format(district=district) for p in intent["paraphrases"]]
            families.append((family, district.lower(), [canon, *paras]))

    # 11 districts × 10 intents = 110 families
    cases: list[dict] = []
    family_idx = 0
    while len(cases) < target:
        family, district, base_queries = families[family_idx % len(families)]
        family_idx += 1
        # Expand family to variants_per_family using exact repeats after paraphrases
        pool = list(base_queries)
        while len(pool) < variants_per_family:
            pool.append(base_queries[0])  # exact repeat of canonical → reliable cache hit

        for i, query in enumerate(pool[:variants_per_family]):
            if len(cases) >= target:
                break
            role = "canonical" if i == 0 else ("paraphrase" if query != pool[0] and i < len(base_queries) else "exact_repeat")
            cases.append(
                {
                    "id": f"{family}-{i:02d}",
                    "family": family,
                    "district": district,
                    "intent": family.split("-", 1)[1],
                    "role": role,
                    "response_type": "short",
                    "query": query,
                    "is_seed": i == 0,
                    "expect_source": "llama3_rag_fallback" if i == 0 else "cache",
                }
            )
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1500, help="Total queries to generate (1000-2000)")
    parser.add_argument(
        "--variants-per-family",
        type=int,
        default=15,
        help="Queries per district/intent family (1 seed + rest repeats/paraphrases)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).parent / "fixtures" / "query_bank.json",
    )
    args = parser.parse_args()
    if not 1000 <= args.count <= 2000:
        raise SystemExit("--count must be between 1000 and 2000")

    cases = build_cases(args.count, args.variants_per_family)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "description": "Tourism RAG cache-vs-baseline query bank",
        "count": len(cases),
        "families": len({c['family'] for c in cases}),
        "response_type": "short",
        "cases": cases,
    }
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    seeds = sum(1 for c in cases if c["is_seed"])
    print(f"Wrote {len(cases)} cases ({seeds} seeds / families) → {args.out}")


if __name__ == "__main__":
    main()
