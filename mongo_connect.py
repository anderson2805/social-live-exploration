from pymongo import MongoClient, ASCENDING, ReadPreference,WriteConcern, UpdateOne
from pymongo.errors import OperationFailure
from pymongo.read_concern import ReadConcern
from pydantic import BaseModel, Field
from configparser import ConfigParser
from typing import Literal, TypedDict
from datetime import datetime as dt
import logging
from urllib.parse import quote_plus
import asyncio
import streamlit as st
import os
class EnrichmentUpdate(TypedDict):
    id: int
    sg: str
    mil: str
    rnr: str
    lang: str
    troll: bool
    toxic: bool
    senti: str
    societal_impact: str

# If it's not an absolute path, make it relative to the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.ini')
config = ConfigParser()
try:
    config.read(config_path)
    username = config['MONGODB']['username']
    password = config['MONGODB']['password']
except KeyError: # If the key is not found in the config file
    username = st.secrets["MONGODB"]["username"]
    password = st.secrets["MONGODB"]["password"]


class ChatMessagesHandler:
    def __init__(self, username=username, password=password):
        # MongoDB connection setup
        username = quote_plus(username)
        password = quote_plus(password)
        uri = f"mongodb+srv://{username}:{password}@livechat.tfh1y.mongodb.net/?retryWrites=true&w=majority&appName=livechat"

        self.client = MongoClient(uri)
        self.db = self.client.chat_messages
        
        # Set up basic logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def collection_start_status(self):
        urls = self.db.collection.find({"status": "start"}, {"url": 1, "_id": 0})
        url_list = list(urls)
        return [url["url"] for url in url_list] if url_list else None

    def get_collection(self):
        return list(self.db.collection.find())

    def insert_collection(self, url, platform="YouTube"):
        try:
            result = self.db.collection.update_one(
                {"url": url},
                {"$set": {"platform": platform, "status": "start"}},
                upsert=True
            )
            if result.upserted_id:
                print(f"Inserted URL '{url}' into the collection.")
                return True
            else:
                print(f"Updated status for URL '{url}' to 'start'.")
                return False
        except Exception as e:
            print(f"Database error: {e}")
            return False

    def collection_start_status(self):
        urls = self.db.collection.find({"status": "start"}, {"url": 1, "_id": 0})
        url_list = list(urls)
        return [url["url"] for url in url_list] if url_list else None

    def check_status(self, url):
        read_preference = ReadPreference.PRIMARY
        read_concern = ReadConcern(level='majority')
        
        result = self.db.collection.with_options(
            read_preference=read_preference,
            read_concern=read_concern
        ).find_one(
            {"url": url},
            {"status": 1},
            max_time_ms=1000
        )
        return result["status"] if result else None

    def stop_collection(self, urls):
        write_concern = WriteConcern(w='majority', wtimeout=5000)
        self.db.collection.with_options(
            write_concern=write_concern
        ).update_many(
            {"url": {"$in": urls}},
            {"$set": {"status": "stopped"}},
            upsert=True
        )
        
    def start_collection(self, urls):
        write_concern = WriteConcern(w='majority', wtimeout=5000)
        self.db.collection.with_options(
            write_concern=write_concern
        ).update_many(
            {"url": {"$in": urls}},
            {"$set": {"status": "start"}},
            upsert=True
        )
        
    def get_service_status(self):
        service_doc = self.db.service.find_one()
        return service_doc['status'] if service_doc else None

    def update_service_status(self, status: Literal['start', 'stopped']):
        write_concern = WriteConcern(w='majority', wtimeout=5000)
        self.db.service.with_options(
            write_concern=write_concern
        ).update_one(
            {},
            {"$set": {"status": status}},
            upsert=True
        )
    
    def read_messages_from_db(self, limit=None):
        pipeline = [
            {"$match": {
                "enriched": False,
                "$expr": {"$gt": [{"$strLenCP": "$message"}, 5]}
            }}
        ]
        
        if limit is not None:
            pipeline.append({"$limit": limit})
        
        return list(self.db.messages.aggregate(pipeline))
    
    def read_messages_from_db_enriched(self):
        return list(self.db.messages.find({
            "enriched": True,
            "$expr": {"$gt": [{"$strLenCP": "$message"}, 5]},
            "$or": [
                {"delete": {"$ne": True}},
                {"delete": {"$exists": False}}
            ]
        }))
        
    def get_recent_message_breakdowns(self, limit=30):
        pipeline = [
            {
                "$match": {
                    "enriched": True,
                    "$expr": {"$gt": [{"$strLenCP": "$message"}, 5]},
                    "$or": [
                        {"delete": {"$ne": True}},
                        {"delete": {"$exists": False}}
                    ]
                }
            },
            {
                "$sort": {"dt_stamp": -1}
            },
            {
                "$facet": {
                    "sentiment_pos": [
                        {"$match": {"senti": "Pos"}},
                        {"$limit": limit}
                    ],
                    "sentiment_neg": [
                        {"$match": {"senti": "Neg"}},
                        {"$limit": limit}
                    ],
                    "sg_favor": [
                        {"$match": {"sg": "Favor"}},
                        {"$limit": limit}
                    ],
                    "sg_against": [
                        {"$match": {"sg": "Against"}},
                        {"$limit": limit}
                    ],
                    "military_favor": [
                        {"$match": {"mil": "Favor"}},
                        {"$limit": limit}
                    ],
                    "military_against": [
                        {"$match": {"mil": "Against"}},
                        {"$limit": limit}
                    ],
                    "religion_race_favor": [
                        {"$match": {"rnr": "Favor"}},
                        {"$limit": limit}
                    ],
                    "religion_race_against": [
                        {"$match": {"rnr": "Against"}},
                        {"$limit": limit}
                    ],
                    "societal_impact_favor": [
                        {"$match": {"societal_impact": "Favor"}},
                        {"$limit": limit}
                    ],
                    "societal_impact_against": [
                        {"$match": {"societal_impact": "Against"}},
                        {"$limit": limit}
                    ]
                }
            }
        ]
        
        results = self.db.messages.aggregate(pipeline).next()
        
        # Organize results into a nested dictionary
        breakdowns = {
            "sentiment": {
                "Pos": results["sentiment_pos"],
                "Neg": results["sentiment_neg"]
            },
            "sg": {
                "Favor": results["sg_favor"],
                "Against": results["sg_against"]
            },
            "military": {
                "Favor": results["military_favor"],
                "Against": results["military_against"]
            },
            "religion_race": {
                "Favor": results["religion_race_favor"],
                "Against": results["religion_race_against"]
            },
            "societal_impact": {
                "Favor": results["societal_impact_favor"],
                "Against": results["societal_impact_against"]
            }
        }
        
        return breakdowns

    def read_all_msgs(self, urls):
        video_ids = [url.split('=')[1] for url in urls]
        return list(self.db.messages.find({
            "enriched": True,
            "$expr": {"$gt": [{"$strLenCP": "$message"}, 5]},
            "vid_id": {"$in": video_ids}
        }))

    def delete_collection(self, urls):
        # Extract video_ids from urls
        video_ids = [url.split('=')[1] for url in urls]
        
        # Delete documents from the collection collection
        delete_result = self.db.collection.delete_many({"url": {"$in": urls}})
        
        # Update the "delete" field to True in the messages collection
        update_result = self.db.messages.update_many(
            {"vid_id": {"$in": video_ids}},
            {"$set": {"delete": True}}
        )
        
        return {
            "deleted_count": delete_result.deleted_count,
            "modified_count": update_result.modified_count
        }

    # async def update_msg_enrichment_async(self, id, sg, mil, rnr, lang, troll, toxic, senti):
    #    await self.db.messages.update_one(
    #         {"id": id},
    #         {"$set": {
    #             "sg": sg,
    #             "mil": mil,
    #             "rnr": rnr,
    #             "lang": lang,
    #             "troll": troll,
    #             "toxic": toxic,
    #             "senti": senti,
    #             "enriched": True
    #         }}
    #     )
    
    async def update_msg_enrichment_async(self, id: int, sg: str, mil: str, rnr: str, lang: str, troll: bool, toxic: bool, senti: str, societal_impact: str):
        update_data = {
            "sg": sg,
            "mil": mil,
            "rnr": rnr,
            "lang": lang,
            "troll": troll,
            "toxic": toxic,
            "senti": senti,
            "societal_impact": societal_impact,
            "enriched": True
        }
        
        # Use a separate method for the actual update operation
        return await self._do_update(id, update_data)

    def update_msg_enrichment_many(self, list_of_updates: list[EnrichmentUpdate]):
        bulk_operations = []
        
        for update in list_of_updates:
            update_data = {
                "sg": update['sg'],
                "mil": update['mil'],
                "rnr": update['rnr'],
                "lang": update['lang'],
                "troll": update['troll'],
                "toxic": update['toxic'],
                "senti": update['senti'],
                "societal_impact": update['societal_impact'],
                "enriched": True,
                "dt_enriched": dt.now()
            }
            
            bulk_operations.append(
                UpdateOne(
                    {"id": update['id']},
                    {"$set": update_data},
                    upsert=True
                )
            )
        
        # Perform the bulk write operation
        result = self.db.messages.bulk_write(bulk_operations)
        
        return result

    def create_msg_index(self):
        # Rebuild the counters collection
        if 'counters' in self.db.list_collection_names():
            self.db.counters.drop()
            print("Dropped existing counters collection.")
        
        self.db.create_collection('counters')
        self.db.counters.insert_one({'_id': 'message_id', 'seq': 0})
        print("Recreated counters collection and initialized message_id counter.")
        
        # Rebuild the messages collection
        if 'messages' in self.db.list_collection_names():
            self.db.messages.drop()
            print("Dropped existing messages collection.")
        
        self.db.create_collection('messages')
        print("Recreated messages collection.")

        # Check and delete existing indexes on the messages collection
        existing_indexes = self.db.messages.index_information()
        indexes_to_create = {
            'id_index': [("id", ASCENDING)],
            'enriched_index': [("enriched", ASCENDING)],
            'vid_id_index': [("vid_id", ASCENDING)],
            'msg_id_index': [("msg_id", ASCENDING)],
            'delete_index': [("delete", ASCENDING)]
        }

        for index_name, index_key in indexes_to_create.items():
            if index_name in existing_indexes:
                try:
                    self.db.messages.drop_index(index_name)
                    print(f"Dropped existing index: {index_name}")
                except OperationFailure as e:
                    print(f"Failed to drop index {index_name}: {e}")
            
            try:
                if index_name in ['id_index', 'msg_id_index']:
                    self.db.messages.create_index(index_key, unique=True, name=index_name)
                else:
                    self.db.messages.create_index(index_key, name=index_name)
                print(f"Created index: {index_name}")
            except OperationFailure as e:
                print(f"Failed to create index {index_name}: {e}")

        print("Finished updating messages indexes and rebuilding counters.")
        
    def get_next_sequence_value(self, sequence_name):
        sequence_document = self.db.counters.find_one_and_update(
            {"_id": sequence_name},
            {"$inc": {"seq": 1}},
            return_document=True
        )
        return sequence_document["seq"]
    
    def insert_messages(self, data):
        logging.info(f"Attempting to insert {len(data)} messages into the database.")
        
        try:
            messages_to_insert = []
            for item in data:
                id = self.get_next_sequence_value('message_id')
                messages_to_insert.append({
                    "id": id,
                    "vid_id": item['vid_id'],
                    "author": item['author'],
                    "author_id": item['author_id'],
                    "dt_stamp": item['dt_stamp'],
                    "msg_id": item['msg_id'],   
                    "message": item['message'],
                    "enriched": False
                })
            
            result = self.db.messages.insert_many(messages_to_insert)
            
            inserted_count = len(result.inserted_ids)
            logging.info(f"Successfully inserted {inserted_count} messages into the database.")
            return inserted_count
        
        except Exception as e:
            logging.error(f"An error occurred while inserting messages: {e}")
            return None

    def test_connection(self):
        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def clear_collection(self):
        self.db.collection.delete_many({})
        print("Deleted all documents from collection collection.")
        
    def insert_summaries(self, summaries):
        try:
            result = self.db.summaries.insert_one(summaries)
            print(f"Inserted summaries for {result.inserted_id}.")
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False
        
    async def _do_update(self, id: int, update_data: dict):
        # This method will handle both synchronous and asynchronous contexts
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._sync_update, 
            id, 
            update_data
        )

    def _sync_update(self, id: int, update_data: dict):
        # Synchronous update operation
        return self.db.messages.update_one(
            {"id": id},
            {"$set": update_data}
        )
if __name__ == "__main__":
    
    
    handler = ChatMessagesHandler()
    
    # print(handler.get_service_status())
    
    # Test the MongoDB connection
    handler.test_connection()

    # Clear the collection
    handler.clear_collection()

    # Test the insert_collection function
    # handler.insert_collection("https://www.youtube.com/watch?v=VW61kRjNtBo")
    # handler.insert_collection("https://www.youtube.com/watch?v=Hu4On8l6GXE")
    # handler.insert_collection("https://www.youtube.com/watch?v=GPNVG0DIAGk")
       
    handler.create_msg_index()

    print(handler.read_messages_from_db())
