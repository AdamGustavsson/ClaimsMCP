"""
Pydantic models for structured outputs in the Claimify pipeline.
These models define the expected response format for each stage.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class SelectionResponse(BaseModel):
    """Response model for the Selection stage."""
    
    sentence: str = Field(description="The original sentence being analyzed")
    
    thought_process: str = Field(
        description="4-step stream of consciousness thought process analyzing the sentence"
    )
    
    final_submission: Literal["Contains a specific and verifiable proposition", "Does NOT contain a specific and verifiable proposition"] = Field(
        description="Whether the sentence contains a specific and verifiable proposition"
    )
    
    sentence_with_only_verifiable_information: Optional[str] = Field(
        description="The sentence with only verifiable information, 'remains unchanged' if no changes needed, or None if no verifiable proposition",
        default=None
    )


class DisambiguationResponse(BaseModel):
    """Response model for the Disambiguation stage."""
    
    incomplete_names_acronyms_abbreviations: str = Field(
        description="Analysis of partial names and undefined acronyms/abbreviations in the sentence"
    )
    
    linguistic_ambiguity_analysis: str = Field(
        description="Step-by-step analysis of referential and structural ambiguity in the sentence"
    )
    
    changes_needed: Optional[str] = Field(
        description="List of changes needed to decontextualize the sentence, or None if cannot be decontextualized",
        default=None
    )
    
    decontextualized_sentence: Optional[str] = Field(
        description="The final decontextualized sentence, or 'Cannot be decontextualized' if ambiguity cannot be resolved",
        default=None
    )


class Claim(BaseModel):
    """A single factual claim with verification properties."""
    
    text: str = Field(description="The claim text with essential context/clarifications in brackets")
    
    verifiable: bool = Field(
        description="Always True - indicates this claim can be fact-checked as true or false",
        default=True
    )


class DecompositionResponse(BaseModel):
    """Response model for the Decomposition stage."""
    
    sentence: str = Field(description="The sentence being decomposed")
    
    referential_terms: Optional[str] = Field(
        description="Overview of referential terms whose referents must be clarified, or 'None' if no referential terms",
        default=None
    )
    
    max_clarified_sentence: str = Field(
        description="Sentence that articulates discrete units of information and clarifies referents"
    )
    
    proposition_range: str = Field(
        description="The range of possible number of propositions (e.g., '3-5')"
    )
    
    propositions: List[str] = Field(
        description="List of specific, verifiable, and decontextualized propositions"
    )
    
    final_claims: List[Claim] = Field(
        description="Final list of claims with text and verifiable property (always True) to guide LLM thinking about fact-checkability"
    ) 