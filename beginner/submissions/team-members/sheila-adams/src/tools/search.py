"""
Web search tool implementations for Tavily and SerpAPI.

This module provides a unified interface for web search across different providers.
Each search result is normalized to a consistent format regardless of the provider.
"""

from typing import List, Dict, Optional, Literal
from dataclasses import dataclass
import sys
sys.path.append('/home/claude/scholarai-beginner')

from src.config import Config


@dataclass
class SearchResult:
    """
    Normalized search result format.
    
    This dataclass ensures consistent data structure regardless of which
    search provider is used. It makes the downstream agents provider-agnostic.
    
    Attributes:
        title: The title of the search result
        url: The URL of the source
        snippet: A brief excerpt or description of the content
        score: Relevance score (0-1, if available)
    """
    title: str
    url: str
    snippet: str
    score: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "score": self.score
        }


class TavilySearch:
    """
    Tavily search provider implementation.
    
    Tavily is designed specifically for AI applications and provides
    high-quality, relevant results optimized for LLM consumption.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Tavily client.
        
        Args:
            api_key: Tavily API key
        """
        try:
            from tavily import TavilyClient
            self.client = TavilyClient(api_key=api_key)
        except ImportError:
            raise ImportError(
                "Tavily not installed. Run: pip install tavily-python"
            )
    
    def search(self, query: str, k: int = 10) -> List[SearchResult]:
        """
        Execute search query using Tavily.
        
        Args:
            query: Search query string
            k: Number of results to return (default: 10)
        
        Returns:
            List of SearchResult objects
        """
        try:
            # Tavily's search method with parameters optimized for research
            response = self.client.search(
                query=query,
                max_results=k,
                search_depth="advanced",  # More thorough search
                include_answer=False,      # We'll synthesize our own
                include_raw_content=False  # Just snippets for now
            )
            
            # Normalize Tavily response to SearchResult format
            results = []
            for item in response.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    score=item.get("score")
                ))
            
            return results
            
        except Exception as e:
            print(f"Error during Tavily search: {e}")
            return []


class SerpAPISearch:
    """
    SerpAPI (Google Search) provider implementation.
    
    SerpAPI provides access to Google search results, which can be
    valuable for finding academic papers, news articles, and general web content.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize SerpAPI client.
        
        Args:
            api_key: SerpAPI key
        """
        self.api_key = api_key
        try:
            from serpapi import GoogleSearch
            self.GoogleSearch = GoogleSearch
        except ImportError:
            raise ImportError(
                "SerpAPI not installed. Run: pip install google-search-results"
            )
    
    def search(self, query: str, k: int = 10) -> List[SearchResult]:
        """
        Execute search query using SerpAPI.
        
        Args:
            query: Search query string
            k: Number of results to return (default: 10)
        
        Returns:
            List of SearchResult objects
        """
        try:
            # Configure SerpAPI search parameters
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": k,  # Number of results
                "engine": "google"
            }
            
            search = self.GoogleSearch(params)
            results_dict = search.get_dict()
            
            # Normalize SerpAPI response to SearchResult format
            results = []
            for item in results_dict.get("organic_results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    score=None  # SerpAPI doesn't provide scores
                ))
            
            return results
            
        except Exception as e:
            print(f"Error during SerpAPI search: {e}")
            return []


class WebSearchTool:
    """
    Unified web search interface.
    
    This class provides a single interface for web search that automatically
    selects the appropriate provider based on available API keys. This makes
    it easy to switch providers or add new ones without changing agent code.
    """
    
    def __init__(
        self, 
        provider: Optional[Literal["tavily", "serpapi"]] = None
    ):
        """
        Initialize web search tool with specified or auto-detected provider.
        
        Args:
            provider: Specific provider to use, or None to auto-detect
        """
        # Determine which provider to use
        if provider is None:
            provider = Config.get_search_provider()
        
        self.provider_name = provider
        
        # Initialize the appropriate provider
        if provider == "tavily":
            if not Config.TAVILY_API_KEY:
                raise ValueError("TAVILY_API_KEY not configured")
            self.provider = TavilySearch(Config.TAVILY_API_KEY)
        elif provider == "serpapi":
            if not Config.SERPAPI_API_KEY:
                raise ValueError("SERPAPI_API_KEY not configured")
            self.provider = SerpAPISearch(Config.SERPAPI_API_KEY)
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        print(f"✓ WebSearchTool initialized with provider: {self.provider_name}")
    
    def search(
        self, 
        query: str, 
        k: int = Config.DEFAULT_SEARCH_RESULTS
    ) -> List[SearchResult]:
        """
        Execute web search.
        
        Args:
            query: Search query string
            k: Number of results to return
        
        Returns:
            List of SearchResult objects
        """
        # Enforce maximum results limit
        k = min(k, Config.MAX_SEARCH_RESULTS)
        
        print(f"🔍 Searching for: '{query}' (requesting {k} results)")
        results = self.provider.search(query, k)
        print(f"✓ Found {len(results)} results")
        
        return results
    
    def search_as_dict(self, query: str, k: int = Config.DEFAULT_SEARCH_RESULTS) -> List[Dict]:
        """
        Execute search and return results as dictionaries.
        
        This is useful for passing to agents that expect dict format.
        
        Args:
            query: Search query string
            k: Number of results to return
        
        Returns:
            List of result dictionaries
        """
        results = self.search(query, k)
        return [r.to_dict() for r in results]


# Factory function for easy instantiation
def create_search_tool(provider: Optional[str] = None) -> WebSearchTool:
    """
    Factory function to create a WebSearchTool instance.
    
    Args:
        provider: Optional provider name ('tavily' or 'serpapi')
    
    Returns:
        Configured WebSearchTool instance
    """
    return WebSearchTool(provider=provider)


if __name__ == "__main__":
    # Simple test when run directly
    print("Testing WebSearchTool...")
    
    try:
        tool = create_search_tool()
        results = tool.search("artificial intelligence in healthcare", k=3)
        
        print(f"\nFound {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Snippet: {result.snippet[:100]}...")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
