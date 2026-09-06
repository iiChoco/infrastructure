"""No network, services, credentials, or production data are used."""
import importlib.util
from pathlib import Path
import plistlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


deploy = load("deploy")
render = load("render_launchagents")


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "Ciel source"
        (self.source / ".git").mkdir(parents=True)
        (self.source / "src/ciel").mkdir(parents=True)
        (self.source / "src/ciel/__main__.py").touch()
        (self.source / "pyproject.toml").write_text('[project]\nname = "ciel"\n')

    def test_infrastructure_or_wrong_project_cannot_be_uploaded(self):
        for source in [ROOT, Path(self.temp.name)]:
            with self.assertRaises((ValueError, FileNotFoundError)):
                deploy.validate_source("ciel", source)
        with self.assertRaises((ValueError, FileNotFoundError)):
            deploy.validate_source("website", self.source)

    def test_preview_with_sync_cannot_mutate_remote(self):
        plan = deploy.commands("ciel", self.source, "user@host", "~/jarvis", True, False)
        self.assertIn("--dry-run", plan[0])
        self.assertEqual(plan[0][-2], str(self.source.resolve()) + "/")
        self.assertIn("--locked", plan[1][-1])
        self.assertNotIn("tail", plan[1][-1])

    def test_default_cli_does_not_contact_server(self):
        argv = ["deploy.py", "ciel", "--source", str(self.source), "--sync"]
        with patch("sys.argv", argv), patch.object(deploy.subprocess, "run") as run:
            deploy.main()
        run.assert_not_called()

    def test_remote_dry_run_does_not_sync_dependencies_or_restart(self):
        argv = ["deploy.py", "ciel", "--source", str(self.source), "--sync", "--dry-run"]
        with patch("sys.argv", argv), patch.object(deploy.subprocess, "run") as run:
            deploy.main()
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0][0], "rsync")
        self.assertIn("--dry-run", run.call_args.args[0])

    def test_rejects_dangerous_destinations_and_host_options(self):
        for destination in ["/", "~", "~/../", "/home/user", "~/app;touch /tmp/x"]:
            with self.assertRaises(ValueError):
                deploy.validate_remote("user@host", destination)
        with self.assertRaises(ValueError):
            deploy.validate_remote("-oProxyCommand=bad", "~/jarvis")

    def test_rendering_handles_spaces_and_xml_characters(self):
        home = Path(self.temp.name) / "A & B"
        for template in (ROOT / "services/launchd").glob("*.plist"):
            document = plistlib.loads(render.render(template, self.source, home))
            self.assertEqual(document["WorkingDirectory"], str(self.source))
            self.assertEqual(document["ProgramArguments"][0], str(self.source / ".venv/bin/python"))
            self.assertEqual(Path(document["StandardOutPath"]).parent, home / ".ciel/log")


if __name__ == "__main__":
    unittest.main()
