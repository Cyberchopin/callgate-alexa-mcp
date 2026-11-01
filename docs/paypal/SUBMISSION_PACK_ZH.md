# CallGate Checkout · PayPal AI Hackathon 提交总控手册

这份文件是唯一总入口。按顺序做即可，不需要在多个聊天记录里找命令。

官方截止：**2026 年 11 月 12 日中午 12:00（美国太平洋时间）**。建议至少提前 24 小时提交，最后一天只处理链接或文字小修，不再改核心流程。

## 0. 现在已经完成什么

- PayPal Checkout 核心流程、AI reader、MCP sales assistant、订单差异检查、地址 gate、幂等 capture、packing/tracking/evidence 已实现。
- 已有一次脱敏后的真实 PayPal sandbox 成功记录：`docs/paypal/sandbox-run.json`。
- PayPal 专项测试：**94 passed**。
- 最近记录的全仓库本地测试：**394 passed, 3 skipped**。
- README、Devpost 英文文案、缩略图和视频脚本均在仓库中。
- GitHub 仓库公开，根目录已有 MIT `LICENSE`。

你本人仍需完成的事情只有：

1. 用自己的 sandbox 账号录制最终视频；
2. 剪到 3 分钟以内并上传为 Public YouTube；
3. 把 YouTube 链接填进 `docs/paypal/DEVPOST.md` 对应位置；
4. 在 Devpost 页面逐项粘贴、预览并由你本人点击 Submit。

## 1. 提交包文件地图

| 文件 | 用途 |
| --- | --- |
| `README.md` | 评委打开仓库后看到的项目首页 |
| `docs/paypal/DEMO_SCRIPT.md` | 中英逐镜头表：点哪里、画面是什么、英文逐字念什么 |
| `docs/paypal/DEVPOST.md` | Devpost 所有英文字段的最终文案 |
| `docs/paypal/YOUTUBE_COPY_EN.md` | YouTube 标题、简介、章节和标签 |
| `docs/paypal/FINAL_SUBMISSION_CHECKLIST_ZH.md` | 提交前最后一遍勾选 |
| `integrations/paypal_checkout/README.md` | 给技术评委的深度实现说明 |
| `docs/paypal/sandbox-run.json` | 脱敏后的 PayPal sandbox 运行证据 |

## 2. 录屏前一天：只做一次环境预检

### 2.1 同步最终代码

提交包合并后，在 Linux/WSL 仓库执行：

```bash
git switch main
git pull --ff-only
git status --short --branch
```

`git status` 应当没有未提交文件。不要在录屏当天随意 merge 其他比赛分支。

### 2.2 激活环境并验证

```bash
source .venv/bin/activate
python -m pytest tests/paypal_checkout -q
python -m evaluation_paypal.run
```

期望看到：

- `94 passed`；
- 12/13 deals exact，1 abstained，0 wrong total；
- 0/5 no-deal chats made payable；
- 67/67 order mutations caught；
- 16/16 risky lines，0/12 false alarms。

如果数字不同，先停下排查，不要照着旧数字录视频。

### 2.3 准备 sandbox 和 AI

你需要：

- PayPal Developer **Sandbox** app 的 Client ID 和 Secret；
- 一个 sandbox Personal buyer 账号；
- Anthropic API key，用于视频里的 AI reader 和 sales assistant。

只在本地终端设置，不要写进文件、截图、聊天或视频：

```bash
export PAYPAL_CLIENT_ID="你的 sandbox Client ID"
export PAYPAL_CLIENT_SECRET="你的 sandbox Secret"
export ANTHROPIC_API_KEY="你的 API key"
export CALLGATE_DEMO=1
```

安全边界：

- 右上角必须确认 PayPal 是 **Sandbox**；
- 不设置 `CALLGATE_ALLOW_LIVE=1`；
- 不使用真实买家、真实卡、真实资金或真实地址；
- 录屏前清空终端，不让环境变量或账号邮箱出镜；
- PayPal sandbox 登录页若显示测试邮箱，后期打码。

## 3. 先彩排，再做唯一最终 sandbox take

### 3.1 离线彩排

先开一个不带 PayPal 凭据的新终端，只练点击和英文，不产生 sandbox 订单：

```bash
unset PAYPAL_CLIENT_ID PAYPAL_CLIENT_SECRET
export CALLGATE_DEMO=1
python -m integrations.paypal_checkout.server
```

打开 `http://127.0.0.1:8787`，完整走一遍 `DEMO_SCRIPT.md`。离线模式必须口头或画面明确标为 simulated PayPal，不能冒充真实 sandbox。

### 3.2 最终录制启动方式

关闭彩排服务，重新设置 sandbox 与 AI 环境变量，然后启动：

```bash
export PAYPAL_CLIENT_ID="你的 sandbox Client ID"
export PAYPAL_CLIENT_SECRET="你的 sandbox Secret"
export ANTHROPIC_API_KEY="你的 API key"
export CALLGATE_DEMO=1
python -m integrations.paypal_checkout.server
```

准备两个浏览器窗口：

- Seller：`http://127.0.0.1:8787`，宽度约 1280 px；
- Buyer：从 seller 页面复制 payer link 后打开，浏览器响应式宽度约 390 px。

PayPal sandbox Personal buyer 在 Buyer 窗口登录。建议提前登录，但开始录制前隐藏邮箱和密码管理器弹窗。

## 4. OBS / 系统录屏设置

- 分辨率：1920×1080；30 fps 足够。
- 只录浏览器窗口和你的麦克风；关闭通知、聊天、邮箱和密码管理器。
- 浏览器缩放 90%–100%，确保金额、风险旗标和按钮可读。
- 鼠标移动慢一点，每次点击后停 0.5–1 秒。
- 英文语速约 125–140 words/min；不要边点击边抢台词。
- 不放背景音乐，避免版权问题，也让英文更清楚。
- 最终成片目标 **2:40–2:55**，绝不能超过 3:00。

按 `docs/paypal/DEMO_SCRIPT.md` 录。推荐分段录制后剪辑，不必强求一次完成；但不要把不同 checkout 的状态剪成看似同一条交易。

## 5. 剪辑与隐私检查

必须删除或打码：

- PayPal sandbox buyer 邮箱；
- API key、Client Secret、终端历史和 `.env` 内容；
- 浏览器书签、个人头像、通知和其他标签页；
- 任何真实聊天姓名、地址、订单或付款信息。

必须保留：

- CallGate 读取出的 `$140` / `$88` 等演示金额及其原文引用；
- AI 草拟错误订单后被 deterministic check 拦下的画面；
- PayPal sandbox 页面或明确的 sandbox 标识；
- order changed / destination hold 至少一个强失败案例；
- packing、tracking 或 evidence chain 至少一个交付后证据画面；
- 结尾项目名和 GitHub 仓库地址。

## 6. 上传 YouTube

1. 用 `docs/paypal/YOUTUBE_COPY_EN.md` 的标题和简介；
2. Visibility 选择 **Public**；
3. 等待 1080p 处理完成；
4. 在无登录/隐身窗口打开一次，确认能播放；
5. 记下视频时长，必须 `< 3:00`；
6. 把 YouTube URL 替换到 `docs/paypal/DEVPOST.md` 的唯一 `[[YouTube link…]]`。

不要为了填链接而把视频设成 Private 或仅自己可见。

## 7. Devpost 怎么填

打开 `docs/paypal/DEVPOST.md`，按下面的映射粘贴：

| Devpost 页面字段 | 从哪里复制 |
| --- | --- |
| Project name | `Project name` |
| Elevator pitch / tagline | `Elevator pitch` |
| Project image / thumbnail | `docs/paypal/media/thumbnail.png` |
| Inspiration / What it does / How we built it / Challenges / Accomplishments / What we learned / What's next | `About the project` 下同名小节 |
| Built with | `Built with (tags)` |
| Try it out / Repository | `Try it out links` 中的 GitHub URL |
| Demo video | 你刚上传的 Public YouTube URL |
| PayPal technologies | 对应 Hackathon question 答案 |
| AI tools | 对应 Hackathon question 答案；已如实写明 runtime AI 和 coding assistants |
| Existing vs new work | 对应 Hackathon question 答案，并链接 `PREEXISTING_WORK.md` |
| How judges run it | 对应本地运行说明；官方允许清晰的本地 setup 代替 hosted demo |

奖项建议勾选：

- Overall / Grand Prize；
- Most Impactful；
- Best Use of Agentic Commerce；
- Best Use of PayPal + AI；
- Most Creative；
- Best Demo Delivery。

只有确实完成 Render 部署并在项目里实际使用时，才选 Best Use of Render。不要仅因为仓库有 `render.yaml` 就申报 sponsor prize。

## 8. 提交前与提交后

逐项完成 `FINAL_SUBMISSION_CHECKLIST_ZH.md`。尤其检查：

```bash
grep -R -F "[[" README.md docs/paypal
python -m scripts.check_paypal_submission_pack
git status --short --branch
```

录视频前可以运行 `python -m scripts.check_paypal_submission_pack --allow-video-placeholder`。真正提交前必须去掉这个参数；如果 YouTube 链接还没替换，预检会失败。Devpost 英文正文不能再有占位符。

由你本人点击 Devpost **Submit**。提交后：

1. 刷新项目公开页；
2. 在隐身窗口检查 GitHub、YouTube 和缩略图；
3. 截图保存 Submitted 状态和提交时间；
4. 不要在截止前最后几分钟重写仓库历史或 force-push；
5. 如果修改视频或文案，重新检查 Devpost 是否仍显示 Submitted。

## 9. 30 秒英文备用 pitch

> CallGate Checkout connects the conversation, the PayPal order, and the parcel. AI reads the messy negotiation and may draft the order, but deterministic code checks every amount against the exact words both people agreed to. Before capture, we re-check the order and PayPal ship-to address; after capture, packing, tracking, and signed evidence stay linked. The result is agentic commerce without giving the agent authority to move money.
