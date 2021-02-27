from dataclasses import dataclass, field


@dataclass
class Rule:
    id: str
    description: str
    ruleset: str
    location: str
    function: str
    excluded: bool = False
    parameters: dict = field(default_factory=dict)
