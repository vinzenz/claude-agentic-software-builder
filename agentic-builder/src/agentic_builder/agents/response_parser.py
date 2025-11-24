"""Parse agent XML responses."""

import re
from dataclasses import dataclass, field


@dataclass
class AgentResponse:
    """Parsed agent response."""

    success: bool
    summary: str
    key_decisions: list[str] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)
    next_tasks: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    raw_xml: str = ""


def extract_tag_content(xml: str, tag: str) -> str | None:
    """Extract content from an XML tag.

    Args:
        xml: XML string to search
        tag: Tag name to extract

    Returns:
        Tag content or None if not found
    """
    pattern = rf"<{tag}[^>]*>(.*?)</{tag}>"
    match = re.search(pattern, xml, re.DOTALL)
    if match:
        content = match.group(1).strip()
        # Handle CDATA sections
        if content.startswith("<![CDATA[") and content.endswith("]]>"):
            content = content[9:-3]  # Remove <![CDATA[ and ]]>
        return content
    return None


def extract_list_items(xml: str, container_tag: str, item_tag: str) -> list[str]:
    """Extract list of items from XML.

    Args:
        xml: XML string to search
        container_tag: Container element tag
        item_tag: Item element tag

    Returns:
        List of extracted item contents
    """
    container = extract_tag_content(xml, container_tag)
    if not container:
        return []
    pattern = rf"<{item_tag}[^>]*>(.*?)</{item_tag}>"
    matches = re.findall(pattern, container, re.DOTALL)
    return [m.strip() for m in matches]


def parse_response(xml: str) -> AgentResponse:
    """Parse agent XML response into structured data.

    Args:
        xml: Raw XML response from agent

    Returns:
        Parsed AgentResponse object
    """
    # Find task_output block
    output_xml = extract_tag_content(xml, "task_output")
    if not output_xml:
        # Try to find it in the raw response
        if "<task_output>" in xml:
            start = xml.index("<task_output>")
            end = xml.index("</task_output>") + len("</task_output>")
            output_xml = xml[start:end]
        else:
            return AgentResponse(
                success=False,
                summary="Failed to parse response - no task_output found",
                raw_xml=xml,
            )

    # Extract fields
    success_str = extract_tag_content(output_xml, "success")
    success = success_str.lower() == "true" if success_str else False

    summary = extract_tag_content(output_xml, "summary") or ""
    key_decisions = extract_list_items(output_xml, "key_decisions", "decision")
    warnings = extract_list_items(output_xml, "warnings", "warning")

    # Parse artifacts
    artifacts = []
    artifacts_xml = extract_tag_content(output_xml, "artifacts")
    if artifacts_xml:
        artifact_pattern = (
            r'<artifact\s+type="([^"]+)"\s+name="([^"]+)"[^>]*>(.*?)</artifact>'
        )
        for match in re.finditer(artifact_pattern, artifacts_xml, re.DOTALL):
            art_type, art_name, art_content = match.groups()
            description = extract_tag_content(art_content, "description") or ""
            content = extract_tag_content(art_content, "content") or ""
            artifacts.append(
                {
                    "type": art_type,
                    "name": art_name,
                    "description": description,
                    "content": content,
                }
            )

    # Parse next_tasks
    next_tasks = []
    tasks_xml = extract_tag_content(output_xml, "next_tasks")
    if tasks_xml:
        task_pattern = r'<task\s+agent="([^"]+)"\s+priority="([^"]+)"[^>]*>(.*?)</task>'
        for match in re.finditer(task_pattern, tasks_xml, re.DOTALL):
            agent, priority, task_content = match.groups()
            title = extract_tag_content(task_content, "title") or ""
            description = extract_tag_content(task_content, "description") or ""
            criteria = extract_list_items(
                task_content, "acceptance_criteria", "criterion"
            )
            next_tasks.append(
                {
                    "agent_type": agent,
                    "priority": priority,
                    "title": title,
                    "description": description,
                    "acceptance_criteria": criteria,
                }
            )

    return AgentResponse(
        success=success,
        summary=summary,
        key_decisions=key_decisions,
        artifacts=artifacts,
        next_tasks=next_tasks,
        warnings=warnings,
        raw_xml=xml,
    )
