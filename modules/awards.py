import re, json, random, string
from unidecode import unidecode
from modules.shared.base import APIProcess


class AwardBotProcess(APIProcess):
    def __init__(self, source_version, subreddit_name):
        # setup PRAW, db and http session
        super().__init__(source_version)

        self.subreddit_name = subreddit_name

        with open('keyword_mapping.json') as json_file:
            self.keyword_mapping = json.load(json_file)

        keywords = map(unidecode, self.keyword_mapping.keys())
        keyword_join = '|'.join(
            re.escape(keyword) for keyword in keywords
        )

        negate_char = re.escape('\\')
        keyword_pattern = '{}{}{}'.format(
            f'(?P<negated>{negate_char})?',
            f'(?P<keyword>{keyword_join})',
            f'(?:[{string.punctuation}])?',
        )

        self.keyword_re = re.compile(keyword_pattern, re.IGNORECASE)

    def add_reply(self, comment, matched_keywords):
        print(f'@@@ {matched_keywords}')

    def run(self):
        """Start process"""
        self.setup_interrupt_handlers()

        # ignored users (bots and such)
        blacklist_config = self.reddit.config.custom['bot_comments_blacklist']
        blacklist = {
            name.strip().lower() for name in blacklist_config.split(',')
        }

        # process submissions
        subreddit = self.reddit.subreddit(self.subreddit_name)
        for comment in subreddit.stream.comments(skip_existing=True):
            print([comment.author, comment.body])
            # Use .name to avoid another API call
            if comment.author.name.lower() not in blacklist:
                tokens = comment.body.split()
                matches = map(self.keyword_re.fullmatch, tokens)

                matched_keywords = {
                    match['keyword'] for match in matches
                    if match is not None and match['negated'] is None
                }

                if matched_keywords:
                    self.add_reply(comment, matched_keywords)
