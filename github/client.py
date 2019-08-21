import http.client
import json
import os
from http import HTTPStatus
from string import Template
from github.types import Repository, Ref, GitHubError, UpdateRefResponse, MergeResponse, GitHubPermissionError

class GitHubClient:

    __apiUrl = 'api.github.com'
    __userAgent = 'OT-AutoMergeUtility'
    __validMergePermissions = ['ADMIN','MAINTAIN', 'WRITE']

    def __init__(self, token: str = '', org: str = ''):
        self.api_token = token
        self.organization = org

    def get_repositories(self, branchName: str) -> [Repository]:

        def inner_get_repositories(branchName: str, cursor: str = '', limit: int = 100):
            query = self.__get_repositories_graphql_query(self.organization, branchName, cursor)
            response = self.__make_graphql_request(query)
            repositories = Repository.create(response)

            if len(repositories) >= limit:
                cursor = response["data"]["organization"]["repositories"]["edges"][-1]["cursor"]
                repositories.extend(inner_get_repositories(branchName, cursor, limit))

            return repositories

        return inner_get_repositories(branchName)

    def merge_branch(self, repository: Repository, base: str, head: str, commitMessage: str = '') -> MergeResponse:
        self.__validate_write_permissions(repository)
        query = self.__get_merge_branch_graphql_query(repository.id, base, head, commitMessage)
        response = self.__make_graphql_request(query)

        return MergeResponse.create(response)

    def update_ref(self, repository: Repository, commitHash: str, force: bool = False) -> UpdateRefResponse:
        self.__validate_write_permissions(repository)
        query = self.__get_update_ref_graphql_query(repository.ref.id, commitHash, force)
        response = self.__make_graphql_request(query)

        return UpdateRefResponse.create(response)

    def __validate_write_permissions(self, repository: Repository):
        if repository.permission not in self.__validMergePermissions:
            raise GitHubPermissionError("Invalid Permission for merge ({}). Valid permissions are: [{}]".format(repository.permission, ','.join(self.__validMergePermissions)))

    def __make_graphql_request(self, query: str) -> dict:
        try:
            conn = http.client.HTTPSConnection(GitHubClient.__apiUrl, 443)
            body = {
                'query': query.replace('\r\n', '').replace('\n', '')
            }
            headers = {
                'Authorization': "Token {}".format(self.api_token),
                'User-Agent': self.__userAgent
            }
            conn.request('POST', '/graphql', body=json.dumps(body), headers=headers)
            response = conn.getresponse()
            return self.__get_response_as_dict(response)
        finally:
            conn.close()

    def __get_response_as_dict(self, response) -> dict:
        if response.status != HTTPStatus.OK:
            raise Exception('Request attempt failed: {}'.format(response.reason))

        data = json.load(response)
        self.__validate_graphql_response(data)

        return data

    def __validate_graphql_response(self, response):
        if not response:
            raise Exception('Request returned no response... huh???')

        if 'errors' in response:
            raise GitHubError.create(response)

    def __get_update_ref_graphql_query(self, refId: str, hash: str, force: bool):
        force_str = str(force).lower()
        query = Template("""
            mutation {
                updateRef(input: {
                    force: $force,
                    oid: "$hash",
                    refId: "$refId"
                }) {
                    ref {
                        id
                        name
                        target {
                            oid
                            commitUrl
                        }
                    }
                }
            }
        """)
        query = query.substitute(refId=refId, hash=hash, force=force_str)
        return query

    def __get_merge_branch_graphql_query(self, repoId: str, baseName: str, headName: str, commitMessage: str):
        query = Template("""
            mutation {
                mergeBranch(input: {
                    base: "$baseName",
                    commitMessage: "$commitMessage",
                    head: "$headName",
                    repositoryId: "$repoId"
                }) {
                    mergeCommit {
                        id
                        oid
                        commitUrl
                        message
                    }
                }
            }
        """)
        query = query.substitute(repoId=repoId, baseName=baseName, headName=headName, commitMessage=commitMessage)
        return query


    def __get_repositories_graphql_query(self, org: str, branch: str, after: str) -> str:
        after = "\"{}\"".format(after) if after else 'null'
        query = Template("""
            query {
                organization(login: "$org") {
                    repositories(after: $after, first: 100) {
                        edges {
                            cursor
                            node {
                                id
                                name
                                viewerPermission
                                ref(qualifiedName: "refs/heads/$branch") {
                                    id
                                    name
                                    target {
                                        id
                                        oid
                                        commitUrl
                                        commitResourcePath
                                        ... on Commit {
                                            message
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """)
        query = query.substitute(org=org, branch=branch, after=after)
        return query