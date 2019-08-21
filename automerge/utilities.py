import logging
from github.client import GitHubClient
from github.types import GitHubError, Repository

def auto_merge(base: str, head: str, curr_rel: str, client: GitHubClient):
    auto_merge_results = []

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

    (succeeded, unprocessed, failed) = merge_branches(base, head, repos_for_merge, client)
    auto_merge_results.append((succeeded, unprocessed, failed))

    logging.info('BASE MERGE COMPLETE')

    # succeeded and unprocessed branches are eligible to be merged into the current release branch
    eligible = []
    eligible.extend(succeeded)
    eligible.extend(unprocessed)

    if not curr_rel or not eligible:
        return auto_merge_results

    logging.info('Beginning merge of base into current release branches...')

    # only merge repos that are eligible and have the current release branch
    names = [repo.name for repo in eligible]
    repos_for_merge = [repo for repo in client.get_repositories(curr_rel) if repo.ref and repo.name in names]

    if not repos_for_merge:
        raise Exception("No eligible repositories matching the current release branch")

    auto_merge_results.append(merge_branches(curr_rel, base, repos_for_merge, client))

    logging.info('CURRENT RELEASE MERGE COMPLETE')

    return auto_merge_results

def merge_branches(base: str, head: str, repos: [Repository], client: GitHubClient):
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

    print('-' * 30)
    print('SUCCEEDED')
    print('-' * 30)
    for (result, repo) in succeeded:
        print("{}: {}".format(repo.name, result.commit_url))
    print('-' * 30)

    print('-' * 30)
    print('UNPROCESSED')
    print('-' * 30)
    for (message, repo) in unprocessed:
        print('{}: {}'.format(repo.name, message))
    print('-' * 30)


    print('-' * 30)
    print('FAILED')
    print('-' * 30)
    for (message, repo) in failed:
        print('{}: {}'.format(repo.name, message))
    print('-' * 30)

    succeeded = [repo for (_, repo) in succeeded]
    unprocessed = [repo for (_, repo) in unprocessed]
    failed = [repo for (_, repo) in failed]

    return (succeeded, unprocessed, failed)