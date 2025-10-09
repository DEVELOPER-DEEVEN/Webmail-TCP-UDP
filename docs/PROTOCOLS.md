## UDP and TCP Overview

### UDP (User Datagram Protocol)

- Connectionless, message-oriented: sends discrete datagrams without a persistent connection.
- No delivery guarantees: packets may be lost, reordered, or duplicated.
- Low overhead and latency: ideal for real-time media where timeliness > reliability.
- Application must handle fragmentation, loss, and reordering if needed.

In this project:
- UDP chat: tolerates loss; simple send/receive of small text messages.
- UDP video: frames are JPEG-encoded and fragmented with a small header containing frame_id, total_chunks, chunk_index, and payload_len. Client reassembles and displays, dropping incomplete frames.

### TCP (Transmission Control Protocol)

- Connection-oriented byte stream with reliability, order, and congestion control.
- Provides flow control and retransmission; suitable for data integrity.
- Higher latency and overhead vs UDP but guarantees delivery and order.

In this project:
- SMTP client: establishes a TCP connection to the mail server and upgrades to TLS (STARTTLS) or uses SMTPS. The `smtplib` library handles the protocol flow over TCP.

### Security Considerations

- UDP: typically unencrypted; consider DTLS or application-level crypto (e.g., libsodium) for confidentiality/integrity.
- TCP SMTP: Always use STARTTLS or SMTPS. Validate server certificates (default SSL context does this) and prefer provider-issued app passwords over raw credentials.

### Performance Considerations

- UDP MTU: keep payloads < 1200 bytes to avoid IP fragmentation across networks.
- Rate: cap FPS/bandwidth to avoid network saturation; consider adaptive quality.
- TCP SMTP: avoid blocking UI by running send in a separate thread or async context if integrating into a GUI.


