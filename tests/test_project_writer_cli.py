import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from examples.project_sync.writer_cli import main
from examples.project_sync.writer_journal import Journal
from tests.test_project_writer import state, NOW
from tests.test_project_writer_github import config


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)
        self.config=self.path/"config.json"; self.config.write_text(json.dumps(config()),encoding="utf-8")
        self.snapshot=self.path/"snapshot.json"; self.snapshot.write_text(json.dumps(state()),encoding="utf-8")
        self.directory=self.path/"operation"

    def run_cli(self,*args):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            return main(list(args))

    def prepare(self):
        return self.run_cli("prepare","--config",str(self.config),"--snapshot",str(self.snapshot),
                            "--operation","one","--directory",str(self.directory))

    def test_offline_prepare_makes_receipt_and_refuses_overwrite(self):
        with patch("examples.project_sync.writer_cli.Backend") as backend:
            self.assertEqual(self.prepare(),0)
            self.assertEqual(self.prepare(),2)
            backend.assert_not_called()
        self.assertEqual(Journal.open(self.directory).events()[0]["kind"],"prepared")

    def test_disabled_apply_and_missing_approval_never_construct_transport(self):
        self.prepare()
        with patch("examples.project_sync.writer_cli.Backend") as backend:
            self.assertEqual(self.run_cli("apply","--config",str(self.config),"--directory",str(self.directory)),2)
            self.assertEqual(self.run_cli("apply","--config",str(self.config),"--directory",str(self.directory),"--execute"),2)
            backend.assert_not_called()

    def test_config_cannot_redirect_recovery_to_other_target(self):
        self.prepare()
        changed=config();changed["target"]["id"]="OTHER"
        self.config.write_text(json.dumps(changed),encoding="utf-8")
        with patch("examples.project_sync.writer_cli.Backend") as backend:
            self.assertEqual(self.run_cli("recover","--config",str(self.config),"--directory",str(self.directory)),2)
            backend.assert_not_called()

    def test_read_only_commands_construct_unarmed_backend(self):
        self.prepare()
        with patch("examples.project_sync.writer_cli.Backend") as backend:
            backend.return_value.read.return_value=state()
            self.assertEqual(self.run_cli("rollback-assess","--config",str(self.config),"--directory",str(self.directory)),2)
            self.assertFalse(backend.call_args.kwargs.get("armed",False))
