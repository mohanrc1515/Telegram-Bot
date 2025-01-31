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
        self.blocked_col = self.db.blocked  # ✅ Added collection for blocked users

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

    # 📌 Profile-related functions
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

    async def delete_profile(self, user_id):
        """Delete the user's profile from the database."""
        result = await self.profile_col.delete_one({"user_id": user_id})
        if result.deleted_count == 1:
            return True
        return False
    
    # 📌 Join request functions
    async def find_join_req(self, user_id, channel_id):
        """Check if a join request exists for the given user ID and channel ID."""
        return await self.req_col.find_one({'id': user_id, 'channel_id': channel_id}) is not None

    async def add_join_req(self, user_id, channel_id):
        """Add a new join request for the given user ID and channel ID."""
        await self.req_col.insert_one({'id': user_id, 'channel_id': channel_id})

    async def del_join_req(self):
        """Clear all join requests from the database."""
        await self.req_col.drop()

    async def get_db_size(self):
        return (await self.db.command("dbstats"))['dataSize']
        
    # 📌 Blocked users functions
    async def get_blocked_users(self, user_id):
        """Fetch the list of blocked users for a given user."""
        blocked = await self.blocked_col.find_one({"user_id": user_id})
        return blocked.get("blocked_users", []) if blocked else []

    async def block_user(self, user_id, target_id):
        """Block a user."""
        blocked = await self.get_blocked_users(user_id)
        if target_id not in blocked:
            blocked.append(target_id)
            await self.blocked_col.update_one(
                {"user_id": user_id}, {"$set": {"blocked_users": blocked}}, upsert=True
            )

    async def unblock_user(self, user_id, target_id):
        """Unblock a user."""
        blocked = await self.get_blocked_users(user_id)
        if target_id in blocked:
            blocked.remove(target_id)
            await self.blocked_col.update_one(
                {"user_id": user_id}, {"$set": {"blocked_users": blocked}}
            )
            return True
        return False

# ✅ Initialize database with connection URL and database name
db = Database(Config.DB_URL, Config.DB_NAME)
