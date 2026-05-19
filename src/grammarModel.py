from dataclasses import dataclass


@dataclass(frozen=True)
class Production:
    left: str
    right: tuple[str, ...]


@dataclass
class Grammar:
    tokens: set[str]
    ignoreTokens: set[str]
    productions: list[Production]
    startSymbol: str
