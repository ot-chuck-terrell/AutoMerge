#!/usr/bin/python3

import configparser
import logging
import argparse
from github.client import GitHubClient
from github.types import GitHubError

access_token = '969bb47731a804a5e4586f8d48904dd96c6dc686'
master_branch = 'master'
rel_branch = ''
current_rel_branch = ''
head_branch = ''
base_branch = ''
is_ocr = False

client = GitHubClient(access_token, 'OneTechLP')

parser = argparse.ArgumentParser(
    prog="AutoMerge",
    description="Script for auto-merging branches across repositories within an organization"
)
parser.add_argument('base_branch', help="Base branch for the merge (i.e. master)")
parser.add_argument('head_branch', help="Branch to be merged into the base (i.e. REL-2910)")
parser.add_argument('--current_rel_branch',
    help="If specified, will attempt to merge the base branch into the current release branch. This can be useful for OCRs")
parser.add_argument('--token', help="GitHub API access token to be used. Overrides the default specified by config")
parser.add_argument('--org', help="GitHub organization to perform the auto merge against. Overrides the default specified by config")
parser.add_argument('--config_path', help="Optionally tell the script where to find the config file. By default it searches in the base directory")

args = parser.parse_args()


head_branch = args.head_branch
base_branch = args.base_branch
current_rel_branch = args.current_rel_branch if args.current_rel_branch else ''

config = configparser.ConfigParser()

if args.config_path:
    config.read(args.config_path)
else:
    config.read('config.ini')

access_token = config['DEFAULT']['access_token']
organization = config['DEFAULT']['organization']

if args.token:
    access_token = args.token

if args.org:
    organization = args.org

def auto_merge(base: str, head: str, curr_rel: str, client: GitHubClient):

    # get repositories with the head branch (i.e. all repos with a 'REL-2910' branch)
    head_repos = [repo for repo in client.get_repositories(head) if repo.ref]

    if not head_repos:
        raise Exception("No repositories were found matching the head: {}".format(head))

    logging.info('Found {} repositories matching head {}'.format(len(head_repos), head))

    head_repo_pairs = [(repo.name, repo) for repo in head_repos]

    # pair repositories with a matching base and head branch
    base_head_repo_pairs = []
    for repo in client.get_repositories(base):
        for pairs in head_repo_pairs:
            if repo.name == pairs[0]:
                base_head_repo_pairs.append((repo, pairs[1]))

    if not base_head_repo_pairs:
        raise Exception("No repositories were found matching the base: {}".format(base))

    logging.info('Found {} repositories matching base {}'.format(len(base_head_repo_pairs), base))

    logging.info('Preparing to merge the following repositories')
    for pair in base_head_repo_pairs:
        logging.info("{}: {} ==>> {}".format(pair[0].name, head, base))




    if not curr_rel:
        return

    rel_repos = [repo for repo in client.get_repositories(curr_rel) if repo.ref]
    

def merge_branches(head_base_pairs: []):
    succeeded = []
    failed = []
    for pair in head_base_pairs:
        logging.info('Merging {}'.format(pairs[0].name))
        try:
            client.merge_branch(pair[0], base, head, 'Merge completed by AutoMerge utility')
            logging.info('Merge completed')
            succeeded.append(pair)
        except GitHubError as err:
            if 'already merged' in err.message.lower():
                logging.warn('{}: Already Merged'.format(pair[0].name))
            else:
                logging.exception('{}: Failed merge. {}'.format(pair[0].name, err.message))
            failed.append((err, pair))

    print('Succeeded:')
    print('----------')
    for pair in succeeded:
        print(pair[0].name)
    print('----------')

    print('Failed:')
    print('---------')
    for pair in failed:
        print('{}: {}'.format(pair[1][0].name, pair[1].message))
    print('---------')