use axum::{
    routing::{get, post},
    Router,
};
use std::net::SocketAddr;
use tower_http::trace::TraceLayer;

mod routes;
mod error;
mod state;
mod merklecore;

use state::AppState;

#[tokio::main]
async fn main() {
    // Initialize tracing
    tracing_subscriber::fmt::init();

    // Create app state
    let state = AppState::new();
    
    // Build our application with a route
    let app = Router::new()
        .route("/trees", post(routes::create_tree))
        .route("/trees/{tree_id}", get(routes::get_tree))
        .route("/verify", post(routes::verify_transaction))
        .route("/trees/{tree_id}/proof", post(routes::get_proof))
        .layer(TraceLayer::new_for_http())
        .with_state(state);

    // Run it
    let addr = SocketAddr::from(([127, 0, 0, 1], 3000));
    tracing::info!("listening on {}", addr);
    // run our app with hyper, listening globally on port 3000
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}