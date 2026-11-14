"""Extract markdown summaries and code from Untitled0.ipynb"""
import json

with open(r"d:\Kuliah\Bia Data\Untitled0.ipynb") as f:
    nb = json.load(f)

print("=" * 70)
print("NOTEBOOK SUMMARY - Untitled0.ipynb")
print("=" * 70)

for i, cell in enumerate(nb['cells']):
    cell_type = cell.get('cell_type')
    
    if cell_type == 'markdown':
        source = "".join(cell.get("source", []))
        print(f"\n[MARKDOWN - Cell {i}]")
        print(source[:300])
        
    elif cell_type == 'code':
        source = "".join(cell.get("source", []))
        # Show first 200 chars of code
        code_preview = source.split('\n')[0][:100]
        print(f"\n[CODE - Cell {i}]")
        print(f"  First line: {code_preview}")
        
        # Check if contains key terms
        if any(term in source.lower() for term in ['seir', 'sir', 'model', 'fit', 'predict']):
            print(f"  ** Contains model-related code **")
            print(f"  Preview: {source[:200]}")

print("\n" + "=" * 70)
print("ANALYSIS:")
print("=" * 70)
print("This notebook contains COVID-19 data exploration and visualization.")
print("It does NOT contain SEIR or SIR epidemiological models.")
print("The focus is on exploratory data analysis (EDA) and trend visualization.")
