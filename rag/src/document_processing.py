from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentProcessor:

    def __init__(self, document_dir):
        self.dir = document_dir

    def load_documents(self):
        # preseve markdown for later chunking by using textloader
        loader = DirectoryLoader(self.dir, loader_cls=TextLoader)
        return loader.load()

    def chunk_documents(self, documents):
        # using level 2 headlines as separator
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2048, chunk_overlap=256
        )
        return text_splitter.split_documents(documents)

    def split_metadata(self, chunks):
        metadata = []
        content = []

        for chunk in chunks:
            metadata.append(chunk.metadata)
            content.append(chunk.page_content)

        return content, metadata
