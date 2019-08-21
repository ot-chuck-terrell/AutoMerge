import unittest
import configparser
from github.client import GitHubClient
from github.types import Repository, Ref, GitHubError, UpdateRefResponse, MergeResponse

base_branch = 'AutoMergeFakeMaster'
rel_branch = 'AutoMergeFakeREL-0000'
current_rel_branch = 'AutoMergeFakeREL-0001'

class TestGitHubClient(unittest.TestCase):

    def setUp(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        access_token = config['DEFAULT']['access_token']
        organization = config['DEFAULT']['organization']
        self.client = GitHubClient(access_token, organization)

    def test_can_fetch_repositories_with_branch(self):
        repos = self.client.get_repositories(rel_branch)
        repos_with_branch = [repo for repo in repos if repo.ref]
        self.assertTrue(len(repos_with_branch) >= 1)

    def test_can_merge_branch_with_base(self):
        test_repo = 'ProductFulfillment'
        repos = self.client.get_repositories(rel_branch)
        pf_rel_repo = [repo for repo in repos if repo.ref and repo.name == test_repo][0]
        master_repos = self.client.get_repositories(base_branch)
        pf_master_repo = [repo for repo in master_repos if repo.ref and repo.name == test_repo][0]
        
        expected_message = 'Merge completed by AutoMerge Integration Test'
        result = self.client.merge_branch(pf_rel_repo, base_branch, rel_branch, expected_message)

        self.assertEqual(result.commit_message, expected_message)

        # cleanup merge commit so the test can be run again
        self.client.update_ref(pf_master_repo, pf_master_repo.ref.oid, True)


if __name__ == '__main__':
    unittest.main()
