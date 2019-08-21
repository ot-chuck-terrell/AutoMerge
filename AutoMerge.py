#!/usr/bin/python3

import configparser
import argparse
import logging
from github.client import GitHubClient
from automerge.utilities import auto_merge

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

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

auto_merge(base_branch, head_branch, current_rel_branch, GitHubClient(access_token, organization))
