import os
from pathlib import Path
import requests

root = Path(__file__).resolve().parents[1]
env_path = root / '.env'
if env_path.exists() and not os.environ.get('DUNE_API_KEY'):
    for line in env_path.read_text(encoding='utf-8').splitlines():
        text = line.strip()
        if not text or text.startswith('#') or '=' not in text:
            continue
        k, v = text.split('=', 1)
        if k.strip() == 'DUNE_API_KEY':
            os.environ['DUNE_API_KEY'] = v.strip().strip('"').strip("'")
            break

key = os.environ.get('DUNE_API_KEY', '').strip()
print('has_key=', bool(key))
headers = {'X-Dune-API-Key': key}
ids = [6881668, 6881718, 6881723, 6881732, 6881740]

for qid in ids:
    print(f"\nQ {qid}")
    meta_url = f"https://api.dune.com/api/v1/query/{qid}"
    res_url = f"https://api.dune.com/api/v1/query/{qid}/results"

    r1 = requests.get(meta_url, headers=headers, timeout=30)
    print(meta_url, '->', r1.status_code)
    if r1.status_code == 200:
        data = r1.json()
        qsql = data.get('query_sql') or (data.get('query') or {}).get('query_sql')
        print('has_sql=', bool(qsql), 'len=', len(qsql) if qsql else 0)

    r2 = requests.get(res_url, headers=headers, timeout=30)
    print(res_url, '->', r2.status_code)
    if r2.status_code == 200:
        rows = r2.json().get('result', {}).get('rows', [])
        print('rows=', len(rows))
