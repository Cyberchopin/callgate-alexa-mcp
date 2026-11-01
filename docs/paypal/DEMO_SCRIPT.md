# CallGate Checkout · 2:50 中英逐镜头演示脚本

目标成片：**2:40–2:55**。Devpost 评委不需要观看超过 3:00 的部分，所以宁可留 5–10 秒余量。

英文栏是可以直接照念的最终台词。中文栏告诉你画面怎么操作，不要把中文也念进视频。

## 录制前画面

- Seller 窗口：`http://127.0.0.1:8787`，约 1280 px 宽。
- Buyer 窗口：payer link，响应式约 390 px 宽。
- PayPal sandbox Personal buyer 已登录；邮箱打码。
- 启动环境包含 `PAYPAL_CLIENT_ID`、`PAYPAL_CLIENT_SECRET`、`ANTHROPIC_API_KEY`、`CALLGATE_DEMO=1`。
- 关闭通知、其他标签页、密码管理器和终端；画面中不出现 credentials。
- 先把下面每句练两遍，语速平稳，不要追求播音腔。

## 逐镜头脚本

| 时间 | 中文操作与画面 | 英文逐字念 | 这一镜必须证明什么 |
| --- | --- | --- | --- |
| 0:00–0:10 | 标题卡 2 秒，然后展示一段已打码的 resale chat，放大 `$80`、`$8 shipping` 和 `deal` | **“Resale deals happen in chat. The buyer and seller negotiate a price, agree, and then move somewhere else to create the payment.”** | 问题来自 chat 与 payment 脱节 |
| 0:10–0:20 | 切到 CallGate 首页，停在输入框 | **“That gap is where the wrong amount, the wrong address, or an unsafe instruction can become a real PayPal order.”** | 清楚定义风险，不夸大成所有诈骗 |
| 0:20–0:34 | 点 `Use a risky cross-border example`，再点 `Read the agreement` | **“CallGate Checkout connects the conversation to the order. A rule reader and an AI reader extract the deal, and every value must point back to the exact words that support it.”** | AI 有 grounding；不是自由生成 |
| 0:34–0:48 | 镜头停在金额 tag 和黄色/红色 flags；鼠标依次指向 redirect 与 friends-and-family 引用 | **“Here the total is one hundred and forty dollars. The same screen also flags a redirect request and an off-platform payment suggestion, with the quote and the reason each one matters.”** | 金额、引用和风险解释同屏 |
| 0:48–1:00 | 点 `Confirm these terms`；快速展示 provenance passport 新增条目 | **“The seller confirms only what the chat supports. Item provenance can travel with the sale as a signed, hash-linked passport, without pretending that a signature proves authenticity.”** | 人确认；provenance 边界表述准确 |
| 1:00–1:14 | 点 `Let the AI sales assistant draft it`，展示 AI panel 与 MCP tools | **“Now an AI sales assistant drafts the PayPal order through our MCP gateway. It can read the deal, propose an order, and check status—but it has no tool to approve, capture, release, or ship.”** | Agent 有能力但无资金权限 |
| 1:14–1:27 | 展示错误 `$180` draft 被标红、没有 payer link；随后展示纠正后的 match | **“If the assistant follows a planted one-hundred-and-eighty-dollar instruction, deterministic code compares every field with the confirmed deal. The mismatch is blocked, and the buyer gets no payment link.”** | 最强 agentic safety moment |
| 1:27–1:40 | Seller 复制 payer link，切 Buyer 窗口；展示金额、flags、passport，点确认 | **“The buyer sees the same terms, warnings, and provenance, then approves this exact order version—not a blank permission for whatever the agent does next.”** | Buyer approval 被 scope 到具体版本 |
| 1:40–1:50 | 切到真实 PayPal sandbox approval 页面，明显露出 sandbox 标识，点 Approve；邮箱已打码 | **“They approve through the PayPal sandbox as usual. No real money or live PayPal account is used in this demo.”** | 明确真实 sandbox、非真实资金 |
| 1:50–2:04 | 回 CallGate；用 demo control 把订单改成 `$180`，再尝试完成 payment，展示 refused / order changed | **“Before capture, CallGate reads the order again. If the amount changed after approval, the fingerprint no longer matches, so the capture is refused and nothing moves.”** | Approval 后篡改仍被阻止 |
| 2:04–2:17 | 展示目的地不符合 `US only` 时的 address hold；再切回已修复/重新同意状态 | **“It also checks PayPal’s ship-to country against the chat. An unsupported destination becomes a hold until the seller explicitly re-agrees; the agent cannot release it.”** | 地址 gate 与人工 re-agreement |
| 2:17–2:31 | 展示成功 capture 和 history；快速点 `How many charges did PayPal make?` 或显示一次 capture | **“For a valid order, a write-ahead ledger and PayPal idempotency make retries, double clicks, timeouts, and duplicate webhooks converge on one capture.”** | 不说绝对生产保证，只解释机制与演示结果 |
| 2:31–2:43 | 展示 packing checklist：item、original box、tags、weight、label destination；添加 tracking | **“After payment, promises from the chat become the packing checklist. The label must match PayPal’s address, weight is recorded, and tracking is sent back to PayPal.”** | 项目覆盖支付后，而非只做 checkout |
| 2:43–2:53 | 展示 signed consent/evidence JSON 或 evidence panel，最后切标题卡和 GitHub URL | **“If a dispute happens, the chat quotes, seller offer, buyer approval, capture, packing evidence, and tracking are already linked. CallGate Checkout: agentic commerce without giving the agent authority to move money.”** | 完整闭环与一句话记忆点 |

## 一镜失败时怎么补拍

- AI API 超时：不要假装成功。先停录，检查网络与 `ANTHROPIC_API_KEY`；最终视频必须使用真实成功画面，或者明确改成 scripted model 并口头说明。
- PayPal 页面没有 ship-to：换一个配置了测试地址的 sandbox Personal account；不要在视频里用真实地址。
- 订单状态混乱：停止当前 take，创建全新的 checkout。不要把两个 checkout 剪成一个连续交易。
- 英文卡住：画面继续录，重新念这一整句；剪辑时保留自然的一版。

## 超时删减顺序

如果粗剪超过 2:55，按顺序删：

1. 删除 0:48–1:00 中 provenance 的半句，只保留 seller confirmation；
2. 把 2:04–2:17 address hold 缩到 7 秒；
3. 把 2:31–2:43 packing 缩到 7 秒。

不要删除：AI draft mismatch、Buyer exact-order approval、PayPal sandbox、capture 前 re-check、结尾一句话。

## 录完后的英文自检

你必须确实说清以下四句意思：

1. **AI reads and drafts; deterministic code gates.**
2. **The payer approves one exact order version.**
3. **This is the PayPal sandbox; no real money is used.**
4. **The agent cannot approve, capture, release, or ship.**

如果任何一项没有表达出来，补录旁白，不要指望评委自己从代码猜。
