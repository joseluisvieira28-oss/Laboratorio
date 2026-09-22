from __future__ import annotations

import unittest

from radar.cli_argv import strip_exact_self_path_echo


class CliArgvTests(unittest.TestCase):
    def test_removes_exact_self_path_echo_only(self):
        exe = r"C:\Users\José\Desktop\Pack\dist\MEXCRiskState.exe"
        args = [
            "--preflight",
            r"C:\Users\José\Desktop\Pack\receipt.json",
            "--out",
            r"C:\Users\José\Desktop\Pack\risk.json",
            exe,
        ]
        cleaned = strip_exact_self_path_echo(args, executable=exe)
        self.assertEqual(
            cleaned,
            [
                "--preflight",
                r"C:\Users\José\Desktop\Pack\receipt.json",
                "--out",
                r"C:\Users\José\Desktop\Pack\risk.json",
            ],
        )

    def test_does_not_hide_other_unknown_exe_argument(self):
        exe = r"C:\Pack\dist\MEXCRiskState.exe"
        other = r"C:\Other\Something.exe"
        args = ["--preflight", "x.json", other]
        self.assertEqual(
            strip_exact_self_path_echo(args, executable=exe),
            args,
        )


if __name__ == "__main__":
    unittest.main()
