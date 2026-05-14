import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pymongo import MongoClient
from bson import ObjectId

from mcp_core.base_server import BaseMCPServer

def convert_objectid(obj):
    """Recursively convert ObjectId to str in dicts/lists."""
    def _convert_dict(d):
        return {k: convert_objectid(v) for k, v in d.items()}

    def _convert_list(l):
        return [convert_objectid(i) for i in l]

    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return _convert_dict(obj)
    if isinstance(obj, list):
        return _convert_list(obj)
    return obj

def map_to_item_data(doc: list[Dict[str, Any]]) -> list['EegItemData']:
    """Map MongoDB document to EegItemData model, handling both '_id' and 'id' keys."""
    def resolve_id(item):
        _id = item.get("_id") or item.get("id")
        return str(_id) if _id is not None else None

    def to_eeg_item(item):
        return EegItemData(
            **{
                "_id": resolve_id(item),
                "createdAt": item.get("createdAt"),
                "status": item.get("status", "")
            }
        )

    return [to_eeg_item(item) for item in doc]

def map_to_eeg_analysis(doc: Dict[str, Any]) -> 'EegAdultAnalysis':
    """Optimized mapping from MongoDB document to EegAdultAnalysis model."""
    def select_step(steps, doc_id_value):
        return next((s for s in steps if s.get("_doc_id") == doc_id_value), steps[0] if steps else {})

    def get_download_url(arr):
        if isinstance(arr, list) and arr and isinstance(arr[0], dict):
            return arr[0].get("downloadURL", "")
        return ""

    _id = doc.get("_id") or doc.get("id")
    steps = doc.get("steps", [{}])
    step = select_step(steps, "eegAdultAnalysis")

    field_map = {
        "rythme_spectral_tendency_analysis_download_url": lambda: get_download_url(step.get("rythmeSpectralTendencyAnalysis", [])),
        "technics": lambda: step.get("technics", ""),
        "map_of_spikes_and_angular_waves_download_url": lambda: get_download_url(step.get("mapOfSpikesAndAngularWaves", [])),
        "base_rythme_description": lambda: step.get("baseRythmeDescription", ""),
        "comparative_analysis_download_url": lambda: get_download_url(step.get("comparativeAnalysis", [])),
        "global_visual_analysis_download_url": lambda: get_download_url(step.get("globalVisualAnalysis", [])),
        "other_anomalies_list": lambda: step.get("otherAnomaliesList", ""),
        "paraxysmal_anomalies_list": lambda: step.get("paraxysmalAnomaliesList", ""),
        "coherences_analysis_download_url": lambda: get_download_url(step.get("coherencesAnalysis", [])),
        "paroxisms_topography_and_morphology_download_url": lambda: get_download_url(step.get("paroxismsTopographyAndMorphology", [])),
    }

    return EegAdultAnalysis(
        **{"_id": str(_id) if _id is not None else None},
        **{field: getter() for field, getter in field_map.items()}
    )

def map_to_eeg_interpretation(doc: Dict[str, Any]) -> 'EegAdultInterpretation':
    """Optimized mapping from MongoDB document to EegAdultInterpretation model."""
    def select_step(steps, doc_id_value):
        return next((s for s in steps if s.get("_doc_id") == doc_id_value), steps[0] if steps else {})

    _id = doc.get("_id") or doc.get("id")
    steps = doc.get("steps", [{}])
    step = select_step(steps, "eegAdultInterpretation")

    field_map = {
        "hpnReactivity": lambda: step.get("hpnReactivity", ""),
        "anomaliesElectrogeneses": lambda: step.get("anomaliesElectrogeneses", ""),
        "select_anomaliesParoxystiques": lambda: step.get("select_anomaliesParoxystiques", ""),
        "baseRythmeDescription": lambda: step.get("baseRythmeDescription", ""),
        "sliReactivity": lambda: step.get("sliReactivity", ""),
        "anomaliesParoxystiques": lambda: step.get("anomaliesParoxystiques", ""),
        "select_baseRythmeDescription": lambda: step.get("select_baseRythmeDescription", ""),
        "clinicalSummary": lambda: step.get("clinicalSummary", ""),
        "select_anomaliesAutres": lambda: step.get("select_anomaliesAutres", ""),
        "select_anomaliesElectrogeneses": lambda: step.get("select_anomaliesElectrogeneses", ""),
        "summary": lambda: step.get("summary", ""),
        "recommendations": lambda: step.get("recommendations", ""),
        "select_summary": lambda: step.get("select_summary", ""),
        "select_sliReactivity": lambda: step.get("select_sliReactivity", ""),
        "baseRythmeDescriptionText": lambda: step.get("baseRythmeDescriptionText", ""),
        "analysisSummary": lambda: step.get("analysisSummary", ""),
        "anomaliesAutres": lambda: step.get("anomaliesAutres", ""),
        "select_hpnReactivity": lambda: step.get("select_hpnReactivity", ""),
        "select_recommendations": lambda: step.get("select_recommendations", ""),
    }

    return EegAdultInterpretation(
        **{"_id": str(_id) if _id is not None else None},
        **{field: getter() for field, getter in field_map.items()}
    )

def map_to_eeg_observation(doc: Dict[str, Any]) -> 'EegAdultObservation':
    """Optimized mapping from MongoDB document to EegAdultObservation model."""
    def select_step(steps, doc_id_value):
        return next((s for s in steps if s.get("_doc_id") == doc_id_value), steps[0] if steps else {})

    _id = doc.get("_id") or doc.get("id")
    steps = doc.get("steps", [{}])
    step = select_step(steps, "eegAdultObservation")

    field_map = {
        "mainSymptoms": lambda: step.get("mainSymptoms", ""),
        "reasonOfPreviousHospitalisation": lambda: step.get("reasonOfPreviousHospitalisation", ""),
        "heartRate": lambda: step.get("heartRate", ""),
        "temperature": lambda: step.get("temperature", ""),
        "lastDrugIntake": lambda: step.get("lastDrugIntake", ""),
        "apparelExamination": lambda: step.get("apparelExamination", ""),
        "accompanyingSymptomsOfFirstEvent": lambda: step.get("accompanyingSymptomsOfFirstEvent", ""),
        "evolutionOfInitialSymptoms": lambda: step.get("evolutionOfInitialSymptoms", ""),
        "precipitatingFactorsOfFirstEvent": lambda: step.get("precipitatingFactorsOfFirstEvent", ""),
        "descriptionOfLastEvent": lambda: step.get("descriptionOfLastEvent", ""),
        "famillialMedicalHistory": lambda: step.get("famillialMedicalHistory", ""),
        "currentWeight": lambda: step.get("currentWeight", ""),
        "lowBloodPressure": lambda: step.get("lowBloodPressure", ""),
        "previousInvestigations": lambda: step.get("previousInvestigations", ""),
        "currentHeight": lambda: step.get("currentHeight", ""),
        "descriptionOfFirstEvent": lambda: step.get("descriptionOfFirstEvent", ""),
        "highBloodPressure": lambda: step.get("highBloodPressure", ""),
        "previousTreatments": lambda: step.get("previousTreatments", ""),
        "medicalHistory": lambda: step.get("medicalHistory", ""),
    }

    return EegAdultObservation(
        **{"_id": str(_id) if _id is not None else None},
        **{field: getter() for field, getter in field_map.items()}
    )

def map_to_eeg_recording(doc: Dict[str, Any]) -> 'EegAdultRecording':
    """Optimized mapping from MongoDB document to EegAdultRecording model."""
    def select_step(steps, doc_id_value):
        return next((s for s in steps if s.get("_doc_id") == doc_id_value), steps[0] if steps else {})

    def get_download_url(arr):
        if isinstance(arr, list) and arr and isinstance(arr[0], dict):
            return arr[0].get("downloadURL", "")
        return ""
    
    _id = doc.get("_id") or doc.get("id")
    steps = doc.get("steps", [{}])
    step = select_step(steps, "eegAdultRecording")

    field_map = {
        "conditions": lambda: step.get("conditions", ""),
        "eegFile": lambda: get_download_url(step.get("eegFile", [])),
        "parameters": lambda: step.get("parameters", ""),
        "fileFormat": lambda: step.get("fileFormat", ""),
        "artefacts": lambda: step.get("artefacts", ""),
    }

    return EegAdultRecording(
        **{"_id": str(_id) if _id is not None else None},
        **{field: getter() for field, getter in field_map.items()}
    )


# Pydantic models for FastAPI serialization
class CoherencesAnalysis(BaseModel):
    downloadURL: str

class Step(BaseModel):
    doc_id: str = Field(..., alias="_doc_id")
    # Add additional fields as needed
    # Example: summary: Optional[str] = None

class EegAdultData(BaseModel):
    id: str = Field(..., alias="_id")
    processType: str
    reporthtmlUrl: str
    createdAt: Any
    status: str
    steps: List[Step]

class EegItemData(BaseModel):
    id: str = Field(..., alias="_id")
    createdAt: Any
    status: str

class EegAdultAnalysis(BaseModel):
    id: str = Field(..., alias="_id")
    rythme_spectral_tendency_analysis_download_url: str
    technics: str
    map_of_spikes_and_angular_waves_download_url: str
    base_rythme_description: str
    comparative_analysis_download_url: str
    global_visual_analysis_download_url: str
    other_anomalies_list: str
    paraxysmal_anomalies_list: str
    coherences_analysis_download_url: str
    paroxisms_topography_and_morphology_download_url: str

class EegAdultInterpretation(BaseModel):
    id: str = Field(..., alias="_id")
    hpnReactivity: str
    anomaliesElectrogeneses: str
    select_anomaliesParoxystiques: str
    baseRythmeDescription: str
    sliReactivity: str
    anomaliesParoxystiques: str
    select_baseRythmeDescription: str
    clinicalSummary: str
    select_anomaliesAutres: str
    select_anomaliesElectrogeneses: str
    summary: str
    recommendations: str
    select_summary: str
    select_sliReactivity: str
    baseRythmeDescriptionText: str
    analysisSummary: str
    anomaliesAutres: str
    select_hpnReactivity: str
    select_recommendations: str

class EegAdultObservation(BaseModel):
    id: str = Field(..., alias="_id")
    mainSymptoms: str
    reasonOfPreviousHospitalisation: str
    heartRate: str
    temperature: str
    lastDrugIntake: str
    apparelExamination: str
    accompanyingSymptomsOfFirstEvent: str
    evolutionOfInitialSymptoms: str
    precipitatingFactorsOfFirstEvent: str
    descriptionOfLastEvent: str
    famillialMedicalHistory: str
    currentWeight: str
    lowBloodPressure: str
    previousInvestigations: str
    currentHeight: str
    descriptionOfFirstEvent: str
    highBloodPressure: str
    previousTreatments: str
    medicalHistory: str

class EegAdultRecording(BaseModel):
    id: str = Field(..., alias="_id")
    conditions: str
    eegFile: str
    parameters: str
    fileFormat: str
    artefacts: str

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
            "getEegAdultAnalysis": {
                "description": "Get analysis element by id from MongoDB.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "eeg_id": {"type": "string", "description": "EEG record ID"},
                    },
                    "required": ["eeg_id"],
                },
            },
            "getEegAdultInterpretation": {
                "description": "Get interpretation element by id from MongoDB.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "eeg_id": {"type": "string", "description": "EEG record ID"},
                    },
                    "required": ["eeg_id"],
                },
            },
            "getEegAdultObservation": {
                "description": "Get observation element by id from MongoDB.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "eeg_id": {"type": "string", "description": "EEG record ID"},
                    },
                    "required": ["eeg_id"],
                },
            },
            "getEegAdultRecording": {
                "description": "Get recording element by id from MongoDB.",
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
            "countEegRecords": {
                "description": "Count total EEG records in MongoDB.",
                "parameters": {
                    "type": "object",
                    "properties": {},
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

    async def getEegAdultAnalysis(self, eeg_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get analysis element by id from MongoDB."""
        # Try to convert to ObjectId if possible
        query_id = eeg_id
        try:
            query_id = ObjectId(eeg_id)
        except Exception:
            pass
        doc = self.collection.find_one({"_id": query_id})
        return map_to_eeg_analysis(doc) if doc else None


    async def getEegAdultInterpretation(self, eeg_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get interpretation element by id from MongoDB."""
        # Try to convert to ObjectId if possible
        query_id = eeg_id
        try:
            query_id = ObjectId(eeg_id)
        except Exception:
            pass
        doc = self.collection.find_one({"_id": query_id})
        return map_to_eeg_interpretation(doc) if doc else None

    async def getEegAdultObservation(self, eeg_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get observation element by id from MongoDB."""
        # Try to convert to ObjectId if possible
        query_id = eeg_id
        try:
            query_id = ObjectId(eeg_id)
        except Exception:
            pass
        doc = self.collection.find_one({"_id": query_id})
        return map_to_eeg_observation(doc) if doc else None

    async def getEegAdultRecording(self, eeg_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get recording element by id from MongoDB."""
        # Try to convert to ObjectId if possible
        query_id = eeg_id
        try:
            query_id = ObjectId(eeg_id)
        except Exception:
            pass
        doc = self.collection.find_one({"_id": query_id})
        return map_to_eeg_recording(doc) if doc else None

    async def countEegRecords(self, **kwargs) -> int:
        """Count total EEG records in MongoDB."""
        count = self.collection.count_documents({})
        return count

    async def getMany(self, skip: int = 0, limit: int = 20, **kwargs) -> List[Dict[str, Any]]:
        """Get all elements by chunk from MongoDB."""
        skip = int(skip)
        limit = int(limit)
        docs = list(self.collection.find().skip(skip).limit(limit))
        return map_to_item_data(docs)


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
        return map_to_item_data(docs)


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
