---
name: qq-send-file
description: >
  Send an image, video, voice, or any file to a QQ group through the 夜琥 bot
  (openclaw_qq send-API). Use when the user asks to push, share, or post a
  file/picture/meme/video to a QQ group, or to have the QQ bot deliver a file
  to a specific group number. The message is sent by bot account 夜琥
  (QQ 2753405784); no agent session or LLM call is involved.
  Triggers: "发到群里", "发图片到群", "发群文件", "把这个发到QQ群", "转发到群",
  "机器人帮我发图", "发个视频到群里", "send file to QQ group", "send to group",
  "post this to the QQ group".
---

# QQ Send File — 把文件发到指定 QQ 群

通过本机 openclaw_qq 插件的 HTTP 发送 API，让 QQ 机器人「夜琥」把文件发进群。

## 服务位置

- 本机: `http://127.0.0.1:7600`
- 局域网: `http://192.168.1.219:7600`（主机 IP 变动时以实际为准）
- 探活: `GET /health` → `{"ok":true,...}`

## 鉴权（token）

三种来源，任选其一：

1. `~/.openclaw/.qq-send-token`（单行文本，推荐；脚本会自动读取）
2. 环境变量 `QQ_SEND_TOKEN`
3. 请求头 `Authorization: Bearer <TOKEN>`（或 `X-Token`、`?token=`）

## 最快用法（脚本）

```bash
python3 ~/.openclaw/skills/qq-send-file/scripts/send.py <群号> <文件路径> [--text "说明文字"]
```

示例——把一张梗图发到「全是助手」(960758971)：

```bash
python3 ~/.openclaw/skills/qq-send-file/scripts/send.py 960758971 /tmp/meme.png --text "看看这个"
```

脚本自动完成 token 读取、URL 编码、类型判断；成功打印 `{"ok":true,...}` 并退出码 0。

## 直接 HTTP 调用

```bash
# 原始字节上传（注意中文参数必须 URL 编码，否则会被 HTTP 层直接 400 拒收）
curl -X POST "http://127.0.0.1:7600/send?group=960758971&filename=meme.png" \
  -H "Authorization: Bearer <TOKEN>" --data-binary @/tmp/meme.png

# JSON 模式（适合脚本内嵌，文件内容放 fileBase64）
curl -X POST "http://127.0.0.1:7600/send" -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"group":960758971,"filename":"meme.png","text":"看看这个","fileBase64":"<BASE64>"}'
```

## 参数（POST /send）

| 参数 | 必填 | 说明 |
|---|---|---|
| `group` | 是 | 目标群号（纯数字） |
| `filename` | 建议 | 文件名；`auto` 类型判断靠扩展名（也可用 `X-Filename` 头） |
| `type` | 否 | `image` / `video` / `record`(语音) / `file`(群文件) / `auto`（默认，按扩展名判断） |
| `text` | 否 | 附带说明文字，图片/视频前先发一条文字 |

响应: `{"ok":true,"group":"...","type":"...","filename":"...","transport":"...","messageId":...}`

## 规则与限制

- 单次上限 **100MB**（服务端 `apiMaxBodyMb` 可调）。
- 群白名单：服务端 `apiAllowedGroups` 留空 = 任意群号可发。
- 查询参数里的中文**必须 URL 编码**（`urlencode` / `curl --data-urlencode` 场景外勿直接拼裸中文）。
- 图片/视频/语音以 base64 直发；`file` 类型走群文件上传（NapCat 回源拉取，失败自动回退 base64）。
- 消息以夜琥本人身份发出，不经过任何 LLM/agent 会话。

## 错误码

| 状态码 | 含义 |
|---|---|
| 400 | 参数缺失/非法（group、type、JSON 解析失败） |
| 401 | token 缺失或错误 |
| 403 | 目标群不在 `apiAllowedGroups` 白名单 |
| 413 | 文件超过体积上限 |
| 502 | OneBot/NapCat 侧发送失败 |
| 503 | 机器人 QQ 未连接（等重连后重试） |

## 运维

- 服务随 openclaw-gateway 启停（`systemctl --user restart openclaw-gateway`）。
- 配置在 `/root/.openclaw/openclaw.json` → `channels.qq`：`apiPort` `apiToken` `apiAllowedGroups` `apiMaxBodyMb` `apiListenHost` `apiPublicBaseUrl`。
- 日志: `journalctl --user -u openclaw-gateway | grep QQ-API`。
