import json
from pathlib import Path

auction = json.loads(Path('raw/dune/auction_revenue_all_time.json').read_text(encoding='utf-8'))
rows = auction if isinstance(auction, list) else auction.get('rows', [])
total_eth = sum(float(r.get('total_eth') or r.get('eth_amount') or 0) for r in rows)
total_usd = sum(float(r.get('total_usd') or r.get('usd_value') or 0) for r in rows)
print(f"Auction revenue: {total_eth:.2f} ETH = ${total_usd:,.0f} USD")

spend = json.loads(Path('raw/dune/proposal_spend_by_category.json').read_text(encoding='utf-8'))
rows2 = spend if isinstance(spend, list) else spend.get('rows', [])
total_usdc = sum(float(r.get('usdc_amount') or 0) for r in rows2)
print(f"Proposal spend (Dune): ${total_usdc:,.0f} USDC across {len(rows2)} proposals")

treasury = json.loads(Path('data/treasury.json').read_text(encoding='utf-8'))
balance = float((treasury.get('overview') or {}).get('treasury_page_total_value_usd') or 0)
print(f"Current balance: ${balance:,.0f}")
print(f"Expected gap: ${total_usd - total_usdc - balance:,.0f}")
