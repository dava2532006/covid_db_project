"""Cek isi MongoDB dan statistik"""
import pymongo
from config import MONGO_URI, MONGO_DB

client = pymongo.MongoClient(MONGO_URI)
db = client[MONGO_DB]

print("=" * 60)
print("MONGODB STATUS")
print("=" * 60)

# List semua collections
collections = db.list_collection_names()
print(f"\n✓ Connected to: {MONGO_DB}")
print(f"✓ Collections: {', '.join(collections)}")

# Statistik per collection
for col in collections:
    count = db[col].count_documents({})
    sample = db[col].find_one({})
    print(f"\n[{col}]")
    print(f"  Documents: {count:,}")
    if sample:
        print(f"  Sample keys: {list(sample.keys())}")

print("\n" + "=" * 60)
print("Contoh query dari MongoDB:")
print("=" * 60)

# Top 5 countries by confirmed cases
print("\n[Top 5 Countries by Confirmed Cases]")
docs = list(db.country_summary.find({}, {"country": 1, "confirmed": 1, "_id": 0}).sort("confirmed", -1).limit(5))
for i, doc in enumerate(docs, 1):
    print(f"  {i}. {doc['country']}: {doc['confirmed']:,}")

# Global summary
print("\n[Global Summary (Latest)]")
summary = db.global_daily.find_one({}, sort=[("date", -1)])
if summary:
    print(f"  Date: {summary['date']}")
    print(f"  Confirmed: {summary['confirmed']:,}")
    print(f"  Deaths: {summary['deaths']:,}")
    print(f"  Recovered: {summary['recovered']:,}")

client.close()
print("\n✓ Connection closed")
