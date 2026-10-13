# 发布与分发指南

## 一、发布到 GitHub

### 1. 创建仓库

在 GitHub 上新建一个 **public** 仓库，建议名 `workbuddy-daily-credits`。

### 2. 推送本目录

**目标文件夹（仓库根）就是本文件所在目录**：

```
<本地路径>  C:\Users\sean\WorkBuddy\skills\github-repo\
<仓库名>    workbuddy-daily-credits
```

> ⚠️ **本地文件夹名不必等于仓库名**。git 的仓库根由 `.git` 所在目录决定（可用
> `git rev-parse --show-toplevel` 确认），与文件夹叫什么无关。上面这二者不同名是正常的，
> **不要**因此去找一个叫 `workbuddy-daily-credits\` 的本地文件夹 —— 那个是仓库*内部*的 skill 子目录。

命令（已在 2026-10-13 执行过 `init` / `add` / `commit` / `branch -M main`，此处保留完整流程备查）：

```bash
cd "C:\Users\sean\WorkBuddy\skills\github-repo"   # ← 就是本文件所在目录
git init                                          # 已执行
git add .
git commit -m "feat: WorkBuddy 每日积分自动领取 skill（v7.7 泛化 + 快路径版）"   # 已执行 → 42a0103
git branch -M main                                # 已执行
git remote add origin https://github.com/<你的用户名>/workbuddy-daily-credits.git
git push -u origin main
```

目录结构（推送后 GitHub 上看到的，注意**仓库根名 = 仓库名**，本地文件夹名不影响）：

```
workbuddy-daily-credits/          ← GitHub 仓库根（= 本地 github-repo/ 的内容）
├── README.md
├── LICENSE
├── SECURITY-AUDIT.md
├── PUBLISH.md
├── .gitignore
└── workbuddy-daily-credits/      ← skill 本体（可被 WorkBuddy 直接安装）
    ├── SKILL.md
    ├── references/
    │   └── troubleshooting.md
    └── scripts/
        ├── claim_gui_final.py
        └── t2_check.py
```

> ⚠️ **注意仓库嵌套**：仓库根下有一个同名子目录，这是为了兼容「把 skill 目录直接放进 `.workbuddy/skills/`」的安装方式，同时让 README 能在仓库首页展示。命名保持一致可避免用户混淆。
> 因此本地文件夹 `github-repo/` 与它内部的 `workbuddy-daily-credits/` 是**两层不同的东西**：前者是仓库根，后者是 skill 本体。这也是最容易看错的一处。

### 3. 打 Release（可选但推荐）

```bash
cd <skill 目录的父目录>
# 生成 workbuddy-daily-credits.zip
```

把 zip 上传到 GitHub Release，README 里给下载链接。这样用户既能 `git clone` 也能下 zip。

## 二、让用户「打开就能装」

### 方式 A：对话式安装（推荐，一行话搞定）

用户在 WorkBuddy 里说：

> 帮我安装这个 skill：https://github.com/<用户名>/workbuddy-daily-credits

WorkBuddy 会调用 skill 安装能力拉取并安装。装完直接说「帮我领积分」即可。

### 方式 B：手动放置

```
1. 下载/克隆仓库
2. 把 workbuddy-daily-credits/ 文件夹复制到：
   Windows:  C:\Users\<用户名>\.workbuddy\skills\
3. 重启 WorkBuddy（或新开一个会话）
```

### 方式 C：zip 安装

把 Release 里的 `workbuddy-daily-credits.zip` 交给 WorkBuddy，说「安装这个 skill」。

## 三、「每个人都能成功」的真实边界

这是本发布要诚实交代的部分。已经做到的与仍有限制的：

### ✅ 已解决（v7.5 泛化 + v7.6 结构校正 + v7.7 快路径）

| 问题 | 旧版 | 现在 |
|------|------|------|
| 屏幕分辨率 / 缩放不同 | 硬编码 2582x1402 常量，换机失配 | 按窗口尺寸比例自适应 + 锚点实测 |
| 用户名不同 | 写死「刘潇潇 Sean」，他人必失败 | **纯几何定位**（侧栏 x 带 + 贴底带 + 锚点下方），与姓名格式无关 |
| 窗口被最小化 | rect 为 -32000 哨兵 → 整轮跑飞 | `ShowWindowAsync(SW_SHOWNORMAL)` + 哨兵校验 |
| 主对话区同名文字抢命中 | 点到聊天消息、T2 读到昨天数字 | `panel_region()` 区域限定 |
| UI 状态未复位导致误判 | 在脏帧上推断，结论全错 | `reset_ui_state()` 先于一切读取 |
| 窗口位置 / hwnd 变化 | 依赖固定坐标 | 每次重新查找与自适应 |
| 每轮重复摸索坐标（慢） | 每轮 60–90s 全量定位 | **v7.7 快路径**：本机首次跑通后固化相对坐标，之后一轮约 13s |
| 客户端版本号变化 | 无依赖 | 无依赖 |

> ⚠️ **历史更正**：此前版本曾声称「任务列表过长会把卡片挤出视口，是换台机器最易踩的坑」。
> 该结论**已被实测推翻** —— 账户行与任务列表是两个互不相干的控件，不存在挤压关系。
> 真实根因是「探测前未复位 UI 状态」。此处如实修正，不再把不存在的场景算作"已解决"。

### ⚠️ 仍存在的限制（需在 README 中告知用户）

1. **仅 Windows**。脚本依赖 `PrintWindow` 与 `pywin32`。macOS / Linux 需重写窗口控制层。

2. **依赖客户端 UI 文案**。厂商改文案（如把「立即领取」改成「领取」）会导致找不到按钮。
   → 缓解：SKILL.md 第九节给出了「改版维护指南」，包含抓真实截图 dump OCR、定位需改常量的完整方法。判定逻辑本身不用改。

3. **依赖积分入口结构不变**。「账户行 → 菜单 → Buddy加油站」是当前版本的入口。
   若厂商改了入口形态（例如新增独立入口、或去掉该菜单项），需更新 `open_gas_panel()`。
   → 缓解：脚本保留了卡片直读、整屏 OCR、模板匹配三条兜底路径；troubleshooting 记录了结构变化的排查法。

4. **首次运行需联网**。`rapidocr-onnxruntime` 要下载约 15MB OCR 模型。

5. **必须以已登录的桌面客户端为前提**。未登录 / 未安装客户端无法领取。
   且**客户端需处于可交互状态**（脚本会自行还原最小化窗口）。

6. **本 skill 不自动创建定时任务**。用户装完只获得「能力」，要每天自动需再让 WorkBuddy 建一个定时任务（SKILL.md 第七节已写明指令模板）。

7. **快路径缓存是本机专属的**（`claim_fastpath.json`，存在脚本同目录，已列入 `.gitignore`）。
   它记录的是该机器实测的成功点击坐标，**绝不能随分发包发出**（脚本内建机器指纹 `USERNAME@COMPUTERNAME`
   校验，跨机会自动忽略并按首跑处理）。若改动锚点常量或客户端改版，删掉该文件即可重新固化。

### 🎯 因此，「每个人都能成功」的准确定义是：

- **同一 Windows 平台、同一客户端 UI 版本、已登录** → 装上即可用，无需任何配置
- **客户端改版后** → 需要更新文本锚点，skill 里已内置维护指南，社区可自行修
- **非 Windows** → 暂不支持

README 已如实告知这些边界，避免过度承诺。

## 三b、为什么不走 API 路线（发布前必读）

社区已存在多个**接口直连**方案（`95junminhuang/`、`bearcms-dotcom/`、`sanjingcheng-crypto/`、`kuzen-so/` 等），
它们读本机 `workbuddy-desktop.info` 里的 `accessToken`，直接 POST
`copilot.tencent.com/billing/meter/daily-checkin`。旧版客户端上它们确实更轻更快。

**但从客户端 5.7.7 起该路线已失效**。实测本机该文件：

```jsonc
"accessToken": { "$wbEncrypted": 1, "envelope": "eyJzdWl0ZSI6MSwia2V5SWQiOiI..." }
// 全文件 0 条明文 JWT；refreshToken、nickname 同样加密；仅 account.uid 明文
```

信封为 AES-GCM（含 `keyId` / `nonce` / `authTag` / `ciphertext`），**解密密钥在客户端主进程内**，
不在文件中 —— 外部脚本拿不到。故读明文 token 的方案会直接失败。

**这正是本 skill 走「界面操作 + 状态证据」的合理性所在**：

| 维度 | API 方案 | 本 skill |
|---|---|---|
| 凭据加密后是否可用 | ❌ 失效 | ✅ 不受影响 |
| 锁屏/后台能否跑 | ✅ | ❌ 需可交互桌面 |
| 是否读取凭据 | ✅ 读 token | ✅ 完全不读 |
| 是否依赖 UI 文案 | ❌ 不依赖 | ✅ 依赖（有维护指南） |
| 是否触碰非公开接口 | ✅ 依赖内部接口 | ❌ 只模拟正常点击 |

发布时应在 README 说明这一前提，避免用户误以为"存在更省事的 API 路径却没做"。

## 四、建议的发布检查清单

- [x] SKILL.md 含 `name` / `description` / `agent_created: true`
- [x] `description` 覆盖中英文触发词（中文用户与英文用户都能触发）
- [x] 脚本自包含，无路径硬编码，无外部资产依赖
- [x] 在「无模板、无历史文件」的干净目录实测通过
- [x] v7.6 面板区限定路径实测通过（`面板区域 (1909,927,2842,1321)` → `T2: 13天/1300分`）
- [x] v7.7 快路径实测通过：坏坐标注入 → 自动判失效 → 回退完整流程成功 → 自动重新固化 → 次轮恢复 ~13s
- [x] 跨机缓存防御实测通过（`someone-else@OTHER-PC` → 忽略并按首跑处理）
- [x] 分发 zip 不含 `__pycache__` / 运行时产物（只含 SKILL.md + references + 2 个脚本）
- [x] 安全审计通过（P2，无 P0/P1 实质风险）
- [x] README 含安装、使用、限制、排查入口
- [x] LICENSE（MIT）
- [x] .gitignore 排除运行时产物
- [x] 三处被推翻的旧结论已在 SKILL.md / troubleshooting.md / README 中更正

## 五、后续维护建议

1. **客户端改版后第一时间更新锚点常量**，并在 Release Notes 里写清楚改了哪些字符串。
2. **把新的故障模式追加到 `references/troubleshooting.md`** —— 这份文档是项目最有价值的资产，它记录的是「真的踩过的坑」。
3. **不要为了兼容而回退泛化改造**。例如不要为了让某台机器跑通而重新引入固定坐标或姓名格式假设。
4. **做推断前先复位 UI 状态**。本项目历史上多次误诊都源于在脏帧上推断 —— 这是最高优先级的纪律。
5. 若要支持 macOS，新建分支重写 `print_window` / `find_window` / `activate` 三个函数，判定逻辑（`judge` / 三态）可原样复用。
6. **改锚点后记得删 `claim_fastpath.json`**。固化坐标基于旧锚点推算，锚点一变缓存即失效（脚本会自愈回退，但删掉更干脆）。
