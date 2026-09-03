"""由 yyds 官方维护的软件包目录。"""

# 新的官方软件包请添加到这里；工具仅检查、安装和升级该清单中的项目。
YYDS_PACKAGES = tuple(
    sorted(
        (
            "yyds-fswatch",
            "yyds-lock",
            "yyds-logger",
            "yyds-mdns",
            "yyds-notify-os",
            "yyds-pip",
            "yyds-pip-audit",
            "yyds-stream-tap",
            "yyds-update",
        ),
        key=str.lower,
    )
)
