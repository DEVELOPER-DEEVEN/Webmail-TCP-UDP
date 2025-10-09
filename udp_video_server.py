#!/usr/bin/env python3
import argparse
import socket
import struct
import time
from typing import Tuple

import cv2


HEADER_STRUCT = struct.Struct("!I H H I")
# Fields: frame_id (uint32), total_chunks (uint16), chunk_index (uint16), payload_len (uint32)


def fragment_and_send(sock: socket.socket, addr: Tuple[str, int], frame_bytes: bytes, mtu: int, frame_id: int) -> None:
	payload_capacity = max(1, mtu - HEADER_STRUCT.size)
	total_chunks = (len(frame_bytes) + payload_capacity - 1) // payload_capacity
	for chunk_index in range(total_chunks):
		offset = chunk_index * payload_capacity
		chunk = frame_bytes[offset : offset + payload_capacity]
		header = HEADER_STRUCT.pack(frame_id, total_chunks, chunk_index, len(chunk))
		sock.sendto(header + chunk, addr)


def main() -> None:
	parser = argparse.ArgumentParser(description="UDP Video Streaming Server")
	parser.add_argument("--host", default="0.0.0.0")
	parser.add_argument("--port", type=int, default=6000)
	parser.add_argument("--camera-index", type=int, default=0)
	parser.add_argument("--mtu", type=int, default=1200, help="Max datagram size including header")
	parser.add_argument("--fps", type=int, default=20)
	parser.add_argument("--quality", type=int, default=60, help="JPEG quality 10-95")
	args = parser.parse_args()

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((args.host, args.port))

	cap = cv2.VideoCapture(args.camera_index)
	if not cap.isOpened():
		raise RuntimeError("Failed to open camera")

	print(f"UDP video server listening on {args.host}:{args.port}")
	print("Waiting for first client packet to learn return address...")
	# Learn client address from a dummy 'hello' packet
	data, client_addr = sock.recvfrom(1024)
	print(f"Client at {client_addr} connected: {data!r}")

	frame_interval = max(0.001, 1.0 / max(1, args.fps))
	encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), max(10, min(args.quality, 95))]
	frame_id = 0

	try:
		while True:
			ok, frame = cap.read()
			if not ok:
				continue
			ok, buf = cv2.imencode(".jpg", frame, encode_params)
			if not ok:
				continue
			frame_bytes = buf.tobytes()
			fragment_and_send(sock, client_addr, frame_bytes, args.mtu, frame_id)
			frame_id = (frame_id + 1) & 0xFFFFFFFF
			time.sleep(frame_interval)
	finally:
		cap.release()
		sock.close()


if __name__ == "__main__":
	main()

