#!/usr/bin/env python3
"""
Build milestones.json from proposals data
Cria estrutura de milestones/deliverables para cada proposta
"""

import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def extract_phases_from_title(title: str) -> str:
    """Extrair fase/categoria do título da proposta"""
    title_lower = title.lower()
    
    if any(x in title_lower for x in ['event', 'irl', 'competition', 'contest']):
        return 'event_planning'
    elif any(x in title_lower for x in ['documentary', 'video', 'media', 'film']):
        return 'media_production'
    elif any(x in title_lower for x in ['park', 'infrastructure', 'facility']):
        return 'infrastructure'
    elif any(x in title_lower for x in ['sponsor', 'athlete', 'team']):
        return 'athlete_support'
    elif any(x in title_lower for x in ['research', 'study', 'analysis']):
        return 'research'
    elif any(x in title_lower for x in ['tool', 'software', 'app', 'platform']):
        return 'tooling'
    else:
        return 'general'


def main() -> None:
    proposals = load(DATA / "proposals_archive.json")
    
    milestones = []
    execution_count = 0
    
    for proposal in proposals.get("records", []):
        archive_id = proposal.get("archive_id")
        if not archive_id:
            continue
        
        status = proposal.get("status", "unknown")
        phase = extract_phases_from_title(proposal.get("title", ""))
        
        # Determinar status do milestone
        if status == "executed":
            milestone_status = "completed"
            completion_pct = 100
        elif status == "active":
            milestone_status = "in_progress"
            completion_pct = 50
        else:
            milestone_status = "not_started"
            completion_pct = 0
        
        # Criar milestone principal
        milestone = {
            "milestone_id": f"{archive_id}:main",
            "proposal_id": archive_id,
            "project_id": archive_id,
            "phase": phase,
            "title": f"Proposal {archive_id}: {proposal.get('title', 'Untitled')}",
            "deliverable": proposal.get("title", "Unknown deliverable"),
            "description": proposal.get("description", ""),
            "status": milestone_status,
            "completion_percentage": completion_pct,
            "start_date": proposal.get("proposal_created_at"),
            "end_date": proposal.get("proposal_executed_at") or proposal.get("proposal_end_at"),
            "chain": proposal.get("chain"),
            "priority": "high" if status == "executed" else "medium"
        }
        
        milestones.append(milestone)
        if status == "executed":
            execution_count += 1
    
    # Create output structure
    output = {
        "dataset": "milestones",
        "as_of": datetime.now().isoformat(),
        "version": 1,
        "records": milestones,
        "summary": {
            "total_milestones": len(milestones),
            "completed": execution_count,
            "in_progress": len([m for m in milestones if m["status"] == "in_progress"]),
            "not_started": len([m for m in milestones if m["status"] == "not_started"])
        }
    }
    
    save(DATA / "milestones.json", output)
    
    print(f"✅ Built milestones.json with {len(milestones)} records")
    print(f"   - Completed: {execution_count}")
    print(f"   - In Progress: {output['summary']['in_progress']}")
    print(f"   - Not Started: {output['summary']['not_started']}")


if __name__ == "__main__":
    main()
