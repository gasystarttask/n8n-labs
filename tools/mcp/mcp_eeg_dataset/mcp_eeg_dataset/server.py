import os
from typing import List, Optional, Dict, Any
from pymongo import MongoClient
from bson import ObjectId
def convert_objectid(obj):
    """Recursively convert ObjectId to str in dicts/lists."""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: convert_objectid(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_objectid(i) for i in obj]
    return obj
from mcp_core.base_server import BaseMCPServer

# Data model (for type hints)
class CoherencesAnalysis:
    def __init__(self, downloadURL: str):
        self.downloadURL = downloadURL

class Step:
    def __init__(self, _doc_id: str, **kwargs):
        self._doc_id = _doc_id
        for k, v in kwargs.items():
            setattr(self, k, v)

class EegAdultData:
    def __init__(self, _id: str, processType: str, reporthtmlUrl: str, createdAt, status: str, steps: List[Step]):
        self._id = _id
        self.processType = processType
        self.reporthtmlUrl = reporthtmlUrl
        self.createdAt = createdAt
        self.status = status
        self.steps = steps

class EegDatasetServer(BaseMCPServer):
    def __init__(self, name: str = "mcp_eeg_dataset"):
        super().__init__(name, version="0.1.0", port=8012)
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://user:pass@mongodb:27017")
        self.db_name = os.getenv("EEG_DB_NAME", "eeg_database")
        self.collection_name = os.getenv("EEG_COLLECTION_NAME", "eeg_records")
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        return {
            "getOne": {
                "description": "Get element by id from MongoDB.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "eeg_id": {"type": "string", "description": "EEG record ID"},
                    },
                    "required": ["eeg_id"],
                },
            },
            "getMany": {
                "description": "Get all elements by chunk from MongoDB.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skip": {"type": "integer", "default": 0, "description": "Records to skip"},
                        "limit": {"type": "integer", "default": 20, "description": "Max records to return"},
                    },
                    "required": [],
                },
            },
            "find": {
                "description": "Find all elements containing the keyword.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string", "description": "Keyword to search for"},
                        "skip": {"type": "integer", "default": 0, "description": "Records to skip"},
                        "limit": {"type": "integer", "default": 20, "description": "Max records to return"},
                    },
                    "required": ["keyword"],
                },
            },
        }


    async def getOne(self, eeg_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get element by id from MongoDB."""
        # Try to convert to ObjectId if possible
        query_id = eeg_id
        try:
            query_id = ObjectId(eeg_id)
        except Exception:
            pass
        doc = self.collection.find_one({"_id": query_id})
        return convert_objectid(doc) if doc else None


    async def getMany(self, skip: int = 0, limit: int = 20, **kwargs) -> List[Dict[str, Any]]:
        """Get all elements by chunk from MongoDB."""
        skip = int(skip)
        limit = int(limit)
        docs = list(self.collection.find().skip(skip).limit(limit))
        return convert_objectid(docs)


    async def find(self, keyword: str, skip: int = 0, limit: int = 20, **kwargs) -> List[Dict[str, Any]]:
        """Find all elements containing the keyword in any string field."""
        skip = int(skip)
        limit = int(limit)
        query = {"$or": [
            {"processType": {"$regex": keyword, "$options": "i"}},
            {"status": {"$regex": keyword, "$options": "i"}},
            {"reporthtmlUrl": {"$regex": keyword, "$options": "i"}},
            {"steps.baseRythmeDescription": {"$regex": keyword, "$options": "i"}},
            {"steps.summary": {"$regex": keyword, "$options": "i"}},
            # Add more fields as needed
        ]}
        docs = list(self.collection.find(query).skip(skip).limit(limit))
        return convert_objectid(docs)


def main():
    import argparse
    print("[DEBUG] Entering main()")
    parser = argparse.ArgumentParser(description="MCP EEG Dataset Server")
    parser.add_argument(
        "--mode",
        choices=["http", "stdio"],
        default="http",
        help="Server mode (http or stdio)",
    )
    args = parser.parse_args()
    print(f"[DEBUG] Args: mode={args.mode}")

    print("[DEBUG] Creating EegDatasetServer instance...")
    server = EegDatasetServer()
    print("[DEBUG] Running server.run()...")
    server.run(mode=args.mode)


if __name__ == "__main__":
    main()
