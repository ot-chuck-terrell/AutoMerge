# AutoMerge

## Requirements

The requirements for this script are:
- Python 3 (3.7.4). Earlier Python 3 versions _may_ work, but are not recommended.
- A GitHub API access token that has permissions to read/write repositories within the OneTech organization.

You can download and install the newest version of Python, [here](https://www.python.org/downloads/).

## Usage

The script looks for a `config.ini` file in the current directory by default, but can be overriden by passing the parameters manually, or by provding an alternate location for the config file. The configuration file is just basic INI format. See the `config.ini.sample` file in this repository for an example. Additional usage information can be discovered using the `-h` flag when calling the script.

```
C:\projects\AutoMerge> python.exe .\AutoMerge.py -h
usage: AutoMerge [-h] [--current_rel_branch CURRENT_REL_BRANCH]
                 [--token TOKEN] [--org ORG] [--config_path CONFIG_PATH]
                 base_branch head_branch

Script for auto-merging branches across repositories within an organization

positional arguments:
  base_branch           Base branch for the merge (i.e. master)
  head_branch           Branch to be merged into the base (i.e. REL-2910)

optional arguments:
  -h, --help            show this help message and exit
  --current_rel_branch CURRENT_REL_BRANCH
                        If specified, will attempt to merge the base branch
                        into the current release branch. This can be useful
                        for OCRs
  --token TOKEN         GitHub API access token to be used. Overrides the
                        default specified by config
  --org ORG             GitHub organization to perform the auto merge against.
                        Overrides the default specified by config
  --config_path CONFIG_PATH
                        Optionally tell the script where to find the config
                        file. By default it searches in the base directory
```

## Scenarios

1. I want to merge `REL-0001` with the `master` branch.

```
python AutoMerge master REL-0001
```

2. I want to merge `REL-0001` with the `master` branch, and then merge master into a new release branch, `REL-0002`.

```
python AutoMerge master REL-0001 --current_rel_branch=REL-0002
```

## Troubleshooting

1. If you are getting an error when you execute the script with `python AutoMerge.py`, be sure to check the version of Python with `python --version`. Make sure that it is version 3 (3.7.4) or higher.

2. If you aren't certain where python3 is on your system, you might want to try `python3`, or directly reference from the executable location.

## Example Output

Below is an example of merging the test release branch `AutoMergeFakeREL-0000` into `AutoMergeFakeMaster`, and then merging eligible branches into the fictious current release branch, `AutoMergeFakeREL-0001`.

```
C:\projects\AutoMerge> python.exe .\AutoMerge.py AutoMergeFakeMaster AutoMergeFakeREL-0000 --current_rel_branch=AutoMergeFakeREL-0001
INFO: Found 3 repositories matching head AutoMergeFakeREL-0000
INFO: Found 3 repositories matching base AutoMergeFakeMaster
INFO: Preparing to merge the following repositories
INFO: ProductFulfillment: AutoMergeFakeREL-0000 ==>> AutoMergeFakeMaster
INFO: EnterpriseServices: AutoMergeFakeREL-0000 ==>> AutoMergeFakeMaster
INFO: WebClients: AutoMergeFakeREL-0000 ==>> AutoMergeFakeMaster
INFO: Merging ProductFulfillment
INFO: Merge completed
INFO: Merging EnterpriseServices
INFO: Merge completed
INFO: Merging WebClients
INFO: Merge completed
------------------------------
SUCCEEDED
------------------------------
ProductFulfillment: https://github.com/OneTechLP/ProductFulfillment/commit/2c135cfe664e9a96afef543736fd14e67a3196e4
EnterpriseServices: https://github.com/OneTechLP/EnterpriseServices/commit/5d8a4b10ca406b6752b690ea13b77b82708f1a54
WebClients: https://github.com/OneTechLP/WebClients/commit/e6e9ced71552dd1a1b40bd7d8a91174ac64db9be
------------------------------
------------------------------
UNPROCESSED
------------------------------
------------------------------
------------------------------
FAILED
------------------------------
------------------------------
INFO: BASE MERGE COMPLETE
INFO: Beginning merge of base into release branches...
INFO: Merging ProductFulfillment
INFO: Merge completed
------------------------------
SUCCEEDED
------------------------------
ProductFulfillment: https://github.com/OneTechLP/ProductFulfillment/commit/2386085b846032e3b074d77d6dd3bf3880d0b339
------------------------------
------------------------------
UNPROCESSED
------------------------------
------------------------------
------------------------------
FAILED
------------------------------
------------------------------
```

## Nitty Gritty

This script works by sending requests to the GitHub GraphQL API. This allows the script to minimize the number of calls made to GitHub by leveraging the additional data that can be pulled via the API.

What is GraphQL? https://graphql.org/

GitHub GraphQL Spec: https://developer.github.com/v4/

GitHub GraphQL Schema: https://developer.github.com/v4/public_schema/

The schema can be imported into Postman: https://learning.getpostman.com/docs/postman/sending_api_requests/graphql/#importing-graphql-schemas

A Postman export for the API calls used by this script can be found in the repository. Import it, and be sure to **update** the access token with your own.