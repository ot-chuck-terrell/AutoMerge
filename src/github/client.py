import http.client
import json
import os
from http import HTTPStatus
from string import Template
from .types import Repository, Ref

class GitHubClient:

    __apiUrl = 'api.github.com'

    def __init__(self, token: str = '', org: str = '', config_path: str = ''):
        self.api_token = token
        self.organization = org

    def get_repositories(self, branchName: str) -> [Repository]:
        query = self.__get_repositories_graphql_query.substitute(org=self.organization, branch=branchName)
        response = __make_graphql_request(query)
        
        return Repository.create(response)


    def create_branch(self, baseName: str, branchName: str):
        pass

    def merge_branch(self):
        pass

    def __make_graphql_request(self, query: str) -> dict:
        try:
            conn = http.client.HTTPSConnection(GitHubClient.__apiUrl, 443)
            body = {
                'query': query.replace(os.linesep, '')
            }
            headers = {
                'Authorization': self.api_token,
                'User-Agent': 'OT-AutoMerge'
            }
            conn.request('POST', '/graphql', body=json.dumps(body), headers=headers)
            response = conn.getresponse()
            return self.__get_response_as_dict(response)
        finally:
            conn.close()

    def __get_response_as_dict(self, response) -> dict:
        if response.status != HTTPStatus.Ok:
            raise Exception('Request attempt failed: {}'.format(response.reason))

        data = json.load(response)
        self.__validate_graphql_response(data))

        return data

    def __validate_graphql_response(self, response):
        pass

    __get_repositories_graphql_query = Template("""
    query {
        organization(login: "$org") {
            repositories(first: 100) {
                edges {
                    node {
                        id
                        name
                        viewerPermission
                        ref(qualifiedName: "/refs/head/$branch") {
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