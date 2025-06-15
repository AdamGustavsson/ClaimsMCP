# Claimify: Research-Based Claim Extraction via MCP

An implementation of the "Claimify" methodology for factual claim extraction, delivered as a local Model Context Protocol (MCP) server. This tool implements the multi-stage claim extraction approach detailed in the academic paper "Towards Effective Extraction and Evaluation of Factual Claims" by Metropolitansky & Larson (2025).

[Read the paper here](https://arxiv.org/abs/2502.10855)


Promps from the paper have been modified for use with Structured Outputs.
THIS IS NOT AN OFFICIAL IMPLEMENTATION. 

## Overview

Claimify extracts verifiable, decontextualized factual claims from text using a sophisticated four-stage pipeline:

1. **Sentence Splitting**: Breaks text into individual sentences with surrounding context
2. **Selection**: Filters for sentences containing verifiable propositions, excluding opinions and speculation
3. **Disambiguation**: Resolves ambiguities or discards sentences that cannot be clarified
4. **Decomposition**: Breaks down sentences into atomic, self-contained factual claims

The tool uses OpenAI's structured outputs feature exclusively for improved reliability and exposes its functionality through the Model Context Protocol, making it available to MCP-compatible clients like Cursor and Claude Desktop.

## Features

- **Research-based methodology**: Implements the peer-reviewed Claimify approach
- **Structured outputs**: Uses OpenAI's structured outputs for reliable, type-safe responses
- **MCP integration**: Seamlessly integrates with development environments
- **Robust parsing**: Handles various text formats including lists and paragraphs
- **Context-aware**: Uses surrounding sentences to resolve ambiguities
- **Multi-language support**: Preserves original language while extracting claims
- **Comprehensive logging**: Detailed logging of all LLM calls, responses, and pipeline stages
- **Production-ready**: Includes error handling, monitoring, and configuration management

## Requirements

- **OpenAI API**: Requires an OpenAI API key
- **Compatible Model**: Must use a model that supports structured outputs:
  - `gpt-4o-2024-08-06` (recommended)
  - `gpt-4o-mini` (faster and cheaper)
  - `gpt-4o` (latest version)
- **Python 3.10+**: For proper type hints and Pydantic support

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd ClaimsMCP

# Create and activate a virtual environment
python -m venv claimify-env
source claimify-env/bin/activate  # On Windows: claimify-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download required NLTK data (done automatically on first run)
python -c "import nltk; nltk.download('punkt_tab')"
```

### 2. Configuration

Create a `.env` file in the project root:

```bash
# Copy the example file
cp env.example .env
```

Edit `.env` and add your API key:

```env
# API Keys
OPENAI_API_KEY="your-openai-api-key-here"

# LLM Configuration
LLM_MODEL="gpt-4o-2024-08-06"  # Model that supports structured outputs

# Logging Configuration
LOG_LLM_CALLS="true"   # Set to "false" to disable logging
LOG_OUTPUT="stderr"    # "stderr" or "file" - where to send logs
LOG_FILE="claimify_llm.log"  # Used only if LOG_OUTPUT="file"
```

### 3. Run the Server

```bash
python claimify_server.py
```

You should see output like:
```
Starting Claimify MCP Server...
Model: gpt-4o-2024-08-06
Structured outputs enabled for improved reliability
Server is ready to accept connections via stdio.
```

Note: The server uses standard IO (stdin/stdout) for communication, not HTTP. This means it will wait for input and won't show a "running" status. This is normal - the server is ready to receive MCP protocol messages from a client.

## MCP Client Configuration

### For Cursor

1. Open Cursor and navigate to **Settings > MCP**
2. Click "Add a New Global MCP Server"
3. Add the following configuration to your MCP settings file (usually `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "claimify-local": {
      "command": "/path/to/your/claimify-env/bin/python",
      "args": [
        "/path/to/your/project/claimify_server.py"
      ]
    }
  }
}
```

4. Replace the paths with the absolute paths to your Python executable and server script

The "Claimify Extraction Server" should now appear as a connected tool in your MCP-enabled chat.

## Usage Examples

Once configured, you can use the tool in your MCP client:

### Example 1: Simple Factual Text
```
Input: "The American flag contains 50 stars and 13 stripes."
Output: [
  "The American flag contains 50 stars [representing the 50 states] and 13 stripes [representing the original 13 colonies].",
  "The American flag was designed in 1777",
  "The American flag has been modified 27 times"
]
```

### Example 2: Mixed Fact and Opinion
```
Input: "Apple Inc. was founded in 1976 by Steve Jobs, Steve Wozniak, and Ronald Wayne. The company is incredibly innovative and has the best products in the world."
Output: [
  "Apple Inc. was founded in 1976 by Steve Jobs, Steve Wozniak, and Ronald Wayne."
]
```
(Note: The subjective content about being "incredibly innovative" and having "the best products" is filtered out)

### Example 3: Multi-language Support
```
Input: "String-systemet är en prisbelönt ikon som kombinerar elegant och minimalistisk design med ett brett utbud av färger och storlekar. Nisse Strinning skapade första hyllan redan 1949."
Output: [
  "String-systemet [ett hyllsystem] är en prisbelönt ikon [inom design]",
  "String-systemet kombinerar elegant och minimalistisk design med ett brett utbud av färger och storlekar",
  "Nisse Strinning skapade den första String-hyllan [String-systemet] 1949"
]
```
(Note: Content preserved in original Swedish, with contextual clarifications added in brackets)

## Project Structure

```
ClaimsMCP/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── env.example                  # Environment configuration template
├── claimify_server.py          # Main MCP server script
├── llm_client.py               # LLM client with structured outputs support
├── pipeline.py                 # Core claim extraction pipeline
├── structured_models.py        # Pydantic models for structured outputs
├── structured_prompts.py       # Optimized prompts for structured outputs
├── setup.py                    # Package setup configuration
├── test_claimify.py            # Test suite for the claim extraction pipeline
└── LICENSE                     # Apache 2.0 license
```

## Architecture

The system follows a modular architecture with structured outputs:

- **MCP Server**: Exposes the claim extraction as a tool via the Model Context Protocol
- **ClaimifyPipeline**: Orchestrates the multi-stage extraction process using structured outputs
- **LLMClient**: Handles communication with OpenAI API using structured outputs and Pydantic models
- **Structured Models**: Pydantic models that define the expected response format for each stage
- **Stage Functions**: Individual functions for Selection, Disambiguation, and Decomposition
- **Prompt Management**: Simplified prompts optimized for structured outputs

## Structured Outputs Benefits

The implementation uses OpenAI's structured outputs feature, which provides:

- **Type Safety**: Responses are automatically validated against Pydantic models
- **Reliability**: No more regex parsing failures or malformed JSON
- **Explicit Refusals**: Safety-based refusals are programmatically detectable
- **Consistency**: Guaranteed adherence to the expected response schema
- **Performance**: Reduced need for retry logic and error handling

## Configuration Options

| Environment Variable | Description | Default | Options |
|---------------------|-------------|---------|---------|
| `LLM_MODEL` | Specific model to use | `gpt-4o-2024-08-06` | Models supporting structured outputs |
| `OPENAI_API_KEY` | OpenAI API key | None | Your API key |
| `LOG_LLM_CALLS` | Enable detailed logging of all LLM interactions | `true` | `true`, `false` |
| `LOG_OUTPUT` | Where to send log output | `stderr` | `stderr`, `file` |
| `LOG_FILE` | Log file name (used when LOG_OUTPUT=file) | `claimify_llm.log` | Any filename |

## Troubleshooting

### Common Issues

1. **"Model does not support structured outputs" error**
   - Ensure you're using a compatible model: `gpt-4o-2024-08-06`, `gpt-4o-mini`, or `gpt-4o`
   - Update your `.env` file: `LLM_MODEL=gpt-4o-2024-08-06`

2. **"API key not set" error**
   - Ensure your `.env` file exists and contains the correct OpenAI API key
   - Check that the key starts with `sk-`

3. **"NLTK punkt tokenizer not found"**
   - Run: `python -c "import nltk; nltk.download('punkt_tab')"` or `python -c "import nltk; nltk.download('punkt')"`

4. **MCP client can't connect**
   - Check that the paths in your MCP configuration are absolute and correct
   - Ensure your Python virtual environment is activated
   - Verify the server script is executable: `chmod +x claimify_server.py`

5. **No claims extracted**
   - Check the logs for detailed information about each pipeline stage
   - Ensure the input text contains verifiable factual statements
   - Try with simpler, more direct factual sentences first

## Development

To extend or modify the system:

1. **Adding new response fields**: Update the Pydantic models in `structured_models.py`
2. **Modifying prompts**: Edit the prompts in `structured_prompts.py`
3. **Adding new stages**: Create new functions in `pipeline.py` following the existing pattern
4. **Testing**: Use the built-in logging to debug pipeline behavior

The structured outputs approach makes the system much more reliable and easier to debug compared to traditional text parsing methods.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## References

Metropolitansky & Larson (2025). "Towards Effective Extraction and Evaluation of Factual Claims"

## Support

For issues related to:
- **Setup and configuration**: Check this README and the troubleshooting section
- **MCP integration**: Refer to the [Model Context Protocol documentation](https://modelcontextprotocol.io/)
- **Research methodology**: Consult the original Claimify paper
