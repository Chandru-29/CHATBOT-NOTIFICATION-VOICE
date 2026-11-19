from vectorr_store import collection


print("Collection name:", collection.name)
print("Total documents:", collection.count())

results = collection.get(
    include=["documents", "metadatas"]
)

for i, (doc, metadata) in enumerate(
    zip(results["documents"], results["metadatas"])
):
    if "SS_WAREHOUSE" in doc and "status" in doc.lower():
        print("\n" + "=" * 100)
        print("DOCUMENT:", i)
        print("METADATA:", metadata)
        print("-" * 100)
        print(doc)