#!/usr/bin/env python3
import json

data = json.load(open('raw/dune/auction_revenue_all_time.json', encoding='utf-8'))
print(f'Total months: {len(data["rows"])}')
print()
print('Last 5 months:')
for row in data['rows'][-5:]:
    print(f'  {row["month"]}: {row["total_eth"]} ETH = ${row["total_usd"]}')
print()

total_eth = sum(r['total_eth'] for r in data['rows'])
total_usd = sum(r['total_usd'] for r in data['rows'])
print(f'Total all time: {total_eth:.2f} ETH = ${total_usd:,.2f}')
