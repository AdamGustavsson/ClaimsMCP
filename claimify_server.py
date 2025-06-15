#!/usr/bin/env python3
"""
Claimify MCP Server

A Model Context Protocol server that exposes the Claimify claim extraction tool.
This implements the multi-stage claim extraction methodology from the paper
"Towards Effective Extraction and Evaluation of Factual Claims".
"""

import asyncio
import os
import sys
from typing import List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv

# Import our custom modules
from llm_client import LLMClient
from pipeline import ClaimifyPipeline


# Load environment variables
load_dotenv()

# Initialize the MCP server
server = Server("claimify-extraction-server")


# Define the extract_claims tool
@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="extract_claims",
            description="""Extracts verifiable, decontextualized factual claims from a given text string.
Claims are decontextualized (self-contained) and verifiable. Each sentence is parsed with surrounding sentences as context. Do not call the tool with long texts as it will timeout (expect roughly 10 seconds per sentence).
If needed, break the text into smaller chunks and call the tool multiple times. Make sure to break in sections with enough context.

Example:
Input: "Apple INC did a fine result last quarter of 2024. The company's revenue increased by 15% due to strong sales."
Output: ["Apple INC's revenue increased by 15% last quarter of 2024"]""",
            inputSchema={
                "type": "object",
                "properties": {
                    "text_to_process": {
                        "type": "string",
                        "description": "The input text string from which to extract claims."
                    },
                    "question": {
                        "type": "string",
                        "description": "An optional question that provides context for the text. This can help in resolving ambiguities during the disambiguation stage.",
                        "default": "The user did not provide a question."
                    }
                },
                "required": ["text_to_process"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "extract_claims":
        try:
            text_to_process = arguments.get("text_to_process", "")
            question = arguments.get("question", "The user did not provide a question.")
            
            # Initialize the LLM client and pipeline
            llm_client = LLMClient()
            pipeline = ClaimifyPipeline(llm_client, question)
            
            # Run the extraction pipeline
            claims = pipeline.run(text_to_process)
            
            # Return the claims as actual structured data
            import json
            
            # Return the raw array as JSON string for proper data structure
            result = json.dumps(claims, indent=2)
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            error_msg = f"Error during claim extraction: {str(e)}"
            return [TextContent(type="text", text=error_msg)]
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point for the server."""
    # Check for required configuration
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set.", file=sys.stderr)
        print("Please create a .env file with your API key or set the environment variable.", file=sys.stderr)
        sys.exit(1)
    elif provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        print("Please create a .env file with your API key or set the environment variable.", file=sys.stderr)
        sys.exit(1)
    
    # Log configuration to stderr (so it doesn't interfere with MCP protocol on stdout)
    print(f"Starting Claimify MCP Server...", file=sys.stderr)
    print(f"LLM Provider: {provider}", file=sys.stderr)
    print(f"Model: {os.getenv('LLM_MODEL', 'gpt-4o')}", file=sys.stderr)
    print("Server is ready to accept connections via stdio.", file=sys.stderr)
    
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, 
                        server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main()) 