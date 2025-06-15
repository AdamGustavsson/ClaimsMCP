"""
Core pipeline implementation for the Claimify claim extraction system.
Implements the multi-stage pipeline as described in the Claimify paper.
Uses structured outputs for improved reliability.
"""

import nltk
import os
import sys
import logging
from typing import List, Tuple, Optional
from structured_prompts import (
    STRUCTURED_SELECTION_SYSTEM_PROMPT, 
    STRUCTURED_DISAMBIGUATION_SYSTEM_PROMPT, 
    STRUCTURED_DECOMPOSITION_SYSTEM_PROMPT
)
from structured_models import SelectionResponse, DisambiguationResponse, DecompositionResponse


def ensure_nltk_data():
    """Ensure NLTK punkt tokenizer data is downloaded."""
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        print("Downloading NLTK punkt tokenizer data...")
        try:
            nltk.download('punkt_tab')
        except:
            # Fallback to older punkt if punkt_tab fails
            nltk.download('punkt')


def split_into_sentences(text: str) -> List[str]:
    """
    Splits a block of text into sentences, handling paragraphs and lists.
    This replicates the methodology from Appendix C.1 of the Claimify paper.
    
    Args:
        text: The input text to split
        
    Returns:
        A list of sentence strings
    """
    ensure_nltk_data()
    
    sentences = []
    # First, split by newlines to handle paragraphs and list items
    paragraphs = text.split('\n')
    for para in paragraphs:
        if para.strip():  # Avoid empty paragraphs
            # Then, use NLTK's sentence tokenizer on each paragraph
            sentences.extend(nltk.sent_tokenize(para))
    return sentences


def create_context_for_sentence(
    sentences: List[str],
    index: int,
    p: int,  # Number of preceding sentences
    f: int   # Number of following sentences
) -> str:
    """
    Creates a context string for a sentence at a given index.
    As per Section 3.1 of the Claimify paper.
    
    Args:
        sentences: List of all sentences
        index: Index of the target sentence
        p: Number of preceding sentences to include
        f: Number of following sentences to include
        
    Returns:
        Context string containing the target sentence and surrounding context
    """
    start = max(0, index - p)
    end = min(len(sentences), index + f + 1)
    
    context_sentences = sentences[start:end]
    
    return "\n".join(context_sentences)


def run_selection_stage(llm_client, question: str, excerpt: str, sentence: str) -> Tuple[str, str]:
    """
    Executes the Selection stage of the Claimify pipeline using structured outputs.
    
    Args:
        llm_client: The LLM client to use
        question: The question/context for the text
        excerpt: The context excerpt
        sentence: The sentence to process
        
    Returns:
        Tuple of (status, processed_sentence) where status is 'verifiable', 'unverifiable', or 'error'
    """
    user_prompt = f"Question:\n{question}\n\nExcerpt:\n{excerpt}\n\nSentence:\n{sentence}"
    
    structured_response = llm_client.make_structured_request(
        system_prompt=STRUCTURED_SELECTION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=SelectionResponse,
        stage="selection"
    )
    
    if not structured_response:
        return 'error', None
    
    return parse_structured_selection_output(structured_response, sentence)


def parse_structured_selection_output(response: SelectionResponse, original_sentence: str) -> Tuple[str, str]:
    """
    Parses the structured output from the Selection stage.
    
    Args:
        response: The structured response from the LLM
        original_sentence: The original sentence being processed
        
    Returns:
        Tuple of (status, sentence) where status indicates the result
    """
    try:
        if response.final_submission == "Contains a specific and verifiable proposition":
            if response.sentence_with_only_verifiable_information:
                if response.sentence_with_only_verifiable_information.lower() == "remains unchanged":
                    return 'verifiable', original_sentence
                elif response.sentence_with_only_verifiable_information.lower() == "none":
                    return 'unverifiable', None
                else:
                    return 'verifiable', response.sentence_with_only_verifiable_information
            else:
                return 'verifiable', original_sentence
        else:
            return 'unverifiable', None
    except Exception as e:
        return 'error', None


def run_disambiguation_stage(llm_client, question: str, excerpt: str, sentence: str) -> Tuple[str, str]:
    """
    Executes the Disambiguation stage of the Claimify pipeline using structured outputs.
    
    Args:
        llm_client: The LLM client to use
        question: The question/context for the text
        excerpt: The context excerpt
        sentence: The sentence to process
        
    Returns:
        Tuple of (status, processed_sentence) where status is 'resolved', 'unresolvable', or 'error'
    """
    user_prompt = f"Question:\n{question}\n\nExcerpt:\n{excerpt}\n\nSentence:\n{sentence}"
    
    structured_response = llm_client.make_structured_request(
        system_prompt=STRUCTURED_DISAMBIGUATION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=DisambiguationResponse,
        stage="disambiguation"
    )
    
    if not structured_response:
        return 'error', None
    
    return parse_structured_disambiguation_output(structured_response, sentence)


def parse_structured_disambiguation_output(response: DisambiguationResponse, original_sentence: str) -> Tuple[str, str]:
    """
    Parses the structured output from the Disambiguation stage.
    
    Args:
        response: The structured response from the LLM
        original_sentence: The original sentence being processed
        
    Returns:
        Tuple of (status, sentence) where status indicates the result
    """
    try:
        if response.decontextualized_sentence:
            if response.decontextualized_sentence == "Cannot be decontextualized":
                return 'unresolvable', None
            else:
                return 'resolved', response.decontextualized_sentence
        else:
            return 'unresolvable', None
    except Exception as e:
        return 'error', None


def run_decomposition_stage(llm_client, question: str, excerpt: str, sentence: str) -> List[str]:
    """
    Executes the Decomposition stage of the Claimify pipeline using structured outputs.
    
    Args:
        llm_client: The LLM client to use
        question: The question/context for the text
        excerpt: The context excerpt
        sentence: The sentence to process
        
    Returns:
        A list of extracted claim strings
    """
    user_prompt = f"Question:\n{question}\n\nExcerpt:\n{excerpt}\n\nSentence:\n{sentence}"
    
    structured_response = llm_client.make_structured_request(
        system_prompt=STRUCTURED_DECOMPOSITION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=DecompositionResponse,
        stage="decomposition"
    )
    
    if not structured_response:
        return []
    
    return parse_structured_decomposition_output(structured_response)


def parse_structured_decomposition_output(response: DecompositionResponse) -> List[str]:
    """
    Parses the structured output from the Decomposition stage.
    
    Args:
        response: The structured response from the LLM
        
    Returns:
        A list of extracted claim strings
    """
    try:
        # Extract text from the Claim objects in final_claims
        return [claim.text for claim in response.final_claims]
    except Exception as e:
        return []


class ClaimifyPipeline:
    """
    Main pipeline class that orchestrates the multi-stage claim extraction process.
    Uses structured outputs for improved reliability.
    """
    
    def __init__(self, llm_client, question: str = "The user did not provide a question."):
        self.llm_client = llm_client
        self.question = question
        
        # Set up logging
        self.setup_logging()
        
        # Verify structured outputs are supported
        if not self.llm_client.supports_structured_outputs():
            raise ValueError(
                f"Model {self.llm_client.model} does not support structured outputs. "
                f"Please use a compatible model like gpt-4o-2024-08-06, gpt-4o-mini, or gpt-4o."
            )
        
        if self.logger:
            self.logger.info("Structured outputs enabled for improved reliability")

    def setup_logging(self):
        """Set up logging for the pipeline."""
        # Check if logging is enabled
        log_enabled = os.getenv("LOG_LLM_CALLS", "true").lower() in ("true", "1", "yes")
        
        if not log_enabled:
            self.logger = None
            return
        
        # Create logger
        self.logger = logging.getLogger("claimify.pipeline")
        self.logger.setLevel(logging.INFO)
        
        # Don't add handlers if they already exist (avoid duplicate logs)
        if self.logger.handlers:
            return
        
        # Determine log output - default to stderr for MCP compatibility
        log_output = os.getenv("LOG_OUTPUT", "stderr").lower()
        
        if log_output == "file":
            # Log to file - but handle read-only file systems gracefully
            try:
                log_file = os.getenv("LOG_FILE", "claimify_pipeline.log")
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

    def run(self, text_to_process: str) -> List[str]:
        """
        Runs the full Claimify pipeline on a given text.
        
        Args:
            text_to_process: The input text to process
            
        Returns:
            A list of extracted claim strings
        """
        if not text_to_process.strip():
            return []

        all_claims = []
        sentences = split_into_sentences(text_to_process)
        
        if self.logger:
            self.logger.info(f"Processing {len(sentences)} sentences")
        
        for i, sentence in enumerate(sentences):
            if self.logger:
                self.logger.info(f"Processing sentence {i+1}/{len(sentences)}: {sentence[:100]}...")
            
            # Create context for the current sentence
            # Using a fixed context window as per the paper's experiments
            context_excerpt = create_context_for_sentence(sentences, i, p=5, f=5)

            # Stage 2: Selection
            selection_status, verifiable_sentence = run_selection_stage(
                self.llm_client, self.question, context_excerpt, sentence
            )
            
            if self.logger:
                self.logger.info(f"SELECTION: Sentence {selection_status}")
            
            if selection_status != 'verifiable':
                continue

            # Stage 3: Disambiguation
            disambiguation_status, clarified_sentence = run_disambiguation_stage(
                self.llm_client, self.question, context_excerpt, verifiable_sentence
            )
            
            if self.logger:
                self.logger.info(f"DISAMBIGUATION: Sentence {disambiguation_status}")
            
            if disambiguation_status != 'resolved':
                continue

            # Stage 4: Decomposition
            extracted_claims = run_decomposition_stage(
                self.llm_client, self.question, context_excerpt, clarified_sentence
            )
            
            if self.logger:
                self.logger.info(f"DECOMPOSITION: Extracted {len(extracted_claims)} claims")
            
            if extracted_claims:
                all_claims.extend(extracted_claims)
        
        # Return a de-duplicated list of claims
        unique_claims = list(dict.fromkeys(all_claims))
        
        if self.logger:
            self.logger.info(f"Pipeline completed: {len(unique_claims)} unique claims extracted")
        
        return unique_claims 