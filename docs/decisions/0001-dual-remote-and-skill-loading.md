# ADR 0001，双远端与 Skill 加载

状态：Accepted，双远端配置已实施

日期：2026-11-21

## 背景

当前正式 MCP 源码位于 C 盘，作者 GitHub 已作为原仓库远端。用户希望在 D 盘持续开发，同时保留作者更新能力，并把个人成果推送到自己的 GitHub。用户随后提供了个人 Fork 地址。

## 决策

- D 盘仓库的 `origin` 指向个人 Fork `https://github.com/wuyeku/solidworks-automation-skill.git`。
- `upstream` 指向作者仓库 `https://github.com/wzyn20051216/solidworks-automation-skill.git`，push URL 设置为 `DISABLED`。
- 个人开发使用 `feature/*`、`fix/*`、`sync/upstream-*` 和 `release/*`。
- 上游更新在独立同步分支中审查和测试，不直接覆盖个人分支。
- 项目级 Skill 放在仓库根目录 `.agents/skills`。
- 当前 C 盘全局 Skill 和正式 MCP 配置在用户批准前保持不变。

## 当前实施状态

- `origin` 和 `upstream` 均已完成 fetch。
- `origin/main` 和 `upstream/main` 当前均为 `36bc337357723b9763759ff06e4a1afab990b823`。
- 当前分支 `feature/stage5-93-tools` 与两个 `main` 指向同一提交。
- 尚未执行 commit 或 push。

## 原因

项目级 Skill 会从当前工作目录向上扫描到仓库根目录。D 盘仓库内的 `.agents/skills` 能在从 D 盘启动 Codex 时被发现，不会影响当前 C 盘运行。

## 切换条件

只有 D 盘 MCP 完成独立启动、工具发现、离线测试、SolidWorks 2025 连接和目标文档读取验证后，才允许修改正式 MCP 配置。

## 回滚

正式配置修改前先备份。任何切换失败都恢复到当前 C 盘启动路径。C 盘源码和 Skill 至少保留一个稳定版本周期。
