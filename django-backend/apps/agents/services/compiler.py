import logging
import json
import re
from datetime import datetime
from typing import Dict, Any, List
from django.conf import settings
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import (
    BaseMessage, HumanMessage, SystemMessage, ToolMessage, AIMessage
)

from ..models import Agent
from .agent_state import AgentState
from ...tools.models import Tool

logger = logging.getLogger(__name__)


def _hydrate_messages(messages: List[Any]) -> List[BaseMessage]:
    """Converts a list of dicts/BaseModels back into LangChain message objects."""
    hydrated = []
    if not messages:
        return []

    for msg in messages:
        # Check if it's already a properly typed message (not just BaseMessage)
        if isinstance(msg, (HumanMessage, AIMessage, SystemMessage, ToolMessage)):
            hydrated.append(msg)
            continue

        # If it's a generic BaseMessage or has type attribute, convert it
        if isinstance(msg, BaseMessage):
            # Get the type attribute
            msg_type = getattr(msg, 'type', None)
            content = msg.content
            additional_kwargs = getattr(msg, 'additional_kwargs', {})

            if msg_type == 'human':
                hydrated.append(HumanMessage(content=content, additional_kwargs=additional_kwargs))
            elif msg_type == 'ai':
                hydrated.append(AIMessage(content=content, additional_kwargs=additional_kwargs))
            elif msg_type == 'tool':
                tool_call_id = getattr(msg, 'tool_call_id', '')
                hydrated.append(ToolMessage(content=content, tool_call_id=tool_call_id, additional_kwargs=additional_kwargs))
            elif msg_type == 'system':
                hydrated.append(SystemMessage(content=content, additional_kwargs=additional_kwargs))
            else:
                # Fallback: try to keep it as is
                hydrated.append(msg)
            continue

        if hasattr(msg, 'model_dump'):
            msg_dict = msg.model_dump()
        elif isinstance(msg, dict):
            msg_dict = msg
        else:
            hydrated.append(HumanMessage(content=str(msg)))
            continue

        msg_type = msg_dict.get('type')

        # Extract only the fields that the message constructors accept
        content = msg_dict.get('content', '')
        additional_kwargs = msg_dict.get('additional_kwargs', {})

        if msg_type == 'human':
            hydrated.append(HumanMessage(content=content, additional_kwargs=additional_kwargs))
        elif msg_type == 'ai':
            hydrated.append(AIMessage(content=content, additional_kwargs=additional_kwargs))
        elif msg_type == 'tool':
            tool_call_id = msg_dict.get('tool_call_id', '')
            hydrated.append(ToolMessage(content=content, tool_call_id=tool_call_id, additional_kwargs=additional_kwargs))
        elif msg_type == 'system':
            hydrated.append(SystemMessage(content=content, additional_kwargs=additional_kwargs))
        else:
            hydrated.append(HumanMessage(content=str(content)))

    return hydrated


def _convert_messages_to_google_format(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    Convert messages to Google-compatible format.
    Google doesn't support SystemMessage, so we merge system messages into human messages.
    Also ensures all messages are properly formatted.
    """
    converted = []
    pending_system_content = []
    
    for msg in messages:
        if isinstance(msg, SystemMessage):
            # Collect system messages to prepend to next human message
            pending_system_content.append(msg.content)
        elif isinstance(msg, HumanMessage):
            # Merge any pending system content with this human message
            if pending_system_content:
                combined_content = "\n\n".join(pending_system_content) + "\n\n" + msg.content
                pending_system_content = []
                converted.append(HumanMessage(content=combined_content))
            else:
                converted.append(HumanMessage(content=msg.content))
        elif isinstance(msg, AIMessage):
            # Extract just the text content from AI messages
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            converted.append(AIMessage(content=content))
        elif isinstance(msg, ToolMessage):
            # Convert tool messages to human messages for Google
            converted.append(HumanMessage(content=f"[Tool Result]: {msg.content}"))
        else:
            # Fallback: convert unknown types to human messages
            content = msg.content if hasattr(msg, 'content') else str(msg)
            converted.append(HumanMessage(content=str(content)))
    
    # If there are leftover system messages, add them as a human message
    if pending_system_content:
        converted.append(HumanMessage(content="\n\n".join(pending_system_content)))
    
    return converted


class SupervisorPromptBuilder:
    """Builds the prompt for the supervisor agent based on the state of other agents."""
    
    @staticmethod
    def build_supervisor_prompt(
        agent: Agent, 
        available_agents: list[Agent],
        available_tools: list[Tool]
    ) -> str:
        
        # Format Agents
        agent_descriptions = []
        agent_names = []
        for a in available_agents:
            agent_descriptions.append(f"- {a.name}: {a.description}")
            agent_names.append(a.name)
        agent_list = "\n".join(agent_descriptions)
        agent_names_str = ", ".join(agent_names)
        
        # Format Tools
        tool_descriptions = []
        tool_names = []
        for t in available_tools:
            tool_descriptions.append(f"- {t.name}: {t.effective_description}")
            tool_names.append(t.name)
        tool_list = "\n".join(tool_descriptions)
        tool_names_str = ", ".join(tool_names)
        
        all_node_names = agent_names + tool_names
        all_node_names_str = ", ".join(all_node_names)
        if not all_node_names_str:
            all_node_names_str = "FINISH"

        supervisor_prompt = f"""
You are a supervisor agent coordinating tasks between a team of agents and tools.
**CRITICAL: Your *entire* response MUST end with a <decision> block.** No text should follow it.
{agent.system_instruction_prompt} 

Available Agents (Workers):
{agent_list if agent_list else '- None'}

Available Tools:
{tool_list if tool_list else '- None'}

**IMPORTANT**: When routing, you MUST choose EXACTLY one name from this list or use FINISH: {all_node_names_str}
Your Responsibilities:
1. Analyze the user's request and the work completed so far.
2. Choose the SINGLE BEST agent or tool to handle the next step.
3. If the request is fully satisfied, use FINISH.
4. **DO NOT** make up names - only use: {all_node_names_str}

Decision Format (REQUIRED AT THE VERY END):
<decision>
next_agent: [exact_agent_or_tool_name | FINISH]
is_complete: [true | false]
task: [optional: specific input/task for the next agent/tool]
reasoning: [brief explanation]
</decision>

**CRITICAL**: 
- Always include the <decision> block at the very end
- Use exact agent/tool names: {all_node_names_str}
- **ACCURACY**: Copy email addresses, names, and IDs *exactly* from the user request. Do not alter them.
- **CHECK CONTEXT**: If the 'LAST TOOL OUTPUT' indicates success for a task, DO NOT repeat it. Move to the next step or FINISH.
"""
        print("\n" + "="*80)
        print("SUPERVISOR PROMPT BUILT")
        print("="*80)
        print(f"Available agents: {agent_names_str}")
        print(f"Available tools: {tool_names_str}")
        print("="*80 + "\n")
        return supervisor_prompt


class AgentCompiler:
    """Compiles and manages the execution of agents in a multi-agent system."""

    def __init__(self):
        self.compiled_agents: Dict[str, Agent] = {}
        from ...tools.registry import ToolRegistry
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
                temperature=0
            )
        else:
            raise NotImplementedError(f"Provider {agent.provider} is not supported yet.")
        
    def _load_agent_tools(self, agent: Agent, user=None):
        """Load and configure tools for the agent."""
        all_tools = []

        # Load regular tools
        if agent.tools.exists():
            regular_tools = self.tool_registry.get_tools_for_agent(
                agent.tools.all(),
                user=user
            )
            all_tools.extend(regular_tools)
            logger.info(f"Loaded {len(regular_tools)} regular tools for agent {agent.name}")

        # Load MCP server tools
        if agent.mcp.exists():
            mcp_tools = self.tool_registry.get_mcp_tools(agent.mcp.all())
            all_tools.extend(mcp_tools)
            logger.info(f"Loaded {len(mcp_tools)} MCP tools for agent {agent.name}")

        return all_tools
    
    def compile_agent(self, agent: Agent, graph_context=None, max_executions=50):
        """Compile an agent into an executable form."""
        if agent.name in self.compiled_agents:
            return self.compiled_agents[agent.name]

        llm = self._create_llm_instance(agent)

        # Load tools for this agent (will be passed via state)
        # Tools are loaded at runtime in the agent_node to access user context
        agent_tools = []

        def agent_node(state: AgentState) -> AgentState:
            # Track agent-specific execution count
            agent_exec_key = f'agent_exec_count_{agent.name}'
            total_exec_count = state.context.get('execution_count', 0)
            agent_exec_count = state.context.get(agent_exec_key, 0)
            
            print("\n" + "█"*80)
            print(f"█ AGENT EXECUTION #{total_exec_count + 1}")
            print(f"█ Agent: {agent.name} (executed {agent_exec_count} times)")
            print(f"█ Role: {agent.role}")
            print("█"*80)
            
            # Check total execution limit
            if total_exec_count >= max_executions:
                print("\n" + "🛑"*40)
                print(f"🛑 EMERGENCY STOP: Maximum total executions reached ({max_executions})!")
                print("🛑"*40 + "\n")
                
                return AgentState(
                    messages=state.messages + [AIMessage(content=f"Maximum iterations ({max_executions}) reached. Stopping execution.")],
                    current_task=state.current_task,
                    context=state.context,
                    user=state.user,
                    next_agent="FINISH",
                    is_complete=True,
                    supervisor_feedback=f"Maximum iterations ({max_executions}) reached",
                    task_queue=state.task_queue,
                    completed_tasks=state.completed_tasks,
                    agent_outputs=state.agent_outputs,
                    supervisor_decision={'next_agent': 'FINISH', 'is_complete': True, 'reasoning': 'Max iterations'}
                )
            
            # Check agent-specific execution limit (prevent loops on same agent)
            if agent_exec_count >= 5:
                print("\n" + "🛑"*40)
                print(f"🛑 LOOP DETECTED: Agent '{agent.name}' has executed {agent_exec_count} times!")
                print("🛑"*40 + "\n")
                
                return AgentState(
                    messages=state.messages + [AIMessage(content=f"Loop detected: Agent '{agent.name}' executed too many times. Stopping.")],
                    current_task=state.current_task,
                    context=state.context,
                    user=state.user,
                    next_agent="FINISH",
                    is_complete=True,
                    supervisor_feedback=f"Loop detected on agent '{agent.name}'",
                    task_queue=state.task_queue,
                    completed_tasks=state.completed_tasks,
                    agent_outputs=state.agent_outputs,
                    supervisor_decision={'next_agent': 'FINISH', 'is_complete': True, 'reasoning': f'Loop detected on {agent.name}'}
                )
            
            # Hydrate messages
            hydrated_messages = _hydrate_messages(state.messages)
            
            # Build messages based on provider and role
            messages = []
            
            if agent.provider == 'google':
                # GOOGLE PROVIDER - No SystemMessage support
                if agent.role == Agent.AgentRole.SUPERVISOR and graph_context:
                    available_agents = graph_context.get('available_agents', [])
                    available_tools = graph_context.get('available_tools', [])
                    system_prompt = SupervisorPromptBuilder.build_supervisor_prompt(
                        agent, available_agents, available_tools
                    )
                    context_info = self._build_supervisor_context(state, hydrated_messages)
                    
                    # Get the history without the first message (which is the original user request)
                    history = hydrated_messages[1:] if len(hydrated_messages) > 1 else []
                    
                    # Convert history to Google-compatible format
                    converted_history = _convert_messages_to_google_format(history)
                    
                    # Combine system prompt + context into first human message
                    full_human_prompt = f"{system_prompt}\n\n{context_info}"
                    messages = [HumanMessage(content=full_human_prompt)] + converted_history
                
                else:
                    # For general Google agents - include tool information if available
                    system_prompt = agent.system_instruction_prompt
                    
                    # Add tool awareness if tools are available
                    available_tools = graph_context.get('available_tools', []) if graph_context else []
                    if available_tools:
                        tool_info = "\n\n**Available Tools You Can Reference:**\n"
                        for t in available_tools:
                            tool_info += f"- {t.name}: {t.effective_description}\n"
                        system_prompt = system_prompt + tool_info
                    
                    first_human_message_content = hydrated_messages[0].content if hydrated_messages else ""
                    
                    # Inject current_task if it differs from the original request
                    current_task_info = ""
                    if state.current_task and state.current_task != first_human_message_content:
                        current_task_info = f"\n\n**Current Task**: {state.current_task}"
                    
                    full_human_prompt = f"{system_prompt}\n\nUser Request: {first_human_message_content}{current_task_info}"
                    
                    # Get history and convert to Google format
                    history = hydrated_messages[1:] if len(hydrated_messages) > 1 else []
                    
                    # CLEAN HISTORY: Remove <decision> blocks to prevent confusion/hallucination
                    cleaned_history = []
                    for msg in history:
                        content = msg.content if hasattr(msg, 'content') else str(msg)
                        # Remove <decision>...</decision> blocks
                        content = re.sub(r'<decision>.*?</decision>', '[Routing Decision Made]', content, flags=re.DOTALL | re.IGNORECASE)
                        if isinstance(msg, HumanMessage):
                            cleaned_history.append(HumanMessage(content=content))
                        elif isinstance(msg, AIMessage):
                            cleaned_history.append(AIMessage(content=content))
                        else:
                            cleaned_history.append(msg)

                    converted_history = _convert_messages_to_google_format(cleaned_history)
                    
                    messages = [HumanMessage(content=full_human_prompt)] + converted_history
            
            else:
                # OPENAI PROVIDER - SystemMessage supported
                if agent.role == Agent.AgentRole.SUPERVISOR and graph_context:
                    available_agents = graph_context.get('available_agents', [])
                    available_tools = graph_context.get('available_tools', [])
                    system_prompt = SupervisorPromptBuilder.build_supervisor_prompt(
                        agent, available_agents, available_tools
                    )
                    context_info = self._build_supervisor_context(state, hydrated_messages)
                    history = hydrated_messages[1:]
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=context_info),
                    ] + history
                else:
                    messages = [
                        SystemMessage(content=agent.system_instruction_prompt)
                    ] + hydrated_messages

            # Load tools for this agent (with user context)
            user = state.user if isinstance(state, BaseModel) else state.get('user')
            tools = self._load_agent_tools(agent, user=user)

            # Bind tools to LLM if available
            llm_with_tools = llm.bind_tools(tools) if tools else llm

            print(f"\n🤖 Calling LLM for agent: {agent.name}...")
            print(f"📝 Message count: {len(messages)}")
            print(f"📝 Message types: {[type(m).__name__ for m in messages]}")
            
            try:
                response = llm.invoke(messages)
                final_messages = hydrated_messages + [response]
                response_content = response.content

            except Exception as e:
                logger.error(f"❌ LLM call for agent '{agent.name}' FAILED: {e}")
                error_message = f"LLM call failed for {agent.name}: {e}"
                
                new_state_dict = state.model_dump() if isinstance(state, BaseModel) else state.copy()
                new_state_dict['messages'] = hydrated_messages + [AIMessage(content=error_message)]
                
                if 'agent_outputs' not in new_state_dict:
                    new_state_dict['agent_outputs'] = {}
                new_state_dict['agent_outputs'][agent.name] = {
                    'response': error_message,
                    'timestamp': str(datetime.now()),
                    'agent_role': agent.role,
                    'agent_id': agent.id,
                    'error': True
                }

                if agent.role == Agent.AgentRole.SUPERVISOR:
                    new_state_dict['next_agent'] = "FINISH"
                    new_state_dict['is_complete'] = True
                    new_state_dict['supervisor_decision'] = {
                        'next_agent': 'FINISH', 
                        'is_complete': True, 
                        'reasoning': f'LLM call failed: {e}'
                    }
                
                return AgentState(**new_state_dict)

            print("\n" + "💬"*40)
            print(f"AGENT RESPONSE ({agent.name}):")
            print("💬"*40)
            print(response_content)
            print("💬"*40 + "\n")

            new_context = state.context.copy()
            new_context['execution_count'] = total_exec_count + 1
            new_context[agent_exec_key] = agent_exec_count + 1

            new_state = AgentState(
                messages=final_messages,
                current_task=state.current_task,
                context=new_context,
                user=state.user, 
                next_agent=state.next_agent,
                is_complete=state.is_complete,
                supervisor_feedback=state.supervisor_feedback,
                task_queue=state.task_queue.copy(),
                completed_tasks=state.completed_tasks.copy(),
                agent_outputs={
                    **state.agent_outputs,
                    agent.name: {
                        'response': response_content, 
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
                print("🎯"*40 + "\n")
            else:
                if state.current_task and state.current_task not in state.completed_tasks:
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
            
    def _build_supervisor_context(self, state: AgentState, hydrated_messages: List[BaseMessage]) -> str:
        """Build context information for the supervisor agent."""
        context_parts = []
        
        if hydrated_messages and isinstance(hydrated_messages[0], HumanMessage):
             context_parts.append(f"**Original User Request**: {hydrated_messages[0].content}")
        
        agent_outputs = state.agent_outputs if isinstance(state, BaseModel) else state.get('agent_outputs', {})
        if agent_outputs:
            context_parts.append("\n**Work Completed So Far**:")
            for agent_name, output in agent_outputs.items():
                if output.get('agent_role') != 'supervisor':
                    context_parts.append(f"- {agent_name}: {output['response'][:150]}...")
        
        completed_tasks = state.completed_tasks if isinstance(state, BaseModel) else state.get('completed_tasks', [])
        if completed_tasks:
            context_parts.append(f"\nCompleted Tasks: {', '.join(completed_tasks)}")
            
        # Add current task/tool output to the context
        current_task = state.current_task if isinstance(state, BaseModel) else state.get('current_task')
        if current_task:
            # Avoid duplicating if it's the same as the original request
            original_request = hydrated_messages[0].content if hydrated_messages and isinstance(hydrated_messages[0], HumanMessage) else ""
            if current_task != original_request:
                context_parts.append(f"\n**LAST TOOL OUTPUT**:\n{current_task}")
        
        return "\n".join(context_parts)
    
    def _handle_supervisor_logic(self, state: AgentState, agent: Agent) -> AgentState:
        """Handle supervisor-specific routing logic"""
        response_content = state.messages[-1].content
        
        # Handle case where content is a list (e.g. from some LLM providers or if it contains multiple blocks)
        if isinstance(response_content, list):
            response_content = " ".join([str(item) for item in response_content])
        elif not isinstance(response_content, str):
            response_content = str(response_content)
        
        print("\n" + "🔍"*40)
        print("PARSING SUPERVISOR DECISION")
        print("🔍"*40)
        
        supervisor_decision = self._parse_supervisor_decision(response_content, agent)
        
        print(f"\n✅ Parsed decision:")
        print(f"   - next_agent: {supervisor_decision.get('next_agent')}")
        print(f"   - is_complete: {supervisor_decision.get('is_complete')}")
        print(f"   - reasoning: {supervisor_decision.get('reasoning', 'N/A')}")
        print("🔍"*40 + "\n")
        
        new_state_dict = state.model_dump()
        new_state_dict['next_agent'] = supervisor_decision.get('next_agent')
        new_state_dict['is_complete'] = supervisor_decision.get('is_complete', False)
        new_state_dict['supervisor_decision'] = supervisor_decision
        
        # Update current_task if provided by supervisor
        if supervisor_decision.get('task'):
            new_state_dict['current_task'] = supervisor_decision.get('task')
        
        return AgentState(**new_state_dict)
    
    def _parse_supervisor_decision(self, response_content: str, agent: Agent) -> Dict[str, Any]:
        """Parse supervisor response to extract routing decisions"""
        decision_match = re.search(r'<decision>(.*?)</decision>', response_content, re.DOTALL | re.IGNORECASE)
        
        if decision_match:
            print("   ✅ Found <decision> block")
            decision_text = decision_match.group(1)
            parsed = self._parse_decision_text(decision_text)
            return parsed
        else:
            print("   ⚠️  No <decision> block found!")
        
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_content, re.DOTALL)
        if json_match:
            print("   ✅ Found JSON block")
            try:
                parsed = json.loads(json_match.group(1))
                return parsed
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON parse error: {e}")
        
        print("   ⚠️  No valid decision block found. Defaulting to FINISH.")
        return {'next_agent': 'FINISH', 'is_complete': True, 'reasoning': 'No valid decision block found'}
    
    def _parse_decision_text(self, decision_text: str) -> Dict[str, Any]:
        """Parse decision text for routing information"""
        decision = {}

        next_agent_match = re.search(r'next_agent:\s*(.+?)(?:\n|$)', decision_text, re.IGNORECASE)
        if next_agent_match:
            # Strip whitespace and remove brackets if present
            agent_name = next_agent_match.group(1).strip()
            agent_name = agent_name.strip('[]')  # Remove [ and ] if LLM included them
            decision['next_agent'] = agent_name

        is_complete_match = re.search(r'is_complete:\s*(true|false)', decision_text, re.IGNORECASE)
        if is_complete_match:
            decision['is_complete'] = is_complete_match.group(1).lower() == 'true'

        reason_match = re.search(r'reasoning:\s*(.+?)(?:\n|$)', decision_text, re.IGNORECASE | re.DOTALL)
        if reason_match:
            decision['reasoning'] = reason_match.group(1).strip()
        
        return decision