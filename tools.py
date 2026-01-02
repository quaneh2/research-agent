"""
Tool execution implementations for the research agent.

This module provides two implementations:
1. Anthropic's native web_search and web_fetch tools
2. Custom implementations using third-party APIs
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
import config


class ToolExecutor:
    """Base class for tool execution"""

    def execute_search(self, query: str) -> str:
        raise NotImplementedError

    def execute_fetch(self, url: str) -> str:
        raise NotImplementedError


class AnthropicToolExecutor(ToolExecutor):
    """
    Uses Anthropic's native web_search and web_fetch tools.

    Note: These tools are executed by Anthropic's API, but we control
    when they're called from our server-side loop.
    """

    def __init__(self, client):
        self.client = client

    def execute_search(self, query: str) -> str:
        """Execute web search using Anthropic's API"""
        try:
            response = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=2000,
                tools=[
                    {
                        "type": "web_search_20250305",
                        "name": "web_search"
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": f"Search for: {query}"
                    }
                ]
            )

            # Extract search results from response
            result_text = ""
            for block in response.content:
                if block.type == "text":
                    result_text += block.text

            return result_text

        except Exception as e:
            return f"Search error: {str(e)}"

    def execute_fetch(self, url: str) -> str:
        """Execute web fetch using Anthropic's API"""
        try:
            response = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=4000,
                tools=[
                    {
                        "type": "web_fetch_20250305",
                        "name": "web_fetch"
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": f"Fetch content from: {url}"
                    }
                ]
            )

            # Extract fetched content from response
            result_text = ""
            for block in response.content:
                if block.type == "text":
                    result_text += block.text

            return result_text

        except Exception as e:
            return f"Fetch error: {str(e)}"


class CustomToolExecutor(ToolExecutor):
    """
    Custom tool implementations using third-party APIs and libraries.

    This gives you complete control over tool execution without
    relying on Anthropic's implementations.
    """

    def execute_search(self, query: str) -> str:
        """
        Execute web search using Brave Search API.
        Alternative: Use SerpAPI, Google Custom Search, etc.
        """
        if not config.BRAVE_API_KEY:
            return "Error: BRAVE_API_KEY not configured"

        try:
            response = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": config.BRAVE_API_KEY},
                params={
                    "q": query,
                    "count": 10
                },
                timeout=10
            )

            if response.status_code != 200:
                return f"Search API error: {response.status_code}"

            results = response.json()

            # Format results for Claude
            formatted = f"Search results for '{query}':\n\n"

            if 'web' in results and 'results' in results['web']:
                for i, result in enumerate(results['web']['results'][:10], 1):
                    formatted += f"{i}. {result.get('title', 'No title')}\n"
                    formatted += f"   URL: {result.get('url', '')}\n"
                    formatted += f"   {result.get('description', '')}\n\n"
            else:
                formatted += "No results found.\n"

            return formatted

        except Exception as e:
            return f"Search error: {str(e)}"

    def execute_fetch(self, url: str) -> str:
        """
        Fetch and extract content from a webpage.
        Uses requests + BeautifulSoup for parsing.
        """
        try:
            # Fetch the page
            response = requests.get(
                url,
                timeout=10,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Research Bot)'
                }
            )

            if response.status_code != 200:
                return f"HTTP {response.status_code} error fetching {url}"

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()

            # Extract text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            # Truncate if too long (keep first 8000 chars)
            if len(text) > 8000:
                text = text[:8000] + "\n\n[Content truncated...]"

            return f"Content from {url}:\n\n{text}"

        except requests.Timeout:
            return f"Timeout fetching {url}"
        except Exception as e:
            return f"Error fetching {url}: {str(e)}"


def get_tool_executor(client) -> ToolExecutor:
    """
    Factory function to get the appropriate tool executor
    based on configuration.
    """
    if config.TOOL_IMPLEMENTATION == "custom":
        return CustomToolExecutor()
    else:
        return AnthropicToolExecutor(client)
