from qdrant_client import QdrantClient
from document_processing import DocumentProcessor


class VectorDbManager:

    def __init__(self):
        self.client = QdrantClient(url="http://localhost:6333")
        print("client initiated")
        self.collection_name = ""

    def init_qdrant(self, collection_name):
        processor = DocumentProcessor("resources/documents")
        docs = processor.load_documents()
        chunked_docs = processor.chunk_documents(docs)
        content, metadata = processor.split_metadata(chunked_docs)

        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=self.client.get_fastembed_vector_params(),
            )
            print("collection created")
            self.client.add(
                collection_name=collection_name,
                documents=content,
                metadata=metadata,
            )
            print("added documents")

        self.collection_name = collection_name
        print("Initiation successful")

    def retrieve_information(self, search_query):
        # embed search query and search
        search_result = self.client.query(
            collection_name=self.collection_name,
            query_text=search_query,
            query_filter=None,  # If you don't want any filters for now
            limit=7,
        )

        return search_result

    # just for fun could also simple metadata filter from qdrant
    def majority_vote(self, retrieval):
        # Extract all source IDs
        ids = [candidate.metadata["source"] for candidate in retrieval]

        # Count occurrences of each source ID
        id_counts = {}
        for id in ids:
            if id in id_counts:
                id_counts[id] += 1
            else:
                id_counts[id] = 1

        # Find the source ID with the highest count
        max_count = 0
        majority_id = None

        for id, count in id_counts.items():
            if count > max_count:
                max_count = count
                majority_id = id

        # Filter retrieval to only include candidates with the majority ID
        majority_candidates = [
            candidate
            for candidate in retrieval
            if candidate.metadata["source"] == majority_id
        ]

        return majority_candidates
