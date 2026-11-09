"""Best-effort public Google Scholar profile statistics scraper.
No login, CAPTCHA bypass, or fabricated fallback values.
"""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER_ID = 'hmaRRBUAAAAJ'
OUT = Path(__file__).resolve().parents[1] / 'scholar.json'
url = f'https://scholar.google.com/citations?user={USER_ID}&hl=en'
resp = requests.get(url, timeout=25, headers={
    'User-Agent': 'Mozilla/5.0 (compatible; PersonalScholarStats/1.0)',
    'Accept-Language': 'en-US,en;q=0.9',
})
resp.raise_for_status()
soup = BeautifulSoup(resp.text, 'html.parser')
# Google Scholar profile table: rows Citations, h-index, i10-index;
# first numeric column is the all-time statistic, second is since-year.
table = soup.select_one('#gsc_rsb_st')
if table is None:
    raise RuntimeError('Scholar statistics table missing (blocked or layout changed)')
values = {}
for row in table.select('tr'):
    label = row.select_one('.gsc_rsb_sth')
    cells = row.select('.gsc_rsb_std')
    if not label or not cells:
        continue
    name = re.sub(r'\s+', ' ', label.get_text(' ', strip=True)).lower()
    raw = cells[0].get_text(strip=True).replace(',', '')
    if not raw.isdigit():
        continue
    if name == 'citations': values['citations'] = int(raw)
    elif name == 'h-index': values['h_index'] = int(raw)
    elif name == 'i10-index': values['i10_index'] = int(raw)
if len(values) != 3:
    raise RuntimeError(f'Incomplete Scholar metrics: {list(values)}')
values['updated_at'] = datetime.now(timezone.utc).isoformat()
values['source'] = url
OUT.write_text(json.dumps(values, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Updated Google Scholar statistics:', values)
