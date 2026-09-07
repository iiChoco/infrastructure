"""No network, services, credentials, or production data are used."""
import importlib.util
from pathlib import Path
import os
import plistlib
import shutil
import signal
import subprocess
import time
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
        plan = deploy.commands("ciel", self.source, "user@host", "~/ciel", True, False)
        self.assertIn("--dry-run", plan[0])
        self.assertEqual(plan[0][-2], str(self.source.resolve()) + "/")
        self.assertIn("--locked", plan[1][-1])
        self.assertNotIn("tail", plan[1][-1])

    def test_website_deploy_preserves_legacy_service_recovery_copy(self):
        (self.source / "door").mkdir()
        (self.source / "door/pyproject.toml").write_text('[project]\nname = "door"\n')
        (self.source / "math/public").mkdir(parents=True)
        (self.source / "math/public/index.html").touch()
        for apply in (False, True):
            command = deploy.commands("website", self.source, "user@host", "~/website", False, apply)[0]
            index = command.index("/door/deploy/door.service")
            self.assertEqual(command[index - 1], "--exclude")
            self.assertNotIn("--delete-excluded", command)
        self.assertNotIn("/door/deploy/door.service", deploy.commands("ciel", self.source, "user@host", "~/ciel", False, True)[0])

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
            deploy.validate_remote("-oProxyCommand=bad", "~/ciel")

    def test_rendering_handles_spaces_and_xml_characters(self):
        home = Path(self.temp.name) / "A & B"
        launcher = home / "Ciel.app/Contents/MacOS/ciel-launcher"
        for template in (ROOT / "services/launchd").glob("*.plist"):
            document = plistlib.loads(render.render(template, self.source, home, launcher))
            self.assertEqual(document["WorkingDirectory"], str(self.source))
            log_dir = home / ".ciel/log"
            self.assertEqual(Path(document["StandardOutPath"]).parent, log_dir)
            # launchd starts the launcher bundle, which starts Python as a
            # child: macOS asks for the microphone on behalf of the
            # application responsible for a process, and neither Python's
            # bundle nor a /bin/sh wrapper can be asked.
            launcher, python, *arguments = document["ProgramArguments"]
            self.assertEqual(launcher, str(home / "Ciel.app/Contents/MacOS/ciel-launcher"))
            self.assertEqual(python, str(self.source / ".venv/bin/python"))
            self.assertEqual(arguments[:2], ["-m", "ciel"])
            self.assertNotIn("/bin/sh", document["ProgramArguments"])

    @unittest.skipUnless(shutil.which("cc") and shutil.which("codesign"), "needs a C compiler and codesign")
    def test_launcher_bundle_starts_a_child_and_forwards_signals(self):
        output = Path(self.temp.name) / "rendered"
        executable = render.build_launcher(output)
        self.assertEqual(executable, output / "Ciel.app/Contents/MacOS/ciel-launcher")
        info = plistlib.loads((output / "Ciel.app/Contents/Info.plist").read_bytes())
        self.assertIn("NSMicrophoneUsageDescription", info)
        self.assertEqual(info["CFBundleExecutable"], "ciel-launcher")
        done = subprocess.run([str(executable), "/bin/sh", "-c", "exit 3"])
        self.assertEqual(done.returncode, 3)
        self.assertEqual(subprocess.run([str(executable)]).returncode, 64)
        self.assertEqual(subprocess.run([str(executable), "/nonexistent/python"], capture_output=True).returncode, 127)
        marker = Path(self.temp.name) / "child.pid"
        proc = subprocess.Popen([str(executable), "/bin/sh", "-c", f"echo $$ > '{marker}'; sleep 30"])
        deadline = time.monotonic() + 5
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        child = int(marker.read_text())
        proc.send_signal(signal.SIGTERM)
        self.assertEqual(proc.wait(timeout=5), 128 + signal.SIGTERM)
        for _ in range(50):
            try:
                os.kill(child, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            self.fail("the child outlived the launcher")

    def test_rendering_makes_the_log_directory_launchd_opens(self):
        home = Path(self.temp.name) / "fresh home"
        self.assertFalse((home / ".ciel/log").exists())
        self.assertEqual(render.ensure_log_dir(home), home / ".ciel/log")
        self.assertTrue((home / ".ciel/log").is_dir())
        render.ensure_log_dir(home)  # idempotent on a machine that already has it


if __name__ == "__main__":
    unittest.main()
