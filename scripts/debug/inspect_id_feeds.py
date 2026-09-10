import json

data = json.load(open('scripts/debug/audit_feed_report.json', encoding='utf-8'))
for d in data:
    if d['region'] == 'Indonesia':
        print('--------------------------------------------------')
        print(f"Media: {d['name']} | Feed: {d['url']}")
        print(f"  Entries Count : {d['entries_count']}")
        print(f"  RSS Date Raw  : {d['date_format_sample']}")
        print(f"  RSS Date Norm : {d['date_normalized']}")
        for idx, a in enumerate(d['article_tests'], 1):
            print(f"  Article {idx}   : HTTP {a['http_status']} | Len: {a['text_length']} | Success: {a['success']}")
            print(f"    Meta Date   : {a['meta_date']}")
            print(f"    Link        : {a['link']}")
