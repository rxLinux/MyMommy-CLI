from mymommy.agent.agent import Agent
from mymommy.tools.shell_tool import ShellTool

class DebugHandler:
    def __init__(self, agent: Agent, shell: ShellTool):
        self.agent = agent
        self.shell = shell

    def run_debug_flow(self, test_command: str = "pytest"):
        """
        Executes the debug flow:
        1. Run tests
        2. Capture error
        3. Send to agent for fix
        """
        # 1. Run tests
        result = self.shell.execute(test_command)
        
        if result["exit_code"] == 0:
            return "All tests passed! Nothing to debug."

        # 2. Extract error
        error_context = f"Tests failed with exit code {result['exit_code']}.\nSTDOUT:\n{result['stdout']}\nSTDERR:\n{result['stderr']}"
        
        # 3. Trigger agent
        prompt = f"I'm in debug mode. The tests failed. Please analyze the error and propose a fix.\n\nCONTEXT:\n{error_context}"
        return self.agent.chat(prompt)
        # Note: In the TUI, this would yield streaming responses.
