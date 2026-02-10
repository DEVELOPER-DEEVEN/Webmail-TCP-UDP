#!/usr/bin/env python3
import argparse
import socket
import sys
import threading
from typing import Tuple


def create_udp_socket(listen_host: str, listen_port: int) -> socket.socket:
	"""Create a UDP socket bound to the given host/port."""
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((listen_host, listen_port))
	return sock


def receiver_loop(sock: socket.socket) -> None:
    """Continuously receive datagrams and print them to stdout."""
    try:
        while True:
            data, addr = sock.recvfrom(2048)
            msg = data.decode(errors='replace')
            # Sanitize output to prevent terminal escape injection
            msg = "".join(ch for ch in msg if ch.isprintable() or ch == "\n")
            print(f"\r<{addr[0]}:{addr[1]}> {msg}\n> ", end="", flush=True)
    except OSError:
        return


def sender_loop(sock: socket.socket, peer: Tuple[str, int]) -> None:
    """Read stdin lines and send as UDP datagrams to the peer."""
    try:
        while True:
            msg = input("> ")
            if msg.strip().lower() in {"/quit", ":q", "exit"}:
                break
            if not msg:
                continue
            sock.sendto(msg.encode('utf-8'), peer)
    except (EOFError, KeyboardInterrupt):
        pass


def main() -> None:
	parser = argparse.ArgumentParser(description="Two-way UDP chat")
	parser.add_argument("--listen-host", default="0.0.0.0")
	parser.add_argument("--listen-port", type=int, required=True)
	parser.add_argument("--peer-host", required=True)
	parser.add_argument("--peer-port", type=int, required=True)
	args = parser.parse_args()

	sock = create_udp_socket(args.listen_host, args.listen_port)

	recv_thread = threading.Thread(target=receiver_loop, args=(sock,), daemon=True)
	recv_thread.start()

	try:
		sender_loop(sock, (args.peer_host, args.peer_port))
	finally:
		sock.close()

	print("Bye.")


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print("\nInterrupted.")
		sys.exit(130)

