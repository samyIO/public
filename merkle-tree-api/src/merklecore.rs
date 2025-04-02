use sha2::{Sha256, Digest};
use serde::{Serialize, Deserialize};
use std::fmt::Debug;
use std::clone::Clone;

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateTreeRequest {
    pub transactions: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateTreeResponse {
    pub tree_id: String,
    pub root_hash: String,
    pub transaction_count: usize,
    pub created_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct VerifyTransactionRequest {
    pub transaction: String,
    pub root_hash: String,
    pub proof: Vec<(String, bool)>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct VerifyTransactionResponse {
    pub is_valid: bool,
    pub verification_time: String,
}

#[derive(Debug, Clone)] 
pub struct MerkleTree {
    pub nodes: Vec<Vec<String>>, // Stores hashes at each level
}

impl MerkleTree {
    pub fn verify_proof(tx: &str, proof: &[(String, bool)], root: &str) -> bool {
        // First hash the transaction
        let mut current_hash = {
            let mut hasher = Sha256::new();
            hasher.update(tx.as_bytes());
            format!("{:x}", hasher.finalize())
        };
        // Process each proof element
        for (sibling_hash, is_left) in proof {
            let mut hasher = Sha256::new();
            if *is_left {
                // Sibling is on the left, so concatenate sibling+current
                hasher.update(format!("{}{}", sibling_hash, current_hash).as_bytes());
            } else {
                // Sibling is on the right, so concatenate current+sibling
                hasher.update(format!("{}{}", current_hash, sibling_hash).as_bytes());
            }
            current_hash = format!("{:x}", hasher.finalize());
        }
        
        // Compare final hash with root
        current_hash == root
    }

    pub fn new(transactions: Vec<String>) -> Self {
        let mut tree = MerkleTree { nodes: Vec::new() };
        
        // Handle empty input case
        if transactions.is_empty() {
            return tree;
        }

        // Create leaf nodes from transactions
        let mut current_level = transactions.iter()
            .map(|tx| {
                let mut hasher = Sha256::new();
                hasher.update(tx.as_bytes());
                format!("{:x}", hasher.finalize())
            })
            .collect::<Vec<String>>();

        // Add leaf level to tree
        tree.nodes.push(current_level.clone());

        // Build tree upwards until we reach root
        while current_level.len() > 1 {
            let mut next_level = Vec::new();
            
            // Process pairs of nodes
            for i in (0..current_level.len()).step_by(2) {
                let left = &current_level[i];
                let right = if i + 1 < current_level.len() {
                    &current_level[i + 1]
                } else {
                    // If we have an odd number of nodes, duplicate the last one
                    left
                };
                
                // Hash the pair
                let mut hasher = Sha256::new();
                hasher.update(format!("{}{}", left, right).as_bytes());
                next_level.push(format!("{:x}", hasher.finalize()));
            }
            
            // Add this level to the tree
            tree.nodes.push(next_level.clone());
            current_level = next_level;
        }

        if tree.nodes.len() == 1 {
            tree.nodes.push(tree.nodes[0].clone());
        }
        
        tree
    }

    pub fn get_root(&self) -> Option<&String> {
        self.nodes.last()?.first()
    }

    pub fn get_proof(&self, tx_idx: usize) -> Vec<(String, bool)> {
        let mut proof = Vec::new();
        let mut current_idx = tx_idx;

        // Go up through each level
        for level in 0..self.nodes.len() - 1 {
            let is_left = current_idx % 2 == 1;
            let sibling_idx = if is_left { 
                current_idx - 1  // Get left sibling
            } else { 
                current_idx + 1  // Get right sibling
            };
            
            if let Some(sibling) = self.nodes[level].get(sibling_idx) {
                proof.push((sibling.clone(), is_left));
            }
            current_idx /= 2;
        }
        proof.reverse();
        proof
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_tree_request() {
        let request = CreateTreeRequest {
            transactions: vec!["transaction1".to_string(), "transaction2".to_string()]
        };
        let tree = MerkleTree::new(request.transactions.clone());
        assert_eq!(tree.nodes[0].len(), 2);
    }

    #[test]
    fn test_verify_transaction_request() {
        let transactions = vec!["transaction1".to_string(), "transaction2".to_string()];
        let tree = MerkleTree::new(transactions.clone());
        let root_hash = tree.get_root().unwrap().clone();
        let proof = tree.get_proof(0);

        let request = VerifyTransactionRequest {
            transaction: transactions[0].clone(),
            root_hash: root_hash.clone(),
            proof: proof.clone(),
        };

        let is_valid = MerkleTree::verify_proof(
            &request.transaction,
            &request.proof,
            &request.root_hash
        );
        assert!(is_valid);
    }

    #[test]
    fn test_new_tree_single_transaction() {
        let transactions = vec!["transaction1".to_string()];
        let tree = MerkleTree::new(transactions);
        
        // Debug prints
        println!("Number of levels: {}", tree.nodes.len());
        for (i, level) in tree.nodes.iter().enumerate() {
            println!("Level {} length: {}", i, level.len());
            println!("Level {} nodes: {:?}", i, level);
        }
        
        // Original assertions
        assert_eq!(tree.nodes.len(), 2, "Should have exactly two levels");
        assert_eq!(tree.nodes[0].len(), 1, "Leaf level should have 1 node");
        assert_eq!(tree.nodes[1].len(), 1, "Root level should have 1 node");
        assert_eq!(tree.nodes[0][0], tree.nodes[1][0], "Root should equal leaf for single transaction");
    }

    #[test]
    fn test_new_tree_even_transactions() {
        let transactions = vec![
            "transaction1".to_string(),
            "transaction2".to_string(),
            "transaction3".to_string(),
            "transaction4".to_string(),
        ];
        let tree = MerkleTree::new(transactions);
        
        // Should have 3 levels: leaves (4 nodes), intermediate (2 nodes), root (1 node)
        assert_eq!(tree.nodes.len(), 3);
        assert_eq!(tree.nodes[0].len(), 4); // leaves
        assert_eq!(tree.nodes[1].len(), 2); // intermediate
        assert_eq!(tree.nodes[2].len(), 1); // root
    }

    #[test]
    fn test_new_tree_odd_transactions() {
        let transactions = vec![
            "transaction1".to_string(),
            "transaction2".to_string(),
            "transaction3".to_string(),
        ];
        let tree = MerkleTree::new(transactions);
        
        // Should have 3 levels, with the last transaction duplicated
        assert_eq!(tree.nodes.len(), 3);
        assert_eq!(tree.nodes[0].len(), 3); // leaves
        assert_eq!(tree.nodes[1].len(), 2); // intermediate
        assert_eq!(tree.nodes[2].len(), 1); // root
    }

    #[test]
    fn test_get_root() {
        let transactions = vec!["transaction1".to_string(), "transaction2".to_string()];
        let tree = MerkleTree::new(transactions);
        
        assert!(tree.get_root().is_some());
        
        // Verify that the root is actually a hash of its children
        let left = &tree.nodes[0][0];
        let right = &tree.nodes[0][1];
        let mut hasher = Sha256::new();
        hasher.update(format!("{}{}", left, right).as_bytes());
        let expected_root = format!("{:x}", hasher.finalize());
        
        assert_eq!(tree.get_root().unwrap(), &expected_root);
    }

    #[test]
    fn test_get_proof() {
        let transactions = vec![
            "transaction1".to_string(),
            "transaction2".to_string(),
            "transaction3".to_string(),
            "transaction4".to_string(),
        ];
        let tree = MerkleTree::new(transactions.clone());
        
        // Get proof for the first transaction
        let mut proof = tree.get_proof(0);
        proof.reverse();
        // For a balanced tree with 4 leaves, proof should have 2 elements
        assert_eq!(proof.len(), 2);
        
        // Verify the proof
        assert!(MerkleTree::verify_proof(
            &transactions[0],
            &proof,
            tree.get_root().unwrap()
        ));

            // Add additional test cases to verify other indices
        for i in 0..transactions.len() {
            let mut proof = tree.get_proof(i);
            proof.reverse();
            assert!(MerkleTree::verify_proof(
                &transactions[i],
                &proof,
                tree.get_root().unwrap()
            ));
        }
    }

    #[test]
    fn test_verify_proof() {
        let transactions = vec![
            "transaction1".to_string(),
            "transaction2".to_string(),
            "transaction3".to_string(),
            "transaction4".to_string(),
        ];
        let tree = MerkleTree::new(transactions.clone());
        
        // Test verification for each transaction
        for (idx, tx) in transactions.iter().enumerate() {
            let mut proof = tree.get_proof(idx);
            proof.reverse();
            assert!(MerkleTree::verify_proof(
                tx,
                &proof,
                tree.get_root().unwrap()
            ));
        }
        
        // Test invalid proof
        let invalid_proof = vec![
            ("invalid_hash".to_string(), false),
            ("another_invalid_hash".to_string(), true),
        ];
        assert!(!MerkleTree::verify_proof(
            &transactions[0],
            &invalid_proof,
            tree.get_root().unwrap()
        ));
    }

    #[test]
    fn test_proof_with_modified_transaction() {
        let transactions = vec![
            "transaction1".to_string(),
            "transaction2".to_string(),
        ];
        let tree = MerkleTree::new(transactions);
        
        let proof = tree.get_proof(0);
        
        // Verify that a modified transaction fails
        assert!(!MerkleTree::verify_proof(
            "modified_transaction1",
            &proof,
            tree.get_root().unwrap()
        ));
    }
}