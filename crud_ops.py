from motor.motor_asyncio import AsyncIOMotorClient
import json 
from dotenv import load_dotenv
import os

with open("data_examples/episodes.json", "r") as f:
    data = json.load(f)
    episode_data = data["episodes"][0]
    print(f"Loaded {episode_data}")
     

# Setup MongoDB client
load_dotenv()
uri = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(uri)
database = client.get_database("podcrashers")
podcasts = database.get_collection("podcasts")
episode = database.get_collection("episodes") 

# Async database functions
async def insert_episode(episode_data: dict) -> dict:
    " returns the inserted episode data with a default UUID if not provided"
    if not episode_data:
        raise ValueError("Episode data cannot be empty")
    await episode.insert_one(episode_data)
    print(f"Episode {episode_data['uuid']} inserted successfully")

async def get_episode_content(episode_uuid):
    """
    episode_uuid: str
    output: dict or None
    returns the content of an episode by its UUID
    """
    selected_episode = await episode.find_one({"episode_uuid": episode_uuid}, {"_id": 0})
    return selected_episode if selected_episode else None

async def get_podcast_url(podcast_uuid):
    " returns the URL of a podcast by its UUID "
    podcast = await podcasts.find_one({"podcast_uuid": podcast_uuid}, {"_id": 0, "url": 1})
    return podcast.get("url") if podcast else None

async def get_episode_url(episode_uuid):
    """
    episode_uuid: str
    output: str or None
    returns the URL of an episode by its UUID
    """
    selected_episode = await episode.find_one({"episode_uuid": episode_uuid}, {"_id": 0, "url": 1})
    return selected_episode.get("url") if selected_episode else None

async def update_episode(episode_uuid, updated_data):
    """ episode_uuid: str
    updated_data: dict
    updates an episode by its UUID with the provided data
    """    
    if not updated_data:
        raise ValueError("Updated data cannot be empty")
    await episode.update_one({"episode_uuid": episode_uuid}, {"$set": updated_data})

async def delete_episode(episode_uuid):
    """
    episode_uuid: str
    deletes an episode by its UUID
    """
    await episode.delete_one({"episode_uuid": episode_uuid})

async def test_connection():
    try:
        await client.admin.command('ping')
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def close_client():
    client.close()

async def main():
    success = await test_connection()
    print("✅ Connected to MongoDB Atlas" if success else "❌ Failed to connect")
    # await insert_episode(episode_data)
    # await update_episode("test-new-one", {"title": "Breaking News"})
    # await delete_episode("test")
    # episode_content = await get_episode_content("test-new-one")
    # print(f"Episode Content: \n\n\n\n\n {episode_content}")



if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
