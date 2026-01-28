from email.header import Header
from email.mime.text import MIMEText
from email.utils import formatdate
from smtplib import SMTP

from command_watcher.channels.base_channel import BaseChannel
from command_watcher.message import Message


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

        mime = MIMEText(message.body, "plain", "utf-8")

        mime["Subject"] = str(Header(message.message, "utf-8"))
        mime["From"] = self.from_addr
        mime["To"] = to_addr
        mime["Date"] = formatdate(localtime=True)

        server = SMTP(self.smtp_server)
        server.starttls()
        server.login(self.smtp_login, self.smtp_password)
        server.sendmail(self.from_addr, [to_addr], mime.as_string())
        server.quit()
