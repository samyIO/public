# Merkle Tree API Documentation

## Base URL
```
http://localhost:3000
```

## Endpoints

### Create Tree
Creates a new Merkle tree from a list of transactions.

**Endpoint:** `POST /trees`

**Command:** 
```bash
curl -X POST http://localhost:3000/trees \
  -H "Content-Type: application/json" \
  -d '{
    "transactions": [
      "transaction1",
      "transaction2",
      "transaction3",
      "transaction4"
      ]
    }'
```

**Request Body:**
```json
{
  "transactions": [
    "transaction1",
    "transaction2",
    "transaction3",
    "transaction4"
  ]
}
```

**Response:** `201 Created`
```json
{
  "tree_id": "98b6c5bd-0273-4af2-9c68-4e74b93c1e1f",
  "root_hash": "0cf77e26eb4a27047852cf39e3868c7a69ff1109acb9e799ba422d3ac350fb97",
  "transaction_count": 4,
  "created_at": "2025-02-08T09:31:50.072936751+00:00"
}
```

### Get Tree
Retrieves information about a specific Merkle tree.

**Endpoint:** `GET /trees/{tree_id}`

**Command:** 
```bash
  curl -X GET http://localhost:3000/trees/98b6c5bd-0273-4af2-9c68-4e74b93c1e1f
``` 

**Parameters:**
- `tree_id`: UUID of the tree (from create response)

**Response:** `200 OK`
```json
{
  "tree_id": "98b6c5bd-0273-4af2-9c68-4e74b93c1e1f",
  "root_hash": "0cf77e26eb4a27047852cf39e3868c7a69ff1109acb9e799ba422d3ac350fb97",
  "transaction_count": 4,
  "created_at": "2025-02-08T09:31:50.072936751+00:00"
}
```

### Get Proof
Generates a Merkle proof for a transaction at a specific index.

**Endpoint:** `POST /trees/{tree_id}/proof`

**Command:**
```bash
curl -X POST http://localhost:3000/trees/YOUR_TREE_ID/proof \
  -H "Content-Type: application/json" \
  -d '{"tx_idx": 0}'
```

**Parameters:**
- `tree_id`: UUID of the tree

**Request Body:**
```json
{
  "tx_idx": 0
}
```

**Response:** `200 OK`
```json
[
  ["4beace8bdcf9b5b74630eaee2e7f501180e46025ca89b05e7e041fbe953d817a", false],
  ["882ed7f97314e753d0084ea24c386afd3cbd0fb34b3744bfb81d9d3a925cc6e6", false]
]
```

Each element in the proof array contains:
- A sibling hash (string)
- A boolean indicating if the sibling is on the left (true) or right (false)

### Verify Transaction
Verifies if a transaction is part of the Merkle tree using a proof.

**Endpoint:** `POST /verify`

**Command:**
```bash
curl -X POST http://localhost:3000/verify \
  -H "Content-Type: application/json" \
  -d '{
    "transaction": "transaction1",
    "root_hash": "YOUR_ROOT_HASH",
    "proof": YOUR_PROOF_ARRAY
    }'
```

**Request Body:**
```json
{
  "transaction": "transaction1",
  "root_hash": "0cf77e26eb4a27047852cf39e3868c7a69ff1109acb9e799ba422d3ac350fb97",
  "proof": [
    ["882ed7f97314e753d0084ea24c386afd3cbd0fb34b3744bfb81d9d3a925cc6e6", false],
    ["4beace8bdcf9b5b74630eaee2e7f501180e46025ca89b05e7e041fbe953d817a", false]
  ]
}
```

**Response:** `200 OK`
```json
{
  "is_valid": true,
  "verification_time": "PT0.000123456S"
}
```

## Error Responses

All endpoints may return the following error responses:

### 404 Not Found
```json
{
  "error": "Tree not found"
}
```

### 400 Bad Request
```json
{
  "error": "Invalid transaction index"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error: [error details]"
}
```

## Notes
- Tree IDs are UUIDv4
- The API uses JSON for all request and response bodies
- All endpoints require `Content-Type: application/json` header for POST requests
