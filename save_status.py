#!/usr/bin/env python3
"""Check status and save to JSON"""
import json
from pathlib import Path

data = {}

try:
    spend = json.load(open('data/spend_ledger.json', encoding='utf-8'))
    members = json.load(open('data/members.json', encoding='utf-8'))
    topics = json.load(open('data/milestones.json', encoding='utf-8'))
    props = json.load(open('data/proposals_archive.json', encoding='utf-8'))
    
    # Check category
    cat_count = len([r for r in spend.get('records',[]) if r.get('category')])
    total_spend = len(spend.get('records',[]))
    
    # Check sport
    sport_count = len([m for m in members.get('records',[]) if m.get('sport')])
    total_mem = len(members.get('records',[]))
    
    # Check milestones
    mile_count = len(topics.get('records',[]))
    
    # Check votes
    vote_count = len([p for p in props.get('records',[]) if p.get('votes') and len(p['votes']) > 0])
    total_props = len(props.get('records',[]))
    
    data = {
        'category': {'filled': cat_count, 'total': total_spend, 'pct': 100*cat_count/total_spend if total_spend > 0 else 0},
        'sport': {'filled': sport_count, 'total': total_mem, 'pct': 100*sport_count/total_mem if total_mem > 0 else 0},
        'milestones': {'count': mile_count},
        'votes': {'filled': vote_count, 'total': total_props, 'pct': 100*vote_count/total_props if total_props > 0 else 0}
    }
except Exception as e:
    data = {'error': str(e)}

# Write to JSON file
with open('reports/status_check.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Status saved to reports/status_check.json")
