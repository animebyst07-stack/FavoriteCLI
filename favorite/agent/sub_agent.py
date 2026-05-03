import json
from pathlib import Path
from typing import Optional
from .roles import AgentRole, SubAgent
from .llm import call_llm
from .tags import extract_tags, strip_tags
from .response_processor import strip_thinking_blocks

def run_sub_agent(role_id: str, task: str, cfg) -> str:
    """
    Spawns a sub-agent with a specific role, runs a task, and returns the result.
    This runs in the same process but with a specialized system prompt.
    """
    roles_file = Path(__file__).resolve().parent.parent / "agent" / "sub_roles_library.json"
    if not roles_file.exists():
        return f"ERROR: sub_roles_library.json not found at {roles_file}"
    
    try:
        roles_text = roles_file.read_text(encoding="utf-8")
        roles = json.loads(roles_text)
    except Exception as e:
        return f"ERROR: Failed to load roles library: {e}"
    
    role_dict = next((r for r in roles if r['id'] == role_id), None)
    if not role_dict:
        return f"ERROR: Role '{role_id}' not found in library"
    
    role = AgentRole(
        id=role_dict['id'],
        name=role_dict['name'],
        description=role_dict['description'],
        system_prompt=role_dict['system_prompt'],
        priority=role_dict.get('priority', 99),
        tags=role_dict.get('tags', [])
    )
    
    # We use the default model and keys for now, but with the sub-agent's system prompt
    messages = [
        {"role": "system", "content": role.system_prompt},
        {"role": "user", "content": task}
    ]
    
    try:
        # Non-streaming for sub-agents to keep it simple and return a single block of text
        response = call_llm(messages, cfg)
        # Clean up any tags or thinking blocks that might leak
        clean_response = strip_tags(strip_thinking_blocks(response))
        return clean_response.strip()
    except Exception as e:
        return f"ERROR: Sub-agent execution failed: {e}"
