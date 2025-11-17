from pymongo import MongoClient
   
uri = "mongodb+srv://imdadshozab_db_user:iuCgDzZJ1n9sKmo7@aitutor.ut0qoxu.mongodb.net/?appName=AiTutor"
client = MongoClient(uri)
   
# Test
db = client['aitutor']
print("Connected:", db.list_collection_names())
