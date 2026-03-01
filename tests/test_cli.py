import pytest

from diviora_kernel import cli


def test_cli_exits_on_python_older_than_311(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(cli.sys, "version_info", (3, 10, 9))
    monkeypatch.setattr(cli, "parse_args", lambda: pytest.fail("parse_args should not run on unsupported Python"))

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "Python >= 3.11 is required" in captured.out
