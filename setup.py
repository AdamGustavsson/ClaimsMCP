#!/usr/bin/env python3
"""
Setup script for the Claimify project.
Helps users quickly configure their environment and download required data.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.10 or newer."""
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10 or newer is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version {sys.version.split()[0]} is compatible")


def install_dependencies():
    """Install project dependencies."""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("ERROR: Failed to install dependencies")
        sys.exit(1)


def download_nltk_data():
    """Download required NLTK data."""
    print("Downloading NLTK data...")
    try:
        import nltk
        try:
            nltk.download('punkt_tab', quiet=True)
            print("✓ NLTK punkt_tab tokenizer downloaded")
        except:
            # Fallback for older NLTK versions
            nltk.download('punkt', quiet=True)
            print("✓ NLTK punkt tokenizer downloaded")
    except Exception as e:
        print(f"Warning: Failed to download NLTK data: {e}")
        print("You may need to run: python -c \"import nltk; nltk.download('punkt_tab')\" or python -c \"import nltk; nltk.download('punkt')\"")


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    example_file = Path("env.example")
    
    if env_file.exists():
        print("✓ .env file already exists")
        return
    
    if example_file.exists():
        # Copy example to .env
        with open(example_file, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("✓ Created .env file from template")
        print("  Please edit .env and add your API keys")
    else:
        # Create basic .env file
        env_content = """# API Keys (set one based on your LLM_PROVIDER choice)
OPENAI_API_KEY="your-openai-api-key-here"
ANTHROPIC_API_KEY="your-anthropic-api-key-here"

# LLM Configuration
LLM_PROVIDER="openai"  # Choose "openai" or "anthropic"
LLM_MODEL="gpt-4o"     # Or "claude-3-5-sonnet-20240620" for Anthropic

# Server Configuration
SERVER_PORT=8080
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✓ Created .env file")
        print("  Please edit .env and add your API keys")


def check_prompt_files():
    """Check if prompt files have been populated."""
    prompts_dir = Path("prompts")
    prompt_files = [
        "selection_prompt.txt",
        "disambiguation_prompt.txt", 
        "decomposition_prompt.txt"
    ]
    
    missing_prompts = []
    for prompt_file in prompt_files:
        file_path = prompts_dir / prompt_file
        if not file_path.exists():
            missing_prompts.append(prompt_file)
            continue
            
        # Check if file contains only placeholder content
        with open(file_path, 'r') as f:
            content = f.read().strip()
        
        if content.startswith('#') or len(content) < 100:  # Assume real prompts are longer
            missing_prompts.append(prompt_file)
    
    if missing_prompts:
        print("⚠ Prompt files need to be populated:")
        for prompt_file in missing_prompts:
            print(f"  - prompts/{prompt_file}")
        print("\nPlease copy the exact prompt texts from the Claimify paper:")
        print("  - Selection System Prompt (Appendix N.1.1) → prompts/selection_prompt.txt")
        print("  - Disambiguation System Prompt (Appendix N.1.2) → prompts/disambiguation_prompt.txt")
        print("  - Decomposition System Prompt (Appendix N.1.3) → prompts/decomposition_prompt.txt")
    else:
        print("✓ All prompt files appear to be populated")


def main():
    """Main setup routine."""
    print("🔧 Setting up Claimify project...\n")
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Download NLTK data
    download_nltk_data()
    
    # Create .env file
    create_env_file()
    
    # Check prompt files
    check_prompt_files()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file and add your API keys")
    print("2. Copy the Claimify prompts from the paper to the prompts/ files")
    print("3. Run: python claimify_server.py")
    print("\nFor detailed instructions, see README.md")


if __name__ == "__main__":
    main() 