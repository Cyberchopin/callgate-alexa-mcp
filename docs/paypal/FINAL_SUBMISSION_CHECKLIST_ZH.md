# PayPal AI Hackathon · 最终提交检查清单

只有全部打勾后才点击 Submit。

## A. 仓库与代码

- [ ] GitHub 仓库为 Public。
- [ ] Devpost 指向 `https://github.com/Cyberchopin/callgate-alexa-mcp` 或明确的 `main` 路径。
- [ ] 根目录能看到新的 CallGate Checkout README 和 MIT `LICENSE`。
- [ ] `python -m pytest tests/paypal_checkout -q` 显示 `94 passed`。
- [ ] `python -m evaluation_paypal.run` 的数字与 README / Devpost 一致。
- [ ] GitHub Actions 全绿；没有 pending 或 failing required check。
- [ ] 没有 `.env`、API key、PayPal Secret、真实邮箱或个人地址进入 Git。
- [ ] `docs/paypal/sandbox-run.json` 只有脱敏 sandbox 证据。
- [ ] `git status --short --branch` 干净。
- [ ] `python -m scripts.check_paypal_submission_pack` 显示 `submission_pack=PASS`。

## B. 视频

- [ ] 时长小于 3:00，建议 2:40–2:55。
- [ ] YouTube Visibility 为 Public，隐身窗口能播放。
- [ ] 1080p 已处理完成，金额和按钮可读。
- [ ] 画面明确是 PayPal Sandbox / test account，不暗示真实资金。
- [ ] 没有 API key、Secret、邮箱、地址、通知或密码管理器出镜。
- [ ] 英文旁白说明 AI 负责读取/草拟，deterministic code 负责 gate。
- [ ] 展示至少一个失败路径：错误金额、订单篡改或目的地不匹配。
- [ ] 展示至少一个交付后证据：packing、tracking 或 signed evidence。
- [ ] 没有有版权的背景音乐或无关第三方素材。
- [ ] YouTube 标题、简介、仓库链接和章节已检查。

## C. Devpost 文案

- [ ] Project name 为 `CallGate Checkout`。
- [ ] Elevator pitch 未超过页面字符限制。
- [ ] 上传 `docs/paypal/media/thumbnail.png`。
- [ ] About the project 使用 `docs/paypal/DEVPOST.md` 的最终英文文案。
- [ ] 没有声称生产安全、真实用户效果、独立评测或无法证明的准确率。
- [ ] 已披露 existing CallGate prior work 和本次新增边界。
- [ ] AI tools 同时写清 runtime AI 与 coding assistants。
- [ ] Repository、YouTube 和技术 README 链接均可公开访问。
- [ ] 英文正文中搜索不到 `[[`、`TODO`、`TBD` 或示例 URL。
- [ ] 没有填写未实际使用的 sponsor tool；Render 未部署则不选 Render prize。

## D. 最终提交

- [ ] 选择适用奖项：Overall、Most Impactful、Agentic Commerce、PayPal + AI、Most Creative、Best Demo Delivery。
- [ ] 用 Preview 从头读一遍，标题层级和列表正常。
- [ ] 由账号所有者本人点击 Submit。
- [ ] 提交后公开页显示 Submitted，而不是 Draft。
- [ ] 保存 Submitted 状态和时间截图。
- [ ] 在隐身窗口再检查一次 GitHub 与 YouTube。

## 一票否决项

出现以下任一情况，不要提交：

- 视频超过 3 分钟或无法公开播放；
- 仓库不是 Public 或没有 LICENSE；
- secret scan 报错且原因尚未确认；
- 视频或仓库暴露 credentials / 个人信息；
- 文案仍有占位符；
- 把 offline stand-in 说成真实 PayPal；
- 把 synthetic benchmark 说成真实用户准确率；
- 使用真实资金或 live PayPal 环境做演示。
