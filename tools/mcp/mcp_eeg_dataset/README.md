# mcp_eeg_dataset

A Model Context Protocol (MCP) tool for querying EEG adult data from MongoDB.

## Features
- **getOne**: Retrieve a single EEG record by its ID.
- **getMany**: Retrieve EEG records in chunks (pagination).
- **find**: Search EEG records containing a keyword in relevant fields.

## Data Model
See the TypeScript interfaces for `EegAdultData`, `Step`, and `CoherencesAnalysis` in your documentation.

## Setup
- Configure MongoDB connection using environment variables:
  - `MONGO_URI` (default: `mongodb://localhost:27017`)
  - `EEG_DB_NAME` (default: `eeg_db`)
  - `EEG_COLLECTION_NAME` (default: `eeg_adult_data`)
- Install dependencies with Poetry.

## Usage
Import and use the functions from `mcp_eeg_dataset.tools`.

## Testing
Run tests in the `tests/` directory with pytest.
