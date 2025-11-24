"""Agent execution logic."""

from datetime import datetime

from agentic_builder.agents.prompt_loader import load_prompt
from agentic_builder.agents.registry import get_model_for_agent
from agentic_builder.agents.response_parser import AgentResponse, parse_response
from agentic_builder.api.claude_cli import ClaudeCLI
from agentic_builder.context.budget import record_usage
from agentic_builder.core.constants import AgentType, ModelTier, TaskStatus
from agentic_builder.storage import tasks as task_storage

# Model aliases for Claude Code CLI
MODEL_ALIASES = {
    ModelTier.HAIKU: "haiku",
    ModelTier.SONNET: "sonnet",
    ModelTier.OPUS: "opus",
}


async def execute_agent(
    task_id: str,
    agent_type: AgentType,
    workflow_run_id: str,
    context_xml: str,
) -> AgentResponse:
    """Execute an agent for a task using Claude Code CLI in headless mode.

    Args:
        task_id: Task identifier
        agent_type: Type of agent to execute
        workflow_run_id: Parent workflow ID
        context_xml: XML context for the task

    Returns:
        Parsed AgentResponse

    Raises:
        AgentExecutionError: If execution fails
    """
    # Update task status
    task_storage.update_task_status(task_id, TaskStatus.RUNNING)

    try:
        # Load prompt
        system_prompt = load_prompt(agent_type)

        # Get model alias
        model_tier = get_model_for_agent(agent_type)
        model_alias = MODEL_ALIASES[model_tier]

        # Build user message
        user_message = f"""Please complete the following task.

{context_xml}

Respond with your output in the XML format specified in your system prompt."""

        # Call Claude CLI in headless mode
        cli = ClaudeCLI()
        start_time = datetime.utcnow()

        result = await cli.execute(
            prompt=user_message,
            system_prompt=system_prompt,
            model=model_alias,
            max_turns=1,  # Single turn for agent execution
        )

        execution_time = int(
            (datetime.utcnow() - start_time).total_seconds() * 1000
        )

        # Extract token usage from CLI response
        input_tokens = result.get("input_tokens", 0)
        output_tokens = result.get("output_tokens", 0)

        # Record token usage
        record_usage(
            workflow_run_id=workflow_run_id,
            task_id=task_id,
            agent_type=agent_type.value,
            model=model_alias,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        # Parse response
        response_text = result.get("result", "")
        parsed = parse_response(response_text)

        # Save output
        task_storage.save_task_output(
            task_id=task_id,
            output_xml=response_text,
            summary=parsed.summary,
            key_decisions=parsed.key_decisions,
            artifacts=parsed.artifacts,
            tokens_used=input_tokens + output_tokens,
            model_used=model_alias,
        )

        # Update task status
        if parsed.success:
            task_storage.update_task_status(task_id, TaskStatus.COMPLETED)
        else:
            task_storage.update_task_status(
                task_id, TaskStatus.FAILED, error_message=parsed.summary
            )

        return parsed

    except Exception as e:
        task_storage.update_task_status(
            task_id, TaskStatus.FAILED, error_message=str(e)
        )
        raise
