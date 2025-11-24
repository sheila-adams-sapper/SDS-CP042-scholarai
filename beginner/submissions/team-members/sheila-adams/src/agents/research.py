"""
Research Agent for gathering and curating web sources.

This agent uses OpenAI's function calling capability to intelligently
search the web and curate the most relevant sources for a given research topic.
"""

import json
from typing import List, Dict, Optional
from openai import OpenAI
import sys
sys.path.append('/home/claude/scholarai-beginner')

from src.config import Config
from src.tools.search import WebSearchTool, SearchResult


class ResearchAgent:
    """
    Research Agent that orchestrates web search for academic/research queries.
    
    This agent acts as an intelligent research assistant that:
    1. Analyzes the user's research question
    2. Formulates optimal search queries
    3. Executes searches using the WebSearchTool
    4. Curates and ranks results by relevance
    5. Returns the most valuable sources
    
    The agent uses OpenAI's function calling to decide when and how to search.
    """
    
    def __init__(
        self,
        model: str = Config.RESEARCH_MODEL,
        search_tool: Optional[WebSearchTool] = None
    ):
        """
        Initialize the Research Agent.
        
        Args:
            model: OpenAI model to use (default from config)
            search_tool: Optional pre-configured search tool
        """
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = model
        self.search_tool = search_tool or WebSearchTool()
        
        # Define the function schema for OpenAI function calling
        # This tells the model what tools are available and how to use them
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": (
                        "Search the web for information on a given topic. "
                        "Returns a list of relevant sources with titles, URLs, and snippets. "
                        "Use this to find research papers, articles, and authoritative sources."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": (
                                    "The search query. Be specific and include key terms. "
                                    "For academic research, include relevant field terminology."
                                )
                            },
                            "k": {
                                "type": "integer",
                                "description": "Number of results to return (1-20)",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        print(f"✓ ResearchAgent initialized with model: {self.model}")
    
    def _execute_tool_call(self, tool_call) -> str:
        """
        Execute a tool call requested by the model.
        
        Args:
            tool_call: The tool call object from OpenAI response
        
        Returns:
            JSON string of search results
        """
        function_name = tool_call.function.name
        
        if function_name == "web_search":
            # Parse the arguments
            arguments = json.loads(tool_call.function.arguments)
            query = arguments.get("query")
            k = arguments.get("k", 10)
            
            # Execute the search
            results = self.search_tool.search(query, k)
            
            # Convert to dict format for the model
            results_dict = [r.to_dict() for r in results]
            
            return json.dumps(results_dict, indent=2)
        else:
            return json.dumps({"error": f"Unknown function: {function_name}"})
    
    def research(
        self,
        topic: str,
        num_results: int = 10,
        style: str = "academic"
    ) -> Dict:
        """
        Conduct research on a given topic.
        
        This is the main entry point for the Research Agent. It takes a research
        topic and returns curated sources with analysis.
        
        Args:
            topic: The research question or topic
            num_results: Number of sources to return
            style: Research style ('academic', 'general', 'technical')
        
        Returns:
            Dictionary containing:
                - query: Original topic
                - sources: List of curated SearchResult dictionaries
                - reasoning: Agent's explanation of source selection
        """
        print(f"\n{'='*60}")
        print(f"🔬 Research Agent: Starting research on '{topic}'")
        print(f"{'='*60}\n")
        
        # Craft the system prompt based on style
        style_prompts = {
            "academic": (
                "You are an academic research assistant. Prioritize peer-reviewed "
                "sources, scientific publications, and authoritative academic content."
            ),
            "general": (
                "You are a general research assistant. Find reliable and accessible "
                "sources suitable for a general audience."
            ),
            "technical": (
                "You are a technical research assistant. Prioritize technical "
                "documentation, specifications, and expert technical resources."
            )
        }
        
        system_prompt = style_prompts.get(style, style_prompts["general"])
        system_prompt += (
            "\n\nYour task is to search for and curate high-quality sources. "
            "You have access to a web_search function. Use it strategically:\n"
            "1. Formulate 1-3 well-crafted search queries\n"
            "2. Analyze and rank the results\n"
            "3. Return the most relevant and authoritative sources\n\n"
            f"Target: {num_results} high-quality sources"
        )
        
        # Initial user message
        user_message = (
            f"Research topic: {topic}\n\n"
            f"Please search for and identify the {num_results} most relevant "
            "and authoritative sources on this topic. After searching, provide "
            "your analysis of why these sources are valuable."
        )
        
        # Start the conversation
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Conversation loop for function calling
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        all_sources = []
        
        while iteration < max_iterations:
            iteration += 1
            print(f"🤖 Agent iteration {iteration}...")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"  # Let model decide when to use tools
            )
            
            response_message = response.choices[0].message
            
            # Check if the model wants to call a function
            if response_message.tool_calls:
                # Add assistant's response to conversation
                messages.append(response_message)
                
                # Execute each tool call
                for tool_call in response_message.tool_calls:
                    print(f"   📞 Calling: {tool_call.function.name}")
                    print(f"   📋 Args: {tool_call.function.arguments}")
                    
                    # Execute the function
                    function_response = self._execute_tool_call(tool_call)
                    
                    # Add function response to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": function_response
                    })
                    
                    # Collect sources
                    try:
                        sources = json.loads(function_response)
                        if isinstance(sources, list):
                            all_sources.extend(sources)
                    except:
                        pass
            else:
                # Model is done with function calls, has final response
                final_response = response_message.content
                print(f"\n✓ Research complete!")
                print(f"   Found {len(all_sources)} total sources")
                
                # Deduplicate sources by URL
                seen_urls = set()
                unique_sources = []
                for source in all_sources:
                    if source['url'] not in seen_urls:
                        seen_urls.add(source['url'])
                        unique_sources.append(source)
                
                # Limit to requested number
                curated_sources = unique_sources[:num_results]
                
                return {
                    "query": topic,
                    "sources": curated_sources,
                    "reasoning": final_response,
                    "total_sources_found": len(all_sources),
                    "sources_returned": len(curated_sources)
                }
        
        # If we hit max iterations
        print("⚠️  Warning: Max iterations reached")
        return {
            "query": topic,
            "sources": all_sources[:num_results],
            "reasoning": "Research completed with maximum iterations.",
            "total_sources_found": len(all_sources),
            "sources_returned": min(len(all_sources), num_results)
        }
    
    def quick_search(self, query: str, k: int = 10) -> List[Dict]:
        """
        Perform a direct search without agent reasoning.
        
        This is a simpler alternative that bypasses the agent's analysis
        and directly returns raw search results. Useful for testing or
        when you don't need curation.
        
        Args:
            query: Search query
            k: Number of results
        
        Returns:
            List of search result dictionaries
        """
        print(f"🔍 Quick search: '{query}'")
        results = self.search_tool.search(query, k)
        return [r.to_dict() for r in results]


if __name__ == "__main__":
    # Test the Research Agent
    print("Testing ResearchAgent...")
    
    try:
        agent = ResearchAgent()
        
        # Test research method
        result = agent.research(
            topic="CRISPR gene editing applications in medicine",
            num_results=5,
            style="academic"
        )
        
        print("\n" + "="*60)
        print("RESEARCH RESULTS")
        print("="*60)
        print(f"\nTopic: {result['query']}")
        print(f"Sources found: {result['sources_returned']}")
        print(f"\nAgent reasoning:\n{result['reasoning']}")
        print(f"\nTop sources:")
        for i, source in enumerate(result['sources'][:3], 1):
            print(f"\n{i}. {source['title']}")
            print(f"   {source['url']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
