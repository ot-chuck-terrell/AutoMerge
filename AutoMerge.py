#!/usr/bin/python3

import configparser
import logging
import argparse
from github.client import GitHubClient
from github.types import GitHubError, Repository

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

    # get corresponding repositories with the base branch
    names = [repo.name for repo in head_repos]
    repos_for_merge = [repo for repo in client.get_repositories(base) if repo.ref and repo.name in names]

    if not repos_for_merge:
        raise Exception("No repositories were found matching the base: {}".format(base))

    logging.info('Found {} repositories matching base {}'.format(len(repos_for_merge), base))

    logging.info('Preparing to merge the following repositories')
    for repo in repos_for_merge:
        logging.info("{}: {} ==>> {}".format(repo.name, head, base))

    (succeeded, unprocessed, _) = merge_branches(base, head, repos_for_merge)

    logging.info('BASE MERGE COMPLETE')

    # succeeded and unprocessed branches are eligible to be merged into the current release branch
    eligible = []
    eligible.extend(succeeded)
    eligible.extend(unprocessed)

    if not curr_rel and not eligible:
        return

    logging.info('Beginning merge of base into release branches...')

    # only merge repos that are eligible and have the current release branch
    names = [repo.name for repo in eligible]
    repos_for_merge = [repo for repo in client.get_repositories(curr_rel) if repo.ref and repo.name in names]

    if not repos_for_merge:
        raise Exception("No eligible repositories matching the current release branch")

    merge_branches(curr_rel, base, repos_for_merge)


def merge_branches(base: str, head: str, repos: [Repository]):
    succeeded = []
    unprocessed = []
    failed = []
    for repo in repos:
        logging.info('Merging {}'.format(repo.name))
        try:
            merge_result = client.merge_branch(repo, base, head, 'Merge completed by AutoMerge utility')
            logging.info('Merge completed')
            succeeded.append((merge_result, repo))
        except GitHubError as err:
            if 'already merged' in err.message.lower():
                logging.warn('{}: Already Merged'.format(repo.name))
                unprocessed.append((err.message, repo))
            else:
                logging.exception('{}: Failed merge. {}'.format(repo.name, err.message))
                failed.append((err.message, repo))

    print('-----SUCCEEDED-----')
    for (result, repo) in succeeded:
        print("{}: {}".format(repo.name, result.commit_url)
    print('-------------------')

    print('----UNPROCESSED-----')
    for (message, repo) in failed:
        print('{}: {}'.format(repo.name, message)
    print('---------------')


    print('----FAILED-----')
    for (message, repo) in failed:
        print('{}: {}'.format(repo.name, message)
    print('---------------')

    succeeded = [repo for (_, repo) in succeeded]
    unprocessed = [repo for (_, repo) in unprocessed]
    failed = [repo for (_, repo) in failed]

    return (succeeded, unprocessed, failed)