import logging
import motor.motor_asyncio
from config import Config
from .utils import send_log
from datetime import datetime, timedelta

class Database:

    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.user_col = self.db.user        
        self.req_col = self.db.channels        
        
    
    
    # User handling
    def new_user(self, id):
        return {
            "_id": int(id),
            "file_id": None,
	}

    async def add_user(self, client, message):
        u = message.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            await self.user_col.insert_one(user)
            await send_log(client, u)
        if not await self.metadata_exists(u.id):
            await self.add_metadata(u.id)
      
      
    async def is_user_exist(self, id):
        user = await self.user_col.find_one({'_id': int(id)})
        return bool(user)
        
    async def total_users_count(self):
        return await self.user_col.count_documents({})

    async def get_all_users(self):
        return self.user_col.find({})

    async def delete_user(self, user_id):
        await self.user_col.delete_many({'_id': int(user_id)})



    async def get_total_renamed_size(self):
        result = await self.global_stats_col.find_one({"_id": "total_renamed_size"})
        return result.get("value", 0) if result else 0

    async def update_total_renamed_size(self, size):
        await self.global_stats_col.update_one(
            {"_id": "total_renamed_size"},
            {"$set": {"value": size}},
            upsert=True
	)	
	
    async def set_user_attr(self, id, field, value):
        await self.user_col.update_one({'_id': int(id)}, {'$set': {field: value}})

    async def get_user_attr(self, id, field, default=None):
        user = await self.user_col.find_one({'_id': int(id)})
        return user.get(field, default) if user else default


    # Check if the user has already sent a join request to the specific channel
    async def find_join_req(self, user_id, channel_id):
        """Check if a join request exists for the given user ID and channel ID."""
        return await self.req_col.find_one({'id': user_id, 'channel_id': channel_id}) is not None

    # Add a join request entry to the database with user ID and channel ID
    async def add_join_req(self, user_id, channel_id):
        """Add a new join request for the given user ID and channel ID."""
        await self.req_col.insert_one({'id': user_id, 'channel_id': channel_id})

    # Delete all join requests (clear the collection)
    async def del_join_req(self):
        """Clear all join requests from the database."""
        await self.req_col.drop()

 
    async def get_db_size(self):
        return (await self.db.command("dbstats"))['dataSize']
        
db = Database(Config.DB_URL, Config.DB_NAME)
