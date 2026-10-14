# WorkBuddy 每日积分自动领取

一个 WorkBuddy skill：无人值守领取每日 100 通用积分，并用**页面状态证据**（而非"脚本跑完了"）判定真实结果。

## 安装（一句话，装完即开启自动领取）

在**另一台**电脑的 WorkBuddy 里发这句即可：

> **安装这个 skill：https://github.com/lxx19970628a/workbuddy-daily-credits ，并设置每天自动领积分**

它一次性完成：clone 到 `~/.workbuddy/skills/workbuddy-daily-credits` → 建每日任务（默认 09:05）→ 回报。换时间写进那句话即可（如「每天 9:30」）。

**手动等价做法**：

```bash
git clone https://github.com/lxx19970628a/workbuddy-daily-credits.git \
  "$HOME/.workbuddy/skills/workbuddy-daily-credits"
```

无 git / agent 无命令权限：在仓库页点 **Code → Download ZIP**，到 WorkBuddy「技能 → 添加技能 → 上传技能」导入解压后的文件夹，再说一句「每天自动领积分」补建任务。

> ⚠️ 仓库根目录即 skill 本体，结果须是 `~/.workbuddy/skills/workbuddy-daily-credits/SKILL.md` 存在；别多套一层同名目录。

## 使用

> 帮我领今天的 WorkBuddy 积分

装好后对 WorkBuddy 说即可。改时间 / 停用：直接说「改成 8:40」，或去侧栏「自动化」里改。

## 环境要求

- **Windows 10 / 11** + 已登录的 WorkBuddy 桌面客户端
- **Python 3.10+**（依赖自动引导安装）
- 依赖仅 2 个、约 15MB，一条命令：
  ```bash
  python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pywin32 Pillow
  ```
- **OCR 用 Windows 系统自带引擎**（Windows.Media.Ocr，零 pip 依赖，~1.4s/次），无需 rapidocr/onnxruntime 那套 ~250MB。

## 工作原理（简述）

定位客户端窗口 → 有本机坐标缓存走**快路径**（~12s），否则走三条路径（账户菜单主路径 / 侧栏常驻卡 / 整屏 OCR），命中即点击 → 用 **T1 状态跃迁**（「立即领取」→「今日已领」）与 **T2 数值证据**（已领天数 / 累计分 +1）判定成败。客户端改版 / 换分辨率会**自动**回退重探，无需手动兼容。

## 为什么安全

- 仅在本机模拟正常点击，**不读 / 不解密 / 不传任何凭据**；客户端 5.7.7 起登录态已信封加密，接口直连方案失效，本 skill 不依赖任何非公开凭据。
- 判定标准是**页面状态**，不是退出码，避免"假成功"。

## 已知限制

- 仅支持 **Windows**；UI 改版可能需更新锚点字符串（见 SKILL.md）。
- 客户端须保持运行，自动化到点才触发；任务建好后次日首次调度，或手动说「现在领一次」验一遍。
- 每日一次由服务端幂等保证，重复点不加分也不扣分。

## 故障排查

见 [`references/troubleshooting.md`](references/troubleshooting.md)。

## 免责声明

本 skill 仅模拟用户在官方客户端上的正常点击，不修改客户端、不伪造请求、不绕过服务端限制、不读取凭据。请遵守 WorkBuddy 服务条款。

## License

MIT
