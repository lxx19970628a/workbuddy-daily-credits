"""T2 复核：账户行 → Buddy加油站面板，读「已领 N 天 | 累计领取 N×100 分」。

v7.5（2026-10-13）泛化改造：
- 账户行改为**结构化识别**（G.find_account_hit），不再写死用户名 —— 旧版把
  「刘潇潇 Sean」硬编码，别人机器必然 NO_ACCOUNT。
- 复用 G.open_gas_panel()，含 toggle 语义处理（菜单已展开时不再盲点）与
  「Buddy加油站·N期」卡片标题排除。
- 产物固定同名覆盖（evidence_t2_panel.png / evidence_t2_step0.png），不按日期堆积。

用法：python t2_check.py
输出：[T2] (days, points)  —— 即权威读数，配合 claim_run.log 的 T1 构成双证。
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import claim_gui_final as G

hwnd = G.find_window()
if isinstance(hwnd, (list, tuple)):
    hwnd = hwnd[0][0] if isinstance(hwnd[0], (list, tuple)) else hwnd[0]
print("[find] hwnd =", hwnd)
if not hwnd:
    sys.exit("NO_WINDOW")

G.activate(hwnd)
time.sleep(1.5)

# 进入面板前若账户行被更新条遮挡，先点 × 关闭（2026-10-08 实测该条会盖住账户行）
pil0, rect0 = G.capture(hwnd)
hits0 = G.ocr_pil(pil0, rect0[0], rect0[1])
if not G.find_account_hit(hits0, rect0):
    if G.dismiss_update_bar(hwnd):
        print("[acc] 更新条遮挡账户行 → 已点 × 关闭，重试")
        time.sleep(1.5)

opened = G.open_gas_panel(hwnd)
if not opened:
    sys.exit("NO_GAS_PANEL")

hits, pil, rect = opened      # ⚠ _read_all() 返回顺序为 (hits, pil, rect)
pil.save("evidence_t2_panel.png")
print(f"[panel] rect={rect} size={pil.size} hits={len(hits)}")
for h in hits:
    if any(k in h[3] for k in ("Buddy", "领", "积分", "结束", "天", "分")):
        print("    ", h)

days, points = G.parse_t2(hits)
print("[T2]", (days, points))

done = G.best_hit_any(hits, ["今日已领", "已领取"], min_score=0.5)
claim = G.best_hit_any(hits, ["立即领取"], min_score=0.55)
print("[panel btn] done =", done, " claim =", claim)

# 复位：收起面板，避免影响后续流程
G.close_gas_panel(hwnd)

sys.exit(0 if (days is not None or points is not None) else 1)
