from unittest.mock import patch
from typer.testing import CliRunner

from apicrafter.cli import app

runner = CliRunner()


@patch("apicrafter.tui.ApiCrafterTUI.run")
def test_tui_command(mock_run):
    result = runner.invoke(app, ["tui"])
    assert result.exit_code == 0
    mock_run.assert_called_once()
