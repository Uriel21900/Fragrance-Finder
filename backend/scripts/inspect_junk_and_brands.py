import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.verify_fragrance_list import FRAGRANCE_LIST
from scripts.audit_and_fix_catalog_50 import CATALOG_50

cat_names = {c["name"].lower(): c for c in CATALOG_50}
print(f"CATALOG_50 has {len(CATALOG_50)} entries.")
print(f"FRAGRANCE_LIST has {len(FRAGRANCE_LIST)} entries.")

missing_in_cat = []
for name, brand in FRAGRANCE_LIST:
    if name.lower() not in cat_names:
        missing_in_cat.append((name, brand))

print(f"\nMissing in CATALOG_50 ({len(missing_in_cat)}):")
for n, b in missing_in_cat:
    print(f"  - {n} by {b}")
