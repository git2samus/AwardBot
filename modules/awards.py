import re, json, random, string
from jinja2 import Environment, FileSystemLoader
from modules.shared.base import APIProcess
from modules.shared.utils import normalize_str


class AwardBotProcess(APIProcess):
    def __init__(self, source_version, subreddit_name):
        # setup PRAW, db and http session
        super().__init__(source_version)

        # internal variables
        self.subreddit_name = subreddit_name

        # setup templates
        self.template_env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=False
        )

        # prepare search patterns and keyword info
        negate_char_config = self.reddit.config.custom['bot_negate_char']
        negate_char = re.escape(negate_char_config)
        negated_keyword_pattern = f'(?P<negated>{negate_char})'

        with open('keyword_mapping.json') as json_file:
            self.keyword_mapping = {
                normalize_str(key): value
                for key, value in json.load(json_file).items()
            }

        keyword_join = '|'.join(
            re.escape(keyword) for keyword in self.keyword_mapping.keys()
        )
        keyword_join_pattern = f'(?P<keyword>{keyword_join})'

        punctuation_pattern = '(?:[{}])'.format(re.escape(string.punctuation))

        keyword_pattern = '{negated}?{keyword}{punctuation}?'.format(
            negated=negated_keyword_pattern,
            keyword=keyword_join_pattern,
            punctuation=punctuation_pattern,
        )
        self.keyword_re = re.compile(keyword_pattern)

    def add_reply(self, comment, matched_keywords):
        reply = []

        for keyword in sorted(matched_keywords):
            award_details = self.keyword_mapping[keyword]

            template_name = award_details['template']
            template = self.template_env.get_template(template_name)

            template_args = self.reddit.config.custom.copy()
            template_args.update({
                'sender': comment.author.name,
                'recipient': 'Samus?',
                'award_singular': award_details['award_singular'],
                'award_plural': award_details['award_plural'],
                'times': 2,
                'image_url': random.choice(award_details['images']),
            })

            reply.append(template.render(**template_args))

        print('\n\n---\n\n'.join(reply))

    def process_comment(self, comment):
        tokens = normalize_str(comment.body).split()

        matches = map(self.keyword_re.fullmatch, tokens)
        matched_keywords = {
            match['keyword'] for match in matches
            if match is not None and match['negated'] is None
        }

        if matched_keywords:
            self.add_reply(comment, matched_keywords)

    def run(self):
        """Start process"""
        self.setup_interrupt_handlers()

        # ignored users (bots and such)
        blacklist_config = self.reddit.config.custom['bot_comments_blacklist']
        blacklist = {
            name.strip() for name in normalize_str(blacklist_config).split(',')
        }

        # process submissions
        subreddit = self.reddit.subreddit(self.subreddit_name)
        for comment in subreddit.stream.comments(skip_existing=True):
            # Use author.name to avoid another API call
            if normalize_str(comment.author.name) not in blacklist:
                self.process_comment(comment)
