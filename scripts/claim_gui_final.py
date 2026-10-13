#!/usr/bin/env python3
"""
WorkBuddy 每日积分 - GUI 自动化脚本 v7.7（2026-10-13）

v7.7 = **快路径版**：本机首次跑通后固化成功坐标，之后直接复用 → 一轮 39s → ~13s。

═══ v7.7 快路径（2026-10-13）═══════════════════════════════════
问题：每台机器每次都从零「找账户行 → 找菜单项」，且反复对整窗做 OCR
      （实测整窗 8.65s/次，一轮要 8-10 次）→ 一轮 60-90s。
做法：**首次成功后把本机实测坐标固化**到 `claim_fastpath.json`（相对量），
      之后直接复用；同时把 OCR 全部限制到侧栏/窄条区域。
效果实测：完整流程 39s → 快路径 **12.75s**（原口径 60-90s → 5-7x）。

⚠⚠ 三条铁律（缺一条就是把用户机器变成"能跑但某天突然永久失败"的雷）：
  1. **快路径只省「定位」，绝不省「判定」**。面板状态仍由 `claim_on_panel()` 用
     与完整流程**完全相同**的 T1/T2 标准判定 —— 不存在"快路径放松了校验"。
  2. **点账户行后必须校验菜单真的弹出来了**。缓存坐标一旦点偏，可能落到别的
     菜单项上 → 必须校验，不符立刻放弃。
  3. **任何一步不符预期 → 立即标记失效 + 回退完整流程**。缓存只能加速，
     绝不能成为单点故障。这是「换台用户也能成功」的底线。
  已实测：注入坏坐标 → 快路径检出失效 → 回退完整流程成功 → **自动重新固化正确坐标**。

失效与自愈：
  - 缓存文件缺失/损坏/schema 不符 → 静默忽略，走完整流程（已在 header 记录）
  - 窗口尺寸与固化时差 > 80px → 本次不用缓存（不删；成功后会用新尺寸重新固化）
  - 单次校验失败 → fail_streak+1；**连续 2 次**才真正删除（防偶发误删）
  - 成功固化时会重建记录 → fail_streak 自动清零

配套优化（一起做才有 3x 效果）：
  - `sidebar_region()` / `read_sidebar()`：只 OCR 侧栏区（3.10s vs 整窗 8.65s）
  - `read_narrow()`：快路径只 OCR 窄条（面板带 1.36s / 菜单带 2.45s）
  - 快路径刻意放在 `reset_ui_state()` / `ensure_live_ui()` **之前**（省 ~11s）：
    快路径自带强校验，异常会回退，回退后完整流程再做这两步。
  - `parse_t2()` 改为**先按行合并再解析**：窄条 OCR 会把「已领13天」切成
    「已领」+「13天」并打乱顺序，逐条正则必然漏读 → T2 证据丢失（已修）。

═══ v7.6 = 泛化版 + UI 结构实测校正版 ═══════════════════════════
详见下方「⚠ 重要：纠正三处此前的错误认知」。

═══ ⚠ 重要：纠正三处此前的错误认知（2026-10-13 实测推翻）═══════════
以下三条是作者此前写进文档/代码的**错误结论**，已用截图 + OCR 双重实测推翻，
任何后续维护者请勿再沿用：

1. ❌「侧栏底部固定有一张积分卡片（Buddy加油站·N期 / 今日可领100积分）」
   → ✅ **错**。干净主界面的侧栏底部**只有账户行 + 2 个图标**，没有任何积分卡片。
     那张卡片是**点击账户行后弹出的覆盖层**，不是侧栏的常驻元素。
2. ❌「任务列表很长时会把卡片挤出视口（45 个任务即复现）」
   → ✅ **错**。账户行与任务列表是**两个互不相干的控件**，不存在挤压关系。
     该结论源于「探测前未复位 UI 状态」导致的脏帧误判（见第 3 条）。
3. ❌「账户名按『中文名 + 空格 + 英文名』特征识别」
   → ✅ **错**。识别 UI 元素不该猜内容格式（用户可用纯英文/纯中文/邮箱/表情）。
     现改为**纯几何定位**：侧栏 x 带 ∩ 距底边 < 0.09H ∩ 位于面板锚点下方。

以上错误的共同根因：**在 UI 状态未复位的情况下探测**，抓到的不是主界面帧。
故新增 `reset_ui_state()`，**先于一切读取**执行。

═══ 实测确认的积分入口结构（v7.6 权威描述）═══════════════════════
    侧栏底部： `...空间(19) / <任务项> / 「<用户名>」  [🔔] [💬]`
                   ↓ 点击账户行
    弹出账户菜单（自上而下）：
        套餐 / 积分余额 / [升级套餐]
        **Buddy加油站**（每日领积分）      ← 积分入口
        去邀约 / 成长计划
        设置 / 外观 / 记忆与进化 / 意见反馈 / 检查更新 / 退出登录
                   ↓ 点击「Buddy加油站」
    打开**积分面板**（覆盖在侧栏下半部）：
        Buddy应用 / 100 / 每日可领通用积分
        已领N天 / 累计领取N分               ← T2 证据
        Buddy加油站·N期  N/N结束
        [立即领取]  或  [今日已领] [体验Buddy应用]   ← 按钮
故 **账户菜单路径 = 主路径**（唯一可靠入口），面板是它的产物。

═══ v7.6 关键修复：面板区限定（防对话区同名文字假阳性）═══════════
- 现象：面板打开时，主对话区可能正显示含「立即领取 / 今日已领 / 已领12天」的
  **历史汇报文本**（本自动化的输出、或用户聊积分），其 OCR 分数（0.92）**高于**
  面板真实读数（0.70-0.86）。
- 后果：best_hit 选中对话区坐标 → 点击落在聊天消息上（实测点 (2850,161)/(3400,477)）
  → 永远点不到按钮；parse_t2 还会读到**昨天的数字**（12天/1200 vs 真实13天/1300）。
- 修复：`panel_region()` 用**面板专属锚点**（「Buddy加油站·N期」「每日可领通用积分」
  「累计领取」）反推面板矩形；`panel_state()` / `parse_t2()` 一律**只在区域内**取候选。

═══ v7.5 泛化改造（保留有效部分）═════════════════════════════════
A) **自适应几何**：删除对固定像素的依赖。
   - 旧版 SIDEBAR_W=380 / CARD_H=340 是「本机 2582x1402 副屏最大化」量出的常量，
     换分辨率/缩放/窗口形态即失配。
   - 现改为按窗口尺寸比例估算（sidebar_w/card_h）+ clamp，并用 OCR 锚点实测纵带
     （card_band 按命中行距动态外扩），不再假设卡片高度。
B) **几何账户识别**：`find_account_hit()` 不写死用户名、不猜姓名格式。
   - 判据：侧栏 x 带 ∩ 距底边 < 0.09H（实测账户行 0.044H、其上方最近项 0.101H，
     2.3 倍间隔）∩ 位于面板锚点下方。**纯几何，与用户怎么起名无关。**
   - ⚠ 历史踩坑：曾用 norm_txt 后按空格切分判「中文+英文尾」，既假设了姓名格式，
     又因 norm_txt 删空格使「刘潇潇 Sean」粘连成「刘潇潇Sean」而必然失败。已废弃。
C) **产物固定文件名、原地覆盖**：`claim_pre.png` / `claim_result.png` / `claim_diag.png`。
   - 历史教训：曾按日期命名 evidence_YYYYMMDD_*.png → 2 周堆积 97 张 PNG / 56MB。
   - 复盘只需「最近一轮」的前后态，旧轮次价值极低。
D) **窗口还原修正**：最小化窗口的 `GetWindowRect` 返回 **-32000 哨兵**（本机 DPI 下
   为 -21333），`capture()` 会得到 237x39 的**假帧**。
   - `win32gui.ShowWindow(SW_RESTORE)` 对最小化窗口**无效**（实测 iconic 仍 1）；
     `ShowWindowAsync(SW_RESTORE)` 时灵时不灵（与最小化动画竞态）；
     **`ShowWindowAsync(SW_SHOWNORMAL)` 稳定生效**。按此顺序尝试并逐步校验。
   - `activate()` 在还原后校验 rect 是否仍为哨兵并告警。

═══ v7.4 关键修复（2026-10-08，务必保留）═════════════════════════
**侧栏底部「新版本就绪 / 更新日志 / 重启升级」更新提示条 → OCR 假阳性 → 点错坐标**
- 症状：真按钮明明可点，脚本却连点 10 次全部落空。
- 真因：更新条贴侧栏最底，该区域 OCR 吐出假阳性「立即领取」（分数高于真按钮）
  → best_hit 选中错点。
- 修复：`sanitize_hits()` 剔除更新条水平带（锚点 y±28）内命中；`card_band()` 以锚点
  求纵带，`judge()` 只认纵带内候选（**同时防噪声伪造 S2 → 假 ALREADY_DONE**）；
  `dismiss_update_bar()` 关闭更新条（⚠ 绝不点「重启升级」）。

═══ v7.4 关键修复（2026-10-08，务必保留）═════════════════════════
**侧栏底部「新版本就绪 / 更新日志 / 重启升级」更新提示条 → OCR 假阳性 → 点错坐标**
- 症状：卡片明明 S1（真按钮 @(204,939)），脚本却连点 10 次全部落空，每次点击后仍 S1。
- 真因：更新条固定贴侧栏最底（y≈1005–1045，并**盖住账户行**），该区域 OCR 吐出
  假阳性「立即领取」@(324,1030) s=0.75（分数高于真按钮）→ best_hit 选中错点。
- 修复：`sanitize_hits()` 剔除更新条水平带（锚点 y±28）内命中；`card_band()` 以卡片锚点
  求纵带，`judge()` 只认纵带内候选（**同时防噪声伪造 S2 → 假 ALREADY_DONE**）；
  路径 3 同规则；`dismiss_update_bar()` 关闭更新条（T2 复核前用，⚠ 绝不点「重启升级」）；
  首读即 S2 的早退分支也落盘 claim_result.png。


═══ v7 关键修复（务必保留）═════════════════════════════════════════
0) **修复 v6 的致命坐标 BUG（2026-10-01 定位，导致 10-01 首跑 UNKNOWN）**
   v6 的 in_panel(cx, cy, rect) 写成：
       rect[0] <= cx <= rect[0]+SIDEBAR_W  and  cy >= rect[1] + CARD_Y_MIN
   但调用处传入的是**卡片 box** `cb=(l, b-CARD_H, l+360, b)`，其 top 已是绝对坐标
   ~1071，再 +CARD_Y_MIN(1000) → 要求 cy>=2071 → **卡片内所有 OCR 命中被全部过滤**，
   因此永远 judge 不出 'claim'/'done'，脚本必然掉到 Step3/4 的无效兜底
   （点「Buddy加油站」标题文字 + 点「做任务赢积分好礼」跳网页），最终 UNKNOWN。
   修复：判定一律用**绝对坐标矩形** in_box(cx,cy,(x0,y0,x1,y1))，彻底删除
   SIDEBAR_W/CARD_Y_MIN 这套"相对+绝对混用"的错误写法。

1) **证据链升级：T1 状态跃迁 + T2 数值证据**
   - T1（主判据）：「立即领取」→ 点击 → 变为「今日已领」且按钮消失 ⇒ SUCCESS
   - T2（最强）：「已领 N 天 / 累计领取 N 分」点击前后 +1 天 / +100 分 ⇒ SUCCESS
   - 初始即 S2 ⇒ ALREADY_DONE；两者皆无 ⇒ S3（导航失败）⇒ 换路径重试，**不得结案**

2) **必须的 WebDriver 式约束**
   - 一律 PrintWindow(PW_RENDERFULLCONTENT=2) 抓窗口自身内容，免疫遮挡
     （屏幕区域截图会把 Edge/微信画面当证据 → 假成功/假失败）
   - 只点「立即领取」按钮；「Buddy加油站-10期」是标题文字，点了无效（勿点）
   - 卡片 OCR 只取左下角卡片 box，屏蔽聊天正文里的同名文字

═══ v4/v5/v6 保留的修复 ══════════════════════════════════════════
3) DPI 感知：进程启动即 SetProcessDpiAwareness(2)（per-monitor v2）。
   根因（2026-09-25）：主屏 1920x1080@150%、副屏 2560x1440@100%；DPI-unaware 时
   GetWindowRect 返回 1.5 倍矩形（2582x1422→3873x2133），导致 OCR 失败、点击落空。
4) 不无条件 SW_MAXIMIZE；仅在最小化/未最大化时才恢复。
5) 侧栏可能折叠 ⇒ OCR 找不到入口时滚动侧栏到底部再判。

依赖：pyautogui, mss, Pillow, pywin32, opencv-python, rapidocr-onnxruntime
运行：python claim_gui_final.py   （务必用系统 Python 3.14）
退出码：0 = SUCCESS / ALREADY_DONE；1 = UNKNOWN（= agent 没搞定，必须重试）
"""
import ctypes

def _set_dpi_aware():
    """必须在导入 pyautogui / 使用任何 GDI 坐标之前调用。"""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)   # per-monitor v2
        return "per-monitor-v2"
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        return "system"
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        return "legacy"
    except Exception:
        return "none"


DPI_MODE = _set_dpi_aware()

import json
import os
import re
import sys
import time
import numpy as np

try:
    import pyautogui
    import mss
    import cv2
    from PIL import Image
    import win32gui
    import win32con
    import win32api
    import win32process
    from rapidocr_onnxruntime import RapidOCR
except ImportError as e:
    print(f"[FATAL] 缺少依赖: {e}")
    sys.exit(2)

pyautogui.FAILSAFE = False

BASE = os.path.dirname(os.path.abspath(__file__))
# 产物一律**固定文件名、原地覆盖**（2026-10-13 改造）。
# 历史教训：曾按日期命名 evidence_YYYYMMDD_*.png，导致 2 周堆积 97 张 PNG / 56MB。
# 复盘只需要「最近一轮」的前后态与日志，旧轮次价值极低 → 不再按日期落盘。
OUTPUT_RESULT = os.path.join(BASE, "claim_result.png")   # 点击后 / 终态（覆盖）
PRE_RESULT = os.path.join(BASE, "claim_pre.png")         # 点击前 S1（覆盖）
GROWTH_SHOT = os.path.join(BASE, "claim_diag.png")       # 路径 3 整屏诊断图（覆盖）
BLACK_BTN_TPL = os.path.join(BASE, "claim_btn_black.png")
RUN_LOG = os.path.join(BASE, "claim_run.log")            # 运行日志（覆盖，非追加）

# ═══════════ v7.7 快路径缓存（2026-10-13）═══════════
# 目标：每台机器**首次跑通后**，把「这台机器上实测的成功坐标」固化下来，
#      之后直接复用 → 跳过绝大部分探测。配合区域 OCR，一轮从 60-90s 降到 ~15s。
#
# ⚠ 三条铁律（缺一条就是把用户机器变成"能跑但某天突然永久失败"的雷）：
#   1. **快路径仍必须做状态校验（T1/T2）**。省掉的只能是「定位」的 OCR，
#      绝不能省「判定」—— 否则会把已领当成领到，或把 UI 改版当成成功。
#   2. **点击账户行后必须验证菜单真的弹出来了**。缓存的坐标一旦点偏，
#      可能落到别的菜单项上（如「退出登录」）→ 必须校验，不符合立刻放弃。
#   3. **任何一步不符预期 → 立即判缓存失效 + 回退完整流程**。
#      缓存只能"加速"，绝不能成为"单点故障"。这是「换台用户也能成功」的底线。
#
# 缓存只存**相对量**（距左/距底/相对账户行的位移），不存绝对坐标 ——
# 窗口移动、副屏切换都不会让它失效。客户端改版会体现为校验失败 → 自动回退。
FASTPATH_FILE = os.path.join(BASE, "claim_fastpath.json")
FASTPATH_SCHEMA = 1

# 本次运行中**实测到**的导航坐标（账户行 / Buddy加油站菜单项），
# 由 open_gas_panel() 填写；main() 在**确认领取成功后**用它固化快路径缓存。
# 用模块级变量是为了不改动现有函数签名（改动面最小）。
_LAST_NAV = {}

OCR_ENGINE = RapidOCR()

KEY_CLAIM = "立即领取"
KEY_DONES = ("今日已领", "今日已领取", "今日已签到", "已签到", "已领取")
KEY_STREAKS = ("连续登录", "已连登")

# 2026-10-08 实测：客户端「新版本就绪 / 更新日志 / 重启升级」更新提示条固定贴在
# 侧栏最底部（会盖住账户行），该区域 OCR 会吐出「立即领取」等假阳性文本
# （窗口相对 y≈1030，而卡片真按钮在 y≈939）→ best_hit 选中错坐标、连点无效。
# 判定：命中里出现更新条锚点时，剔除锚点水平带（±28px）内的所有命中。
KEY_UPDATE_BAR = ("新版本就绪", "重启升级", "更新日志")
KEY_CARD_ANCHOR = ("Buddy加油站", "今日可领100积分", "Buddy应用")


def sanitize_hits(hits):
    """剔除更新提示条带造成的假阳性命中（见 KEY_UPDATE_BAR 注释）。"""
    bars = [h for h in hits if any(k in norm_txt(h[3]) for k in KEY_UPDATE_BAR)]
    if not bars:
        return hits
    bands = [(h[1] - 28, h[1] + 28) for h in bars]
    kept = [h for h in hits if not any(a <= h[1] <= b for a, b in bands)]
    return kept


def card_band(hits):
    """以卡片锚点（Buddy加油站 / 今日可领100积分 / Buddy应用）求卡片纵带 (y0, y1)；
    无锚点返回 None。

    2026-10-13：上下余量由「像素常量」改为按命中行距动态外扩，
    使本函数在不同字号/缩放下同样成立。
    """
    anchors = [h for h in hits if is_card_hit(h)]
    if not anchors:
        return None
    ys = [h[1] for h in anchors]
    span = max(ys) - min(ys)
    pad = max(90, min(int(span * 0.75) + 80, 200))   # 自适应余量
    return (min(ys) - pad, max(ys) + pad)


# OCR 常见形近字混淆：2026-10-01 实测「今日已领」被识别成「今日已额」，
# 导致点击后的 S2 判定失败（这是 v7 首跑回退到路径2 的原因）。
# 仅用于关键词匹配前的归一化，不影响坐标。
_CONFUSABLE = {"额": "领"}


def norm_txt(s):
    s = (s or "").replace(" ", "")
    return "".join(_CONFUSABLE.get(c, c) for c in s)

# ⚠ 以下常量描述的是**侧栏底部区域**，不是「常驻积分卡片」。
# 实测（2026-10-13）：侧栏底部常态只有账户行 + 2 个图标，没有积分卡片；
# 积分卡片是点账户行后弹出的覆盖层。这些常量用于给「账户行/面板」圈定大致范围。
# 2026-10-13 泛化改造：不再假设固定像素尺寸。
#   旧版 SIDEBAR_W=380 / CARD_H=340 是「本机 2582x1402 副屏最大化」时量出来的常量，
#   换台机器（不同分辨率 / 缩放 / 窗口是否最大化）就会失配。
#   现在改为：① 按窗口尺寸的比例估算；② 用 OCR 锚点实测校正。
SIDEBAR_W = 380          # 侧栏宽度的**保守上限**（比例估算失败时的兜底）
CARD_H = 340             # 侧栏底部区域的**保守上限**（同上）
SIDEBAR_RATIO = 0.16     # 侧栏宽 ≈ 窗口宽 × 0.16（实测 380/2582≈0.147，取 0.16 留余量）
SIDEBAR_MAX = 520        # 侧栏宽度上限（防宽屏下比例估算过大）
CARD_RATIO = 0.26        # 卡片区高 ≈ 窗口高 × 0.26（实测 340/1402≈0.243）


def sidebar_w(rect):
    """自适应侧栏宽度：按窗口宽度比例估算，clamp 到 [260, SIDEBAR_MAX]。"""
    return max(260, min(int((rect[2] - rect[0]) * SIDEBAR_RATIO), SIDEBAR_MAX))


def card_h(rect):
    """自适应卡片区高度：按窗口高度比例估算，clamp 到 [240, 460]。"""
    return max(240, min(int((rect[3] - rect[1]) * CARD_RATIO), 460))



def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ────────────────────────────── 窗口 ──────────────────────────────
def find_window():
    """查找 WorkBuddy 桌面客户端主窗口（严格排除浏览器）。

    v7.2（2026-10-05）：主窗口可能被隐藏到托盘/被外部脚本 SW_HIDE
    （IsWindowVisible=False 但窗口存在，PrintWindow 抓不到有效内容，
    屏幕截图也拍不到）。此类窗口一并返回（排在可见窗口之后），
    由 activate() 先 SW_SHOW 恢复。2026-10-05 实测：00:02 窗口被隐藏后
    v7.1 因只收集可见窗口而误报 NO_WINDOW。
    """
    vis, hid = [], []
    stats = {"min": 0}

    def cb(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if "WorkBuddy" not in title:
            return
        if any(b in title for b in ("Microsoft Edge", "Google Chrome", "Mozilla Firefox")):
            return
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            h = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, pid)
            exe = win32process.GetModuleFileNameEx(h, 0)
            win32api.CloseHandle(h)
            if any(b in exe.lower() for b in ("msedge.exe", "chrome.exe", "firefox.exe")):
                return
        except Exception:
            pass
        # 只认真正的主窗口类（Chrome_WidgetWin_1），排除 0x0 的辅助窗口
        try:
            if win32gui.GetClassName(hwnd) != "Chrome_WidgetWin_1":
                return
        except Exception:
            return
        # v7.5.2：最小化窗口的 GetWindowRect 返回 -32000 哨兵，
        # capture() 会得到假帧 → 必须识别出来，交给 activate() 用
        # ShowWindowAsync 还原，绝不能拿它的 rect 当真值。
        if win32gui.IsIconic(hwnd):
            stats["min"] += 1
        (vis if win32gui.IsWindowVisible(hwnd) else hid).append((hwnd, title))

    win32gui.EnumWindows(cb, None)
    if stats["min"]:
        log(f"[find_window] 注意：{stats['min']} 个候选窗口处于最小化（rect 为 -32000 哨兵）")
    # 可见且非最小化的排最前，避免选到最小化的假窗口
    vis.sort(key=lambda w: win32gui.IsIconic(w[0]))
    return vis + hid


def activate(hwnd):
    """恢复+置前。置前失败也返回当前是否前台（PrintWindow 不依赖前台）。

    v7.2：隐藏窗口必须先 SW_SHOW（SW_RESTORE 对 hidden 窗口不够），
    否则 PrintWindow 抓到黑帧/旧帧，OCR 全部落空。
    v7.5.2（2026-10-13 实测修复）：**最小化窗口必须用 ShowWindowAsync**。
      win32gui.ShowWindow(hwnd, SW_RESTORE) 对 minimized 窗口**无效**（实测返回后
      IsIconic 仍为 1），而 minimized 窗口的 GetWindowRect 返回 -32000 哨兵值
      （本机 DPI 缩放下是 -21333）→ capture() 得到 237x39 的假帧 →
      后续所有 OCR/推断全部建立在垃圾数据上（一次实测整轮跑飞即由此而来）。
      ShowWindowAsync(hwnd, SW_RESTORE) 才真正还原（实测 iconic 1 → 0）。
    """
    u = ctypes.windll.user32
    if win32gui.IsIconic(hwnd):
        # ⚠ 必须用 ShowWindowAsync + SW_SHOWNORMAL，且**校验生效**。
        #   实测（2026-10-13）：
        #     - win32gui.ShowWindow(SW_RESTORE)  对 minimized 窗口**无效**（iconic 仍 1）
        #     - ShowWindowAsync(SW_RESTORE)      时灵时不灵（与最小化动画存在竞态）
        #     - ShowWindowAsync(SW_SHOWNORMAL)   稳定生效（iconic 1 → 0）
        #   故按 SW_SHOWNORMAL → SW_RESTORE → SetWindowPos 依次尝试，每步校验。
        for cmd in (win32con.SW_SHOWNORMAL, win32con.SW_RESTORE):
            u.ShowWindowAsync(hwnd, cmd)
            time.sleep(1.2)
            if not win32gui.IsIconic(hwnd):
                break
        if win32gui.IsIconic(hwnd):
            # 最后一招：SetWindowPos + SWP_SHOWWINDOW，把窗口搬回可见区
            u.SetWindowPos(hwnd, 0, 200, 100, 1400, 900,
                           0x0040 | 0x0001 | 0x0002 | 0x0020)
            time.sleep(1.0)
    if not win32gui.IsWindowVisible(hwnd):
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        except Exception:
            pass
        time.sleep(0.6)
    # 校验：还原后 rect 不应再是 -32000 哨兵
    _l, _t, _r, _b = win32gui.GetWindowRect(hwnd)
    if _l <= -32000 or _t <= -32000:
        log(f"[activate] 警告：还原后矩形仍为哨兵 {(_l,_t,_r,_b)}（窗口仍最小化/不可用）")
    if not u.IsZoomed(hwnd):
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        except Exception:
            pass
        time.sleep(0.4)
    u.AllowSetForegroundWindow(-1)
    u.keybd_event(0, 0, 0, 0)
    for _ in range(8):
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
        if u.GetForegroundWindow() == hwnd:
            return True
        time.sleep(0.3)
    return u.GetForegroundWindow() == hwnd


# ═══════════════ v7.3（2026-10-06 实测定位并修复）渲染层 wedged 自愈 ═══════════════
# 新故障模式（比「窗口被隐藏」更隐蔽）：
#   WorkBuddy 主窗口**可见、标题正常、消息循环正常**（WM_NULL 有响应、可最小化/还原），
#   但其 **renderer 进程挂死** → 窗口不再重绘（hover / 合成点击 / WM_SIZE 均 0 像素变化），
#   PrintWindow 返回**陈旧帧**（与上一天截图逐像素相同，maxdiff=0）。
#   合成鼠标点击被丢弃 → 「立即领取」永远点不到。
# 危害：卡片显示的是**上一天**的「今日已领」，据此判定会得到**假 ALREADY_DONE → 漏领**。
# 2026-10-06 实测：窗口帧与 10-05 01:37 帧逐像素相同；日界后卡片仍显示「今日已领」。
#   杀 renderer → Electron 自动拉起新 renderer 并重载页面 → 卡片立刻回到真实状态
#   「立即领取」（当日确实未领）→ 点击领取成功（S1→S2），面板 T2 证据
#   「已领 6 天 / 累计领取 600 分 / 今日已领」。
# 安全前提：本 agent 会话由 daemon-app-server / codebuddy CLI 承载（**不在 renderer 内**），
#   故重启 renderer 不会中断本任务；脚本事先排除自身祖先链，绝不误杀宿主进程。
_UI_LIVE_DIFF_MIN = 3000      # 探针点击后判定「UI 活着」的最小像素变化量
_RENDERER_WAIT = 30           # 等待新 renderer + 新窗口出现的秒数


def _img_diff(a, b):
    try:
        if a is None or b is None:
            return 0
        if a.size != b.size:
            return 10 ** 9
        na = np.asarray(a.convert("RGB"), dtype=np.int16)
        nb = np.asarray(b.convert("RGB"), dtype=np.int16)
        return int((np.abs(na - nb).sum(axis=2) > 30).sum())
    except Exception:
        return 0


def _ancestor_pids():
    """自身进程的祖先链（含自身），用于避免误杀承载本会话的进程。"""
    TH32CS_SNAPPROCESS = 2

    class _PE(ctypes.Structure):
        _fields_ = [("dwSize", ctypes.c_uint32), ("cntUsage", ctypes.c_uint32),
                    ("th32ProcessID", ctypes.c_uint32), ("th32DefaultHeapID", ctypes.c_void_p),
                    ("th32ModuleID", ctypes.c_uint32), ("cntThreads", ctypes.c_uint32),
                    ("th32ParentProcessID", ctypes.c_uint32), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", ctypes.c_uint32), ("szExeFile", ctypes.c_char * 260)]
    k = ctypes.windll.kernel32
    snap = k.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    e = _PE()
    e.dwSize = ctypes.sizeof(_PE)
    parent = {}
    ok = k.Process32First(snap, ctypes.byref(e))
    while ok:
        parent[e.th32ProcessID] = e.th32ParentProcessID
        ok = k.Process32Next(snap, ctypes.byref(e))
    chain, pid = set(), k.GetCurrentProcessId()
    for _ in range(12):
        if not pid or pid in chain:
            break
        chain.add(pid)
        pid = parent.get(pid, 0)
    return chain


def _wb_procs():
    """{pid: (ppid, cmdline)}；用 WMI（win32com），失败返回 {}。"""
    out = {}
    try:
        import win32com.client
        wmi = win32com.client.GetObject("winmgmts:")
        rows = wmi.ExecQuery(
            "SELECT ProcessId,ParentProcessId,CommandLine FROM Win32_Process "
            "WHERE Name='WorkBuddy.exe'")
        for r in rows:
            out[int(r.ProcessId)] = (int(r.ParentProcessId or 0), r.CommandLine or "")
    except Exception as exc:
        log(f"[revive] WMI 枚举失败: {exc}")
    return out


def _restart_renderer(main_hwnd):
    """杀掉挂死的 renderer，等待 Electron 拉起新 renderer 并重载页面。
    返回新窗口 hwnd（失败返回 None）。"""
    import subprocess
    chain = _ancestor_pids()
    procs = _wb_procs()
    if not procs:
        log("[revive] 无法枚举进程，放弃自愈")
        return None
    try:
        _, main_pid = win32process.GetWindowThreadProcessId(main_hwnd)
    except Exception:
        main_pid = None
    victims = []
    for pid, (ppid, cmd) in procs.items():
        if "--type=renderer" not in cmd:
            continue
        if pid in chain:                       # 绝不误杀自身宿主
            continue
        if main_pid and ppid != main_pid:      # 只认主进程的直接子 renderer
            continue
        victims.append(pid)
    if not victims:
        log("[revive] 未找到可重启的 renderer（命令行为空的旧版 Electron 会走此分支）")
        return None
    log(f"[revive] 重启 renderer: {victims}（主进程 {main_pid}）")
    for pid in victims:
        try:
            r = subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                               capture_output=True, text=True, timeout=20)
            log(f"[revive]   taskkill {pid} → {(r.stdout or r.stderr or '').strip()}")
        except Exception as exc:
            log(f"[revive]   taskkill {pid} 异常: {exc}")
    log("[revive] 等待新窗口/页面重载 …")
    old = main_hwnd
    for _ in range(_RENDERER_WAIT):
        time.sleep(1.0)
        wins = find_window()
        if wins and wins[0][0] != old:
            log(f"[revive] 新窗口出现 hwnd={wins[0][0]}")
            time.sleep(2.5)                    # 等页面首屏渲染
            return wins[0][0]
    log("[revive] 未监测到新窗口（原窗口可能已就地重载）")
    wins = find_window()
    return wins[0][0] if wins else None


def ensure_live_ui(hwnd):
    """v7.3：检测渲染层是否 wedged（点击无重绘 = 陈旧帧），是则重启 renderer。
    返回 (hwnd, revived)。"""
    snap = print_window(hwnd)
    if snap is None:
        return hwnd, False
    pil0, rect0 = snap
    hits = ocr_pil(pil0, rect0[0], rect0[1])
    probe = None
    for kw in ("更多", "资料库", "定时任务", "助理", "项目"):
        for h in hits:
            if norm_txt(h[3]).strip() == kw:
                probe = h
                break
        if probe:
            break
    if not probe:
        log("[live] 未找到探针项，跳过 wedged 检测")
        return hwnd, False
    log(f"[live] 探针：点击侧栏「{probe[3]}」({probe[0]},{probe[1]})")
    click(probe[0], probe[1], "probe")
    time.sleep(2.4)
    snap2 = print_window(hwnd)
    if snap2 is None:
        return hwnd, False
    d = _img_diff(pil0, snap2[0])
    log(f"[live] 探针重绘像素差 = {d}（阈值 {_UI_LIVE_DIFF_MIN}）")
    if d >= _UI_LIVE_DIFF_MIN:
        click(probe[0], probe[1], "probe-back")     # 尽量还原原状态
        time.sleep(1.6)
        log("[live] 渲染层存活，继续正常流程")
        return hwnd, False
    log("[live] ⚠ 渲染层 wedged（点击无任何重绘）→ 重启 renderer 自愈")
    new = _restart_renderer(hwnd)
    if not new:
        log("[live] 自愈失败，将在陈旧帧上继续（预计判 UNKNOWN）")
        return hwnd, False
    return new, True


class _BMIH(ctypes.Structure):
    _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32),
                ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16),
                ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32),
                ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_int32),
                ("biYPelsPerMeter", ctypes.c_int32), ("biClrUsed", ctypes.c_uint32),
                ("biClrImportant", ctypes.c_uint32)]


def print_window(hwnd):
    """PrintWindow(PW_RENDERFULLCONTENT=2) 抓窗口自身内容。
    返回 (PIL_Image, (l,t,r,b)) 或 None。"""
    try:
        l, t, r, b = win32gui.GetWindowRect(hwnd)
    except Exception:
        return None
    w, h = r - l, b - t
    if w <= 0 or h <= 0:
        return None
    hdc = ctypes.windll.user32.GetWindowDC(hwnd)
    mdc = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
    bmp = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, w, h)
    ctypes.windll.gdi32.SelectObject(mdc, bmp)
    # PW_RENDERFULLCONTENT = 0x2（可抓到 DirectComposition 渲染内容）
    ok = ctypes.windll.user32.PrintWindow(hwnd, mdc, 2)
    bi = _BMIH()
    bi.biSize = ctypes.sizeof(_BMIH)
    bi.biWidth, bi.biHeight = w, -h        # 负高 = 自顶向下
    bi.biPlanes, bi.biBitCount, bi.biCompression = 1, 32, 0
    buf = ctypes.create_string_buffer(w * h * 4)
    ctypes.windll.gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    ctypes.windll.gdi32.DeleteObject(bmp)
    ctypes.windll.gdi32.DeleteDC(mdc)
    ctypes.windll.user32.ReleaseDC(hwnd, hdc)
    if not ok:
        return None
    arr = np.frombuffer(buf, dtype=np.uint8).reshape((h, w, 4))
    return Image.fromarray(arr[:, :, [2, 1, 0]]), (l, t, r, b)


def virtual_screen():
    u = ctypes.windll.user32
    return (u.GetSystemMetrics(76), u.GetSystemMetrics(77),
            u.GetSystemMetrics(76) + u.GetSystemMetrics(78),
            u.GetSystemMetrics(77) + u.GetSystemMetrics(79))


def grab_screen_fallback(hwnd):
    """PrintWindow 失败时的兜底（屏幕区域截图）。"""
    l, t, r, b = win32gui.GetWindowRect(hwnd)
    try:
        mi = win32api.GetMonitorInfo(
            win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST))
        wa = mi["Work"]
        l, t = max(l, wa[0]), max(t, wa[1])
        r, b = min(r, wa[2]), min(b, wa[3])
    except Exception:
        pass
    vx0, vy0, vx1, vy1 = virtual_screen()
    l, t = max(l, vx0), max(t, vy0)
    r, b = min(r, vx1), min(b, vy1)
    if r <= l or b <= t:
        l, t, r, b = win32gui.GetWindowRect(hwnd)
    with mss.mss() as sct:
        img = sct.grab({"left": int(l), "top": int(t), "width": int(r - l), "height": int(b - t)})
        return Image.frombytes("RGB", img.size, img.rgb), (l, t, r, b)


def capture(hwnd):
    """返回 (PIL_Image, (l,t,r,b))，优先 PrintWindow。"""
    res = print_window(hwnd)
    if res:
        pil, rect = res
        return pil, rect
    return grab_screen_fallback(hwnd)


# ────────────────────────────── OCR ──────────────────────────────
def ocr_pil(pil, ox=0, oy=0, min_score=0.0):
    """OCR 一张图，返回 [(cx, cy, score, text)]（绝对坐标 = 内部坐标 + 偏移）。"""
    img = np.array(pil.convert("RGB"))
    res, _ = OCR_ENGINE(img)
    out = []
    for item in (res or []):
        pts = np.array(item[0], dtype=np.float32)
        try:
            sc, txt = float(item[2]), str(item[1])
        except Exception:
            sc, txt = float(item[1]), str(item[2])
        if sc < min_score:
            continue
        out.append((int(pts[:, 0].mean()) + ox, int(pts[:, 1].mean()) + oy, sc, txt))
    return out


def in_box(hit, box):
    """绝对坐标矩形包含判定（v7：修正了 v6 的相对/绝对混用 bug）。"""
    x0, y0, x1, y1 = box
    return x0 <= hit[0] <= x1 and y0 <= hit[1] <= y1


def card_box(rect):
    """侧栏**底部区域**的绝对坐标矩形（自适应窗口尺寸）。

    ⚠ 措辞更正（2026-10-13）：此区域**并非**「常驻积分卡片」的位置。
    实测：侧栏底部常态只有账户行，没有积分卡片。本函数给出的是侧栏底部区域，
    卡片若存在（部分版本/页面）会落在此区域或其稍上方；不存在时靠账户菜单路径。
    """
    l, t, r, b = rect
    return (l, max(t, b - card_h(rect)), min(l + sidebar_w(rect), r), b)


def is_card_hit(hit):
    """卡片锚点特征判定：用于从「未知窗口」中反推卡片区实际位置。

    2026-10-13 新增。文案锚点独立于任何像素常量，故可跨机器复用。
    """
    t = norm_txt(hit[3])
    return any(k in t for k in KEY_CARD_ANCHOR)


def measure_card_band(hwnd):
    """实测卡片纵带：找卡片锚点后取其 y 邻域。

    2026-10-13 新增。比按比例估算的 card_box() 更准 —— 锚点在哪，卡片就在哪，
    彻底摆脱「卡片高度必须是 340px」这类硬编码假设。
    返回 (y0, y1) 或 None。
    """
    pil, rect = capture(hwnd)
    if pil is None:
        return None
    hits = ocr_pil(pil, rect[0], rect[1])
    anchors = [h for h in hits if is_card_hit(h)]
    if not anchors:
        return None
    ys = [h[1] for h in anchors]
    # 卡片是竖向一叠文字：锚点行上方留标题行余量，下方留按钮行余量
    return (min(ys) - 120, max(ys) + 90)



def read_card(hwnd, rect=None):
    """读卡片区，返回 (hits_in_card, card_box, full_pil, full_rect)。
    第二遍：对按钮条（卡片右下）放大 3x 复扫，提升灰底胶囊小字识别率。"""
    pil, rect = capture(hwnd)
    box = card_box(rect)
    x0, y0, x1, y1 = box
    crop = pil.crop((x0 - rect[0], y0 - rect[1], x1 - rect[0], y1 - rect[1]))
    hits = ocr_pil(crop, x0, y0)
    cw, ch = crop.size
    if cw > 40 and ch > 40:
        sx, sy = int(cw * 0.4), int(ch * 0.55)
        strip = crop.crop((sx, sy, cw, ch))
        strip = strip.resize((strip.size[0] * 3, strip.size[1] * 3), Image.LANCZOS)
        hits += ocr_pil(strip, x0 + sx, y0 + sy)
    return hits, box, pil, rect


def judge(hits, tag=""):
    """卡片区三态判定 → ('claim', hit) / ('done', kw) / (None, None)。
    min_score=0.5（2026-10-01 实测 0.6 会漏掉灰底胶囊上的「今日已领」）；
    匹配前先做形近字归一化（已额→已领）。
    v7.4（2026-10-08）：先 sanitize_hits 剔除更新条假阳性；若锚点给出卡片纵带，
    则只在纵带内判定（防更新条/其它区域噪声抢走点击坐标或伪造 S2）。"""
    hits = sanitize_hits(hits)
    band = card_band(hits)
    if band:
        inb = [h for h in hits if band[0] <= h[1] <= band[1]]
        if len(inb) != len(hits):
            log(f"{tag}[fix] 卡片纵带 {band} 之外的 {len(hits) - len(inb)} 条命中已忽略")
        hits = inb
    claim = best_hit(hits, (KEY_CLAIM,), 0.5)
    if claim:
        log(f"{tag}S1 可领取：OCR 命中「{KEY_CLAIM}」({claim[0]},{claim[1]}) s={claim[2]:.2f}")
        return "claim", claim
    done_hit, done_kw = best_hit_any(hits, KEY_DONES, 0.5)
    if done_hit:
        log(f"{tag}S2 已领取：OCR 命中「{done_kw}」({done_hit[0]},{done_hit[1]}) s={done_hit[2]:.2f}")
        return "done", done_kw
    return None, None


def best_hit(hits, keywords, min_score=0.6):
    best = None
    for h in hits:
        t = norm_txt(h[3])
        if any(k in t for k in keywords) and h[2] >= min_score:
            if best is None or h[2] > best[2]:
                best = h
    return best


def best_hit_any(hits, keywords, min_score=0.6):
    for kw in keywords:
        r = best_hit(hits, (kw,), min_score)
        if r:
            return r, kw
    return None, None


def parse_t2(hits, region=None):
    """T2 数值证据：解析「已领 N 天 / 累计领取 N 分」。返回 (days, points)。

    ⚠ region 不为 None 时只在区域内的命中里解析。
      必须限定区域：主对话区常出现含「已领12天 / 累计领取1200分」的**历史汇报文本**
      （实测 OCR 0.92，比面板真实读数还清晰），不限定就会读到昨天的数字。
    ⚠ v7.7：**先按行合并再解析**。实测窄条 OCR 会把整行切成碎片
      （「已领13天」→「已领」+「13天」，还打乱顺序），逐条正则必然漏读 → T2 证据丢失。
      按 y 分行、行内按 x 排序拼接即可还原成完整文本。
    """
    if region is not None:
        hits = [h for h in hits if in_box(h, region)]
    # 按 y 分行（20px 粒度；实测文字行距约 50px，不会误并），行内按 x 排序
    rows = {}
    for cx, cy, sc, txt in hits:
        rows.setdefault(round(cy / 20.0), []).append((cx, txt or ""))
    days = pts = None
    for _k, items in rows.items():
        line = "".join(t for _x, t in sorted(items, key=lambda z: z[0])).replace(" ", "")
        m = re.search(r"已领\s*(\d+)\s*天", line)
        if m:
            days = int(m.group(1))
        # 「分」在窄条下可能被 OCR 吞掉 → 不强制要求，靠「累计领取」这个强锚点即可
        m = re.search(r"累计领取\s*(\d+)", line)
        if m:
            pts = int(m.group(1))
    return days, pts


def dump(hits, label):
    if not hits:
        log(f"{label} 卡片区无 OCR 命中")
        return
    txt = " | ".join(f"{h[3]}@{h[0]},{h[1]}" for h in hits)
    log(f"{label} 卡片区 OCR: {txt}")


# ────────────────────────────── 动作 ──────────────────────────────
def click(x, y, label=""):
    pyautogui.click(int(x), int(y))
    log(f"点击 ({int(x)}, {int(y)}) [{label}]")


def dismiss_update_bar(hwnd):
    """关闭侧栏底部「新版本就绪 / 更新日志 / 重启升级」更新提示条。

    2026-10-08 实测：该更新条贴住侧栏最底部，会盖住账户入口，
    导致 T2 复核（账户菜单 → Buddy加油站 面板）无法进入。
    关闭 × 位于条右上角：实测「重启升级」按钮 @(300,1013) → × @(355,992)，
    即相对偏移 (+55, -21)（窗口相对，与实际窗口尺寸无关）。
    ⚠ 切勿点「重启升级」（会重启客户端）。
    """
    pil, rect = capture(hwnd)
    hits = ocr_pil(pil, rect[0], rect[1])
    bar = best_hit_any(hits, ("重启升级", "新版本就绪"), 0.5)[0]
    if not bar:
        return False
    dx, dy = (55, -21) if "重启" in norm_txt(bar[3]) else (281, -21)
    click(bar[0] + dx, bar[1] + dy, "close-update-bar")
    return True


def find_account_hit(hits, rect):
    """定位侧栏底部「账户行」（用户条目，点它弹出账户菜单）。

    ═══ v7.5.1 重写（2026-10-13，修正上一版的错误假设）═══
    上一版按「中文名 + 空格 + 英文名」的文案特征识别 —— **这个假设是错的**：
    用户可能用纯英文名、纯中文名、带数字、带邮箱、带表情符号……任何格式都可能。
    识别一个 UI 元素，不应该去猜它的**内容长什么样**，而应该用它的**几何位置**——
    位置由客户端布局决定，与用户怎么起名无关。

    稳定判据（三条，均为几何/结构事实）：
      ① 位于侧栏 x 带内（rect[0] ~ rect[0] + sidebar_w）；
      ② **紧贴窗口底边**：距底边 < 0.09H（实测账户行 0.044H，其上方最近一条 0.101H，
         有 2.3 倍间隔，阈值取中很稳）；
      ③ 位于卡片锚点**之下**（y 大于卡片锚点 y）——账户行是本客户端侧栏最低的条目。
    再排除卡片自身的文字与用量/升级等噪声。

    返回 hit 或 None。**不做任何姓名格式假设。**
    """
    l, t, r, b = rect
    x_max = l + sidebar_w(rect)
    H = b - t
    # ② 贴底阈值：实测 0.044H vs 0.101H，取 0.09H 居中
    y_min = b - H * 0.09

    # ③ 卡片锚点作为上界参考（账户行必在卡片之下）
    anchors = [h for h in hits if is_card_hit(h)]
    card_bottom = max((h[1] for h in anchors), default=None)

    NOISE = ("已使用", "升级", "Buddy应用", "每日可领", "累计领取", "已领",
             "今日已领", "立即领取", "结束", "加油站", "体验Buddy应用", "积分")
    cands = []
    for h in hits:
        if not (l <= h[0] <= x_max and h[1] >= y_min):
            continue
        raw = (h[3] or "").strip()
        if len(raw) < 2:
            continue
        if any(k in raw for k in NOISE):
            continue
        # 纯数字/纯日期/纯路径不是账户行
        if re.fullmatch(r"[\d\-/:.\s]+", raw) or "\\" in raw or "/" in raw:
            continue
        # ③ 若已知卡片位置，要求账户行在其下方
        if card_bottom is not None and h[1] <= card_bottom:
            continue
        cands.append(h)
    if not cands:
        return None
    # 取最靠底边的一条
    return max(cands, key=lambda h: h[1])





def _read_all(hwnd):
    """整窗 OCR，返回 (hits, pil, rect)。"""
    pil, rect = capture(hwnd)
    return ocr_pil(pil, rect[0], rect[1]), pil, rect


def sidebar_region(rect):
    """侧栏「功能区」的绝对矩形 —— 账户行/菜单/积分面板都落在这里。

    v7.7 新增。用于**只 OCR 这一块**：实测全屏 OCR 8.65s / 本区域 2.54s，
    **提速 3.4 倍**（面积只占 17%）。当前一轮要跑 8-10 次 OCR，
    全部改为区域 OCR 就是主要的提速来源。
    范围取：纵向 0.30H~底边（覆盖菜单顶部到账户行）、横向左 0.42W
    （覆盖侧栏 0.16W + 面板外扩，与 panel_region 的上界一致）。
    """
    l, t, r, b = rect
    W, H = r - l, b - t
    return (l, t + int(H * 0.30), min(r, l + int(W * 0.42)), b)


def read_sidebar(hwnd):
    """只 OCR 侧栏区域，返回 (hits, pil, rect, region)。比整窗快 3.4x。"""
    pil, rect = capture(hwnd)
    reg = sidebar_region(rect)
    x0, y0, x1, y1 = reg
    crop = pil.crop((x0 - rect[0], y0 - rect[1], x1 - rect[0], y1 - rect[1]))
    return ocr_pil(crop, x0, y0), pil, rect, reg


def read_narrow(hwnd, bottom_y, up, wfrac=0.20):
    """只 OCR「左起 wfrac 宽 × 从 bottom_y 往上 up 像素」的**窄条**。

    v7.7 快路径专用。账户行/菜单/积分面板的内容都落在这一竖带里，
    实测耗时：面板带 1.36s、菜单带 2.45s（对比整窗 8.65s、侧栏区 3.10s）。
    返回 (hits, pil, rect)。
    """
    pil, rect = capture(hwnd)
    l, t, r, b = rect
    x0, x1 = l, min(r, l + int((r - l) * wfrac))
    y0, y1 = max(t, bottom_y - up), min(b, bottom_y + 20)
    crop = pil.crop((x0 - l, y0 - t, x1 - l, y1 - t))
    return ocr_pil(crop, x0, y0), pil, rect


def load_fastpath():
    """读取本机成功坐标缓存。不存在/损坏/schema 不符/**非本机** → None（静默降级）。"""
    try:
        if not os.path.exists(FASTPATH_FILE):
            return None
        with open(FASTPATH_FILE, encoding="utf-8") as f:
            d = json.load(f)
        if not isinstance(d, dict) or d.get("schema") != FASTPATH_SCHEMA:
            log("[fast] 缓存 schema 不符 → 忽略（将在成功后重建）")
            return None
        for k in ("acc", "gas"):
            if not isinstance(d.get(k), dict):
                return None
        # ⚠ 机器指纹：缓存是**本机实测坐标**，跨机/跨账户使用没有意义
        #   （万一被误随分发包带出，这里兜住，避免新用户首跑点到别人的坐标上）。
        m, cur = d.get("machine"), _machine_id()
        if m and cur and m != cur:
            log(f"[fast] 缓存属于其他机器/账户（{m} ≠ {cur}）→ 忽略，按首跑处理")
            return None
        return d
    except Exception as e:
        log(f"[fast] 缓存读取失败（忽略，不影响正常流程）: {e}")
        return None


def _machine_id():
    """本机标识：Windows 账户名 + 计算机名。只用于判断"缓存是不是我这台机器生成的"。"""
    try:
        user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
        comp = os.environ.get("COMPUTERNAME") or ""
        return f"{user}@{comp}" if (user or comp) else ""
    except Exception:
        return ""


def save_fastpath(rect, acc, gas):
    """固化本机实测的成功坐标（相对量，免疫窗口移动/副屏切换）。

    acc 用「距左边距 + 距底边」表示（实测账户行距底约为固定像素，如本机 61px）；
    gas（Buddy加油站菜单项）用「相对账户行的位移」表示 —— 菜单锚定在账户行上弹出，
    这样表达最稳。
    """
    l, t, r, b = rect
    prev = load_fastpath() or {}
    d = {
        "schema": FASTPATH_SCHEMA,
        "machine": _machine_id(),          # 机器指纹：防止缓存跨机误用
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "win_w": r - l,
        "win_h": b - t,
        "acc": {"dx": int(acc[0] - l), "dy_from_bottom": int(b - acc[1])},
        "gas": {"dx": int(gas[0] - acc[0]), "dy": int(gas[1] - acc[1])},
        "streak": int(prev.get("streak", 0)) + 1,   # 连续成功固化次数
    }
    try:
        with open(FASTPATH_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        log(f"[fast] 已固化本机成功坐标：账户行=距左{d['acc']['dx']}px/距底{d['acc']['dy_from_bottom']}px，"
            f"加油站=相对位移({d['gas']['dx']},{d['gas']['dy']})，连续成功 {d['streak']} 次")
    except Exception as e:
        log(f"[fast] 缓存写入失败（忽略）: {e}")


def drop_fastpath(reason=""):
    """标记快路径失效。**连续 2 次**失败才真正删除缓存 ——
    避免偶发（动画慢、一次点击落空）把好缓存误删，导致下次又走慢路径。"""
    d = load_fastpath()
    if not d:
        return
    d["fail_streak"] = int(d.get("fail_streak", 0)) + 1
    log(f"[fast] 失效标记：{reason}（fail_streak={d['fail_streak']}）")
    try:
        if d["fail_streak"] >= 2:
            os.remove(FASTPATH_FILE)
            log("[fast] 连续失败 ≥2 → 删除缓存；下次走完整流程，成功后自动重新固化")
            return
        with open(FASTPATH_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def panel_region(hits, rect):
    """从当前帧反推**积分面板**的实际区域 (x0,y0,x1,y1)，或 None。

    ═══ 为什么需要它（2026-10-13 定位的新故障模式）═══
    面板打开后，主对话区（窗口中部）里可能正显示含「立即领取」「今日已领」的**对话文本**
    ——例如本自动化的历史汇报、或用户关于积分的话题。这些文本 OCR 分数甚至更高
    （实测 0.92 vs 面板按钮 0.70），若不限定区域，best_hit 会选到对话区的文字坐标，
    点击必然落空（实测两轮点击 (2850,161)/(3400,477) 全打在聊天消息上）。

    稳定判据：**面板专属**元素「Buddy加油站·N期」或「每日可领通用积分」或
    「累计领取」所在位置就是面板中心；面板必然在侧栏一侧（x 较小）。
    返回以面板锚点为基准的矩形，供后续只在该区域内找按钮。
    """
    anchors = []
    for h in hits:
        t = h[3] or ""
        if ("Buddy加油站" in t and ("期" in t or "结束" in t)) \
           or "每日可领通用积分" in t or "累计领取" in t:
            anchors.append(h)
    if not anchors:
        return None
    l, tp, r, b = rect
    W = r - l
    H = b - tp
    ys = [a[1] for a in anchors]
    xs = [a[0] for a in anchors]
    y0, y1 = min(ys) - 170, max(ys) + 130     # 上方含「Buddy应用/100」，下方含按钮行
    x0 = l
    x1 = l + min(sidebar_w(rect) + 520, int(W * 0.42))   # 面板横向不超出侧栏一带
    return (x0, max(tp, y0), min(x1, r), min(b, y1))


def panel_state(hwnd, preloaded=None):
    """读当前画面，判断 Buddy加油站**面板**状态。
    返回 ('claim', hit) / ('done', hit) / (None, None)。

    ⚠ v7.6 修正：所有候选**必须落在 panel_region() 内**，否则会命中主对话区里
      恰好含有「立即领取 / 今日已领」字样的聊天文本（实测分数更高，导致点空）。
    v7.7：改用 read_sidebar（区域 OCR，快 3.4x）；支持传入已读数据避免重复 OCR。
    """
    if preloaded is None:
        hits, pil, rect, _ = read_sidebar(hwnd)
    else:
        hits, pil, rect = preloaded
    reg = panel_region(hits, rect)
    if reg is None:
        log("[panel] 未找到面板锚点（Buddy加油站·N期 / 每日可领通用积分 / 累计领取）")
        return None, None
    inside = [h for h in hits if in_box(h, reg)]
    log(f"[panel] 面板区域 {reg}，区域内命中 {len(inside)} 条")
    hit = best_hit(inside, (KEY_CLAIM,), 0.5)
    if hit:
        return "claim", hit
    hit, kw = best_hit_any(inside, KEY_DONES, 0.5)
    if hit:
        return "done", hit
    return None, None


def open_gas_panel(hwnd):
    """经「账户行 → 账户菜单 → Buddy加油站」打开积分面板。

    ═══ 实测 UI 结构（v7.6，2026-10-13 截图 + OCR 双重确认）═══
    侧栏底部**没有**常驻积分卡片；只有账户行 + 2 个图标。必须：
      ① 点击账户行「<用户名>」
      ② 弹出账户菜单，菜单项（自上而下）：
           套餐/积分余额 … 升级套餐
           **Buddy加油站**（每日领积分）   ← 入口，菜品第一项
           去邀约 / 成长计划
           设置 / 外观 / 记忆与进化 / 意见反馈 / 检查更新 / 退出登录
      ③ 点「Buddy加油站」→ 打开完整积分面板（含 T2 证据）。

    ⚠ 账户菜单是 **toggle**：已展开时再点账户行会收起。故先检测菜单是否已开。
    ⚠ 菜单展开判据必须用**菜单专属**项：「积分余额」「购买积分」「去邀约」
      「成长计划」「记忆与进化」「退出登录」——它们只出现在菜单里。
      绝不能用「Buddy加油站」：它同时出现在菜单项 + 面板标题，会误判。
    返回 (hits, pil, rect) 或 None。
    """
    MENU_ONLY = ("积分余额", "购买积分", "去邀约", "成长计划", "记忆与进化", "退出登录")

    # ⚠ 全程用 read_sidebar（区域 OCR，比整窗快 3.4x）：账户行/菜单都落在侧栏区，
    #   没有必要为了读它们去 OCR 整个窗口（其中 80% 是主对话区，纯浪费）。
    hits, pil, rect, _ = read_sidebar(hwnd)
    menu_open = bool(best_hit(hits, MENU_ONLY, 0.5))

    acc = None
    if not menu_open:
        # 面板可能已开着 → 先 Esc 收起，回到主界面再走菜单
        pyautogui.press("esc")
        time.sleep(1.0)
        hits, pil, rect, _ = read_sidebar(hwnd)
        acc = find_account_hit(hits, rect)
        if not acc:
            log("[menu] 未识别到侧栏底部账户行 → 放弃菜单路径")
            return None
        log(f"[menu] 点击账户行 ({acc[0]},{acc[1]}) 「{acc[3]}」")
        click(acc[0], acc[1], "account")
        time.sleep(2.6)
        hits, pil, rect, _ = read_sidebar(hwnd)
        if not best_hit(hits, MENU_ONLY, 0.5):
            log("[menu] 点击后仍未出现账户菜单（可能被 Esc 收起或点击落空）")
            return None
    else:
        log("[menu] 账户菜单已是展开态，直接使用")
        acc = find_account_hit(hits, rect)

    # 菜单里找「Buddy加油站」入口；排除侧栏卡片标题「Buddy加油站·N期」这类纯文字
    cands = [h for h in hits if "Buddy加油站" in norm_txt(h[3] or "")]
    cands = [h for h in cands if "期" not in (h[3] or "") and "结束" not in (h[3] or "")]
    if not cands:
        log("[menu] 账户菜单中未找到「Buddy加油站」入口")
        return None
    # 取最靠上的一条（菜单第一项），避免误选其他区域的同名文字
    gas = min(cands, key=lambda h: h[1])
    log(f"[menu] 点击「Buddy加油站」({gas[0]},{gas[1]})")
    click(gas[0], gas[1], "gas-entry")
    time.sleep(4.0)

    # 记录本次**实测**的导航坐标，供成功后固化快路径（v7.7）
    if acc is not None:
        _LAST_NAV["acc"] = (acc[0], acc[1])
        _LAST_NAV["gas"] = (gas[0], gas[1])

    hits2, pil2, rect2, _ = read_sidebar(hwnd)
    return hits2, pil2, rect2



def close_gas_panel(hwnd):
    """Esc 收起积分面板，恢复主界面（幂等，供失败重试前复位用）。"""
    try:
        pyautogui.press("esc")
        time.sleep(0.8)
    except Exception:
        pass


def claim_on_panel(hwnd, opened, max_clicks=2):
    """假定积分面板**已打开**（opened = (hits, pil, rect)）→ 判 S1/S2 → 点「立即领取」→ 强校验。

    返回 'SUCCESS' / 'ALREADY_DONE' / None。
    主路径（open_gas_panel 之后）与快路径（缓存导航之后）**共用本函数** ——
    这样两条路径的判定标准完全一致，不存在"快路径放松了校验"的风险。
    """
    hits, pil, rect = opened
    pil.save(PRE_RESULT)
    log(f"点击前快照(面板): {PRE_RESULT}")
    dump(hits, "[panel-pre]")
    reg0 = panel_region(hits, rect)
    if reg0 is None:
        log("[panel] 未找到面板锚点 → S3（面板未正常打开）")
        return None
    inside = [h for h in hits if in_box(h, reg0)]
    hit_claim = best_hit(inside, (KEY_CLAIM,), 0.5)
    hit_done, _kw = best_hit_any(inside, KEY_DONES, 0.5)
    d0, p0 = parse_t2(hits, reg0)
    log(f"[panel-pre] T2 基线: 已领={d0}天 累计={p0}分  "
        f"按钮={'claim' if hit_claim else ('done' if hit_done else 'none')}")

    if hit_done and not hit_claim:
        pil.save(OUTPUT_RESULT)
        log("[panel] 面板显示「已领」且无可点按钮 → S2")
        log("CLAIM_ACTION=ALREADY_CLAIMED")
        log("CLAIM_STATUS=ALREADY_DONE")
        return "ALREADY_DONE"
    if not hit_claim:
        log("[panel] 面板内既无「立即领取」也无已领字样 → S3（面板未正常打开）")
        return None

    data = hit_claim           # 首次直接用刚读到的坐标，省一次 OCR
    for i in range(1, max_clicks + 1):
        if i > 1:
            # 重试时才重新定位（面板可能有动画/落位变化；且必须限定在面板区内）
            act_i, data_i = panel_state(hwnd)
            if act_i == "done":
                pil.save(OUTPUT_RESULT)
                log("[panel] 点击前已是「今日已领」→ S2")
                log("CLAIM_ACTION=ALREADY_CLAIMED")
                log("CLAIM_STATUS=ALREADY_DONE")
                return "ALREADY_DONE"
            if act_i != "claim" or not data_i:
                log(f"[panel] 第 {i} 次点击前未能在面板区内定位「立即领取」→ 放弃")
                break
            data = data_i
        cx, cy, sc = data[0], data[1], data[2]
        log(f"CLAIM_ACTION=CLICKED (面板第 {i} 次) @({cx},{cy}) s={sc:.2f}")
        click(cx, cy, KEY_CLAIM)
        time.sleep(3.0)
        hits2, pil2, rect2, _ = read_sidebar(hwnd)
        dump(hits2, f"[panel-post{i}]")
        act2, data2 = panel_state(hwnd, preloaded=(hits2, pil2, rect2))
        d1, p1 = parse_t2(hits2, panel_region(hits2, rect2))
        log(f"[panel-post{i}] T2: 已领={d1}天 累计={p1}分")

        if act2 == "done":
            pil2.save(OUTPUT_RESULT)
            log("T1 证据(面板)：立即领取 → 今日已领，按钮消失")
            if d0 is not None and d1 is not None and d1 == d0 + 1:
                log(f"T2 证据：已领 {d0} → {d1} 天 (+1)")
            if p0 is not None and p1 is not None and p1 == p0 + 100:
                log(f"T2 证据：累计 {p0} → {p1} 分 (+100)")
            log("CLAIM_STATUS=SUCCESS")
            return "SUCCESS"
        if act2 == "claim":
            log(f"[WARN] 面板第 {i} 次点击后仍是 S1 → 判为假成功，重试")
            time.sleep(2.0)
            continue
        # act2 is None → 面板区读数异常，再给一次机会
        log(f"[WARN] 面板第 {i} 次点击后面板区无有效读数，重试")
        time.sleep(2.0)
    return None


def try_claim_via_panel(hwnd, max_clicks=2):
    """面板路径领取（完整流程）：账户菜单 → Buddy加油站 → 点「立即领取」→ 强校验。

    返回 'SUCCESS' / 'ALREADY_DONE' / None。这是完整流程的主路径；
    快路径（fast_claim）是它的"跳过定位"版本。
    """
    opened = open_gas_panel(hwnd)
    if not opened:
        return None
    return claim_on_panel(hwnd, opened, max_clicks)


def fast_claim(hwnd, rect, cache):
    """快路径：按**缓存的坐标**直接走 账户行 → Buddy加油站，全程用区域 OCR 校验。

    ═══ v7.7 新增（2026-10-13）═══
    每台机器首次跑通后会把成功坐标固化到 claim_fastpath.json；
    之后直接复用 → 跳过「找账户行 / 找菜单项」的 OCR 搜索，一轮 60-90s → ~15s。

    ═══ 三条铁律（见 FASTPATH_FILE 上方注释）═══
    1. 只省"定位"，**不省"判定"** —— 面板状态仍由 claim_on_panel 用同一套 T1/T2 标准判定。
    2. **点账户行后必须校验菜单真的弹出来了**（缓存的坐标点偏可能落到别的菜单项上）。
    3. 任一步不符预期 → `drop_fastpath()` 标记失效并返回 None，由 main 回退完整流程。

    返回 'SUCCESS' / 'ALREADY_DONE' / None（None = 缓存不可用/已失效，请走完整流程）。
    """
    l, t, r, b = rect
    acc = (l + cache["acc"]["dx"], b - cache["acc"]["dy_from_bottom"])
    gas = (acc[0] + cache["gas"]["dx"], acc[1] + cache["gas"]["dy"])
    MENU_ONLY = ("积分余额", "购买积分", "去邀约", "成长计划", "记忆与进化", "退出登录")

    # 窗口尺寸与固化时差异过大 → 相对量可能不再适用，直接不用缓存（不删，留待验证）
    dw = abs((r - l) - int(cache.get("win_w") or (r - l)))
    dh = abs((b - t) - int(cache.get("win_h") or (b - t)))
    if dw > 80 or dh > 80:
        log(f"[fast] 窗口尺寸差异过大（Δ{dw}x{dh}px）→ 本次不用缓存")
        return None

    # 移开鼠标：避免悬停浮层遮挡/干扰。快路径前只做**一次轻量 Esc**（不做区域 OCR 的
    # 状态复位，也不做 wedged 探针）—— 因为快路径自带强校验，任何异常都会导致校验失败
    # 并回退完整流程（完整流程里才有这两步）。这是快路径提速的主要来源（省 ~11s）。
    pyautogui.moveTo(l + int((r - l) * 0.55), t + int((b - t) * 0.5), duration=0.15)
    try:
        pyautogui.press("esc")
    except Exception:
        pass
    time.sleep(0.8)

    # ① 点缓存的账户行位置
    log(f"[fast] 复用缓存坐标：账户行 ({acc[0]},{acc[1]})")
    click(acc[0], acc[1], "account(fast)")
    time.sleep(2.2)

    # ② 校验菜单真的开了（铁律 2：不能省）—— 用窄条区域 OCR（~2.4s，整窗要 8.6s）
    hits, pil, rect2 = read_narrow(hwnd, acc[1], up=int((b - t) * 0.55))
    if not best_hit(hits, MENU_ONLY, 0.5):
        drop_fastpath("点账户行后菜单未弹出（坐标可能已失效）")
        return None
    log("[fast] ✓ 账户菜单已弹出")

    # ③ 点缓存的 Buddy加油站位置
    log(f"[fast] 复用缓存坐标：「Buddy加油站」({gas[0]},{gas[1]})")
    click(gas[0], gas[1], "gas-entry(fast)")
    time.sleep(3.2)

    # ④ 校验面板开了 → 交给共用的判定逻辑（铁律 1）—— 窄条 OCR ~1.4s
    hits2, pil2, rect3 = read_narrow(hwnd, acc[1], up=int((b - t) * 0.22))
    if panel_region(hits2, rect3) is None:
        drop_fastpath("点加油站后未出现积分面板锚点")
        return None
    log("[fast] ✓ 积分面板已打开，进入与完整流程相同的判定")

    res = claim_on_panel(hwnd, (hits2, pil2, rect3), max_clicks=2)
    if res is None:
        # 面板开了但判定异常：多为 UI 改版或动画异常 → 标记失效但不当场删除
        drop_fastpath("面板已开但判定为 S3")
    return res


def scroll_sidebar(rect, clicks=18, direction=-1):
    """把侧栏滚到最底（用于兜底路径里寻找可能存在的卡片）。"""
    l, t, r, b = rect
    mx, my = int(l + 150), int(t + (b - t) * 0.55)
    pyautogui.moveTo(mx, my)
    for _ in range(clicks):
        pyautogui.scroll(int(15 * direction))
        time.sleep(0.08)
    time.sleep(0.8)


def try_claim(hwnd, max_clicks=3):
    """命中 S1 → 点击 → 强校验。返回 'SUCCESS' / 'ALREADY_DONE' / None(S3)。

    强校验：
      T1：点击后卡片变「今日已领」且「立即领取」消失 ⇒ SUCCESS
      T2：「已领N天」+1 或「累计领取N分」+100 ⇒ SUCCESS
      仍是 S1 ⇒ 判为假成功，重试（服务端幂等，重复点击安全）
    """
    hits, box, pil, rect = read_card(hwnd)
    pil.save(PRE_RESULT)
    log(f"点击前快照: {PRE_RESULT} ({pil.size[0]}x{pil.size[1]})")
    dump(hits, "[pre]")
    act, data = judge(hits, "[pre]")
    if act == "done":
        # v7.4：初始即 S2 时也要落盘终态截图（此前该分支不保存，
        # 导致 claim_result.png 停留在上一日，复盘时缺当天终态证据）
        pil.save(OUTPUT_RESULT)
        log(f"终态截图: {OUTPUT_RESULT}")
        log("CLAIM_ACTION=ALREADY_CLAIMED")
        log("CLAIM_STATUS=ALREADY_DONE")
        return "ALREADY_DONE"
    if act != "claim":
        log("[S3] 卡片区既无「立即领取」也无「今日已领」→ 导航失败，换路径")
        return None

    d0, p0 = parse_t2(hits)
    log(f"[pre ] T2 基线: 已领={d0}天 累计={p0}分")

    for i in range(1, max_clicks + 1):
        cx, cy, sc, _ = data
        log(f"CLAIM_ACTION=CLICKED (第 {i} 次)")
        click(cx, cy, KEY_CLAIM)
        time.sleep(3.0)
        hits2, box2, pil2, rect2 = read_card(hwnd)
        dump(hits2, f"[post{i}]")
        act2, data2 = judge(hits2, f"[post{i}]")
        d1, p1 = parse_t2(hits2)
        log(f"[post{i}] T2: 已领={d1}天 累计={p1}分")

        if act2 == "done":
            pil2.save(OUTPUT_RESULT)
            log(f"校验截图: {OUTPUT_RESULT}")
            log("T1 证据：立即领取 → 今日已领，按钮消失")
            if d0 is not None and d1 is not None and d1 == d0 + 1:
                log(f"T2 证据：已领 {d0} → {d1} 天 (+1)")
            if p0 is not None and p1 is not None and p1 == p0 + 100:
                log(f"T2 证据：累计 {p0} → {p1} 分 (+100)")
            log("CLAIM_STATUS=SUCCESS")
            return "SUCCESS"
        if act2 == "claim":
            log(f"[WARN] 第 {i} 次点击后仍是 S1 → 判为假成功，重试")
            data = data2
            time.sleep(2.0)
            continue
        # act2 is None → S3，但可能只是动画/toast 遮挡；再读一次
        pil2.save(OUTPUT_RESULT)
        log(f"[WARN] 点击后卡片区既无按钮也无已领字样（第 {i} 次）")
        time.sleep(2.5)
        hits3, box3, pil3, _ = read_card(hwnd)
        act3, data3 = judge(hits3, f"[recheck{i}]")
        if act3 == "done":
            pil3.save(OUTPUT_RESULT)
            log("T1 证据（复检）：今日已领")
            log("CLAIM_STATUS=SUCCESS")
            return "SUCCESS"
        if act3 == "claim":
            data = data3
            continue
    return None


def reset_ui_state(hwnd, tries=2):
    """把客户端 UI 复位到「主界面、无任何弹层」的干净状态。

    ═══ 为什么必须有这一步（2026-10-13 事故根因）═══
    此前多次探测得出错误结论（"任务列表把底部卡片挤出视口"），
    真正的根因不是布局，而是**探测前没有复位 UI 状态**：
    上一次探测遗留的账户菜单/积分面板还开着，于是抓到的根本不是主界面帧，
    后续所有推断全建立在脏帧之上。

    故：任何"读画面 → 推断"的动作之前，先调用本函数。

    判据：用**仅有弹层才有**的文字判断是否残留浮层。
    ⚠ 绝不能用「今日已领」「立即领取」——它们在**侧栏卡片/面板上常态存在**，
      用作标记会导致每次都误判"弹层未收"，空按 N 次 Esc（实测踩坑）。
      真正只有弹层才出现的词：账户菜单的「积分余额 / 购买积分」、
      积分面板的「累计领取 / 体验Buddy应用」。
      「Buddy加油站」也不可用：它同时是菜单项和面板标题。

    ⚠ 收浮层不能只按 Esc：**悬停触发的浮层**鼠标一停就出现，Esc 关不掉（实测踩坑）。
      必须先**把鼠标移到安全位置**（窗口中部空白区）再 Esc，二者结合才有效。
    ⚠ tries 保持较小（默认 2）：残留的**积分面板**（含「累计领取」）按 Esc 不一定能关，
      而这不是问题——路径 1 本来就要重新打开它。多按只是浪费 5 秒/次。
    本函数**幂等**且**绝不点击**（只移鼠标 + Esc），任何状态下调用都安全。
    """
    OVERLAY_MARKERS = ("积分余额", "购买积分", "累计领取", "体验Buddy应用")
    # 安全位置：窗口中部偏右，远离侧栏与顶部菜单
    safe_x = safe_y = None
    try:
        _, _r = capture(hwnd)          # rect = (l,t,r,b)，不依赖前台
        l, t, r, b = _r
        safe_x = l + int((r - l) * 0.55)
        safe_y = t + int((b - t) * 0.5)
        pyautogui.moveTo(safe_x, safe_y, duration=0.15)
        time.sleep(0.4)
    except Exception:
        pass
    for i in range(tries):
        try:
            # v7.7：浮层标记都出现在侧栏区 → 用区域 OCR（快 3.4x）
            hits, pil, rect, _reg = read_sidebar(hwnd)
        except Exception as e:
            log(f"[reset] 读取失败: {e}")
            return False
        if not best_hit(hits, OVERLAY_MARKERS, 0.5):
            log(f"[reset] UI 已干净（第 {i} 次检查）")
            return True
        log(f"[reset] 检测到残留浮层 → 移开鼠标 + Esc（第 {i+1}/{tries} 次）")
        if safe_x is not None:
            try:
                pyautogui.moveTo(safe_x, safe_y, duration=0.15)
            except Exception:
                pass
        pyautogui.press("esc")
        time.sleep(1.2)
    log("[reset] 仍有浮层标记，继续（路径 1 会自行打开面板，无影响）")
    return False


def main():
    log("=" * 60)
    log("WorkBuddy 每日积分 - GUI 自动化 v7.7 (快路径缓存 + 区域OCR + 账户菜单主路径 + wedged 自愈)")
    log(f"DPI 模式: {DPI_MODE}")

    wins = find_window()
    if not wins:
        log("[FAIL] 未找到 WorkBuddy 桌面客户端窗口（已排除浏览器）")
        return False, "NO_WINDOW"
    hwnd, title = wins[0]
    log(f"窗口: {title}  hwnd={hwnd}")
    fg = activate(hwnd)
    log(f"置前: {'成功' if fg else '失败（PrintWindow 不依赖前台，继续）'}")
    time.sleep(0.6)

    # ═══════════ 路径 0（v7.7，最优先）：快路径 ═══════════
    # 每台机器首次跑通后会把成功坐标固化到 claim_fastpath.json；之后直接复用，
    # 跳过「找账户行 / 找菜单项」的 OCR 搜索，并把 OCR 限制在窄条区域。
    #
    # ⚠ 快路径**刻意放在 reset_ui_state / ensure_live_ui 之前**：
    #   这两步共约 11s，而快路径自带强校验（菜单必须弹出 + 面板必须有锚点 +
    #   同一套 T1/T2 判定）。任一步不符预期 → 立即失效回退，由下面的完整流程
    #   再做复位与 wedged 检测。这样"稳妥"没有被牺牲，只是被挪到了真正需要时。
    #
    # ⚠ 快路径失败**不影响本次成功**——它会回退到完整流程继续领，只是慢一点。
    cache = load_fastpath()
    if cache:
        log(f"[路径0] 发现本机成功坐标缓存（连续成功 {cache.get('streak', '?')} 次，"
            f"固化于 {cache.get('saved_at', '?')}）→ 尝试快路径")
        _r0 = capture(hwnd)[1]
        res = fast_claim(hwnd, _r0, cache)
        if res:
            log(f"[路径0] 快路径命中：{res}")
            return True, res
        log("[路径0] 快路径不可用 → 本次回退完整流程（仍会正常完成）")
    else:
        log("[路径0] 无快路径缓存（本机首跑，或缓存已失效）→ 走完整流程")

    # ── 路径 -1：UI 状态复位（**先于一切读取**）──
    # 上次运行/上次探测遗留的菜单或面板会污染抓帧，产生错误推断。
    reset_ui_state(hwnd)

    # ── 路径 0.5（v7.3）：渲染层 wedged 自愈 ──
    # 若卡片读到的是「陈旧帧」（= 上一天的今日已领），直接判定会漏领，必须先自愈。
    hwnd2, revived = ensure_live_ui(hwnd)
    if revived and hwnd2 and hwnd2 != hwnd:
        hwnd = hwnd2
        log(f"[路径0.5] 自愈成功，切换新窗口 hwnd={hwnd}")
        activate(hwnd)
        time.sleep(1.2)
        reset_ui_state(hwnd)

    pil, rect = capture(hwnd)
    log(f"窗口矩形: {rect}  抓取 {pil.size[0]}x{pil.size[1]}")
    log(f"自适应几何: 侧栏宽≈{sidebar_w(rect)}  卡片区高≈{card_h(rect)}")

    # ═══ 路径顺序说明（v7.7，2026-10-13）═══
    # 实测确认（截图 + OCR 双重验证）的客户端积分入口结构：
    #   ① 侧栏底部**没有**常驻的积分卡片；侧栏底部只有账户行「<用户名>」+ 2 个图标。
    #   ② **点击账户行** → 弹出账户菜单，菜单项含：
    #        「套餐/积分余额 … 升级套餐」「Buddy加油站 每日领积分」
    #        「去邀约」「成长计划」「设置」「外观」「记忆与进化」「意见反馈」
    #        「检查更新」「退出登录」
    #   ③ 点菜单里的「Buddy加油站」→ 打开完整积分面板（含「立即领取」/「今日已领」
    #       与 T2 证据「已领 N 天 / 累计领取 N 分」）。
    #   ④ 另有一个 hover 浮层（悬停侧栏某处触发）也能显示积分摘要，但触发点不稳定，
    #       不作为主路径。
    # 故：**账户菜单路径是唯一可靠的主路径**，放在最前；卡片路径保留为兜底
    #     （某些版本/某些页面可能确实有侧栏卡片）。
    #
    # v7.7 新增**路径 0（快路径）**：本机成功过后，读缓存的坐标直接导航，
    #   跳过"找账户行/找菜单项"的 OCR 搜索，并把 OCR 全部限制在侧栏区。
    #   铁律：快路径必须能自动失效回退（见 fast_claim / drop_fastpath 注释）。

    # ── 路径 1（主路径）：账户菜单 → Buddy加油站 面板 ──
    log("[路径1] 主路径：账户菜单 → Buddy加油站 完整面板")
    res = try_claim_via_panel(hwnd, max_clicks=2)
    if res:
        # 成功后固化/刷新快路径坐标（只在真正拿到结果时才写，避免把失败态固化）
        if _LAST_NAV.get("acc") and _LAST_NAV.get("gas"):
            save_fastpath(rect, _LAST_NAV["acc"], _LAST_NAV["gas"])
        return True, res
    close_gas_panel(hwnd)

    # ── 路径 2（兜底）：读侧栏卡片区（部分版本/页面可能存在常驻卡片）──
    res = try_claim(hwnd)
    if res:
        return True, res

    # ── 路径 3：滚侧栏后再读卡片 ──
    for attempt in range(2):
        log(f"[路径3.{attempt}] 滚动侧栏到最底")
        scroll_sidebar(rect, clicks=18, direction=-1)
        res = try_claim(hwnd, max_clicks=2)
        if res:
            return True, res
        log(f"[路径3.{attempt}] 反向试探")
        scroll_sidebar(rect, clicks=6, direction=1)
        res = try_claim(hwnd, max_clicks=2)
        if res:
            return True, res

    # ── 路径 3：整屏 OCR 找「立即领取」按钮（不限卡片区） ──
    pil, rect = capture(hwnd)
    pil.save(GROWTH_SHOT)
    allhits = ocr_pil(pil, rect[0], rect[1])
    hits_txt = " | ".join(h[3] for h in allhits)
    log(f"[路径3] 整屏 OCR ({len(allhits)}): {hits_txt}")
    allhits = sanitize_hits(allhits)
    claim = best_hit(allhits, (KEY_CLAIM,), 0.6)
    band = card_band(allhits)
    if claim and band and not (band[0] <= claim[1] <= band[1]):
        c2 = best_hit([h for h in allhits if band[0] <= h[1] <= band[1]], (KEY_CLAIM,), 0.6)
        if c2:
            log(f"[路径3][fix] 忽略卡片带外候选 ({claim[0]},{claim[1]})，改用卡片内 ({c2[0]},{c2[1]})")
            claim = c2
    if claim:
        log(f"[路径3] 整屏命中「{KEY_CLAIM}」({claim[0]},{claim[1]}) → 点击")
        pil.save(PRE_RESULT)
        click(claim[0], claim[1], KEY_CLAIM)
        time.sleep(3.5)
        res = try_claim(hwnd, max_clicks=2)
        if res:
            return True, res

    # ── 路径 4：黑按钮模板兜底 ──
    btn = locate_claim_button(pil, rect)
    if btn:
        log(f"[路径4] 模板命中黑按钮 {btn} → 点击")
        pil.save(PRE_RESULT)
        click(btn[0], btn[1], "template")
        time.sleep(3.5)
        res = try_claim(hwnd, max_clicks=2)
        if res:
            return True, res

    log("[FAIL] 全部路径均未获得 T1/T2 领取证据 → UNKNOWN（agent 未搞定，不得结案）")
    pil.save(OUTPUT_RESULT)
    log("CLAIM_STATUS=UNKNOWN")
    return False, "UNKNOWN"


def locate_claim_button(pil_img, rect):
    """模板匹配定位黑色「立即领取」按钮；返回屏幕绝对坐标。

    2026-10-13：模板文件可能不存在（分发时不带 PNG 资产）。
    此时优雅返回 None —— 这只是**兜底路径 4**，主线靠文案锚点（路径 1/2/2.5/3），
    缺模板不影响正常领取，故仅提示不报错。
    """
    if not os.path.exists(BLACK_BTN_TPL):
        log("[路径4] 模板文件不存在（分发版可不带）→ 跳过模板兜底")
        return None
    try:
        tmpl = cv2.imread(BLACK_BTN_TPL, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception:
        return None
    if tmpl is None:
        return None
    best = None
    for s in np.linspace(0.5, 1.6, 23):
        tw, th = int(tmpl.shape[1] * s), int(tmpl.shape[0] * s)
        if tw < 5 or th < 5 or tw > img.shape[1] or th > img.shape[0]:
            continue
        tt = cv2.resize(tmpl, (tw, th))
        res = cv2.matchTemplate(img, tt, cv2.TM_CCOEFF_NORMED)
        _, mx, _, ml = cv2.minMaxLoc(res)
        if best is None or mx > best[0]:
            best = (mx, ml, tw, th)
    if best is None or best[0] < 0.75:
        return None
    return best[1][0] + best[2] // 2 + rect[0], best[1][1] + best[3] // 2 + rect[1]


if __name__ == "__main__":
    try:
        ok, status = main()
    except Exception:
        import traceback
        traceback.print_exc()
        ok, status = False, "EXCEPTION"
    log(f"RESULT={status}")
    sys.exit(0 if ok else 1)
