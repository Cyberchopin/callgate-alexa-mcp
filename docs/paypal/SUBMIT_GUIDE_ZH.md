# PayPal AI Hackathon 提交步骤（中文）

截止时间：**2026 年 11 月 12 日中午 12:00（太平洋时间）**。建议 11 月 10 日前交完，留两天改。

代码在 GitHub 的 `paypal/checkout` 分支。所有命令都在仓库根目录运行。

---

## 第 1 步：准备 PayPal sandbox（约 15 分钟）

1. 打开 https://developer.paypal.com ，用你的 PayPal 账号登录。
2. 进入 **Apps & Credentials**，确认右上角是 **Sandbox**，然后点 **Create App**（类型选 Merchant），名字随意，比如 `callgate-checkout`。
3. 复制这个 App 的 **Client ID** 和 **Secret**。
4. 进入 **Testing Tools → Sandbox Accounts**。系统会自带一个 Personal（买家）账号；点进去，记下它的邮箱和密码，演示付款时用它登录。
5. 可选：把这个买家账号的收货地址改成加拿大（例如多伦多），就能在视频里演示“地址超出约定，付款被拦下”。

## 第 2 步：在你电脑上装好并跑通（约 15 分钟）

```bash
git fetch origin
git checkout paypal/checkout
python -m venv .venv
source .venv/bin/activate        # Windows 用 .venv\Scripts\activate
pip install -r requirements-lock.txt -r integrations/alexa_mcp/requirements.txt -r integrations/paypal_checkout/requirements.txt
python -m pytest tests/paypal_checkout -q          # 应该显示 93 passed
```

## 第 3 步：跑一遍真实 sandbox 检查（约 10 分钟）

```bash
export PAYPAL_CLIENT_ID=你的ClientID
export PAYPAL_CLIENT_SECRET=你的Secret
# Windows PowerShell 用：$env:PAYPAL_CLIENT_ID="..."
python -m scripts.paypal_sandbox_check
```

脚本会打印一个 PayPal 链接。用浏览器打开，用第 1 步记下的**买家账号**登录并点付款。付完会跳转到 example.com，这是正常的，回到终端等它跑完。

跑通后会生成 `docs/paypal/sandbox-run.json`，里面有真实的订单号、扣款号和物流记录。把这个文件提交到仓库，Devpost 文案里所有 `[[…]]` 都用它里面的号码填。

**如果某一步报错**：把终端里的完整报错复制给我，我来修。那就说明真实 PayPal 和模拟器有差别，正好是这一步要发现的。

## 第 4 步：打开 AI 部分（重要）

比赛要求“实质性使用 AI”。没有 API key 时，页面上会写 “rules only”，AI 助手的按钮也不会出现，评委会觉得 AI 用得很弱。所以录视频之前必须设置：

```bash
export ANTHROPIC_API_KEY=你的key
```

在 https://console.anthropic.com 申请 key，充值 5 美元就足够比赛期间使用。

**设好 key 之后先试跑一次**（这一步我在云端没法替你做）：
```bash
python -m integrations.paypal_checkout.server     # 终端 1
python -m scripts.paypal_llm_agent                # 终端 2，看 Claude 怎么起草订单
```
然后在网页上点“Let the AI sales assistant draft it”，确认右侧会出现 “What the AI sales assistant did” 面板。

## 第 5 步：部署在线演示（可选，约 15 分钟）

评委不想自己装环境的话，有个在线地址会加分；部署在 Render 上还能参评 Render 的单项奖。

1. 打开 https://render.com ，用 GitHub 登录。
2. 选 **New → Blueprint**，选 `callgate-alexa-mcp` 仓库、`paypal/checkout` 分支。它会自动读取根目录的 `render.yaml`。
3. 部署完会得到一个网址，例如 `https://callgate-checkout.onrender.com`。
4. 想让在线版也连真 sandbox，就在 Render 的 Environment 里填 `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET` / `ANTHROPIC_API_KEY`，再加一个 `CALLGATE_DEMO=1`，演示按钮才会保留。
5. 免费版闲置 15 分钟会休眠，第一次打开要等大约 30 秒。

## 第 6 步：让你哥真用一两单（强烈建议）

这是最能打动评委的部分，比任何测试数字都有说服力。

- 拿他最近真实的一段买卖聊天（隐去名字），粘贴进去，看读出的价格对不对、有没有标出风险。
- 记下来：读对没有？标出了什么？他觉得有用还是麻烦？
- 能有一句他的原话最好，比如“上次那单要是有这个，就不会寄错地址了”。
- 写进 Devpost 的 Accomplishments，填掉那行 `[[Real use…]]`。只写真实发生的事，没有就删掉那一行，不要编。

## 第 7 步：录视频（约 1–2 小时）

- 照 `docs/paypal/DEMO_SCRIPT.md` 录，里面有逐句英文旁白和每个时间点的画面。
- 用 sandbox + `ANTHROPIC_API_KEY` + `CALLGATE_DEMO=1` 启动，画面里要出现**真实的 PayPal 付款页**。
- 控制在 **3 分钟以内**，超过的部分评委可以不看。
- 不要用有版权的背景音乐。
- 上传 YouTube，可见性选 **Public**（不能是 Unlisted 或 Private）。

## 第 8 步：填 Devpost

打开 `docs/paypal/DEVPOST.md`，按里面的顺序逐项复制：

1. Project name、Elevator pitch
2. Thumbnail：上传 `docs/paypal/media/thumbnail.png`
3. About the project：整段复制，并把所有 `[[…]]` 换成真实内容
4. Built with：复制标签
5. Try it out：GitHub 分支链接，加上 Render 网址（如果部署了）
6. Video：YouTube 链接
7. 比赛附加问题：复制对应的回答。如果你写代码时用了 AI 编程助手，在 AI 工具那一题如实写上。
8. 奖项勾选：Overall、Most Impactful、Best Use of Agentic Commerce、Best Use of PayPal + AI、Most Creative、Best Demo Delivery；部署了 Render 再勾 Best Use of Render。

**提交前检查：**
- [ ] 全文搜一下 `[[`，确保一个都不剩
- [ ] 仓库是公开的，根目录有 LICENSE（MIT，已经有了）
- [ ] 视频是公开的，且不到 3 分钟
- [ ] 打开 GitHub 分支链接，能看到 `integrations/paypal_checkout/README.md`
- [ ] `docs/paypal/sandbox-run.json` 已经提交上去

## 关于 main 分支

`main` 是你 Amazon 比赛的提交版本，这次的代码都在 `paypal/checkout` 分支，互不影响。Devpost 上直接给分支链接就行。等 Amazon 评完，再决定要不要合并到 `main`。
