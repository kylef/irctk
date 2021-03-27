from typing import List

from irctk.client import Client


class MockClient(Client):
    def __init__(self, *args, **kwargs):
        self.sent_lines: List[str] = []
        super(MockClient, self).__init__(*args, **kwargs)

    def send_line(self, line: str) -> None:
        self.sent_lines.append(line)
