#!/usr/bin/env python3
import argparse
import base64
import os
import smtplib
import ssl
from email.message import EmailMessage

from email_validator import validate_email, EmailNotValidError


def build_message(from_addr: str, to_addr: str, subject: str, body: str) -> EmailMessage:
	msg = EmailMessage()
	msg["From"] = from_addr
	msg["To"] = to_addr
	msg["Subject"] = subject
	msg.set_content(body)
	return msg


def send_mail(
	smtp_host: str,
	smtp_port: int,
	username: str,
	password: str,
	from_addr: str,
	to_addr: str,
	subject: str,
	body: str,
	smtps: bool = False,
) -> None:
	context = ssl.create_default_context()
	msg = build_message(from_addr, to_addr, subject, body)

	if smtps:
		with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
			server.login(username, password)
			server.send_message(msg)
			print("Sent via SMTPS (implicit TLS)")
	else:
		with smtplib.SMTP(smtp_host, smtp_port) as server:
			server.ehlo()
			server.starttls(context=context)
			server.ehlo()
			server.login(username, password)
			server.send_message(msg)
			print("Sent via SMTP with STARTTLS")


def main() -> None:
	parser = argparse.ArgumentParser(description="Secure TCP SMTP client (STARTTLS/SMTPS)")
	parser.add_argument("--smtp-host", required=True)
	parser.add_argument("--smtp-port", type=int, required=True)
	parser.add_argument("--username", required=True)
	parser.add_argument("--password", required=True)
	parser.add_argument("--from-addr", required=True)
	parser.add_argument("--to-addr", required=True)
	parser.add_argument("--subject", default="")
	parser.add_argument("--body", default="")
	parser.add_argument("--smtps", action="store_true", help="Use SMTPS (implicit TLS)")
	args = parser.parse_args()

	try:
		validate_email(args.from_addr)
		validate_email(args.to_addr)
	except EmailNotValidError as e:
		raise SystemExit(f"Invalid email: {e}")

	send_mail(
		smtp_host=args.smtp_host,
		smtp_port=args.smtp_port,
		username=args.username,
		password=args.password,
		from_addr=args.from_addr,
		to_addr=args.to_addr,
		subject=args.subject,
		body=args.body,
		smtps=args.smtps,
	)


if __name__ == "__main__":
	main()

