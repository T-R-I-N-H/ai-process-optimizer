from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union

# Data Models for Agent Communication

class ProcessDescription(BaseModel):
    name: str = Field(description="Name of the process.")
    steps: List[str] = Field(description="A list of sequential steps in the process.")
    inputs: List[str] = Field(default=[], description="Key inputs required for the process.")
    outputs: List[str] = Field(default=[], description="Key outputs produced by the process.")
    pain_points: Optional[List[str]] = Field(default=[], description="Observed problems or inefficiencies in the current process.")
    metrics: Optional[Dict[str, str]] = Field(default={}, description="Current performance metrics (e.g., 'Avg_Resolution_Time': '3 days').")
    goal: Optional[str] = Field(description="The primary goal for improving this process.")

class BottleneckHypothesis(BaseModel):
    location: str = Field(description="The specific step or area where the bottleneck is suspected.")
    reason_hypothesis: str = Field(description="Hypothesized reason for the bottleneck.")
    info_needed: List[str] = Field(description="Specific information required to confirm/refine this bottleneck and propose solutions.")

class VerifiedInformation(BaseModel):
    query: str = Field(description="The original query for information.")
    sources: List[str] = Field(description="URLs or database references where information was found.")
    summary: str = Field(description="A concise summary of the verified information.")
    confidence: str = Field(description="Confidence level in the information (e.g., 'High', 'Medium', 'Low').")
    relevance: str = Field(description="How relevant the information is to the bottleneck (e.g., 'Direct', 'Indirect').")

class ProposedImprovement(BaseModel):
    step_number: Optional[int] = Field(description="The step number in the original process this improvement targets (if applicable). Null if it's a general improvement.")
    description: str = Field(description="A detailed description of the proposed change.")
    expected_impact: str = Field(description="Expected benefits (e.g., time savings, cost reduction, quality increase).")
    tools_or_tech: Optional[List[str]] = Field(default=[], description="Recommended tools or technologies.")
    actors_involved: Optional[List[str]] = Field(default=[], description="Roles or departments involved in the change.")

class ImprovedProcess(BaseModel):
    name: str = Field(description="Name of the improved process.")
    original_process: ProcessDescription = Field(description="The original process description.")
    improvements: List[ProposedImprovement] = Field(description="List of proposed improvements applied.")
    improved_steps: List[str] = Field(description="The new, sequential steps of the improved process.")
    summary_of_changes: str = Field(description="A high-level summary of all changes.")