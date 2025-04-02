use std::sync::Arc;
use tokio::sync::RwLock;
use std::collections::HashMap;
use crate::merklecore::MerkleTree;

#[derive(Clone)]
pub struct AppState {
    pub trees: Arc<RwLock<HashMap<String, MerkleTree>>>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            trees: Arc::new(RwLock::new(HashMap::new())),
        }
    }
}