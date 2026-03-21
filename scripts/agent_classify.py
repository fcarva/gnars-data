from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from google import genai
    from pydantic import BaseModel
except ImportError:
    print("Error: Missing required packages.")
    print("Please run: pip install google-genai pydantic")
    sys.exit(1)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ARCHIVE_PATH = DATA_DIR / "proposals_archive.json"
TAGS_PATH = DATA_DIR / "proposal_tags.json"


class ProposalClassification(BaseModel):
    semantic_category: str
    confidence: float
    sport: Optional[str] = None
    capital_breakdown: dict[str, float] = {}
    reasoning: str


ONTOLOGY = """
- athletes_riders: Sponsoring athletes, riders, providing gear or travel for extreme sports and competitions.
- public_goods: Philanthropy, charity, positive externalities outside the DAO ecosystem.
- workstream_ops: Core DAO operations, developer compensation, infrastructure costs, community management, moderation.
- workstream_media: Content creation, video production, documentaries, podcasts, newsletters.
- workstream_products: Physical products, merch, branding, Noggles production, apparel.
- irl_events: General IRL events, meetups, parties, contests NOT strictly tied to sponsoring a specific independent athlete.
- governance_policy: Metagovernance, changes to quorum, treasury management strategies, autonomous agents, setup.
"""

SPORT_ONTOLOGY = """
- sk8: skateboarding-focused proposal
- surf: surfing-focused proposal
- bmx: bmx/bike-focused proposal
- snow: snowboarding-focused proposal
- mx: motocross-focused proposal
- mtb: mountain biking-focused proposal
- multi: multi-sport proposal
- null: not athlete-focused
"""

PROMPT_SYSTEM = f"""
You are an expert crypto-governance analyst specializing in the Gnars DAO. 
Your task is to classify DAO proposals into one of the following exact semantic categories based on the proposal's content and intent:

{ONTOLOGY}

Also infer optional sport classification when proposal is athlete-focused:
{SPORT_ONTOLOGY}

Provide a capital breakdown with percentages summing to 100 over keys:
athletes, media, ops, dev, events, public_goods, other

If none fit perfectly, use "uncategorized". 
Read the proposal title and description, then provide the category, confidence score (0.0 to 1.0), and a brief rationale.
"""

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=4, ensure_ascii=False)
        handle.write("\n")

def classify_proposal(client: genai.Client, title: str, description: str) -> ProposalClassification:
    truncated_desc = description[:3000] if description else ""
    
    prompt = f"{PROMPT_SYSTEM}\n\nTitle: {title}\n\nDescription: {truncated_desc}"
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config={
            'response_mime_type': 'application/json',
            'response_schema': ProposalClassification,
            'temperature': 0.1,
        },
    )
    
    parsed: Any = response.parsed
    if isinstance(parsed, ProposalClassification):
        return parsed
    if isinstance(parsed, dict):
        return ProposalClassification.model_validate(parsed)
    raise ValueError("Unexpected Gemini response payload")

def main():
    parser = argparse.ArgumentParser(description="Enrich proposal tags using an Agent (AEP)")
    parser.add_argument("--test-id", type=str, help="Run only on a specific archive_id (e.g. gnars-base-117)")
    parser.add_argument("--force", action="store_true", help="Re-classify even if semantic_category exists")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)

    archive = load_json(ARCHIVE_PATH)
    tags_data = load_json(TAGS_PATH)
    
    archive_dict = {p["archive_id"]: p for p in archive["records"]}
    
    records = tags_data.get("records", [])
    updated_count = 0
    
    for record in records:
        arch_id = record["archive_id"]
        
        if args.test_id and arch_id != args.test_id:
            continue
            
        if "semantic_category" in record and not args.force and not args.test_id:
            continue
            
        proposal = archive_dict.get(arch_id)
        if not proposal:
            print(f"[{arch_id}] Not found in archive. Skipping.")
            continue
            
        title = proposal.get("title", "")
        description = proposal.get("description", "")
        
        print(f"Classifying: {arch_id} - {title[:50]}...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                classification = classify_proposal(client, title, description)
                print(f"  -> {classification.semantic_category} ({classification.confidence:.2f})")
                print(f"  -> {classification.reasoning}")
                
                record["semantic_category"] = classification.semantic_category
                record["semantic_confidence"] = classification.confidence
                record["confidence"] = classification.confidence
                record["semantic_reasoning"] = classification.reasoning
                if classification.sport is not None:
                    record["sport"] = classification.sport
                if classification.capital_breakdown:
                    record["capital_breakdown"] = classification.capital_breakdown
                updated_count += 1
                
                # Avoid Gemini free tier rate limit: 15 RPM for 2.5-flash / free tier usually 15 RPM (4s) -> using 15s for safety
                time.sleep(15)
                break  # Success, break the retry loop
            except Exception as e:
                error_str = str(e)
                print(f"  -> Error classifying {arch_id} (Attempt {attempt+1}/{max_retries}): {e}")
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    print("  -> Rate limit hit. Sleeping for 30 seconds before retrying...")
                    time.sleep(30)
                else:
                    break # Break on non-rate-limit errors

    if updated_count > 0:
        tags_data["as_of"] = isoformat_utc(utc_now())
        write_json(TAGS_PATH, tags_data)
        print(f"\nSuccessfully updated {updated_count} records.")
    else:
        print("\nNo records were updated.")

if __name__ == "__main__":
    main()
