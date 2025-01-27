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
        self.coupons_col = self.db.coupons
        self.req_col = self.db.channels
        self.media_info_col = self.db.media_info
        self.auth_users_col = self.db.auth_users
        self.referral_col = self.db.referrals
        self.metadata_col = self.db.metadata
        self.file_count_col = self.db.file_counts
        self.global_stats_col = self.db.global_stats
        
    # Metadata handling
    async def metadata_data(self, id):
        return dict(
            _id=int(id),
            title="By @Elites_Bots",
            author="@Elites_Bots",
            artist="@Elites_Bots",
            subtitle="@Elites_Bots",
            audio="@Elites_Bots",
            video="Encoded By @Elites_Bots"
        )

    async def add_metadata(self, id):
        data = await self.metadata_data(id)
        await self.metadata_col.insert_one(data)

              
    async def metadata_exists(self, chat_id):
        meta = await self.metadata_col.find_one({'_id': chat_id})
        return meta is not None        
    
    # User handling
    def new_user(self, id):
        return {
            "_id": int(id),
            "file_id": None,
            "caption": None,
            "format_template": None,
            "media_type": None,
            "dump_files": False,
            "forward_mode": "Normal",
            "dump_channel": None,
            "sequence_queue": [],
            "referral_points": 0,
            "metadata": False,
            "file_count": 0,
            "mode": False  # Default mode is Auto Rename (False)
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

   # Global statistics handling
    async def get_total_files_renamed(self):
        result = await self.global_stats_col.find_one({"_id": "total_files_renamed"})
        return result.get("value", 0) if result else 0

    async def update_total_files_renamed(self, count):
        await self.global_stats_col.update_one(
            {"_id": "total_files_renamed"},
            {"$set": {"value": count}},
            upsert=True
        )

    async def get_total_renamed_size(self):
        result = await self.global_stats_col.find_one({"_id": "total_renamed_size"})
        return result.get("value", 0) if result else 0

    async def update_total_renamed_size(self, size):
        await self.global_stats_col.update_one(
            {"_id": "total_renamed_size"},
            {"$set": {"value": size}},
            upsert=True
	)	
	
	# Generic setter and getter for user attributes
    async def set_user_attr(self, id, field, value):
        await self.user_col.update_one({'_id': int(id)}, {'$set': {field: value}})

    async def get_user_attr(self, id, field, default=None):
        user = await self.user_col.find_one({'_id': int(id)})
        return user.get(field, default) if user else default

    # Coupon management
    async def save_coupon(self, code, duration, expiry_time):
        coupon = {
            'code': code,
            'duration': duration,
            'expiry_time': expiry_time,
            'redeemed': False,
            'redeemed_by': None
        }
        await self.coupons_col.insert_one(coupon)

    async def get_coupon(self, code):
        return await self.coupons_col.find_one({'code': code})

    async def redeem_coupon(self, code, user_id):
        await self.coupons_col.update_one(
            {'code': code},
            {'$set': {'redeemed': True, 'redeemed_by': user_id}}
        )

    # Authorization management
    async def is_user_authorized(self, user_id):
        user = await self.auth_users_col.find_one({"_id": user_id})
        return user and user["expiry_time"] > datetime.utcnow()

    async def authorize_user(self, user_id, expiry_time):
        await self.auth_users_col.update_one(
            {"_id": user_id},
            {"$set": {"expiry_time": expiry_time}},
            upsert=True
        )

    async def unauthorize_user(self, user_id):
        await self.auth_users_col.delete_one({"_id": user_id})

    async def get_all_authorized_users(self):
        return self.auth_users_col.find({})

    async def get_authorization_expiry(self, user_id):
        user = await self.auth_users_col.find_one({"_id": user_id})
        return user.get("expiry_time") if user else None

    # Dump Settings Management
    async def set_dump_files(self, id, dump_files):
        await self.set_user_attr(id, "dump_files", dump_files)

    async def get_dump_files(self, id):
        return await self.get_user_attr(id, "dump_files", False)

    async def set_forward_mode(self, id, forward_mode):
        await self.set_user_attr(id, "forward_mode", forward_mode)

    async def get_forward_mode(self, id):
        return await self.get_user_attr(id, "forward_mode", "Normal")

    async def set_dump_channel(self, id, channel_id):
        await self.set_user_attr(id, "dump_channel", channel_id)

    async def get_dump_channel(self, id):
        return await self.get_user_attr(id, "dump_channel", None)

    # Sequence Queue Management
    async def get_user_sequence_queue(self, user_id):
        user_data = await self.user_col.find_one({"_id": int(user_id)})
        return user_data.get("sequence_queue", [])

    async def add_to_sequence_queue(self, user_id, file_data):
        await self.user_col.update_one({"_id": int(user_id)}, {"$push": {"sequence_queue": file_data}})

    async def clear_user_sequence_queue(self, user_id):
        await self.user_col.update_one({"_id": int(user_id)}, {"$set": {"sequence_queue": []}})

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


    #======================= Metadata Function ========================#
        
    async def set_meta(self, id, bool_meta):
        await self.user_col.update_one({'_id': int(id)}, {'$set': {'metadata': bool_meta}})

    async def get_meta(self, id):
        user = await self.user_col.find_one({'_id': int(id)})
        return user.get('metadata', None)

    async def add_metadata(self, id):
        data = await self.metadata_data(id)
        await self.metadata_col.insert_one(data)
        
    async def metadata_exists(self, chat_id):
        meta = await self.metadata_col.find_one({'_id': chat_id})
        return meta is not None

    async def get_metadata(self, chat_id):
        return await self.metadata_col.find_one({'_id': chat_id})
    
    async def update_metadata(self, chat_id, field, value):
        await self.metadata_col.update_one({'_id': chat_id}, {'$set': {field: value}}, upsert=True)
               

    async def set_format_template(self, id, format_template):
        await self.user_col.update_one({'_id': int(id)}, {'$set': {'format_template': format_template}})

    async def get_format_template(self, id):
        user = await self.user_col.find_one({'_id': int(id)})
        return user.get('format_template', None)

    async def set_media_preference(self, id, media_type):
        await self.user_col.update_one({'_id': int(id)}, {'$set': {'media_type': media_type}})

    async def get_media_preference(self, id):
        user = await self.user_col.find_one({'_id': int(id)})
        return user.get('media_type', None)

    #======================= Thumbnail ========================#
    
    async def set_thumbnail(self, id, file_id):
        await self.user_col.update_one({'_id': int(id)}, {'$set': {'file_id': file_id}})

    async def get_thumbnail(self, id):
        user = await self.user_col.find_one({'_id': int(id)})
        return user.get('file_id', None)
        
    #======================= Caption ========================#    

    async def set_caption(self, id, caption):
        await self.user_col.update_one({'_id': int(id)}, {'$set': {'caption': caption}})

    async def get_caption(self, id):
        user = await self.user_col.find_one({'_id': int(id)})
        return user.get('caption', None)

    async def set_prefix(self, id, prefix):
        await self.col.update_one({'_id': int(id)}, {'$set': {'prefix': prefix}})  
        
    async def get_prefix(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('prefix', None)      
    

    #======================= Suffix ========================#

    async def set_suffix(self, id, suffix):
        await self.col.update_one({'_id': int(id)}, {'$set': {'suffix': suffix}})  
        
    async def get_suffix(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('suffix', None)
	
    async def store_media_info_in_db(self, media_info):
        result = await self.media_info_col.insert_one(media_info)
        return result.inserted_id    
           

    async def update_file_count(self, user_id, count):
        logging.info(f"Updating file count for user {user_id} to {count}")
        await self.file_count_col.update_one(
            {'_id': int(user_id)},
            {'$set': {'file_count': count}},
            upsert=True
        )

    async def get_file_count(self, user_id):
        user = await self.file_count_col.find_one({'_id': int(user_id)}, {'_id': 0, 'file_count': 1})
        file_count = user.get('file_count', 0) if user else 0
        logging.info(f"Retrieved file count for user {user_id}: {file_count}")
        return file_count

    async def get_top_users_by_file_count(self, limit=10):
        top_users = await self.file_count_col.find(
            {},
            {'_id': 1, 'file_count': 1}
        ).sort('file_count', -1).limit(limit).to_list(length=limit)
        logging.info(f"Top users by file count: {top_users}")
        return top_users

# ======================= Referral Functions ======================== #
    async def add_referral(self, referrer_id, user_id):
        referrer = await self.user_col.find_one({'_id': int(referrer_id)})
        if referrer:
            points = referrer.get('referral_points', 0) + 10  # Example increment value
            await self.update_referral_points(referrer_id, points)

            await self.referral_col.update_one(
                {'_id': int(referrer_id)},
                {'$inc': {'referral_count': 1}},
                upsert=True
            )
        else:
            logging.warning(f"Referrer with ID {referrer_id} not found.")

    async def get_referral_points(self, user_id):
        user = await self.user_col.find_one({"_id": user_id})
        return user.get("referral_points", 0) if user else 0

    async def add_referral_points(self, user_id, points=1):
        current_points = await self.get_referral_points(user_id)
        await self.update_referral_points(user_id, current_points + points)

    async def update_referral_points(self, user_id, points):
        if isinstance(points, int):
            try:
                await self.user_col.update_one(
                    {'_id': int(user_id)},
                    {'$set': {'referral_points': points}},
                    upsert=True
                )
            except Exception as e:
                logging.error(f"Error updating referral points: {e}")
        else:
            logging.warning(f"Invalid points value: {points}")

    async def increment_referral_count(self, user_id: int):
        user = await self.referral_col.find_one({"_id": user_id})
        if user:
            await self.referral_col.update_one({"_id": user_id}, {"$inc": {"referral_count": 1}})
        else:
            await self.referral_col.insert_one({"_id": user_id, "referral_count": 1})

    async def get_top_referrers(self, limit=10):
        try:
            top_referrers = await self.referral_col.find(
                {},
                {'_id': 1, 'referral_count': 1}
            ).sort('referral_count', -1).limit(limit).to_list(length=limit)
            logging.info(f"Top referrers: {top_referrers}")
            return top_referrers
        except Exception as e:
            logging.error(f"Error retrieving top referrers: {e}")
            return []

    async def get_referral_count(self, user_id: int):
        user = await self.referral_col.find_one({"_id": user_id})
        return user["referral_count"] if user and "referral_count" in user else 0

    async def get_db_size(self):
        return (await self.db.command("dbstats"))['dataSize']

    async def store_referral(self, referred_user_id, referrer_id):
        referral_data = {
            "_id": referred_user_id,  # referred user ID
            "referrer_id": referrer_id  # referrer ID
        }
        await self.referral_col.insert_one(referral_data)

    # Function to retrieve the referrer of a user
    async def get_referrer(self, user_id):
        referral = await self.referral_col.find_one({"_id": user_id})
        if referral:
            return referral.get("referrer_id")
        return None

    # Save start message
    async def set_start_message(self, user_id, text=None, image_id=None, sticker_id=None):
        update_data = {'start_message': {}}
        if text:
            update_data['start_message']['text'] = text
        if image_id:
            update_data['start_message']['image_id'] = image_id
        if sticker_id:
            update_data['start_message']['sticker_id'] = sticker_id

        await self.user_col.update_one(
            {'_id': user_id},
            {'$set': update_data},
            upsert=True
        )

    # Save end message
    async def set_end_message(self, user_id, text=None, image_id=None, sticker_id=None):
        update_data = {'end_message': {}}
        if text:
            update_data['end_message']['text'] = text
        if image_id:
            update_data['end_message']['image_id'] = image_id
        if sticker_id:
            update_data['end_message']['sticker_id'] = sticker_id

        await self.user_col.update_one(
            {'_id': user_id},
            {'$set': update_data},
            upsert=True
        )

    # Get start message
    async def get_start_message(self, user_id):
        user = await self.user_col.find_one({'_id': user_id})
        return user.get('start_message', None)

    # Get end message
    async def get_end_message(self, user_id):
        user = await self.user_col.find_one({'_id': user_id})
        return user.get('end_message', None)

    # Delete start message
    async def delete_start_message(self, user_id):
        await self.user_col.update_one(
            {'_id': user_id},
            {'$unset': {'start_message': ""}}
        )

    # Delete end message
    async def delete_end_message(self, user_id):
        await self.user_col.update_one(
            {'_id': user_id},
            {'$unset': {'end_message': ""}}
	)
    # User preference handling
    async def get_user_preference(self, user_id):
        user_data = await self.user_col.find_one({'_id': int(user_id)})
        return user_data.get('message_mode', 'season')

    # Function to set user preference in DB
    async def set_user_preference(self, user_id, mode):
        await self.user_col.update_one(
            {'_id': int(user_id)},
            {'$set': {'message_mode': mode}},
            upsert=True
	)
               	    
    # User Dump Batch Management
    async def set_user_dumpbatch(self, id, dump_batch):
        await self.set_user_attr(id, "dump_batch", dump_batch)

    async def get_user_dumpbatch(self, id):
        return await self.get_user_attr(id, "dump_batch", None)

     # Sequence Mode 
    async def is_user_sequence_mode(self, user_id):
        return await self.get_user_attr(user_id, "sequence_mode", False)

    async def set_user_sequence_mode(self, user_id, mode):
        await self.set_user_attr(user_id, "sequence_mode", mode)
    
    async def initialize_sequence_queue(self, user_id):
        await self.set_user_attr(user_id, "sequence_queue", [])

    async def add_to_sequence_queue(self, user_id, file_data):
        await self.user_col.update_one(
            {"_id": int(user_id)},
            {"$push": {"sequence_queue": file_data}}
        )
    
    async def get_sequence_queue(self, user_id):
        return await self.get_user_attr(user_id, "sequence_queue", [])
    
        
    async def clear_sequence_queue(self, user_id):
        await self.set_user_attr(user_id, "sequence_queue", [])
	    
    # Get user preference for caption mode
    async def get_caption_preference(self, user_id):
        user = await self.user_col.find_one({"_id": user_id})
        return user.get("caption_mode", "normal") 

    async def set_caption_preference(self, user_id, mode):
        await self.user_col.update_one(
            {"_id": user_id},
            {"$set": {"caption_mode": mode}},
            upsert=True
	)
	
    # Fetch the user's mode
    async def get_mode(self, user_id):
        user = await self.user_col.find_one({"_id": int(user_id)})
        if user and "mode" in user:
            return user["mode"]
        return False  # Default to Auto Rename if mode is not set

    async def set_mode(self, user_id, mode):
        user = await self.user_col.find_one({"_id": int(user_id)})
        if not user:
            # Create a new user if they don't exist
            new_user = self.new_user(user_id)
            new_user["mode"] = mode
            await self.user_col.insert_one(new_user)
        else:
            # Update the mode for the existing user
            await self.user_col.update_one(
                {"_id": int(user_id)},
                {"$set": {"mode": mode}}
            )
	
    async def get_db_size(self):
        return (await self.db.command("dbstats"))['dataSize']
        
db = Database(Config.DB_URL, Config.DB_NAME)
