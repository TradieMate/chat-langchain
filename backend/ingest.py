"""Load html from files, clean up, split, ingest into Supabase."""
import logging
import os
import re
from typing import Optional

from bs4 import BeautifulSoup, SoupStrainer
from langchain.document_loaders import RecursiveUrlLoader, SitemapLoader
from langchain.indexes import SQLRecordManager, index
from langchain.utils.html import PREFIXES_TO_IGNORE_REGEX, SUFFIXES_TO_IGNORE_REGEX
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SupabaseVectorStore
from supabase import create_client

from backend.constants import SUPABASE_EMBEDDINGS_TABLE, SUPABASE_MATCH_FUNCTION
from backend.embeddings import get_embeddings_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def metadata_extractor(
    meta: dict, soup: BeautifulSoup, title_suffix: Optional[str] = None
) -> dict:
    title_element = soup.find("title")
    description_element = soup.find("meta", attrs={"name": "description"})
    html_element = soup.find("html")
    title = title_element.get_text() if title_element else ""
    if title_suffix is not None:
        title += title_suffix

    return {
        "source": meta["loc"],
        "title": title,
        "description": description_element.get("content", "")
        if description_element
        else "",
        "language": html_element.get("lang", "") if html_element else "",
        **meta,
    }


def simple_extractor(html: str | BeautifulSoup) -> str:
    if isinstance(html, str):
        soup = BeautifulSoup(html, "lxml")
    elif isinstance(html, BeautifulSoup):
        soup = html
    else:
        raise ValueError(
            "Input should be either BeautifulSoup object or an HTML string"
        )
    return re.sub(r"\n\n+", "\n\n", soup.text).strip()


def load_custom_docs():
    """Load custom documentation sources.
    
    Replace this function with your own document sources.
    For example, you could load from:
    - Your company's documentation
    - Product manuals
    - Knowledge base articles
    - etc.
    """
    # Example: Return empty list for now, or add your custom document sources
    return []


def ingest_docs():
    # Supabase configuration
    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
    embedding = get_embeddings_model()

    # Create Supabase client (replaces weaviate client)
    client = create_client(supabase_url, supabase_key)

    # Create vector store (replaces Weaviate vectorstore)
    vectorstore = SupabaseVectorStore(
        client=client,
        embedding=embedding,
        table_name=SUPABASE_EMBEDDINGS_TABLE,
        query_name=SUPABASE_MATCH_FUNCTION,
    )

    record_manager = SQLRecordManager(
        "supabase/rag_documents", db_url=RECORD_MANAGER_DB_URL
    )
    record_manager.create_schema()

    docs_from_custom = load_custom_docs()
    logger.info(f"Loaded {len(docs_from_custom)} docs from custom sources")

    docs_transformed = text_splitter.split_documents(docs_from_custom)
    docs_transformed = [
        doc for doc in docs_transformed if len(doc.page_content) > 10
    ]

    # We try to return 'source' and 'title' metadata when querying vector store and
    # Supabase will error at query time if one of the attributes is missing from a
    # retrieved document.
    for doc in docs_transformed:
        if "source" not in doc.metadata:
            doc.metadata["source"] = ""
        if "title" not in doc.metadata:
            doc.metadata["title"] = ""

    indexing_stats = index(
        docs_transformed,
        record_manager,
        vectorstore,
        cleanup="full",
        source_id_key="source",
        force_update=(os.environ.get("FORCE_UPDATE") or "false").lower() == "true",
    )

    logger.info(f"Indexing stats: {indexing_stats}")
    
    # Note: Supabase doesn't have a direct equivalent to Weaviate's collection count
    # You would need to query the table directly if you want to get the count
    logger.info("Documents successfully indexed to Supabase")


if __name__ == "__main__":
    ingest_docs()
