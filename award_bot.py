#!/usr/bin/env python3
"""Reddit AwardBot

Usage: award_bot.py <subreddit> [--debug]
       award_bot.py -h | --help
       award_bot.py --version

Options:
    --debug                     Enable HTTP debugging
    -h, --help                  Show this screen

Environment Variables:
    PRAW_SITE                   The name of the config section on praw.ini for this process
    DATABASE_URL                URI of the Postgres instance to use
"""
import os
from docopt import docopt, DocoptExit
from modules.awards import AwardBotProcess
from modules.shared.utils import setup_http_debugging

__version__ = '1.0.0'


if __name__ == '__main__':
    # process commandline args
    args = docopt(__doc__, version=f'Reddit AwardBot v{__version__}')

    # check environment variables
    database_url = os.getenv('DATABASE_URL')
    if database_url is None:
        raise DocoptExit("Missing DATABASE_URL variable.\n")

    # we use uppercase for consistency but convert it to lowercase since that's what PRAW uses
    praw_site = os.getenv('PRAW_SITE')
    if praw_site is not None:
        os.environ['praw_site'] = praw_site

    praw_site = os.getenv('praw_site')
    if praw_site is None:
        raise DocoptExit("Missing PRAW_SITE variable.\n")

    # run process
    if args['--debug']:
        setup_http_debugging()

    subreddit = args['<subreddit>']
    bot_process = AwardBotProcess(__version__, subreddit)

    bot_process.run()
