"""Tests for agent response parsing."""


from agentic_builder.agents.response_parser import (
    AgentResponse,
    extract_list_items,
    extract_tag_content,
    parse_response,
)


class TestExtractTagContent:
    """Test XML tag content extraction."""

    def test_extract_simple_tag(self):
        """Test extracting content from a simple XML tag."""
        xml = "<summary>This is a summary</summary>"
        result = extract_tag_content(xml, "summary")
        assert result == "This is a summary"

    def test_extract_nested_tag(self):
        """Test extracting content from nested XML."""
        xml = "<response><summary>Nested content</summary></response>"
        result = extract_tag_content(xml, "summary")
        assert result == "Nested content"

    def test_extract_with_attributes(self):
        """Test extracting content from tag with attributes."""
        xml = '<artifact type="code" name="test.py">print("hello")</artifact>'
        result = extract_tag_content(xml, "artifact")
        assert result == 'print("hello")'

    def test_extract_nonexistent_tag(self):
        """Test extracting from nonexistent tag."""
        xml = "<summary>Content</summary>"
        result = extract_tag_content(xml, "missing")
        assert result is None

    def test_extract_multiline_content(self):
        """Test extracting multiline content."""
        xml = """<summary>
        Line 1
        Line 2
        </summary>"""
        result = extract_tag_content(xml, "summary")
        assert "Line 1" in result
        assert "Line 2" in result


class TestExtractListItems:
    """Test XML list item extraction."""

    def test_extract_simple_list(self):
        """Test extracting simple list items."""
        xml = """<warnings>
        <warning>Warning 1</warning>
        <warning>Warning 2</warning>
        </warnings>"""
        result = extract_list_items(xml, "warnings", "warning")
        assert result == ["Warning 1", "Warning 2"]

    def test_extract_empty_list(self):
        """Test extracting from empty list."""
        xml = "<warnings></warnings>"
        result = extract_list_items(xml, "warnings", "warning")
        assert result == []

    def test_extract_missing_container(self):
        """Test extracting when container tag is missing."""
        xml = "<other>Content</other>"
        result = extract_list_items(xml, "warnings", "warning")
        assert result == []


class TestParseResponse:
    """Test full response parsing."""

    def test_parse_successful_response(self):
        """Test parsing a successful agent response."""
        xml = """<task_output>
        <success>true</success>
        <summary>Task completed successfully</summary>
        <key_decisions>
        <decision>Decision 1</decision>
        <decision>Decision 2</decision>
        </key_decisions>
        <warnings>
        <warning>Minor issue</warning>
        </warnings>
        <artifacts>
        <artifact type="code" name="test.py" description="Test file">
        <content>print("hello")</content>
        </artifact>
        </artifacts>
        <next_tasks>
        <task agent="DEV_PYTHON" priority="high">
        <title>Implement feature</title>
        <description>Implement the requested feature</description>
        <acceptance_criteria>
        <criterion>Feature works</criterion>
        </acceptance_criteria>
        </task>
        </next_tasks>
        </task_output>"""

        response = parse_response(xml)

        assert response.success is True
        assert response.summary == "Task completed successfully"
        assert response.key_decisions == ["Decision 1", "Decision 2"]
        assert response.warnings == ["Minor issue"]
        assert len(response.artifacts) == 1
        assert response.artifacts[0]["type"] == "code"
        assert response.artifacts[0]["name"] == "test.py"
        assert response.artifacts[0]["content"] == 'print("hello")'
        assert len(response.next_tasks) == 1
        assert response.next_tasks[0]["agent_type"] == "DEV_PYTHON"
        assert response.next_tasks[0]["title"] == "Implement feature"

    def test_parse_failed_response(self):
        """Test parsing a failed agent response."""
        xml = """<task_output>
        <success>false</success>
        <summary>Task failed due to error</summary>
        </task_output>"""

        response = parse_response(xml)

        assert response.success is False
        assert response.summary == "Task failed due to error"
        assert response.key_decisions == []
        assert response.warnings == []
        assert response.artifacts == []
        assert response.next_tasks == []

    def test_parse_minimal_response(self):
        """Test parsing a minimal response."""
        xml = """<task_output>
        <success>true</success>
        <summary>Done</summary>
        </task_output>"""

        response = parse_response(xml)

        assert response.success is True
        assert response.summary == "Done"

    def test_parse_missing_task_output(self):
        """Test parsing response without task_output wrapper."""
        xml = "<success>true</success><summary>No wrapper</summary>"

        response = parse_response(xml)

        assert response.success is False
        assert "no task_output found" in response.summary

    def test_parse_malformed_xml(self):
        """Test parsing malformed XML."""
        xml = "Not XML at all"

        response = parse_response(xml)

        assert response.success is False
        assert "no task_output found" in response.summary

    def test_parse_with_cdata(self):
        """Test parsing XML with CDATA sections."""
        xml = """<task_output>
        <success>true</success>
        <summary><![CDATA[Summary with <tags> & special chars]]></summary>
        </task_output>"""

        response = parse_response(xml)

        assert response.success is True
        assert response.summary == "Summary with <tags> & special chars"


class TestAgentResponse:
    """Test AgentResponse dataclass."""

    def test_agent_response_creation(self):
        """Test creating an AgentResponse instance."""
        response = AgentResponse(
            success=True,
            summary="Test summary",
            key_decisions=["Decision 1"],
            artifacts=[{"type": "code", "name": "test.py"}],
            next_tasks=[{"agent_type": "DEV_PYTHON", "title": "Task"}],
            warnings=["Warning"],
            raw_xml="<xml></xml>",
        )

        assert response.success is True
        assert response.summary == "Test summary"
        assert response.key_decisions == ["Decision 1"]
        assert response.artifacts == [{"type": "code", "name": "test.py"}]
        assert response.next_tasks == [{"agent_type": "DEV_PYTHON", "title": "Task"}]
        assert response.warnings == ["Warning"]
        assert response.raw_xml == "<xml></xml>"

    def test_agent_response_defaults(self):
        """Test AgentResponse default values."""
        response = AgentResponse(success=False, summary="Failed")

        assert response.success is False
        assert response.summary == "Failed"
        assert response.key_decisions == []
        assert response.artifacts == []
        assert response.next_tasks == []
        assert response.warnings == []
        assert response.raw_xml == ""