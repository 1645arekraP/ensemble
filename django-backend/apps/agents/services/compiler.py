from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage, AIMessage
from pydantic import BaseModel, Field
import os
import json
import re
from datetime import datetime
from django.conf import settings
from ..models import Agent
from .agent_state import AgentState
from ...tools.registry import ToolRegistry

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
        agent_names_str = ", ".join(agent_names)
        
        supervisor_prompt = f"""
You are a supervisor agent coordinating tasks between specialized agents. 
**CRITICAL: Your *entire* response MUST end with a <decision> block.** No text should follow it.

{agent.system_instruction_prompt} 

Available Agents (You MUST choose EXACTLY one of these names or use FINISH):
{agent_list if agent_list else '- None'}

**IMPORTANT**: When routing, use the EXACT agent name from this list: {agent_names_str}

Your Responsibilities:
1. Analyze the user's request
2. Choose the SINGLE BEST agent to handle it from the list above
3. If the user's request has been fully satisfied, use FINISH
4. **DO NOT** make up agent names - only use: {agent_names_str}

Decision Format (REQUIRED AT THE VERY END):
You MUST end your response with exactly this format:

<decision>
next_agent: [exact_agent_name | FINISH]
is_complete: [true | false]
reasoning: [brief explanation]
</decision>

Examples:

For a request like "write me a poem":
<decision>
next_agent: Poet
is_complete: false
reasoning: User wants a poem, routing to Poet agent
</decision>

For a request like "tell me a joke":
<decision>
next_agent: Joker
is_complete: false
reasoning: User wants a joke, routing to Joker agent
</decision>

After an agent completes its task successfully:
<decision>
next_agent: FINISH
is_complete: true
reasoning: The agent has completed the user's request
</decision>

**CRITICAL**: 
- Always include the <decision> block at the very end
- Use exact agent names: {agent_names_str}
- After ONE agent successfully completes a task, use FINISH unless the user asks for more
"""
        print("\n" + "="*80)
        print("SUPERVISOR PROMPT BUILT")
        print("="*80)
        print(f"Available agents: {agent_names_str}")
        print("="*80 + "\n")
        return supervisor_prompt
    
class AgentCompiler:
    """Compiles and manages the execution of agents in a multi-agent system."""

    def __init__(self):
        self.compiled_agents: Dict[str, Agent] = {}
        self.tool_registry = ToolRegistry()

    def _create_llm_instance(self, agent: Agent):
        """Create an LLM instance based on the agent's provider and model."""
        if agent.provider == Agent.AgentProvider.OPENAI:
            api_key = agent.api_key or settings.OPENAI_API_KEY
            if not api_key:
                raise ValueError("OpenAI API key is required.")
            return ChatOpenAI(model=agent.model, api_key=api_key, temperature=0)
        
        elif agent.provider == 'google':
            api_key = agent.api_key or settings.GOOGLE_API_KEY
            if not api_key:
                raise ValueError("Google API key is required.")
            return ChatGoogleGenerativeAI(
                model=agent.model,
                api_key=api_key,
                temperature=0,
                convert_system_message_to_human=True
            )
        else:
            raise NotImplementedError(f"Provider {agent.provider} is not supported yet.")
        
    def _load_agent_tools(self, agent: Agent):
        """Load and configure tools for the agent."""
        return self.tool_registry.get_tools_for_agent(agent.tools.all())
    
    def compile_agent(self, agent: Agent, graph_context=None):
        """Compile an agent into an executable form."""
        if agent.name in self.compiled_agents:
            return self.compiled_agents[agent.name]
        
        llm = self._create_llm_instance(agent)
        tools = self._load_agent_tools(agent)

        def agent_node(state: AgentState) -> AgentState:
            # SAFETY: Prevent infinite loops
            execution_count = state.context.get('execution_count', 0)
            
            print("\n" + "█"*80)
            print(f"█ AGENT EXECUTION #{execution_count + 1}")
            print(f"█ Agent: {agent.name}")
            print(f"█ Role: {agent.role}")
            print(f"█ Current Task: {state.current_task}")
            print(f"█ Is Complete: {state.is_complete}")
            print(f"█ Next Agent (before): {state.next_agent}")
            print("█"*80)
            
            if execution_count > 10:
                print("\n" + "🛑"*40)
                print("🛑 EMERGENCY STOP: Maximum execution count reached!")
                print(f"🛑 Execution count: {execution_count}")
                print(f"🛑 Last agent: {agent.name}")
                print(f"🛑 Current task: {state.current_task}")
                print(f"🛑 Agent outputs so far: {list(state.agent_outputs.keys())}")
                print("🛑"*40 + "\n")
                
                return AgentState(
                    messages=state.messages + [AIMessage(content="Maximum iterations reached. Stopping execution.")],
                    current_task=state.current_task,
                    context=state.context,
                    next_agent="FINISH",
                    is_complete=True,
                    supervisor_feedback="Maximum iterations reached",
                    task_queue=state.task_queue,
                    completed_tasks=state.completed_tasks,
                    agent_outputs=state.agent_outputs,
                    supervisor_decision={'next_agent': 'FINISH', 'is_complete': True, 'reasoning': 'Max iterations'}
                )
            
            # Build messages based on agent role
            if agent.role == Agent.AgentRole.SUPERVISOR and graph_context:
                available_agents = graph_context.get('available_agents', [])
                system_prompt = SupervisorPromptBuilder.build_supervisor_prompt(agent, available_agents)

                context_info = self._build_supervisor_context(state)
                
                print("\n" + "📋"*40)
                print("SUPERVISOR CONTEXT:")
                print("📋"*40)
                print(context_info)
                print("📋"*40 + "\n")
                
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=context_info)
                ] + state.messages[-3:]
            else:
                messages = [
                    SystemMessage(content=agent.system_instruction_prompt)
                ] + state.messages

                if state.current_task:
                    task_message = HumanMessage(content=f"Current Task Focus: {state.current_task}")
                    messages.append(task_message)

            print(f"\n🤖 Calling LLM for agent: {agent.name}...")
            
            # Handle tool calling loop
            if tools:
                print(f"   Tools available: {[t.name for t in tools]}")
                llm_with_tools = llm.bind_tools(tools)
                response = llm_with_tools.invoke(messages)
                
                all_messages = messages.copy()
                tool_call_count = 0
                while hasattr(response, 'tool_calls') and response.tool_calls:
                    tool_call_count += 1
                    print(f"\n   🔧 Tool call iteration #{tool_call_count}")
                    all_messages.append(response)
                    
                    tool_messages = []
                    for tool_call in response.tool_calls:
                        print(f"      Executing: {tool_call['name']} with args: {tool_call['args']}")
                        matching_tool = None
                        for tool in tools:
                            if tool.name == tool_call['name']:
                                matching_tool = tool
                                break
                        
                        if matching_tool:
                            try:
                                tool_result = matching_tool.invoke(tool_call['args'])
                                print(f"      ✅ Result: {str(tool_result)[:100]}...")
                                tool_messages.append(
                                    ToolMessage(
                                        content=str(tool_result),
                                        tool_call_id=tool_call['id']
                                    )
                                )
                            except Exception as e:
                                print(f"      ❌ Error: {str(e)}")
                                tool_messages.append(
                                    ToolMessage(
                                        content=f"Error executing tool: {str(e)}",
                                        tool_call_id=tool_call['id']
                                    )
                                )
                        else:
                            print(f"      ❌ Tool not found: {tool_call['name']}")
                            tool_messages.append(
                                ToolMessage(
                                    content=f"Tool {tool_call['name']} not found",
                                    tool_call_id=tool_call['id']
                                )
                            )
                    
                    all_messages.extend(tool_messages)
                    response = llm_with_tools.invoke(all_messages)
                
                final_messages = state.messages + [response]
            else:
                response = llm.invoke(messages)
                final_messages = state.messages + [response]

            print("\n" + "💬"*40)
            print(f"AGENT RESPONSE ({agent.name}):")
            print("💬"*40)
            print(response.content)
            print("💬"*40 + "\n")

            # Update execution count
            new_context = state.context.copy()
            new_context['execution_count'] = execution_count + 1

            # Create a new state with updated values
            new_state = AgentState(
                messages=final_messages,
                current_task=state.current_task,
                context=new_context,
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
                
                print("\n" + "🎯"*40)
                print("SUPERVISOR DECISION MADE:")
                print("🎯"*40)
                print(f"   Next Agent: {new_state.next_agent}")
                print(f"   Is Complete: {new_state.is_complete}")
                print(f"   Full Decision: {new_state.supervisor_decision}")
                print("🎯"*40 + "\n")
            else:
                if state.current_task and state.current_task not in new_state.completed_tasks:
                    new_state.completed_tasks.append(state.current_task)
                    print(f"✅ Task completed: {state.current_task}")
            
            print("█"*80)
            print(f"█ FINISHED: {agent.name}")
            print(f"█ Next Agent (after): {new_state.next_agent}")
            print(f"█ Is Complete (after): {new_state.is_complete}")
            print("█"*80 + "\n")
            
            return new_state
        
        self.compiled_agents[agent.name] = agent_node
        return agent_node
            
    def _build_supervisor_context(self, state: AgentState) -> str:
        """Build context information for the supervisor agent."""
        context_parts = []
        
        # Show the original user request
        if state.current_task:
            context_parts.append(f"**User Request**: {state.current_task}")
        
        # Show what's been done so far
        if state.agent_outputs:
            context_parts.append("\n**Work Completed So Far**:")
            for agent_name, output in state.agent_outputs.items():
                if output['agent_role'] != 'supervisor':
                    context_parts.append(f"- {agent_name}: {output['response'][:150]}...")
        
        if state.completed_tasks:
            context_parts.append(f"\nCompleted Tasks: {', '.join(state.completed_tasks)}")
        
        return "\n".join(context_parts)
    
    def _handle_supervisor_logic(self, state: AgentState, agent: Agent) -> AgentState:
        """Handle supervisor-specific routing logic"""
        response_content = state.messages[-1].content
        
        print("\n" + "🔍"*40)
        print("PARSING SUPERVISOR DECISION")
        print("🔍"*40)
        print(f"Response length: {len(response_content)} chars")
        print(f"Looking for <decision> block...")
        
        # Parse supervisor decision
        supervisor_decision = self._parse_supervisor_decision(response_content, agent)
        
        print(f"\n✅ Parsed decision:")
        print(f"   - next_agent: {supervisor_decision.get('next_agent')}")
        print(f"   - is_complete: {supervisor_decision.get('is_complete')}")
        print(f"   - reasoning: {supervisor_decision.get('reasoning', 'N/A')}")
        print("🔍"*40 + "\n")
        
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
        
        if supervisor_decision.get('new_tasks'):
            new_state.task_queue.extend(supervisor_decision['new_tasks'])
        
        return new_state
    
    def _parse_supervisor_decision(self, response_content: str, agent: Agent) -> Dict[str, Any]:
        """Parse supervisor response to extract routing decisions"""
        # Look for decision block
        decision_match = re.search(r'<decision>(.*?)</decision>', response_content, re.DOTALL | re.IGNORECASE)
        if decision_match:
            print("   ✅ Found <decision> block")
            decision_text = decision_match.group(1)
            print(f"   Decision text: {decision_text}")
            parsed = self._parse_decision_text(decision_text)
            return parsed
        else:
            print("   ⚠️  No <decision> block found!")
        
        # Look for JSON decision block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_content, re.DOTALL)
        if json_match:
            print("   ✅ Found JSON block")
            try:
                parsed = json.loads(json_match.group(1))
                print(f"   Parsed JSON: {parsed}")
                return parsed
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON parse error: {e}")
        
        # Fallback to keyword-based parsing
        print("   ⚠️  Falling back to keyword parsing")
        return self._parse_keywords_decision(response_content, agent)
    
    def _parse_decision_text(self, decision_text: str) -> Dict[str, Any]:
        """Parse decision text for routing information"""
        decision = {}
        
        # Extract next agent
        next_agent_match = re.search(r'next_agent:\s*(.+?)(?:\n|$)', decision_text, re.IGNORECASE)
        if next_agent_match:
            decision['next_agent'] = next_agent_match.group(1).strip()
            print(f"      Extracted next_agent: {decision['next_agent']}")
        else:
            print("      ⚠️  Could not extract next_agent")
        
        # Check for completion
        is_complete_match = re.search(r'is_complete:\s*(true|false)', decision_text, re.IGNORECASE)
        if is_complete_match:
            decision['is_complete'] = is_complete_match.group(1).lower() == 'true'
            print(f"      Extracted is_complete: {decision['is_complete']}")
        else:
            print("      ⚠️  Could not extract is_complete")
        
        # Extract reasoning
        reason_match = re.search(r'reasoning:\s*(.+?)(?:\n|$)', decision_text, re.IGNORECASE | re.DOTALL)
        if reason_match:
            decision['reasoning'] = reason_match.group(1).strip()
            print(f"      Extracted reasoning: {decision['reasoning'][:50]}...")
        
        return decision
    
    def _parse_keywords_decision(self, content: str, agent: Agent) -> Dict[str, Any]:
        """Fallback keyword-based decision parsing"""
        print("   🔎 Using keyword-based parsing...")
        content_lower = content.lower()
        
        # Get available agents from the project
        available_agents = list(agent.project.agents.exclude(
            id=agent.id
        ).values_list('name', flat=True))
        
        print(f"   Available agents to check: {available_agents}")
        
        # Look for agent names mentioned
        for agent_name in available_agents:
            if agent_name.lower() in content_lower:
                print(f"   ✅ Found agent name '{agent_name}' in response")
                return {
                    'next_agent': agent_name,
                    'is_complete': False,
                    'reasoning': 'Keyword match in supervisor response'
                }
        
        # Check for completion keywords
        completion_keywords = ['complete', 'finished', 'done', 'end', 'final']
        found_keywords = [kw for kw in completion_keywords if kw in content_lower]
        if found_keywords:
            print(f"   ✅ Found completion keywords: {found_keywords}")
            return {'next_agent': 'FINISH', 'is_complete': True, 'reasoning': 'Completion keyword detected'}
        
        # Default: FINISH to prevent loops
        print("   ⚠️  No clear routing found, defaulting to FINISH")
        return {'next_agent': 'FINISH', 'is_complete': True, 'reasoning': 'No clear routing found, defaulting to finish'}