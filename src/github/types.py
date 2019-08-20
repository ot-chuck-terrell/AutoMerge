
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
    def create(cls, data: dict):
        return Repository('', '', '', None)
