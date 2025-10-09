## WebMail-less Mailing and Designing

A Python project that demonstrates practical networking with UDP and TCP:

- Two-way UDP chat application
- UDP live video streaming service (server/client)
- Secure TCP SMTP mail client (STARTTLS)
- Protocol overview docs for UDP and TCP

### Table of Contents

- Features
- Prerequisites
- Setup
- Project Structure
- Two-way UDP Chat (usage, options, how it works)
- UDP Live Video Streaming (usage, options, how it works)
- Secure TCP SMTP Mail Client (usage, options, security)
- Troubleshooting
- Security Notes
- Local Testing Tips
- Documentation

### Features

- Simple, readable Python implementations of core networking patterns
- UDP text chat with concurrent send/receive
- UDP video streaming with JPEG framing, fragmentation, and client-side reassembly
- SMTP over TCP with STARTTLS and SMTPS support, plus email validation

### Prerequisites

- Python 3.10+
- macOS (tested), Linux should work similarly

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional: export credentials for SMTP so you do not type them on the command line.
```bash
export SMTP_USER="your_email@example.com"
export SMTP_PASS="your_app_password"
```

### Project Structure

```text
.
├─ udp_chat.py                # Two-way UDP chat CLI
├─ udp_video_server.py        # UDP video server (camera capture → UDP datagrams)
├─ udp_video_client.py        # UDP video client (reassembly → OpenCV display)
├─ smtp_client.py             # Secure TCP SMTP (STARTTLS/SMTPS)
├─ docs/
│  └─ PROTOCOLS.md           # UDP vs TCP overview used in this project
├─ requirements.txt
└─ README.md
```

### Two-way UDP Chat

Run one instance as a listener and one as a sender (or both bi-directionally). Each instance both listens and sends.

Terminal A (listen on 5000, send to 127.0.0.1:5001):
```bash
python udp_chat.py --listen-port 5000 --peer-host 127.0.0.1 --peer-port 5001
```

Terminal B (listen on 5001, send to 127.0.0.1:5000):
```bash
python udp_chat.py --listen-port 5001 --peer-host 127.0.0.1 --peer-port 5000
```

Type to chat; Ctrl+C to quit.

Options:
```bash
python udp_chat.py --help
```
- `--listen-host` (default `0.0.0.0`): interface to bind for incoming packets
- `--listen-port` (required): UDP port to listen on
- `--peer-host` (required): destination peer host/IP
- `--peer-port` (required): destination peer port

How it works:
- A UDP socket is bound to `listen-host:listen-port`
- A background thread continuously prints received datagrams
- The main thread reads stdin lines and sends them to the peer via UDP

### UDP Live Video Streaming

Start the server (captures from default camera index 0):
```bash
python udp_video_server.py --host 0.0.0.0 --port 6000 --camera-index 0
```

Start the client (receives and displays):
```bash
python udp_video_client.py --server-host 127.0.0.1 --server-port 6000
```

Controls: press 'q' in the video window to quit the client. Server can be stopped with Ctrl+C.

Notes:
- Frames are JPEG-encoded and fragmented across UDP datagrams with headers for reassembly.
- Defaults use safe datagram payload size (1200 bytes). Adjust with `--mtu` if needed.

Server options:
```bash
python udp_video_server.py --help
```
- `--host` (default `0.0.0.0`): bind address
- `--port` (default `6000`): UDP port
- `--camera-index` (default `0`): OpenCV camera index
- `--mtu` (default `1200`): total datagram size including header
- `--fps` (default `20`): target frames per second
- `--quality` (default `60`): JPEG quality (10–95)

Client options:
```bash
python udp_video_client.py --help
```
- `--server-host` (required): server hostname or IP
- `--server-port` (default `6000`): server port
- `--listen-host` (default `0.0.0.0`): local bind address
- `--listen-port` (default `0`): local port (0 = OS chooses ephemeral)
- `--timeout` (default `2.0`): socket timeout
- `--max-buffer-frames` (default `5`): max frames tracked for reassembly

How it works:
- Server flow:
  1. Bind UDP socket and wait for a small "hello" packet from client to learn its address
  2. Capture a frame from the camera with OpenCV
  3. JPEG-encode the frame; fragment into chunks size ≤ `mtu - header`
  4. Send each chunk with a small header: `frame_id`, `total_chunks`, `chunk_index`, `payload_len`
  5. Repeat at target FPS
- Client flow:
  1. Send a "hello" packet to the server and begin receiving packets
  2. Group chunks by `frame_id` and reassemble when all chunks received
  3. Decode JPEG and display; drop incomplete/outdated frames to keep latency low

Header layout (network byte order):
```text
frame_id:      uint32
total_chunks:  uint16
chunk_index:   uint16
payload_len:   uint32
```

ASCII overview:
```text
[Camera] -> [JPEG Encode] -> [Fragment] -> [UDP] ~~network~~> [UDP] -> [Reassemble] -> [Decode] -> [Display]
```

### Secure TCP SMTP Mail Client

Send an email via SMTP with STARTTLS:
```bash
python smtp_client.py \
  --smtp-host smtp.gmail.com --smtp-port 587 \
  --username your_email@gmail.com --password 'app_password' \
  --from-addr your_email@gmail.com \
  --to-addr recipient@example.com \
  --subject "Hello" \
  --body "This is a test sent via secure TCP."
```

Notes:
- Many providers require an App Password and 2FA.
- For SMTPS (implicit TLS, e.g., port 465), use `--smtps`.

Options:
```bash
python smtp_client.py --help
```
- `--smtp-host` / `--smtp-port`: SMTP server and port (587 STARTTLS, 465 SMTPS)
- `--username` / `--password`: credentials (consider env vars)
- `--from-addr` / `--to-addr`: validated sender/recipient
- `--subject` / `--body`: message content
- `--smtps`: use implicit TLS instead of STARTTLS

Example using environment variables:
```bash
python smtp_client.py \
  --smtp-host smtp.gmail.com --smtp-port 587 \
  --username "$SMTP_USER" --password "$SMTP_PASS" \
  --from-addr "$SMTP_USER" --to-addr recipient@example.com \
  --subject "Hello" --body "From env vars"
```

How it works:
- For STARTTLS: connect via TCP → `EHLO` → `STARTTLS` → TLS handshake → `EHLO` → `AUTH LOGIN` → `MAIL FROM`/`RCPT TO`/`DATA`
- For SMTPS: connect via TLS-wrapped TCP socket, then authenticate and send

### Troubleshooting

- UDP chat/stream not receiving:
  - Verify IP/ports and that both sides are on the same network
  - Check firewall rules; on macOS you may need to allow Python for incoming connections
  - Try `--mtu 1000` on the server to reduce packet sizes
- Video client window black:
  - Ensure the server prints that a client connected
  - Confirm the camera index is correct (try `--camera-index 1`)
  - Close other apps using the camera
- SMTP auth fails:
  - Use provider-specific App Passwords; many disable password logins with regular credentials
  - Double-check `--from-addr` matches the authenticated account for some providers
  - Port 587 usually requires STARTTLS; port 465 is SMTPS

### Security Notes

- UDP video and chat are unencrypted; for sensitive content consider DTLS or application-layer encryption
- SMTP client validates server certificates using the default SSL context
- Avoid passing secrets directly on CLI history; prefer environment variables

### Local Testing Tips

- Loopback testing: run all components on `127.0.0.1` using different ports
- Cross-machine LAN test: replace `127.0.0.1` with the host machine's LAN IP
- Performance knobs: lower `--fps` or `--quality` to reduce bandwidth

### Documentation

See `docs/PROTOCOLS.md` for a concise overview of UDP and TCP and how they are used in this project.


### Deployment (Docker + Compose)

Build images and run with Docker Compose:
```bash
docker compose build
docker compose up -d udp_video_server

# Use the tools container interactively for CLIs
docker compose run --rm tools python udp_chat.py --help
docker compose run --rm tools python smtp_client.py --help
docker compose run --rm tools python udp_video_client.py --server-host host.docker.internal --server-port 6000
```

Environment variables for SMTP (Compose auto-loads `.env` in project root):
```env
SMTP_USER=your_email@example.com
SMTP_PASS=your_app_password
```

Notes:
- Linux camera passthrough: map `/dev/video0` into the `udp_video_server` service if needed.
- macOS: containers cannot access host camera; run `udp_video_server.py` on the host and point clients to `host.docker.internal` or host IP.
- Port mapping: UDP `6000` is exposed by default in `docker-compose.yml`.

Build and run images directly (without Compose):
```bash
# Multi-purpose tools
docker build -t webmailless/tools:latest -f Dockerfile .
docker run --rm -it -e SMTP_USER -e SMTP_PASS webmailless/tools:latest python smtp_client.py --help

# Video server
docker build -t webmailless/udp-video-server:latest -f Dockerfile.video-server .
docker run --rm -it -p 6000:6000/udp webmailless/udp-video-server:latest --host 0.0.0.0 --port 6000
```

