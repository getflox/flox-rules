from typing import Tuple

from click import Group
from flox_rules.command import rules
from flox_rules.config import handle_configuration_change

from floxcore.command import Stage
from floxcore.config import Configuration, ParamDefinition
from floxcore.plugin import Plugin


class RulesConfiguration(Configuration):
    def parameters(self):
        return (
            ParamDefinition("source", "Rules source location", multi=True, default=""),
            ParamDefinition("exclude", "Rules exclusion pattern", multi=True, default=""),
            ParamDefinition("include", "Force inclusion of the rules matching pattern", multi=True, default=""),
        )

    def secrets(self) -> Tuple[ParamDefinition, ...]:
        return tuple()

    def schema(self):
        pass


class RulesPlugin(Plugin):
    def configuration(self):
        return RulesConfiguration()

    def add_commands(self, cli: Group):
        cli.add_command(rules)

    def handle_configuration_change(self, flox):
        return (
            Stage(handle_configuration_change),
        )


def plugin():
    return RulesPlugin()
