# WorkBuddy 每日积分自动领取

一个 WorkBuddy skill：**无人值守领取每日 100 通用积分**，并用状态证据（而不是"脚本跑完了"）判定真实结果。

## 30 秒上手

在另一台电脑的 WorkBuddy 里发这一句就够了（**装完即自动建好每日任务**）：

> **安装这个 skill：https://github.com/lxx19970628a/workbuddy-daily-credits ，并设置每天自动领积分**

---

## 给 AI 的执行指令（用户把本仓库地址交给你时，照此执行）

**不要**去技能市场搜 —— 本 skill 不在市场上架。照下面四步做：

**1. 克隆到用户级 skill 目录**（Windows 上 `$HOME` = `C:\Users\<用户名>`）

```bash
git clone https://github.com/lxx19970628a/workbuddy-daily-credits.git \
  "$HOME/.workbuddy/skills/workbuddy-daily-credits"
```

目录已存在 → 改用 `git -C "<目录>" pull --ff-only`。
git 不可用 → 下载 `https://codeload.github.com/lxx19970628a/workbuddy-daily-credits/zip/refs/heads/main` 解压到同一路径。

**2. 校验安装**

```bash
test -f "$HOME/.workbuddy/skills/workbuddy-daily-credits/SKILL.md" && echo OK
```

必须看到 `OK`。看不到说明层级套错了。

**3. 读 SKILL.md，执行它的「第〇节 安装后立即执行」**

用 Read 打开 `<目标目录>/SKILL.md`，按第〇节做。核心是**用自动化工具创建一个每日常规任务**
（默认 `FREQ=DAILY;BYHOUR=9;BYMINUTE=5`，`skills: ["workbuddy-daily-credits"]`，prompt 模板在第〇节里）——
**不要再问用户「要不要建定时任务」**，直接建。用户给了别的时间就用那个时间。

> 💡 **刚装好的 skill 往往要新开一个会话才会被「激活」**，所以**别等 skill 被识别** ——
> 直接用 Read 读磁盘上的 `SKILL.md` 并照做，本次会话就能把自动化任务建完。

**4. 一句话回报**：装好了 + 任务已建（默认每天 09:05）+ 去哪改时间/停用。

> ⚠️ 本仓库**根目录就是 skill 本体**（`SKILL.md` 在根），不要再往里套一层同名目录，
> 否则 `~/.workbuddy/skills/<name>/SKILL.md` 不存在，WorkBuddy 识别不出这个 skill。

---

## 为什么需要它

WorkBuddy 的每日积分只能在**桌面客户端**领，网页端没有入口。手动领要三步：点开侧栏底部的账户名 → 在账户菜单里点「Buddy加油站」→ 在积分面板点「立即领取」。每天做一次，容易忘。

更麻烦的是，这件事**很容易假成功**。客户端置前经常失败，屏幕截图会抓到别的窗口（浏览器、聊天软件），据此判断必然出错。桌面 UI 又会随版本更新漂移。

这个 skill 把这些坑全踩过一遍，并且**把判定标准从"脚本退出码"换成了"页面状态跃迁"**。

## 客户端 UI 结构（先搞清楚这一点）

实测确认（客户端 5.7.7，截图 + OCR 双重验证）：

```
侧栏底部：  ...空间(19) / <任务项> / 「<用户名>」  [🔔] [💬]      ← 没有常驻的积分卡片
                    ↓ 点击账户行
账户菜单：  套餐 / 积分余额 / [升级套餐]
            Buddy加油站（每日领积分）   ← 积分入口
            去邀约 / 成长计划 / 设置 / 外观 / 记忆与进化 / 意见反馈 / 检查更新 / 退出登录
                    ↓ 点击「Buddy加油站」
积分面板：  Buddy应用 / 100 / 每日可领通用积分
            已领N天 / 累计领取N分            ← T2 证据
            Buddy加油站·N期 / [立即领取] 或 [今日已领]
```

⚠️ **侧栏底部并没有一张常驻的积分卡片** —— 底部只有账户行和两个图标。
积分面板是点击账户行后弹出的**覆盖层**。这一点常被误解，也是脚本以「账户菜单」为主路径的原因。

## 工作原理

```
定位窗口（按 exe 路径过滤，排除浏览器）
    ↓
【快路径】有本机成功坐标缓存？ → 直接复用坐标导航 + 窄条 OCR 校验  ← 首次跑通后 ~13s
    ↓ 无缓存 / 缓存失效
UI 状态复位 + 还原最小化窗口 + 渲染层存活探针（检测"陈旧帧"）
    ↓
五条路径逐级降级，命中即返回：
    路径 1    账户菜单 → Buddy加油站完整面板   ← 主路径（唯一可靠入口）
    路径 2    直读侧栏底部区域（少数版本有常驻卡片）
    路径 3    滚侧栏到底再读
    路径 4    整屏 OCR 搜「立即领取」
    路径 5    黑色按钮模板匹配（兜底）
    ↓
点击 → 回读强校验 → 输出 T1/T2 证据 → 成功后固化坐标供下次走快路径
```

### 会越用越快（v7.7）

首次在某台机器跑通后，脚本把该机器**实测的成功坐标**固化到 `claim_fastpath.json`，
之后每次直接复用：

| | 耗时（本机实测） |
|---|---|
| 首次（完整流程：探测 + 定位） | ~39s |
| 之后（快路径：复用坐标） | **~13s** |

**它为什么安全**（这是设计重点）：

1. **快路径只省「定位」，不省「判定」** —— 面板状态仍用与完整流程**完全相同**的
   T1/T2 标准判定，不存在"快路径放松了校验"。
2. **点账户行后强制校验菜单真的弹出** —— 坐标点偏会落到别的菜单项上，必须拦。
3. **任何异常自动回退** —— 缓存只是加速器，绝不成为单点故障。
   实测闭环：注入坏坐标 → 检出失效 → 回退完整流程成功 → **自动重新固化正确坐标**。

客户端改版、换分辨率、改系统缩放都会让旧坐标失效，脚本会**自动**检测并回退，
不需要手动兼容。想强制重新探测就删掉 `claim_fastpath.json`。

### 判定标准：只认状态证据

| 级别 | 内容 |
|------|------|
| **T0 无效** | 脚本退出码、"未找到入口"、"已发出点击" |
| **T1 状态跃迁（主判据）** | 「立即领取」→ 点击 → 「今日已领」且可点按钮消失 |
| **T2 数值证据（最强）** | 「已领 N 天 / 累计领取 N×100 分」点击前后 +1 天 / +100 分 |

三态判定：**S1** 可领取 / **S2** 已领取 / **S3** 画面不对（= 导航失败，**不是结果**，必须换路径重试）。

> 头号陷阱：「没找到『立即领取』」**不等于**「今日已领」。只有"看到已领字样"**且**"没有可点按钮"才算 S2。

## 为什么不走 API（重要）

社区里已存在若干**接口直连**方案（读本机登录态文件里的 `accessToken`，直接 POST
`copilot.tencent.com/billing/meter/daily-checkin`）。它们在旧版客户端上确实可行、也更轻。

**但从客户端 5.7.7 起，登录态文件里的凭据已改为信封加密**：

```jsonc
"accessToken": { "$wbEncrypted": 1, "envelope": "eyJzdWl0ZSI6MSwia2V5SWQiOiI..." }
// 全文件 0 条明文 JWT；refreshToken / nickname 同样加密
// 仅 account.uid 仍为明文
```

解密密钥由客户端主进程持有，不在文件里 —— 所以**读明文 token 的方案在此版本上会直接失效**。
这也是本 skill 采用「界面操作 + 状态证据」路线的现实原因：它不依赖任何非公开凭据格式，
在凭据加密后依然有效。

> 本 skill **不读取、不解密、不传输任何凭据**，只在用户自己的桌面上模拟正常点击。

## 安装（一句话，装完就是「已开启自动领取」）

在**另一台**电脑的 WorkBuddy 里，把下面这句原样发给它：

> **安装这个 skill：https://github.com/lxx19970628a/workbuddy-daily-credits ，并设置每天自动领积分**

它会在同一次操作里做完三件事：

1. 把仓库 clone 到用户级 skill 目录 `~/.workbuddy/skills/workbuddy-daily-credits`（Windows 上 `~` = `C:\Users\<用户名>`）
2. 创建**每日常规自动化任务**（默认每天 09:05）
3. 回你一句话，告诉你装好了、任务建好了、去哪改时间

想换时间就把时间写进那句话里：

> 安装 https://github.com/lxx19970628a/workbuddy-daily-credits ，每天早上 **9:30** 自动领积分

### 为什么能「一句话」

WorkBuddy 官方并没有「从 GitHub URL 一键安装 skill」的通道 —— 官方只有技能市场、上传技能包、让 AI 创建这三条路。
所以这句话之所以成立，是靠两件事：

- 仓库根目录**就是** skill 本体（`SKILL.md` 在根），clone 下来直接就是可用的 skill 目录；
- `SKILL.md` 第〇节写着**「安装动作」与「开启每日自动领取」是同一件事**，agent 读完必须顺手把自动化任务建掉，
  且**不允许反问用户「要不要建定时任务」**。

> ⚠️ 别 clone 到带多余层级的路径。正确结果是 `~/.workbuddy/skills/workbuddy-daily-credits/SKILL.md` 存在。

### 方式二：手动 clone（等价于上面第 1 步）

如果你更喜欢自己动手，clone 到用户级 skill 目录即可：

```bash
git clone https://github.com/lxx19970628a/workbuddy-daily-credits.git \
  "$HOME/.workbuddy/skills/workbuddy-daily-credits"
```

- **仅自己可用**（推荐）：`~/.workbuddy/skills/`
- **当前项目共享**：`<项目目录>/.workbuddy/skills/`

放好后重启 WorkBuddy（或新开会话），再说一句「每天自动领积分」，skill 会补建定时任务。

## 使用

装好后对 WorkBuddy 说：

> 帮我领今天的 WorkBuddy 积分

或者：

> 今天积分领了吗？

Skill 会自动：确认客户端在运行 → 检查/安装依赖 → 执行领取 → 复核并报告结果。

### 修改时间 / 停用

装的时候就已经建好了每日任务，不需要额外操作。要改：

> 把每日积分任务改成早上 8:40

或直接去侧边栏「自动化」里改时间、暂停。

## 环境要求

- **Windows 10 / 11**（客户端是 Electron + Win32 窗口，脚本依赖 `PrintWindow` 与 `pywin32`）
- **WorkBuddy 桌面客户端已安装并登录**
- **Python 3.10+**（依赖由 skill 引导自动安装，无需手动准备）

依赖清单：`pywin32` `Pillow` `numpy` `opencv-python` `rapidocr-onnxruntime` `pyautogui` `mss`

> 首次运行 `rapidocr-onnxruntime` 会下载约 15MB 的 OCR 模型，需要网络。

## 已知限制

- **WorkBuddy 没有官方的「从 URL 一键装 skill」通道**。本仓库的「一句话安装」是靠 agent 自己 `git clone` 到
  skill 目录 + 读 `SKILL.md` 后自动建任务实现的，不是客户端内置能力。若你所在环境禁用了命令执行，
  请改用「技能 → 添加技能 → 上传技能」导入本仓库的 zip。
- **仅支持 Windows**。macOS / Linux 客户端若存在，需要重写截图与窗口控制层。
- **UI 改版会导致脚本失效**。厂商改文案或布局时，锚点需要更新 —— 判定标准（T1/T2）不用改，改的是字符串常量（见 SKILL.md 第九节）。
- **依赖客户端保持已登录**（界面操作的前提）。
- **自动化任务不会自动跑第一次** —— 建好后要么等到次日调度时间，要么手动说一句「现在领一次」验一遍。
- **WorkBuddy 客户端必须在运行状态**，自动化到点才会触发（本地调度，客户端关掉就不跑）。
- RRULE 用**本地时区**，`BYHOUR=9` 就是本机 9 点，不需要换算 UTC。
- 每天只领一次是**服务端幂等**的，重复点击不会多领也不会扣分。

## 故障排查

见 [`references/troubleshooting.md`](references/troubleshooting.md) —— 收录了实际踩过的坑，每类都附根因、判据与修复方式。

遇到问题也可以直接问 WorkBuddy：

> 帮我领积分，如果失败就按 skill 的排查决策树自查

## 目录结构

**仓库根目录就是 skill 本体**（这样 clone 到 `~/.workbuddy/skills/` 下即可直接被识别）：

```
workbuddy-daily-credits/          ← 仓库根 = skill 目录
├── SKILL.md                      # skill 主体（第〇节：安装即建任务；其余：UI 结构 / 路径设计 / 硬约束 / 维护指南）
├── references/
│   └── troubleshooting.md        # 故障模式详录（含误诊案例）
├── scripts/
│   ├── claim_gui_final.py        # 主领取脚本（自包含全流程）
│   └── t2_check.py               # T2 数值复核工具
├── README.md                     # 本文件（仓库首页展示用）
├── PUBLISH.md                    # 发布与分发指南（维护者看）
├── SECURITY-AUDIT.md             # 安全审计报告
└── LICENSE
```

> 运行时产物（`claim_fastpath.json`、`claim_*.png`、`claim_run.log`）会写在 skill 目录里，已被 `.gitignore` 排除。

## 免责声明

本 skill 通过模拟用户在官方桌面客户端上的正常点击操作来领取积分，不修改客户端、不伪造请求、不绕过任何服务端限制、不读取任何凭据。领取行为受官方积分规则的约束（每日一次、服务端幂等）。请遵守 WorkBuddy 的服务条款。

## License

MIT
