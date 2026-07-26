from mymommy.agent.agent import Agent


def test_extract_tool_call_with_nested_parameters():
    agent = Agent.__new__(Agent)
    calls = agent._extract_tool_calls(
        '''```json
{
  "tool": "direct_pc_file_manager",
  "parameters": {"action": "write", "path": "/utils/calc.py", "content": "x"}
}
```'''
    )

    assert calls == [
        {
            "tool": "direct_pc_file_manager",
            "parameters": {"action": "write", "path": "/utils/calc.py", "content": "x"},
        }
    ]
