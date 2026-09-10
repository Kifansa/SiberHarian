import json

data = json.load(open('scripts/debug/audit_feed_report.json', encoding='utf-8'))
for idx, d in enumerate(data[:15], 1):
    if d['region'] == 'Indonesia':
        print(f"[{idx}] {d['name']} | {d['url']}")
        print(f"    Entries: {d['entries_count']} | RawDate: {d['date_format_sample']} | NormDate: {d['date_normalized']}")
