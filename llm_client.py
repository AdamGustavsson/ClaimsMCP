"""
LLM Client for the Claimify system.
Supports OpenAI API with structured outputs using Pydantic models.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Optional, Type, TypeVar
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """
    A client that communicates with OpenAI API and supports structured outputs with Pydantic models.
    """
    
    def __init__(self):
        load_dotenv()
        self.provider = "openai"
        self.model = os.getenv("LLM_MODEL", "gpt-4o-2024-08-06")
        self.call_count = 0
        
        # Set up logging
        self.setup_logging()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        self.client = OpenAI(api_key=api_key)

    def setup_logging(self):
        """Set up logging for LLM calls."""
        # Check if logging is enabled
        log_enabled = os.getenv("LOG_LLM_CALLS", "true").lower() in ("true", "1", "yes")
        
        if not log_enabled:
            self.logger = None
            return
        
        # Create logger
        self.logger = logging.getLogger(f"claimify.llm.{self.provider}")
        self.logger.setLevel(logging.INFO)
        
        # Don't add handlers if they already exist (avoid duplicate logs)
        if self.logger.handlers:
            return
        
        # Determine log output - default to stderr for MCP compatibility
        log_output = os.getenv("LOG_OUTPUT", "stderr").lower()
        
        if log_output == "file":
            # Log to file - but handle read-only file systems gracefully
            try:
                log_file = os.getenv("LOG_FILE", "claimify_llm.log")
                handler = logging.FileHandler(log_file)
            except (OSError, PermissionError):
                # Fall back to stderr if file logging fails
                handler = logging.StreamHandler(sys.stderr)
        else:
            # Log to stderr (default) - won't interfere with MCP protocol on stdout
            handler = logging.StreamHandler(sys.stderr)
        
        # Set formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def supports_structured_outputs(self) -> bool:
        """Check if the current model supports structured outputs."""
        # Structured outputs are supported by OpenAI models gpt-4o-mini and gpt-4o-2024-08-06 and later
        supported_models = [
            "gpt-4o-mini",
            "gpt-4o-mini-2024-07-18", 
            "gpt-4o-2024-08-06",
            "gpt-4o-2024-11-20",
            "gpt-4o-2024-12-17",
            "gpt-4o"  # Latest gpt-4o should support it
        ]
        
        # Check if any supported model name is contained in the current model
        model_lower = self.model.lower()
        
        # Special handling for gpt-4o to avoid false positives with gpt-4o-mini
        if "gpt-4o-mini" in model_lower:
            return True
        elif "gpt-4o-2024" in model_lower:
            return True
        elif model_lower == "gpt-4o":
            return True
        
        return False

    def make_structured_request(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        response_model: Type[T],
        stage: str = "unknown"
    ) -> Optional[T]:
        """
        Makes a structured request to the LLM using Pydantic models.
        
        Args:
            system_prompt: The system prompt to use
            user_prompt: The user prompt to use
            response_model: Pydantic model class for the expected response
            stage: The pipeline stage making this request (for logging)
            
        Returns:
            Parsed response as the specified Pydantic model, or None on failure
        """
        if not self.supports_structured_outputs():
            raise ValueError(
                f"Model {self.model} does not support structured outputs. "
                f"Please use a compatible model like gpt-4o-2024-08-06, gpt-4o-mini, or gpt-4o."
            )
        
        self.call_count += 1
        start_time = datetime.now()
        
        # Log the request
        if self.logger:
            self.logger.info(f"=== STRUCTURED LLM CALL #{self.call_count} - STAGE: {stage.upper()} ===")
            self.logger.info(f"Provider: {self.provider}, Model: {self.model}")
            self.logger.info(f"Response Model: {response_model.__name__}")
            
            # Log only first sentence of system prompt
            system_first_sentence = system_prompt.split('.')[0] + '.' if '.' in system_prompt else system_prompt[:100] + '...'
            self.logger.info(f"System Prompt ({len(system_prompt)} chars): {system_first_sentence}")
            
            # Log user prompt
            self.logger.info(f"User Prompt ({len(user_prompt)} chars): {user_prompt}")
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # Use structured outputs with beta.chat.completions.parse
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                response_format=response_model,
                temperature=0.0,
                max_tokens=2048,
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Check for refusal
            if response.choices[0].message.refusal:
                if self.logger:
                    self.logger.warning(f"Call #{self.call_count} refused: {response.choices[0].message.refusal}")
                return None
            
            # Get the parsed response
            parsed_response = response.choices[0].message.parsed
            
            # Log the response
            if self.logger:
                self.logger.info(f"Structured response received in {duration:.2f}s:")
                self.logger.info(f"Parsed response: {parsed_response}")
                
                # Log token usage if available
                if hasattr(response, 'usage') and response.usage:
                    usage = response.usage
                    self.logger.info(f"Token usage - Prompt: {usage.prompt_tokens}, "
                                   f"Completion: {usage.completion_tokens}, "
                                   f"Total: {usage.total_tokens}")
                
                self.logger.info(f"=== END STRUCTURED CALL #{self.call_count} ===\n")
            
            return parsed_response
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            error_msg = f"Error during structured LLM API call: {e}"
            if self.logger:
                self.logger.error(f"Structured call #{self.call_count} failed after {duration:.2f}s: {error_msg}")
                self.logger.error(f"=== END STRUCTURED CALL #{self.call_count} (ERROR) ===\n")
            else:
                print(error_msg, file=sys.stderr)
            
            return None 