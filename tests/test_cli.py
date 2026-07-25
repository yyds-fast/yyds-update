import json
import unittest
from subprocess import CompletedProcess
from unittest.mock import patch

from yyds_update.cli import PackageStatus, action_packages, check_packages, select_packages
from yyds_update.packages import YYDS_PACKAGES


class OfficialCatalogTests(unittest.TestCase):
    def test_catalog_is_sorted_alphabetically(self) -> None:
        self.assertEqual(YYDS_PACKAGES, tuple(sorted(YYDS_PACKAGES, key=str.lower)))
        self.assertEqual(len(YYDS_PACKAGES), 8)

    def test_select_packages_normalizes_names_and_preserves_catalog_order(self) -> None:
        self.assertEqual(
            select_packages(("YYDS_UPDATE", "yyds-lock", "yyds-lock")),
            ("yyds-lock", "yyds-update"),
        )

    def test_select_packages_rejects_unknown_names(self) -> None:
        with self.assertRaisesRegex(Exception, "不是官方"):
            select_packages(("yyds-unofficial",))


class UpgradePlanTests(unittest.TestCase):
    @patch("yyds_update.cli._run_pip")
    def test_plan_keeps_catalog_order_and_includes_missing_packages(self, run_pip) -> None:
        installed = json.dumps(
            [
                {"name": "yyds-pip", "version": "0.4.7"},
                {"name": "yyds-unofficial", "version": "1.0.0"},
            ]
        )
        report = json.dumps(
            {
                "install": [
                    {"metadata": {"name": "yyds-pip", "version": "0.5.0"}},
                    {"metadata": {"name": "yyds-lock", "version": "0.3.0"}},
                    {"metadata": {"name": "click", "version": "8.3.1"}},
                ]
            }
        )
        run_pip.side_effect = [
            CompletedProcess(args=[], returncode=0, stdout=installed, stderr=""),
            CompletedProcess(args=[], returncode=0, stdout=report, stderr=""),
        ]

        packages = check_packages(timeout=3)

        self.assertEqual([package.name for package in packages], list(YYDS_PACKAGES))
        self.assertEqual(packages[1], PackageStatus("yyds-lock", None, "0.3.0"))
        self.assertEqual(packages[4], PackageStatus("yyds-pip", "0.4.7", "0.5.0"))
        self.assertEqual(action_packages(packages), [packages[1], packages[4]])
        command = run_pip.call_args_list[1].args
        self.assertEqual(command[-len(YYDS_PACKAGES):], YYDS_PACKAGES)
        self.assertEqual(command[command.index("--retries") + 1], "0")

    @patch("yyds_update.cli._run_pip")
    def test_plan_can_be_limited_to_one_official_package(self, run_pip) -> None:
        run_pip.side_effect = [
            CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps([{"name": "yyds-lock", "version": "0.2.0"}]),
                stderr="",
            ),
            CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps(
                    {"install": [{"metadata": {"name": "yyds-lock", "version": "0.3.0"}}]}
                ),
                stderr="",
            ),
        ]

        packages = check_packages(timeout=3, package_names=("yyds-lock",))

        self.assertEqual(packages, [PackageStatus("yyds-lock", "0.2.0", "0.3.0")])
        self.assertEqual(run_pip.call_args_list[1].args[-1:], ("yyds-lock",))
