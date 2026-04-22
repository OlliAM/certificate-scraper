from dataclasses import dataclass

@dataclass
class Certificate:
    name: str
    url: str
    type: str