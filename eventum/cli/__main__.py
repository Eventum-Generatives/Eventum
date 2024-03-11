import os
import argparse
import logging

import eventum.logging_config
from eventum.repository.manage import load_app_config, ContentReadError


eventum.logging_config.apply()
logger = logging.getLogger(__name__)


def _initialize_argparser(argparser: argparse.ArgumentParser) -> None:
    """Add arguments for initial argparser object."""

    argparser.add_argument(
        '-c', '--config',
        required=True,
        help='Configuration file'
    )


def main() -> None:
    argparser = argparse.ArgumentParser(
        prog="eventum",
        description="Flexible event generation tool",
        epilog="Repository: https://github.com/rnv812/Eventum",
    )

    _initialize_argparser(argparser)

    args = argparser.parse_args()

    logger.info(f'Resolving location of config file "{args.config}"')

    if os.path.isabs(args.config):
        config_path = args.config
    else:
        config_path = os.path.join(
            os.path.abspath(os.getcwd()), args.config
        )

        if not os.path.exists(config_path):
            logger.info(
                'Config file not found from current location and '
                'will be read from repository'
            )
            config_path = args.config

    try:
        app_config = load_app_config(config_path)
    except ContentReadError as e:
        logger.error(f'Failed to read config file: {e}')
        exit(1)


if __name__ == '__main__':
    main()
