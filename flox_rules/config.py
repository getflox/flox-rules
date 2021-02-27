from floxcore import CONFIG_DIRS
from floxcore.context import Flox
from floxcore.remotes import universal_copy


def handle_configuration_change(flox: Flox, out, **kwargs):
    """Update rules configuration"""

    for source in flox.settings.rules.source:
        universal_copy(flox, CONFIG_DIRS.get_in("user", "rules"), source)
