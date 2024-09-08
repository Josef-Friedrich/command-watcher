import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formatdate

from command_watcher.channel import BaseChannel
from command_watcher.message import Message


def send_email(
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
    smtp_login: str,
    smtp_password: str,
    smtp_server: str,
) -> dict[str, tuple[int, bytes]]:
    """
    Send a email.

    :param from_addr: The email address of the sender.
    :param to_addr: The email address of the recipient.
    :param subject: The email subject.
    :param body: The email body.
    :param smtp_login: The SMTP login name.
    :param smtp_password: The SMTP password.
    :param smtp_server: The URL of the SMTP server, for
      example: `smtp.example.com:587`.

    :return: Problems
    """
    message = MIMEText(body, "plain", "utf-8")

    message["Subject"] = str(Header(subject, "utf-8"))
    message["From"] = from_addr
    message["To"] = to_addr
    message["Date"] = formatdate(localtime=True)

    server = smtplib.SMTP(smtp_server)
    server.starttls()
    server.login(smtp_login, smtp_password)
    problems = server.sendmail(from_addr, [to_addr], message.as_string())
    server.quit()
    return problems


class EmailChannel(BaseChannel):
    """Send reports by e-mail."""

    smtp_server: str
    smtp_login: str
    smtp_password: str
    to_addr: str
    from_addr: str
    to_addr_critical: str

    def __init__(
        self,
        smtp_server: str,
        smtp_login: str,
        smtp_password: str,
        to_addr: str,
        from_addr: str,
        to_addr_critical: str,
    ) -> None:
        self.smtp_server = smtp_server
        self.smtp_login = smtp_login
        self.smtp_password = smtp_password
        self.to_addr = to_addr
        self.from_addr = from_addr
        self.to_addr_critical = to_addr_critical

    def __str__(self) -> str:
        return self._obj_to_str(
            [
                "smtp_server",
                "smtp_login",
                "to_addr",
                "from_addr",
            ]
        )

    def report(self, message: Message) -> None:
        """Send an e-mail message.

        :param message: A message object.
        """
        if message.status == 2 and self.to_addr_critical:
            to_addr = self.to_addr_critical
        else:
            to_addr = self.to_addr

        send_email(
            from_addr=self.from_addr,
            to_addr=to_addr,
            subject=message.message,
            body=message.body,
            smtp_login=self.smtp_login,
            smtp_password=self.smtp_password,
            smtp_server=self.smtp_server,
        )
