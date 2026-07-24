"""yyds-update 的命令行入口。"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .__version__ import __version__
from .packages import YYDS_PACKAGES


console = Console()
DEFAULT_TIMEOUT = 5.0


@dataclass(frozen=True)
class PackageStatus:
    """官方软件包在当前环境中的安装与更新状态。"""

    name: str
    installed_version: str | None
    target_version: str | None = None

    @property
    def needs_install(self) -> bool:
        return self.installed_version is None and self.target_version is not None

    @property
    def needs_upgrade(self) -> bool:
        return (
            self.installed_version is not None
            and self.target_version is not None
            and self.installed_version != self.target_version
        )

    @property
    def needs_action(self) -> bool:
        return self.needs_install or self.needs_upgrade


def _run_pip(*arguments: str) -> subprocess.CompletedProcess[str]:
    """在当前解释器环境运行 pip，并以文本形式收集结果。"""
    return subprocess.run(
        [sys.executable, "-m", "pip", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def _load_json(result: subprocess.CompletedProcess[str], action: str) -> list[dict[str, object]]:
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "未知错误"
        raise click.ClickException(f"{action}失败：{detail}")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise click.ClickException(f"{action}失败：pip 返回了无法识别的数据。") from error
    if not isinstance(data, list):
        raise click.ClickException(f"{action}失败：pip 返回的数据格式不正确。")
    return [item for item in data if isinstance(item, dict)]


def _normalized_name(name: str) -> str:
    """按 Python 包名规则统一横线、下划线和点号。"""
    return "-".join(part for part in name.lower().replace("_", "-").replace(".", "-").split("-") if part)


def installed_versions() -> dict[str, str]:
    """读取官方目录中软件包的已安装版本；不从本地发现新包。"""
    data = _load_json(_run_pip("list", "--format=json"), "读取已安装软件包")
    catalog = {_normalized_name(name): name for name in YYDS_PACKAGES}
    installed: dict[str, str] = {}
    for item in data:
        name = item.get("name")
        version = item.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            continue
        official_name = catalog.get(_normalized_name(name))
        if official_name:
            installed[official_name] = version
    return installed


def _network_options(timeout: float, *, quiet: bool = False) -> tuple[str, ...]:
    """提供快速失败且不会额外交互的 pip 网络参数。"""
    options = [
        "--disable-pip-version-check",
        "--no-input",
        "--retries",
        "0",
        "--timeout",
        str(timeout),
    ]
    if quiet:
        options.append("--quiet")
    return tuple(options)


def _load_report(result: subprocess.CompletedProcess[str], action: str) -> list[dict[str, object]]:
    """读取 pip install --report 输出的安装计划。"""
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "未知错误"
        if "connection" in detail.lower() or "resolution" in detail.lower():
            detail = "无法连接或解析当前 pip 软件源，请检查网络和镜像配置。"
        raise click.ClickException(f"{action}失败：{detail}")
    try:
        report = json.loads(result.stdout)
        install = report["install"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise click.ClickException(f"{action}失败：pip 返回了无法识别的安装计划。") from error
    if not isinstance(install, list):
        raise click.ClickException(f"{action}失败：pip 返回的安装计划格式不正确。")
    return [item for item in install if isinstance(item, dict)]


def check_packages(timeout: float) -> list[PackageStatus]:
    """检查官方目录中的包；未安装项同样会进入安装计划。"""
    installed = installed_versions()
    result = _run_pip(
        *_network_options(timeout, quiet=True),
        "install",
        "--upgrade",
        "--dry-run",
        "--report",
        "-",
        *YYDS_PACKAGES,
    )
    plan = _load_report(result, "检查 yyds 软件包")
    catalog = {_normalized_name(name): name for name in YYDS_PACKAGES}
    targets: dict[str, str] = {}
    for item in plan:
        metadata = item.get("metadata")
        if not isinstance(metadata, dict):
            continue
        name = metadata.get("name")
        version = metadata.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            continue
        official_name = catalog.get(_normalized_name(name))
        if official_name:
            targets[official_name] = version

    return [PackageStatus(name, installed.get(name), targets.get(name)) for name in YYDS_PACKAGES]


def action_packages(packages: list[PackageStatus]) -> list[PackageStatus]:
    """筛选需要安装或升级的软件包。"""
    return [package for package in packages if package.needs_action]


def _status_label(package: PackageStatus, *, checked: bool) -> str:
    if package.needs_install:
        return "[bold bright_blue]↓ 待安装[/bold bright_blue]"
    if package.needs_upgrade:
        return "[bold bright_yellow]↑ 可升级[/bold bright_yellow]"
    if package.installed_version is None:
        return "[dim]未安装[/dim]"
    if checked:
        return "[bold green]✓ 已是最新[/bold green]"
    return "[cyan]已安装[/cyan]"


def package_table(packages: list[PackageStatus], *, checked: bool) -> Table:
    """渲染紧凑的官方软件包总表。"""
    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold bright_cyan",
        border_style="bright_blue",
        expand=False,
        pad_edge=True,
    )
    table.add_column("软件包", style="bold turquoise2")
    table.add_column("当前版本", justify="right", style="gold1")
    table.add_column("可用版本", justify="right", style="bold bright_green")
    table.add_column("状态", justify="center")

    for package in packages:
        current = package.installed_version or "[dim]未安装[/dim]"
        target = package.target_version if package.needs_action else "[dim]—[/dim]"
        table.add_row(package.name, current, target, _status_label(package, checked=checked))
    return table


def print_catalog(packages: list[PackageStatus], *, checked: bool) -> None:
    installed_count = sum(package.installed_version is not None for package in packages)
    upgrade_count = sum(package.needs_upgrade for package in packages)
    install_count = sum(package.needs_install for package in packages)
    latest_count = sum(
        package.installed_version is not None and not package.needs_action for package in packages
    )
    if checked:
        subtitle = (
            f"[green]已安装 {installed_count}[/green]  ·  "
            f"[bright_green]已是最新 {latest_count}[/bright_green]  ·  "
            f"[yellow]可升级 {upgrade_count}[/yellow]  ·  "
            f"[bright_blue]待安装 {install_count}[/bright_blue]"
        )
    else:
        subtitle = f"[green]已安装 {installed_count}[/green]  ·  [dim]未安装 {len(packages) - installed_count}[/dim]"
    console.print(
        Panel(
            package_table(packages, checked=checked),
            title="[bold bright_cyan]🦉 yyds 软件包[/bold bright_cyan]",
            subtitle=subtitle,
            subtitle_align="center",
            border_style="bright_blue",
            expand=False,
            padding=(0, 1),
        )
    )


def install_or_upgrade(packages: list[PackageStatus], *, dry_run: bool, timeout: float) -> None:
    """按已确认的精确版本安装缺失包或升级旧包。"""
    names = [f"{package.name}=={package.target_version}" for package in packages]
    command = [
        sys.executable,
        "-m",
        "pip",
        *_network_options(timeout),
        "install",
        "--upgrade",
        *names,
    ]
    if dry_run:
        console.print("[yellow]演练模式：没有安装或升级任何软件包。[/yellow]")
        return

    result = subprocess.run(command, check=False)
    if result.returncode:
        raise click.ClickException("操作未完成。请查看上方 pip 输出后重试。")
    installed = sum(package.needs_install for package in packages)
    upgraded = sum(package.needs_upgrade for package in packages)
    console.print(f"[bold green]✔ 操作完成：安装 {installed} 个，升级 {upgraded} 个。[/bold green]")


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-v", "-V", "--version")
@click.pass_context
def main(ctx: click.Context) -> None:
    """🦉 一键安装和升级官方 yyds 软件包。"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(update)


@main.command("list")
def list_packages() -> None:
    """查看官方软件包目录及本地安装状态。"""
    installed = installed_versions()
    packages = [PackageStatus(name, installed.get(name)) for name in YYDS_PACKAGES]
    print_catalog(packages, checked=False)


@main.command("check")
@click.option("--timeout", default=DEFAULT_TIMEOUT, show_default=True, type=click.FloatRange(min=0.1))
def check(timeout: float) -> None:
    """检查官方软件包的安装与升级状态，不作修改。"""
    with console.status(f"[bold blue]正在检查 {len(YYDS_PACKAGES)} 个官方 yyds 软件包…[/bold blue]"):
        packages = check_packages(timeout)
    print_catalog(packages, checked=True)


@main.command("update")
@click.option("--yes", "assume_yes", is_flag=True, help="不询问确认，直接开始操作。")
@click.option("--dry-run", is_flag=True, help="只展示安装与升级计划，不作任何修改。")
@click.option("--timeout", default=DEFAULT_TIMEOUT, show_default=True, type=click.FloatRange(min=0.1))
def update(assume_yes: bool = False, dry_run: bool = False, timeout: float = DEFAULT_TIMEOUT) -> None:
    """一键安装缺失的官方包，并升级可更新的官方包。"""
    with console.status(f"[bold blue]正在检查 {len(YYDS_PACKAGES)} 个官方 yyds 软件包…[/bold blue]"):
        packages = check_packages(timeout)
    print_catalog(packages, checked=True)
    candidates = action_packages(packages)
    if not candidates:
        console.print("[bold green]✔ 所有官方 yyds 软件包均已就绪。[/bold green]")
        return
    if not dry_run and not assume_yes:
        click.confirm(f"确认安装 / 升级以上 {len(candidates)} 个软件包？", abort=True)
    install_or_upgrade(candidates, dry_run=dry_run, timeout=timeout)


if __name__ == "__main__":
    main()
