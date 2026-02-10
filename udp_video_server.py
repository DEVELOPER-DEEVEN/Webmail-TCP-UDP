#!/usr/bin/env python3
"""
UDP Video Streaming Server.

Captures video from a local camera, compresses it as JPEG, fragments it
into UDP datagrams, and sends it to a connected client.
"""

import argparse
import logging
import socket
import struct
import time
from typing import Tuple

import cv2


HEADER_STRUCT = struct.Struct("!I H H I")
# Fields: frame_id (uint32), total_chunks (uint16), chunk_index (uint16), payload_len (uint32)


def fragment_and_send(sock: socket.socket, addr: Tuple[str, int], frame_bytes: bytes, mtu: int, frame_id: int) -> None:
	"""
	Fragment a JPEG frame into chunks and send them over UDP.

	Args:
		sock: The socket to send through.
		addr: The destination address (host, port).
		frame_bytes: The complete JPEG bytestream.
		mtu: Maximum Transmission Unit (max packet size).
		frame_id: The unique identifier for this frame.
	"""
	payload_capacity = max(1, mtu - HEADER_STRUCT.size)
	total_chunks = (len(frame_bytes) + payload_capacity - 1) // payload_capacity
	for chunk_index in range(total_chunks):
		offset = chunk_index * payload_capacity
		chunk = frame_bytes[offset : offset + payload_capacity]
		header = HEADER_STRUCT.pack(frame_id, total_chunks, chunk_index, len(chunk))
		sock.sendto(header + chunk, addr)


def main() -> None:
	"""Main entry point for the UDP video server."""
	parser = argparse.ArgumentParser(description="UDP Video Streaming Server")
	parser.add_argument("--host", default="0.0.0.0")
	parser.add_argument("--port", type=int, default=6000)
	parser.add_argument("--camera-index", type=int, default=0)
	parser.add_argument("--mtu", type=int, default=1200, help="Max datagram size including header")
	parser.add_argument("--fps", type=int, default=20)
	parser.add_argument("--quality", type=int, default=60, help="JPEG quality 10-95")
	parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
	args = parser.parse_args()

	logging.basicConfig(
		level=logging.DEBUG if args.verbose else logging.INFO,
		format="%(asctime)s - %(levelname)s - %(message)s"
	)

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((args.host, args.port))

	cap = cv2.VideoCapture(args.camera_index)
	if not cap.isOpened():
		logging.error("Failed to open camera index %d", args.camera_index)
		raise RuntimeError("Failed to open camera")

	logging.info("UDP video server listening on %s:%d", args.host, args.port)
	logging.info("Waiting for first client packet to learn return address...")
	
	# Learn client address from a dummy 'hello' packet
	data, client_addr = sock.recvfrom(1024)
	logging.info("Client at %s connected: %r", client_addr, data)

	frame_interval = max(0.001, 1.0 / max(1, args.fps))
	encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), max(10, min(args.quality, 95))]
	frame_id = 0

	try:
		while True:
			ok, frame = cap.read()
			if not ok:
				logging.warning("Failed to capture frame")
				continue
			ok, buf = cv2.imencode(".jpg", frame, encode_params)
			if not ok:
				logging.warning("Failed to encode frame")
				continue
			frame_bytes = buf.tobytes()
			fragment_and_send(sock, client_addr, frame_bytes, args.mtu, frame_id)
			frame_id = (frame_id + 1) & 0xFFFFFFFF
			time.sleep(frame_interval)
	except KeyboardInterrupt:
		logging.info("Server stopping...")
	finally:
		cap.release()
		sock.close()
		logging.info("Resources released")


if __name__ == "__main__":
	main()

