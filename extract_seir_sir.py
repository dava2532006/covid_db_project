"""Extract SEIR/SIR model code from Untitled0.ipynb"""
import json

with open(r"d:\Kuliah\Bia Data\Untitled0.ipynb") as f:
    nb = json.load(f)

print("=" * 80)
print("SEARCHING FOR SEIR/SIR MODELS IN UNTITLED0.ipynb")
print("=" * 80)

found_count = 0

for i, cell in enumerate(nb['cells']):
    cell_type = cell.get('cell_type')
    source = "".join(cell.get("source", []))
    
    # Search for SEIR or SIR mentions
    if 'SEIR' in source.upper() or 'SIR' in source.upper():
        found_count += 1
        print(f"\n[Cell {i}] - {cell_type.upper()}")
        print("-" * 80)
        print(source[:1500])
        print("\n...")

if found_count == 0:
    print("\n❌ NO SEIR/SIR MODEL FOUND IN THIS NOTEBOOK")
    print("\nThis notebook contains only data exploration and visualization.")
    print("No epidemiological modeling (SEIR/SIR) implementation detected.")
else:
    print(f"\n✓ Found {found_count} cells with SEIR/SIR references")
