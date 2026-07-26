import pytest
from pathlib import Path
from mymommy.sandbox.sandbox import Sandbox, SandboxError

def test_sandbox_restrict_to_cwd(tmp_path):
    # Create a dummy project dir
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    # Create a file outside
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("secret")
    
    sandbox = Sandbox(base_path=project_dir)
    
    # Test valid path
    inner_file = project_dir / "inner.txt"
    inner_file.write_text("hello")
    assert sandbox.validate_path("inner.txt") == inner_file.resolve()
    
    # Test invalid path (parent)
    with pytest.raises(SandboxError):
        sandbox.validate_path("../outside.txt")
        
    # Test invalid absolute path
    with pytest.raises(SandboxError):
        sandbox.validate_path(str(outside_file))

def test_sandbox_read_write(tmp_path):
    sandbox = Sandbox(base_path=tmp_path)
    sandbox.write_file("test.txt", "content")
    assert sandbox.read_file("test.txt") == "content"
    assert (tmp_path / "test.txt").read_text() == "content"
