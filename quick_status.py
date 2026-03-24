#!/usr/bin/env python3
"""Simple audit status check"""
import json

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
    
    print(f"Category: {100*cat_count/total_spend:.1f}% ({cat_count}/{total_spend})")
    print(f"Sport: {100*sport_count/total_mem:.1f}% ({sport_count}/{total_mem})")
    print(f"Milestones: {mile_count} records")
    print(f"Votes: {100*vote_count/total_props:.1f}% ({vote_count}/{total_props})")
except Exception as e:
    print(f"Error: {e}")
