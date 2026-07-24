# 🦉 yyds-update

`yyds-update` 用于一键安装和升级官方 yyds 软件包。软件包目录由工具维护，因此即使某个官方包尚未安装，也会在确认后自动安装。

## 安装

```bash
python -m pip install -U yyds-update
```

本地开发时：

```bash
python -m pip install -e .
```

## 使用

直接运行会检查可更新的软件包，确认后开始升级：

```bash
yyds-update
```

常用命令：

```bash
# 查看官方软件包目录与本地安装状态
yyds-update list

# 仅检查哪些包可以升级，不作修改
yyds-update check

# 网络较慢时可缩短单次网络等待时间（默认 5 秒，且不会重试）
yyds-update check --timeout 3

# 跳过确认，一键升级所有可升级的软件包
yyds-update update --yes

# 查看将要执行的命令，不作修改
yyds-update update --dry-run
```

`yyds-update` 与 `yyds_update` 两种命令写法均可使用。

> 工具始终调用运行它的 Python 解释器对应的 `python -m pip`，因此在虚拟环境中使用时只会操作该虚拟环境。官方软件包目录位于 `yyds_update/packages.py`；新增官方包时只需在该列表添加名称。
