import logging
import motor.motor_asyncio
from config import Config
from .utils import send_log

class Database:

    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.user_col = self.db.user        
        self.req_col = self.db.channels        
        self.profile_col = self.db.profiles

    def new_user(self, id):
        return {
            "_id": int(id),
            "file_id": None,
        }

    async def add_user(self, b, m):
        u = m.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            await self.user_col.insert_one(user)            
            await send_log(b, u)

    async def is_user_exist(self, id):
        user = await self.user_col.find_one({'_id': int(id)})
        return bool(user)

    async def get_all_users(self):
        return self.user_col.find({})

    async def delete_user(self, user_id):
        await self.user_col.delete_many({'_id': int(user_id)})
    
    async def set_user_attr(self, id, field, value):
        await self.user_col.update_one({'_id': int(id)}, {'$set': {field: value}})

    async def get_user_attr(self, id, field, default=None):
        user = await self.user_col.find_one({'_id': int(id)})
        return user.get(field, default) if user else default

    # Profile-related functions
    async def get_profile(self, user_id):
        """Retrieve user profile from database."""
        return await self.profile_col.find_one({"user_id": user_id})

    async def save_profile(self, user_id, profile_data):
        """Save or update user profile in the database."""
        await self.profile_col.update_one(
            {"user_id": user_id}, 
            {"$set": profile_data}, 
            upsert=True
        )

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
        
    async def get_profile_by_id_or_username(self, identifier):
        """Fetch user profile by ID or username."""
        query = "SELECT * FROM profiles WHERE user_id = ? OR username = ?"
        return await self.fetch_one(query, (identifier, identifier))

    async def get_like_count(self, user_id):
        """Get the total number of likes on a profile."""
        query = "SELECT COUNT(*) FROM likes WHERE liked_user_id = ?"
        result = await self.fetch_one(query, (user_id,))
        return result[0] if result else 0

    async def toggle_like(self, liker_id, liked_user_id):
        """Toggle like status for a profile."""
        query_check = "SELECT * FROM likes WHERE liker_id = ? AND liked_user_id = ?"
        existing_like = await self.fetch_one(query_check, (liker_id, liked_user_id))

        if existing_like:
            # Unlike if already liked
            query_remove = "DELETE FROM likes WHERE liker_id = ? AND liked_user_id = ?"
            await self.execute(query_remove, (liker_id, liked_user_id))
            return False  # Unlike action
        else:
            # Like if not already liked
            query_add = "INSERT INTO likes (liker_id, liked_user_id) VALUES (?, ?)"
            await self.execute(query_add, (liker_id, liked_user_id))
            return True  # Like action

db = Database(Config.DB_URL, Config.DB_NAME)
