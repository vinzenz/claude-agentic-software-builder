"""XML context serialization for agent communication."""

import xml.etree.ElementTree as ET


def escape_xml(text: str) -> str:
    """Escape XML special characters.

    Args:
        text: Text to escape

    Returns:
        XML-safe text
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def dict_to_xml(data: dict, root_tag: str = "data") -> str:
    """Convert dictionary to XML string.

    Args:
        data: Dictionary to convert
        root_tag: Root element tag name

    Returns:
        XML string representation
    """
    root = ET.Element(root_tag)
    _add_dict_to_element(root, data)
    return ET.tostring(root, encoding="unicode")


def _add_dict_to_element(parent: ET.Element, data: dict) -> None:
    """Recursively add dictionary to XML element.

    Args:
        parent: Parent XML element
        data: Dictionary to add
    """
    for key, value in data.items():
        tag = key.replace(" ", "_").replace("-", "_")
        if isinstance(value, dict):
            child = ET.SubElement(parent, tag)
            _add_dict_to_element(child, value)
        elif isinstance(value, list):
            child = ET.SubElement(parent, tag)
            for item in value:
                if isinstance(item, dict):
                    item_elem = ET.SubElement(child, "item")
                    _add_dict_to_element(item_elem, item)
                else:
                    item_elem = ET.SubElement(child, "item")
                    item_elem.text = str(item)
        elif value is not None:
            child = ET.SubElement(parent, tag)
            child.text = str(value)


def build_task_context(
    task_id: str,
    agent_type: str,
    workflow_id: str,
    summary: str,
    requirements: list[str],
    constraints: list[str],
    dependencies: list[dict],
    artifacts: list[dict],
    acceptance_criteria: list[str],
) -> str:
    """Build the XML context for a task.

    Args:
        task_id: Unique task identifier
        agent_type: Agent type executing the task
        workflow_id: Parent workflow ID
        summary: Task summary/description
        requirements: List of requirements
        constraints: List of constraints
        dependencies: List of dependency outputs
        artifacts: List of existing artifacts
        acceptance_criteria: List of acceptance criteria

    Returns:
        XML context string
    """
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append("<task_input>")

    # Meta section
    lines.append("  <meta>")
    lines.append(f"    <task_id>{escape_xml(task_id)}</task_id>")
    lines.append(f"    <agent_type>{escape_xml(agent_type)}</agent_type>")
    lines.append(f"    <workflow_id>{escape_xml(workflow_id)}</workflow_id>")
    lines.append("  </meta>")

    # Summary
    lines.append(f"  <summary>{escape_xml(summary)}</summary>")

    # Requirements
    if requirements:
        lines.append("  <requirements>")
        for req in requirements:
            lines.append(f"    <requirement>{escape_xml(req)}</requirement>")
        lines.append("  </requirements>")

    # Constraints
    if constraints:
        lines.append("  <constraints>")
        for con in constraints:
            lines.append(f"    <constraint>{escape_xml(con)}</constraint>")
        lines.append("  </constraints>")

    # Dependencies
    if dependencies:
        lines.append("  <dependencies>")
        for dep in dependencies:
            task_id_attr = escape_xml(dep.get("task_id", ""))
            agent_attr = escape_xml(dep.get("agent_type", ""))
            lines.append(
                f'    <dependency task_id="{task_id_attr}" agent="{agent_attr}">'
            )
            lines.append(f"      <summary>{escape_xml(dep.get('summary', ''))}</summary>")
            if dep.get("key_decisions"):
                lines.append("      <key_decisions>")
                for dec in dep["key_decisions"]:
                    lines.append(f"        <decision>{escape_xml(dec)}</decision>")
                lines.append("      </key_decisions>")
            lines.append("    </dependency>")
        lines.append("  </dependencies>")

    # Existing artifacts
    if artifacts:
        lines.append("  <existing_artifacts>")
        for art in artifacts:
            art_type = escape_xml(art.get("type", ""))
            art_path = escape_xml(art.get("path", ""))
            lines.append(f'    <artifact type="{art_type}" path="{art_path}">')
            lines.append(f"      {escape_xml(art.get('description', ''))}")
            lines.append("    </artifact>")
        lines.append("  </existing_artifacts>")

    # Acceptance criteria
    if acceptance_criteria:
        lines.append("  <acceptance_criteria>")
        for crit in acceptance_criteria:
            lines.append(f"    <criterion>{escape_xml(crit)}</criterion>")
        lines.append("  </acceptance_criteria>")

    lines.append("</task_input>")
    return "\n".join(lines)
