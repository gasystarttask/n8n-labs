# mcp_eeg_dataset

This MCP tool provides access to EEG adult data stored in MongoDB. It supports:
- `getOne`: Retrieve a single EEG record by its ID.
- `getMany`: Retrieve EEG records in chunks (pagination).
- `find`: Search EEG records containing a keyword.

## Data Model
See the main documentation for the `EegAdultData`, `Step`, and `CoherencesAnalysis` interfaces.

## Usage
Configure MongoDB connection in your environment. Use the provided API to query EEG data for downstream applications.
