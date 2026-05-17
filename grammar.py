from dataclasses import dataclass


@dataclass(frozen=True)
class Production:
    left: str
    right: tuple[str, ...]


@dataclass
class Grammar:
    tokens: set[str]
    ignore_tokens: set[str]
    productions: list[Production]
    start_symbol: str
