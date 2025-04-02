# Merkle Tree API
Developed in February 2025

## Introduction

Due to the rise of on-chain AI Agents and real world asset tokenization,
I wanted to learn about the core ideas in blockchain technologies.

This project was the part of a deep dive into the core topics.
Blockchain is an innovative and future-proof technology that will
also empower the next generation of AI, in my opinion, especially in fintech.

This implementation provides a Rust-based RESTful API for creating and 
verifying Merkle trees, which are fundamental data structures used in blockchain technologies for ensuring data integrity and efficient verification.

## Key Components

- **MerkleTree**: The core implementation of the Merkle tree data structure
- **AppState**: Manages concurrent access to trees using RwLocks
- **Routes**: Defines the API endpoints and request/response handling
- **Error**: Custom error types and HTTP response formatting

## Why Rust

Rust was chosen for this implementation for several reasons that make it particularly well-suited for blockchain and cryptographic applications:

1. **Memory Safety Without Garbage Collection**: Rust's ownership model prevents common bugs like null pointer dereferencing, buffer overflows, and data races at compile time without requiring a garbage collector, making it ideal for high-integrity systems.

2. **Performance**: Rust offers performance comparable to C and C++ while providing stronger safety guarantees, which is crucial for computationally intensive operations like hashing in blockchain systems.

3. **Concurrency Without Data Races**: Rust's type system and ownership model ensure thread safety and prevent data races, making it easier to build concurrent systems with confidence.

4. **Zero-Cost Abstractions**: Rust allows for high-level programming abstractions without runtime overhead, which is essential for efficient blockchain implementations.

5. **Strong Type System**: The robust type system helps catch many errors at compile time rather than runtime, improving reliability in critical blockchain infrastructure.

6. **Growing Blockchain Ecosystem**: Many modern blockchain projects are implemented in Rust, including Solana and Polkadot.

## Learning Outcomes

Through this project, I've gained practical experience with:
- Blockchain fundamentals and cryptographic verification
- Rust programming language and its ecosystem
- Building RESTful APIs with Axum framework
- Writing comprehensive tests
- Asynchronous programming patterns
- Error handling in web applications

# User Guide

## Overview

Merkle Tree API provides a RESTful service for creating and verifying Merkle trees - a fundamental data structure used in various cryptographic applications including blockchain technology, certificate transparency, and secure data verification.

This service allows you to:
- Create Merkle trees from transaction lists
- Retrieve information about existing trees
- Generate Merkle proofs for transactions
- Verify that a transaction is included in a tree using a proof

## Features

- **Fast and Efficient**: Built with Rust for maximum performance and memory efficiency
- **RESTful API**: Clean, well-structured API endpoints
- **Concurrent Processing**: Leverages Tokio for asynchronous request handling
- **Detailed Error Handling**: Comprehensive error reporting for easier debugging
- **Production-Ready Logging**: Built-in tracing for observability
- **Thread-Safe State Management**: Uses RwLocks for concurrent access to application state

## Requirements

- Rust 1.84.1 or higher
- Cargo package manager

## Installation

After cloning the Project, proceed with the following steps:

1. Build the project:
  ```bash
  cargo build
  ```

2. Run the server:
  ```bash
  cargo run
  ```

The server will start listening on `127.0.0.1:3000` by default.

Note: you can run the implemented unit tests with:
  ```bash
  cargo test
  ```

## Understanding Merkle Trees

A Merkle tree is a hash-based data structure that efficiently verifies the integrity of data. 

### How it Works

1. Each transaction is hashed individually (leaf nodes)
2. Pairs of hashes are combined and hashed again to form parent nodes
3. This process continues until reaching a single hash (the root)
4. To prove a transaction is part of the tree, you only need to provide the "sibling" 
hashes along the path from the transaction to the root

### Benefits

- **Efficient Verification**: Only logarithmic number of hashes needed to verify any transaction
- **Data Integrity**: Any change to any transaction invalidates the root hash
- **Partial Disclosure**: Ability to prove inclusion of a specific transaction without revealing others

## Usage Examples

For detailed API usage examples, please refer to the [api documentation](api-documentation.md).

### Basic Usage

1. Start the server:

  ```bash
  cargo run
  ```

2. Create a new Merkle tree with transactions

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

  get information about your tree:

  ```bash
  curl -X GET http://localhost:3000/trees/YOUR_TREE_ID
  ```    

3. Get a proof for a specific transaction

  ```bash
  curl -X POST http://localhost:3000/trees/YOUR_TREE_ID/proof \
    -H "Content-Type: application/json" \
    -d '{"tx_idx": 0}'
  ```
4. Verify the proof against the root hash

  ```bash
  curl -X POST http://localhost:3000/verify \
    -H "Content-Type: application/json" \
    -d '{
      "transaction": "transaction1",
      "root_hash": "YOUR_ROOT_HASH",
      "proof": YOUR_PROOF_ARRAY
      }'
  ```

## Future Improvements

- Add single transaction endpoint for trees
- Add persistent storage for Merkle trees
- Implement batch verification for multiple transactions
- Add authentication and rate limiting
- Add metrics and monitoring endpoints