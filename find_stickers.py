import json
import os
import glob
import sys

# Load loc_ru.json
with open('loc_ru.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

strings = data.get('namespaces', {}).get('', {})
stickers = set()
for v in strings.values():
    if isinstance(v, str) and ('наклейка' in v.lower() or 'флаг' in v.lower()):
        stickers.add(v)

with open('found_stickers.txt', 'w', encoding='utf-8') as f:
    for s in sorted(list(stickers)):
        f.write(s + '\n')

print("Done. Saved to found_stickers.txt")
