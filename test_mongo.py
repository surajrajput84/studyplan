from pymongo import MongoClient
from bson import ObjectId

try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
    client.server_info()
    print("✓ MongoDB is connected!")
    
    db = client['study_planner']
    
    # Check collections
    users = db['users'].count_documents({})
    plans = db['plans'].count_documents({})
    
    print(f"✓ Users: {users}")
    print(f"✓ Plans: {plans}")
    
    # List all plans
    if plans > 0:
        print("\nYour plans:")
        for plan in db['plans'].find():
            print(f"  - {plan['title']} (ID: {plan['_id']})")
            print(f"    Weeks: {len(plan.get('weeks', []))}")
            for w in plan.get('weeks', []):
                print(f"      Week {w['week_number']}: {len(w.get('days', []))} days")
    
except Exception as e:
    print(f"✗ MongoDB Error: {e}")
    print("\nMongoDB is not running!")
    print("Install MongoDB from: https://www.mongodb.com/try/download/community")
    print("Or use MongoDB Atlas (cloud): https://www.mongodb.com/cloud/atlas")
