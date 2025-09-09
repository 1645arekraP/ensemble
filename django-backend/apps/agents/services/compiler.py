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
from .agent_state import AgentState

class SupervisorPromptBuilder:
    """Builds the prompt for the supervisor agent based on the state of other agents."""
    
    @staticmethod
    def build_supervisor_prompt(agent: Agent, available_agents: list[Agent]) -> str:
        agent_descriptions = []
        agent_names = []
        for agent in available_agents:
            agent_descriptions.append(f"- {agent.name}: {agent.description}")
            agent_names.append(agent.name)
        agent_list = "\n".join(agent_descriptions)
        supervisor_prompt = f"""
            {agent.system_instruction_prompt}
            You are a supervisor agent responsible for coordinating and routing tasks between multiple specialized agents.

            Available Agents:
            {agent_list}

            Your Responsibilities:
            1. Analyze incoming tasks and determine the most appropriate agent to handle them
            2. Break down complex tasks into subtasks if needed
            3. Monitor progress and decide when tasks are complete
            4. Coordinate between agents to ensure efficient workflow

            Decision Format:
            Always end your response with a decision block in this format:

            <decision>
            next_agent: [agent_name]
            reason: [brief explanation of why this agent is chosen]
            is_complete: [true/false - whether the overall task is finished]
            </decision>

            Available agent options: {', '.join(agent_names)}
            Use "FINISH" as next_agent when the task is completely done.

            Guidelines:
            - Consider each agent's specialization when routing
            - Provide clear reasoning for your decisions
            - Monitor the overall progress toward task completion
            - If an agent's output is insufficient, you can route back to them or to another agent
            - Always include the decision block - this is critical for routing
            """
        return supervisor_prompt
    
class AgentCompiler:
    """Compiles and manages the execution of agents in a multi-agent system."""

    def __init__(self):
        self.compiled_agents: Dict[str, Agent] = {}

    def _create_llm_instance(self, agent: Agent):
        """Create an LLM instance based on the agent's provider and model."""
        if agent.provider == Agent.AgentProvider.OPENAI:
            # Try agent-specific key first, then fall back to global settings
            api_key = agent.api_key or settings.OPENAI_API_KEY
            
            if not api_key:
                raise ValueError("OpenAI API key is required. Set it in the agent configuration or in settings.OPENAI_API_KEY")
                
            return ChatOpenAI(model=agent.model, api_key=api_key, temperature=0)
        else:
            raise NotImplementedError(f"Provider {agent.provider} is not supported yet.")
        
    def _load_agent_tools(self, agent: Agent):
        """Load and configure tools for the agent."""
        # Placeholder for tool loading logic
        return []
    
    def compile_agent(self, agent: Agent, graph_context=None):
        """Compile an agent into an executable form."""
        if agent.name in self.compiled_agents:
            return self.compiled_agents[agent.name]
        
        llm = self._create_llm_instance(agent)
        tools = self._load_agent_tools(agent)

        def agent_node(state: AgentState) -> AgentState:
            if agent.role == Agent.AgentRole.SUPERVISOR and graph_context:
                available_agents = graph_context.get('available_agents', [])
                system_prompt = SupervisorPromptBuilder.build_supervisor_prompt(agent, available_agents)

                context_info = self._build_supervisor_context(state)
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=context_info)
                ] + state.messages[-3:] # Keep last 3 messages for context
            else:
                messages = [
                    SystemMessage(content=agent.system_instruction_prompt)
                ] + state.messages

                if state.current_task:
                    task_message = HumanMessage(content=f"Current Task Focus: {state.current_task}")
                    messages.append(task_message)

            if tools:
                llm_with_tools = llm.bind_tools(tools)
                response = llm_with_tools.invoke(messages)
            else:
                response = llm.invoke(messages)

            # Create a new state with updated values
            new_state = AgentState(
                messages=state.messages + [response],
                current_task=state.current_task,
                context=state.context.copy(),
                next_agent=state.next_agent,
                is_complete=state.is_complete,
                supervisor_feedback=state.supervisor_feedback,
                task_queue=state.task_queue.copy(),
                completed_tasks=state.completed_tasks.copy(),
                agent_outputs={
                    **state.agent_outputs,
                    agent.name: {
                        'response': response.content,
                        'timestamp': str(datetime.now()),
                        'agent_role': agent.role,
                        'agent_id': agent.id
                    }
                },
                supervisor_decision=state.supervisor_decision
            )

            if agent.role == Agent.AgentRole.SUPERVISOR:
                new_state = self._handle_supervisor_logic(new_state, agent)
            else:
                if state.current_task and state.current_task not in new_state.completed_tasks:
                    new_state.completed_tasks.append(state.current_task)
            
            return new_state
        
        self.compiled_agents[agent.name] = agent_node
        return agent_node
            
    def _build_supervisor_context(self, state: AgentState) -> str:
        """Build context information for the supervisor agent."""
        context_parts = []
        if state.current_task:
            context_parts.append(f"Current Task: {state.current_task}")
        if state.completed_tasks:
            context_parts.append(f"Completed Tasks: {', '.join(state.completed_tasks)}")
        if state.task_queue:
            context_parts.append(f"Task Queue: {', '.join(state.task_queue)}")
        if state.agent_outputs:
            context_parts.append("Previous Agent Outputs:")
            for agent_name, output in state.agent_outputs.items():
                context_parts.append(f"- {agent_name} ({output['agent_role']}): {output['response'][:100]}...") # Truncate for brevity
        if state.context:
            context_parts.append(f"Additional Context: {json.dumps(state.context, indent=2)}")
        
        return "\n\n".join(context_parts)
    
    def _handle_supervisor_logic(self, state: AgentState, agent: Agent) -> AgentState:
        """Handle supervisor-specific routing logic"""
        response_content = state.messages[-1].content
        
        # Parse supervisor decision using structured output
        supervisor_decision = self._parse_supervisor_decision(response_content, agent)
        
        # Create a new state for immutability
        new_state = AgentState(
            messages=state.messages.copy(),
            current_task=state.current_task,
            context=state.context.copy(),
            next_agent=supervisor_decision.get('next_agent'),
            is_complete=supervisor_decision.get('is_complete', False),
            supervisor_feedback=state.supervisor_feedback,
            task_queue=state.task_queue.copy(),
            completed_tasks=state.completed_tasks.copy(),
            agent_outputs=state.agent_outputs.copy(),
            supervisor_decision=supervisor_decision
        )
        
        # Add to task queue if supervisor assigned new tasks
        if supervisor_decision.get('new_tasks'):
            new_state.task_queue.extend(supervisor_decision['new_tasks'])
        
        return new_state
    
    def _parse_supervisor_decision(self, response_content: str, agent: Agent) -> Dict[str, Any]:
        """Parse supervisor response to extract routing decisions"""
        # Look for decision block
        decision_match = re.search(r'<decision>(.*?)</decision>', response_content, re.DOTALL)
        if decision_match:
            decision_text = decision_match.group(1)
            return self._parse_decision_text(decision_text)
        
        # Look for JSON decision block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Fallback to keyword-based parsing
        return self._parse_keywords_decision(response_content, agent)
    
    def _parse_decision_text(self, decision_text: str) -> Dict[str, Any]:
        """Parse decision text for routing information"""
        decision = {}
        
        # Extract next agent
        next_agent_match = re.search(r'next_agent:\s*(\w+)', decision_text, re.IGNORECASE)
        if next_agent_match:
            decision['next_agent'] = next_agent_match.group(1)
        
        # Check for completion
        is_complete_match = re.search(r'is_complete:\s*(true|false)', decision_text, re.IGNORECASE)
        if is_complete_match:
            decision['is_complete'] = is_complete_match.group(1).lower() == 'true'
        
        # Extract reasoning
        reason_match = re.search(r'reason:\s*(.+?)(?:\n|$)', decision_text, re.IGNORECASE)
        if reason_match:
            decision['reasoning'] = reason_match.group(1).strip()
        
        return decision
    
    def _parse_keywords_decision(self, content: str, agent: Agent) -> Dict[str, Any]:
        """Fallback keyword-based decision parsing"""
        content_lower = content.lower()
        
        # Get available agents from the project
        available_agents = list(agent.project.agents.exclude(
            id=agent.id
        ).values_list('name', flat=True))
        
        # Look for agent names mentioned
        for agent_name in available_agents:
            if agent_name.lower() in content_lower:
                return {
                    'next_agent': agent_name,
                    'reasoning': 'Keyword match in supervisor response'
                }
        
        # Check for completion keywords
        completion_keywords = ['complete', 'finished', 'done', 'end', 'final']
        if any(keyword in content_lower for keyword in completion_keywords):
            return {'is_complete': True, 'reasoning': 'Completion keyword detected'}
        
        # Default: continue with first available agent
        if available_agents:
            return {
                'next_agent': available_agents[0],
                'reasoning': 'Default routing to first available agent'
            }
        
        return {'is_complete': True, 'reasoning': 'No available agents found'}