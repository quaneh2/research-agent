"""
Research Agent with server-side agentic loop.

This module implements the core agentic behavior with explicit
server-side control over each step of the research process.
"""

from anthropic import Anthropic
import config
from tools import get_tool_executor
from typing import Dict, List, Callable, Optional


# System prompt that guides Claude's behavior
SYSTEM_PROMPT = """You are a research assistant helping to gather information step by step.

You will be called multiple times as part of a research process. Each time you're called, you should:

1. Analyze the current conversation state and any tool results you've received
2. Decide what to do next:
   - Use web_search to find information on a topic
   - Use web_fetch to read content from a specific URL
   - Provide a final answer if you have sufficient information

IMPORTANT RULES:
- You can only use ONE tool per response (either web_search OR web_fetch)
- After using a tool, you'll be called again with the results
- Think step-by-step and explain your reasoning
- When you have enough information to answer the question thoroughly, provide your final answer WITHOUT using any tools
- Cite sources in your final answer with URLs

Your goal is to provide accurate, well-researched answers based on the most relevant and recent information available."""


class ResearchAgent:
    """
    Research agent with server-side agentic loop control.

    The server orchestrates:
    - When to call Claude
    - When to execute tools
    - When to stop the loop
    - What information to pass between iterations

    Claude decides:
    - Which tool to use (if any)
    - What query/URL to use
    - When it has enough information
    - How to synthesize the final answer
    """

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.tool_executor = get_tool_executor(self.client)

    def research(
        self,
        question: str,
        stream_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Execute the research process with server-side loop control.

        Args:
            question: The research question to answer
            stream_callback: Optional callback function for streaming updates
                            Called with dict: {"type": str, "content": any}

        Returns:
            Dict with keys:
                - answer: Final answer text
                - sources: List of source URLs used
                - steps: List of all steps taken
                - iterations: Number of iterations used
                - success: Boolean indicating completion
        """

        # Initialize conversation
        messages = [
            {"role": "user", "content": question}
        ]

        # Track progress
        steps = []
        sources = []

        # Server-controlled agentic loop
        for iteration in range(config.MAX_ITERATIONS):

            # STEP 1: Call Claude with current conversation state
            try:
                response = self.client.messages.create(
                    model=config.CLAUDE_MODEL,
                    max_tokens=config.MAX_TOKENS,
                    system=SYSTEM_PROMPT,
                    tools=self._get_tool_definitions(),
                    messages=messages
                )
            except Exception as e:
                return {
                    "answer": f"Error calling Claude: {str(e)}",
                    "sources": sources,
                    "steps": steps,
                    "iterations": iteration,
                    "success": False,
                    "error": str(e)
                }

            # STEP 2: Process Claude's response
            text_content = ""
            tool_uses = []

            for block in response.content:
                if block.type == "text":
                    text_content += block.text

                    # Stream thinking to frontend
                    if stream_callback:
                        stream_callback({
                            "type": "thinking",
                            "content": block.text
                        })

                    steps.append({
                        "type": "thinking",
                        "content": block.text,
                        "iteration": iteration + 1
                    })

                elif block.type == "tool_use":
                    tool_uses.append(block)

            # STEP 3: Check if Claude is done (no tools requested)
            if not tool_uses:
                # Claude provided final answer
                return {
                    "answer": text_content,
                    "sources": sources,
                    "steps": steps,
                    "iterations": iteration + 1,
                    "success": True
                }

            # STEP 4: Execute tools on server

            # Add Claude's response to conversation
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Execute each tool Claude requested
            tool_results = []

            for tool_use in tool_uses:
                tool_name = tool_use.name
                tool_input = tool_use.input
                tool_use_id = tool_use.id

                # Log tool use
                if stream_callback:
                    stream_callback({
                        "type": "tool_use",
                        "tool": tool_name,
                        "input": tool_input
                    })

                steps.append({
                    "type": "tool_use",
                    "tool": tool_name,
                    "input": tool_input,
                    "iteration": iteration + 1
                })

                # EXECUTE TOOL (on our server)
                try:
                    if tool_name == "web_search":
                        result = self.tool_executor.execute_search(
                            tool_input["query"]
                        )

                    elif tool_name == "web_fetch":
                        url = tool_input["url"]
                        result = self.tool_executor.execute_fetch(url)

                        # Track source
                        if url not in [s.get("url") for s in sources]:
                            sources.append({"url": url})

                    else:
                        result = f"Unknown tool: {tool_name}"

                except Exception as e:
                    result = f"Error executing {tool_name}: {str(e)}"

                # Log tool result
                result_summary = f"Retrieved {len(result)} characters"

                if stream_callback:
                    stream_callback({
                        "type": "tool_result",
                        "tool": tool_name,
                        "summary": result_summary
                    })

                steps.append({
                    "type": "tool_result",
                    "tool": tool_name,
                    "summary": result_summary,
                    "iteration": iteration + 1
                })

                # Format tool result for Claude
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": result
                })

            # STEP 5: Add tool results to conversation
            messages.append({
                "role": "user",
                "content": tool_results
            })

            # Loop continues - call Claude again with tool results

        # Max iterations reached without completion
        return {
            "answer": text_content or "Research incomplete - maximum iterations reached without final answer.",
            "sources": sources,
            "steps": steps,
            "iterations": config.MAX_ITERATIONS,
            "success": False,
            "error": "Maximum iterations reached"
        }

    def _get_tool_definitions(self) -> List[Dict]:
        """
        Define the tools available to Claude.

        These are tool schemas that Claude can request to use.
        The actual execution happens on our server.
        """
        return [
            {
                "name": "web_search",
                "description": "Search the web for information on a topic. Returns a list of search results with titles, URLs, and descriptions.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query. Be specific and concise."
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "web_fetch",
                "description": "Fetch and read the full content from a specific URL. Use this after finding relevant URLs through search.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The full URL to fetch content from."
                        }
                    },
                    "required": ["url"]
                }
            }
        ]
