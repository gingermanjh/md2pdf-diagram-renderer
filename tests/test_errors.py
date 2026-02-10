from md2pdf_cli.errors import DependencyError, ExitCode


def test_dependency_error_uses_exit_code_2() -> None:
    err = DependencyError(["node missing", "java missing"])
    assert err.exit_code == ExitCode.DEPENDENCY_ERROR
    assert "node missing" in str(err)
    assert "java missing" in str(err)
