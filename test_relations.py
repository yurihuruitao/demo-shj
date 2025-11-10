"""
Test script to verify that relationships are displayed in English
"""
import pandas as pd
from network_generator import get_item_relationships, load_cooccurrence_data

# Load data
df = load_cooccurrence_data()

if df is not None:
    print("✅ Successfully loaded cooccurrence data")
    print(f"Total rows: {len(df)}")
    
    # Check if 'relation' column exists
    if 'relation' in df.columns:
        print("✅ 'relation' column exists")
    else:
        print("❌ 'relation' column does NOT exist")
        print(f"Available columns: {df.columns.tolist()}")
    
    # Test a specific entity
    test_entity = df['名字'].iloc[0]
    print(f"\n🔍 Testing entity: {test_entity}")
    
    rel_data = get_item_relationships(test_entity, df)
    
    if rel_data:
        print(f"✅ Found relationships for {test_entity}")
        print(f"Number of relationships: {len(rel_data['relationships'])}")
        
        # Display first 3 relationships
        for i, rel in enumerate(rel_data['relationships'][:3]):
            print(f"\n  Relationship {i+1}:")
            print(f"    Target: {rel['target']}")
            print(f"    Target (Pinyin): {rel['target_pinyin']}")
            print(f"    Relation: {rel['relation']}")
            
            # Check if relation is in English
            if rel['relation'] in ['Independent', 'exist', 'coexistence', 'reside', 'treat', 'flow', 'juxtaposition', 'roost', 'No']:
                print(f"    ✅ Relation is in English!")
            else:
                print(f"    ⚠️  Relation might be in Chinese: {rel['relation']}")
    else:
        print(f"❌ No relationships found for {test_entity}")
else:
    print("❌ Failed to load cooccurrence data")
