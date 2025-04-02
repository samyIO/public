use axum::{
    extract::{Path, State},
    Json,
};
use chrono::Utc;
use crate::merklecore::{CreateTreeRequest, CreateTreeResponse, MerkleTree, 
    VerifyTransactionRequest, VerifyTransactionResponse};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use std::time::Instant;

use crate::error::ApiError;
use crate::state::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct GetProofRequest {
    pub tx_idx: usize,
}

pub async fn create_tree(
    State(state): State<AppState>,
    Json(request): Json<CreateTreeRequest>,
) -> Result<Json<CreateTreeResponse>, ApiError> {
    // Create new Merkle tree
    let tree = MerkleTree::new(request.transactions);
    
    // Generate UUID for the tree
    let tree_id = Uuid::new_v4().to_string();
    
    // Get root hash
    let root_hash = tree.get_root()
        .ok_or_else(|| ApiError::InternalError("Failed to get root hash".to_string()))?
        .clone();
    
    // Store tree in state
    state.trees.write().await.insert(tree_id.clone(), tree.clone());
    
    // Create response
    let response = CreateTreeResponse {
        tree_id,
        root_hash,
        transaction_count: tree.nodes[0].len(),
        created_at: Utc::now().to_rfc3339(),
    };
    
    Ok(Json(response))
}

pub async fn get_tree(
    State(state): State<AppState>,
    Path(tree_id): Path<String>,
) -> Result<Json<CreateTreeResponse>, ApiError> {
    // Get tree from state
    let trees = state.trees.read().await;
    let tree = trees.get(&tree_id)
        .ok_or(ApiError::TreeNotFound)?;
    
    // Create response
    let response = CreateTreeResponse {
        tree_id,
        root_hash: tree.get_root()
            .ok_or_else(|| ApiError::InternalError("Failed to get root hash".to_string()))?
            .clone(),
        transaction_count: tree.nodes[0].len(),
        created_at: Utc::now().to_rfc3339(), // Note: In a production system, we'd store the creation time
    };
    
    Ok(Json(response))
}

pub async fn get_proof(
    State(state): State<AppState>,
    Path(tree_id): Path<String>,
    Json(request): Json<GetProofRequest>,
) -> Result<Json<Vec<(String, bool)>>, ApiError> {
    // Get tree from state
    let trees = state.trees.read().await;
    let tree = trees.get(&tree_id)
        .ok_or(ApiError::TreeNotFound)?;
    
    // Check if transaction index is valid
    if request.tx_idx >= tree.nodes[0].len() {
        return Err(ApiError::InternalError("Invalid transaction index".to_string()));
    }
    
    // Get proof and reverse it to match the verification order
    let mut proof = tree.get_proof(request.tx_idx);
    proof.reverse();
    
    Ok(Json(proof))
}

pub async fn verify_transaction(
    Json(request): Json<VerifyTransactionRequest>,
) -> Result<Json<VerifyTransactionResponse>, ApiError> {
    // Record start time
    let start = Instant::now();
    
    // Verify the proof
    let is_valid = MerkleTree::verify_proof(
        &request.transaction,
        &request.proof,
        &request.root_hash,
    );
    
    // Calculate verification time
    let duration = start.elapsed();
    
    // Create response
    let response = VerifyTransactionResponse {
        is_valid,
        verification_time: format!("PT{:.9}S", duration.as_secs_f64()),
    };
    
    Ok(Json(response))
}