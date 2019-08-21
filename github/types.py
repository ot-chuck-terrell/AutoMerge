
class Ref:

    def __init__(self, id: str, name: str, oid: str, message: str):
        self.id = id
        self.name = name
        self.oid = oid
        self.message = message

class Repository:

    def __init__(self, id: str, name: str, permission: str, ref: Ref):
        self.id = id
        self.name = name
        self.ref = ref
        self.permission = permission

    @staticmethod
    def create(data: dict):
        repos = []
        for edge in data["data"]["organization"]["repositories"]["edges"]:
            repoDict = edge["node"]
            refDict = edge["node"]["ref"]
            repo = Repository(
                repoDict["id"], 
                repoDict["name"], 
                repoDict["viewerPermission"],
                None)
            if refDict:
                targetDict = refDict["target"]
                ref = Ref(
                    refDict["id"],
                    refDict["name"],
                    targetDict["oid"],
                    targetDict["message"])
                repo.ref = ref
            repos.append(repo)
            
        return repos

class MergeResponse:

    def __init__(self, hash: str, url: str, message: str):
        self.commit_hash = hash
        self.commit_url = url
        self.commit_message = message

    @staticmethod
    def create(data: dict):
        info = data['data']['mergeBranch']["mergeCommit"]
        return MergeResponse(info["oid"], info["commitUrl"], info["message"])

class UpdateRefResponse:

    def __init__(self, hash: str, url: str):
        self.commit_hash = hash
        self.commit_url = url

    @staticmethod
    def create(data: dict):
        info = data['data']['updateRef']['ref']['target']
        return UpdateRefResponse(info['oid'], info['commitUrl'])

class GitHubError(Exception):

    def __init__(self, error_type: str, message: str):
        self.error_type = error_type
        self.message = message

    @staticmethod
    def create(data: dict):
        firstError = data['errors'][0]
        err_type = ''
        if 'type' in firstError:
            err_type = firstError['type']
        return GitHubError(err_type, firstError['message'])

class GitHubPermissionError(GitHubError):
    
    def __init__(self, message):
        super().__init__('PERMISSION', message)
