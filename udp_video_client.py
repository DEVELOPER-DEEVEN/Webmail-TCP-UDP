#!/usr/bin/env python3
"""
UDP Video Streaming Client.

Connects to the UDP video server, reassembles fragmented JPEG frames,
and displays them using OpenCV.
"""

import argparse
import socket
import struct
import time
from collections import defaultdict
from typing import Dict, Optional, TypedDict

import cv2
import numpy as np


HEADER_STRUCT = struct.Struct("!I H H I")
# frame_id, total_chunks, chunk_index, payload_len


class FrameBuffer(TypedDict):
    """Buffer for reassembling fragmented video frames."""
    chunks: Dict[int, bytes]
    total: Optional[int]
    ts: float


def main() -> None:
	"""Main entry point for the UDP video client."""
	parser = argparse.ArgumentParser(description="UDP Video Streaming Client")
	parser.add_argument("--server-host", required=True)
	parser.add_argument("--server-port", type=int, default=6000)
	parser.add_argument("--listen-host", default="0.0.0.0")
	parser.add_argument("--listen-port", type=int, default=0, help="0 = ephemeral")
	parser.add_argument("--timeout", type=float, default=2.0)
	parser.add_argument("--max-buffer-frames", type=int, default=5)
	args = parser.parse_args()

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((args.listen_host, args.listen_port))
	sock.settimeout(args.timeout)

	server = (args.server_host, args.server_port)
	# Send a hello to announce ourselves
	sock.sendto(b"hello", server)

	# Using FrameBuffer TypedDict for better type safety
	frames: Dict[int, FrameBuffer] = defaultdict(lambda: {"chunks": {}, "total": None, "ts": time.time()})
	curr_frame_id = -1

	try:
		while True:
			try:
				packet, _ = sock.recvfrom(65535)
			except socket.timeout:
				continue
			if len(packet) < HEADER_STRUCT.size:
				continue
			frame_id, total_chunks, chunk_index, payload_len = HEADER_STRUCT.unpack_from(packet, 0)
			payload = packet[HEADER_STRUCT.size : HEADER_STRUCT.size + payload_len]
			buf = frames[frame_id]
			chunks = buf["chunks"]
			chunks[chunk_index] = bytes(payload)
			if buf["total"] is None:
				buf["total"] = total_chunks
			# Evict old frames to limit memory
			while len(frames) > args.max_buffer_frames:
				oldest = min(frames.keys())
				if oldest != frame_id:
					frames.pop(oldest, None)
					break
				else:
					break
			if len(chunks) == total_chunks:
				# Reassemble
				ordered = [chunks[i] for i in range(total_chunks)]
				jpeg_bytes = b"".join(ordered)
				arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
				frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
				if frame is not None:
					cv2.imshow("UDP Stream", frame)
					if cv2.waitKey(1) & 0xFF == ord('q'):
						break
				frames.pop(frame_id, None)
				curr_frame_id = frame_id
	finally:
		cv2.destroyAllWindows()
		sock.close()


if __name__ == "__main__":
	main()

