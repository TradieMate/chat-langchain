"""Web search functionality using Tavily API."""
import os
from typing import List, Optional

from langchain_core.documents import Document
from tavily import TavilyClient


class TavilyWebSearch:
    """Web search using Tavily API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Tavily client.
        
        Args:
            api_key: Tavily API key. If not provided, will use TAVILY_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("Tavily API key is required. Set TAVILY_API_KEY environment variable.")
        
        self.client = TavilyClient(api_key=self.api_key)
    
    def search(
        self, 
        query: str, 
        max_results: int = 5,
        search_depth: str = "advanced",
        include_answer: bool = True,
        include_raw_content: bool = False,
        include_images: bool = False
    ) -> List[Document]:
        """Search the web using Tavily and return results as LangChain Documents.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            search_depth: "basic" or "advanced" search depth
            include_answer: Whether to include AI-generated answer
            include_raw_content: Whether to include raw HTML content
            include_images: Whether to include images in results
            
        Returns:
            List of Document objects with search results
        """
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
                include_images=include_images
            )
            
            documents = []
            
            # Add the AI-generated answer as the first document if available
            if include_answer and response.get("answer"):
                answer_doc = Document(
                    page_content=response["answer"],
                    metadata={
                        "source": "tavily_answer",
                        "title": f"AI Answer for: {query}",
                        "type": "answer",
                        "query": query
                    }
                )
                documents.append(answer_doc)
            
            # Add search results as documents
            for result in response.get("results", []):
                content = result.get("content", "")
                if include_raw_content and result.get("raw_content"):
                    content = result["raw_content"]
                
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": result.get("url", ""),
                        "title": result.get("title", ""),
                        "type": "web_search_result",
                        "query": query,
                        "score": result.get("score", 0.0)
                    }
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            # Return empty list if search fails, with error logged
            print(f"Tavily search failed for query '{query}': {str(e)}")
            return []


def create_web_search_tool() -> TavilyWebSearch:
    """Create a configured Tavily web search tool."""
    return TavilyWebSearch()