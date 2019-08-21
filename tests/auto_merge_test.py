import unittest
import types
from unittest.mock import Mock
from automerge.utilities import auto_merge
from github.client import GitHubClient
from github.types import Repository, Ref, MergeResponse, GitHubError

class AutoMergeTest(unittest.TestCase):

    def test_should_raise_exception_when_no_head_branch_is_found(self):
        client = GitHubClient('', '')
        client.get_repositories = Mock(return_value=[])

        with self.assertRaises(Exception):
            auto_merge('master', 'rel', '', client)

    def test_should_raise_exception_when_no_matching_base_branch_is_found(self):
        client = GitHubClient('', '')
        mock_repos = [
            [
                Repository('', 'RepoA', 'WRITE', 
                    Ref('', '', 'release', '')),
            ],
            [
            ]
        ]
        client.get_repositories = Mock(side_effect=mock_repos)

        with self.assertRaises(Exception):
            auto_merge('master', 'release', '', client)

    def test_should_only_merge_repos_with_matching_base_and_head(self):
        client = GitHubClient('', '')
        mock_repos = [
            [
                Repository('', 'RepoA', 'WRITE', 
                    Ref('', '', 'release', '')),
                Repository('', 'RepoB', 'WRITE', 
                    Ref('', '', 'release', '')),
                Repository('', 'RepoC', 'WRITE', 
                    Ref('', '', 'release', '')),
                Repository('', 'RepoD', 'WRITE', None)    		
            ],
            [
                Repository('', 'RepoA', 'WRITE', 
                    Ref('', '', 'master', '')),
                Repository('', 'RepoB', 'WRITE', 
                    Ref('', '', 'master', '')),
                Repository('', 'RepoC', 'WRITE', 
                    Ref('', '', 'master', '')),
                Repository('', 'RepoD', 'WRITE', 
                    Ref('', '', 'master', '')),
            ]
        ]
        mock_merge_response = MergeResponse('', 'https://github.com/org/repo/commits/#hash', 'merged')
        expected_merged_repos = 3

        client.get_repositories = Mock(side_effect=mock_repos)
        client.merge_branch = Mock(return_value=mock_merge_response)

        results = auto_merge('master', 'release', '', client)
        (succeeded, unprocessed, failed) = results[0]

        self.assertEqual(client.merge_branch.call_count, expected_merged_repos)
        self.assertEqual(len(succeeded), expected_merged_repos)
        self.assertEqual(len(unprocessed), 0)
        self.assertEqual(len(failed), 0)

    def test_should_not_fail_when_branches_are_already_merged(self):
        client = GitHubClient('', '')
        mock_repos = [
            [
                Repository('', 'RepoA', 'WRITE', 
                    Ref('', '', 'release', '')),
                Repository('', 'RepoB', 'WRITE', 
                    Ref('', '', 'release', '')),
            ],
            [
                Repository('', 'RepoA', 'WRITE', 
                    Ref('', '', 'master', '')),
                Repository('', 'RepoB', 'WRITE', 
                    Ref('', '', 'master', '')),
            ]
        ]

        count = 0
        def mock_merge_branch(repo, base, head, message):
            nonlocal count
            if count > 0:
                raise GitHubError('UNPROCESSABLE', 'Failed to merge: \"Already merged\"')

            count = count + 1
            return MergeResponse('', 'https://github.com/org/repo/commits/#hash', 'merged')

        expected_merged_repos = 2
        expected_succeeded_repos = 1
        expected_unprocessed_repos = 1

        client.get_repositories = Mock(side_effect=mock_repos)
        client.merge_branch = Mock(side_effect=mock_merge_branch)

        results = auto_merge('master', 'release', '', client)
        (succeeded, unprocessed, failed) = results[0]

        self.assertEqual(client.merge_branch.call_count, expected_merged_repos)
        self.assertEqual(len(succeeded), expected_succeeded_repos)
        self.assertEqual(len(unprocessed), expected_unprocessed_repos)
        self.assertEqual(len(failed), 0)
        
    def test_should_fail_repos_with_invalid_permissions(self):
        client = GitHubClient('', '')
        mock_repos = [
            [
                Repository('', 'RepoB', 'READ', 
                    Ref('', '', 'release', ''))
            ],
            [
                Repository('', 'RepoB', 'READ', 
                    Ref('', '', 'master', ''))
            ]
        ]
        expected_failed_repos = 1

        client.get_repositories = Mock(side_effect=mock_repos)

        results = auto_merge('master', 'release', '', client)
        (succeeded, unprocessed, failed) = results[0]

        self.assertEqual(len(succeeded), 0)
        self.assertEqual(len(unprocessed), 0)
        self.assertEqual(len(failed), expected_failed_repos)

    def test_should_merge_eligible_repos_base_branch_with_release_branch(self):
        client = GitHubClient('', '')
        mock_repos = [
            [
                Repository('', 'RepoA', 'WRITE', 
                    Ref('', '', 'release', '')),
                Repository('', 'RepoB', 'WRITE', 
                    Ref('', '', 'release', '')),
                Repository('', 'RepoC', 'READ', 
                    Ref('', '', 'release', '')),
                Repository('', 'RepoD', 'WRITE', None)
            ],
            [
                Repository('', 'RepoA', 'WRITE', 
                    Ref('', '', 'master', '')),
                Repository('', 'RepoB', 'WRITE', 
                    Ref('', '', 'master', '')),
                Repository('', 'RepoC', 'READ', 
                    Ref('', '', 'master', '')),
                Repository('', 'RepoD', 'WRITE', 
                    Ref('', '', 'master', '')),
            ],
            [
                Repository('', 'RepoA', 'WRITE', 
                    Ref('', '', 'current_release', '')),
                Repository('', 'RepoB', 'WRITE', 
                    Ref('', '', 'current_release', ''))
            ]
        ]
        def mock_merge_branch(repo, base, head, message):
            if repo.permission != 'WRITE':
                raise GitHubError('UNPROCESSABLE', 'Failed to merge: \"Already merged\"')

            return MergeResponse('', 'https://github.com/org/repo/commits/#hash', 'merged')

        expected_succeeded_repos = 2
        expected_unprocessed_repos = 1

        expected_curr_release_succeeded_repos = 2

        client.get_repositories = Mock(side_effect=mock_repos)
        client.merge_branch = Mock(side_effect=mock_merge_branch)

        results = auto_merge('master', 'release', 'current_release', client)

        # assert the first merge from head to base
        (succeeded, unprocessed, failed) = results[0]

        self.assertEqual(len(succeeded), expected_succeeded_repos)
        self.assertEqual(len(unprocessed), expected_unprocessed_repos)
        self.assertEqual(len(failed), 0)

        # assert the second merge from base to current release
        (succeeded, unprocessed, failed) = results[1]

        self.assertEqual(len(succeeded), expected_curr_release_succeeded_repos)
        self.assertEqual(len(unprocessed), 0)
        self.assertEqual(len(failed), 0)        


if __name__ == '__main__':
    unittest.main()