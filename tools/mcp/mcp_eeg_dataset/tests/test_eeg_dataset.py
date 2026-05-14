import os
import sys
# Add tools/mcp to sys.path so sibling packages are importable
os.environ["MONGO_URI"] = "mongodb://user:pass@localhost:27017"
os.environ["EEG_DB_NAME"] = "eeg_database"
os.environ["EEG_COLLECTION_NAME"] = "eeg_records"


import pytest
from mcp_eeg_dataset.mcp_eeg_dataset.tools import getEegAdultAnalysis, getMany, find

class TestEegDatasetTools:
    @pytest.mark.asyncio
    async def test_getEegAdultAnalysis(self):
        result = await getEegAdultAnalysis("example_id")
        assert isinstance(result, dict) or result is None
        
    @pytest.mark.asyncio
    async def test_getMany(self):
        result = await getMany(skip=0, limit=2)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_find(self):
        result = await find("keyword", skip=0, limit=2)
        assert isinstance(result, list)