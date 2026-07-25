# 🦉 yyds-update

`yyds-update` 是 yyds Python 工具链的一键安装与升级器。它维护一份官方软件包目录，检查当前 Python 环境后会以清晰的终端表格展示每个包的状态：已是最新、可升级，或尚未安装。

确认后，工具会一次性安装缺失的官方包，并升级已有的新版本。

```bash
yyds-update
```

## 特性

- 🦉 **统一管理**：只操作官方目录中的 yyds 软件包，不会误扫环境中其他第三方包。
- 📦 **自动补齐**：目录中的官方包即使尚未安装，也会标记为“待安装”并进入操作计划。
- ⬆️ **精确升级**：检查阶段确定目标版本，确认后按该版本执行，避免展示结果与实际安装版本不一致。
- 🎨 **紧凑终端界面**：一张总表同时展示当前版本、可用版本和安装状态。
- ⚡ **快速失败**：默认单次网络超时为 5 秒，失败不重试；适合网络不稳定时快速获得结果。
- 🐍 **环境隔离**：始终调用当前 `python` 对应的 `pip`，在虚拟环境中运行时仅影响该虚拟环境。
- 🔄 **支持自更新**：`yyds-update` 自身也在官方目录中，发布新版本后可由工具升级。

## 官方软件包目录

目前管理以下软件包，界面会自动按字母顺序展示：

| 软件包 | 说明 |
| --- | --- |
| `yyds-fswatch` | 文件系统监听工具 |
| `yyds-lock` | 锁与并发控制工具 |
| `yyds-logger` | 日志工具 |
| `yyds-notify-os` | 操作系统通知工具 |
| `yyds-pip` | pip 镜像源管理工具 |
| `yyds-pip-audit` | Python 软件包审计工具 |
| `yyds-stream-tap` | 流式输出处理工具 |
| `yyds-update` | 本工具 |

目录定义在 [yyds_update/packages.py](yyds_update/packages.py)。新增官方包时，只需将包名加入该列表；工具会自动按字母顺序检查、显示和处理。

## 安装

### 从软件源安装

```bash
python -m pip install --upgrade yyds-update
```

### 本地开发安装

在项目根目录执行：

```bash
python -m pip install -e .
```

项目要求 Python 3.9 或更高版本。

## 快速开始

直接运行：

```bash
yyds-update
```

工具会依次完成：

1. 读取当前环境中官方目录内软件包的已安装版本；
2. 向当前配置的 pip 软件源查询安装与升级计划；
3. 显示统一状态表；
4. 在有待安装或可升级项目时请求确认；
5. 安装缺失包并升级旧版本。

典型输出中的状态含义：

| 状态 | 含义 | 后续动作 |
| --- | --- | --- |
| `✓ 已是最新` | 已安装且没有更高版本 | 不作修改 |
| `↑ 可升级` | 已安装，但存在新版本 | 确认后升级 |
| `↓ 待安装` | 官方目录中存在，但当前环境未安装 | 确认后安装 |
| `未安装` | 仅执行 `list` 时发现尚未安装 | 不作修改 |

## 命令参考

### 默认：检查后安装或升级

```bash
yyds-update
```

显示完整状态表；如有待处理项，输入 `y` 确认。

### 查看本地安装状态

```bash
yyds-update list
```

只读取本地环境，不访问软件源。适合快速确认哪些官方包已经安装。

### 仅检查，不作修改

```bash
yyds-update check
```

查询软件源并展示可安装、可升级状态，但不会进行安装。

也可仅检查某一个官方包：

```bash
yyds-update check --package yyds-lock
```

### 自动确认

```bash
yyds-update update --yes
```

适合脚本、自动化任务或不需要人工确认的场景。

仅操作指定包时，可重复传入 `--package`：

```bash
yyds-update update --package yyds-lock --package yyds-pip
```

### 演练模式

```bash
yyds-update update --dry-run
```

生成并展示安装、升级计划，但不修改当前环境。

### 调整网络超时

```bash
yyds-update check --timeout 3
yyds-update update --timeout 10
```

默认超时为 5 秒，且不会自动重试。网络较慢时可适当增大；希望快速失败时可减小，例如 `--timeout 3`。

### JSON 输出

`list` 与 `check` 支持 `--json`，便于在 CI 或其他脚本中读取状态：

```bash
yyds-update check --json
yyds-update list --package yyds-update --json
```

### 命令别名

以下两种命令完全等价：

```bash
yyds-update
yyds_update
```

## 软件源与网络

工具会沿用当前 Python 环境的 pip 配置，包括 `index-url`、镜像源和证书设置。可使用 `yyds-pip` 管理镜像源：

```bash
yyds-pip show
yyds-pip best
```

若查询失败，请先检查网络和 pip 镜像配置；工具会在超时后停止，不会无限等待。

## 开发与发布

运行测试：

```bash
python -m unittest discover -s tests -v
```

构建发布包前，请先确保测试通过。项目提供 [build.sh](build.sh) 作为构建并上传脚本；它会清理旧产物、构建包，并将 `dist/` 内容上传到当前 twine 配置的仓库。发布前请仔细确认目标仓库和版本号。

版本信息需保持同步：

- `pyproject.toml` 的 `project.version`
- `yyds_update/__version__.py` 的 `__version__`

## 设计说明

工具不使用本地环境中所有 `yyds-*` 名称来决定管理范围，而是以官方目录为准。这意味着：

- 本地存在未知的同前缀包时，不会被误升级；
- 官方目录新增包时，未安装环境也能自动发现并安装；
- 表格顺序和自动化行为都保持一致、可审计。
