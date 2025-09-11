from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
import os
import json
import re
from datetime import datetime
from django.conf import settings
from ..models import Agent

class AgentState(BaseModel):
    """Shared state between agents in the graph"""
    messages: List[BaseMessage] = Field(default_factory=list)
    current_task: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)
    next_agent: Optional[str] = None
    is_complete: bool = False
    supervisor_feedback: Optional[str] = None
    task_queue: List[str] = Field(default_factory=list)
    completed_tasks: List[str] = Field(default_factory=list)
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    supervisor_decision: Optional[Dict[str, Any]] = None

    class Config:
        arbitrary_types_allowed = True
