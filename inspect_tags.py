#!/usr/bin/env python3
import json
import pprint

tags = json.load(open('data/proposal_tags.json', encoding='utf-8'))
print(f'Total tags: {len(tags.get("records", []))}')
print(f'File as_of: {tags.get("as_of")}')
print()

if tags.get('records'):
    print(f'First tag record:')
    pprint.pprint(tags['records'][0], width=100)
    print()

# Count by category
categories = {}
for record in tags.get('records', []):
    cat = record.get('semantic_category') or record.get('primary_category') or 'uncategorized'
    categories[cat] = categories.get(cat, 0) + 1

print(f'Tags by category:')
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f'  {cat}: {count}')
