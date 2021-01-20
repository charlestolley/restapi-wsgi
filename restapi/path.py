class Tree:
    def __init__ (self):
        self.root = {}

    def add (self, endpoint, path):
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        node = self.root

        start = 1
        while True:
            end = path.find("/", start)
            if end < 0:
                node[path[start:]] = endpoint
                break
            else:
                node = node.setdefault(path[start:end], {})
                start = end + 1

    def find (self, path):
        node = self.root
        for segment in path.split("/")[1:]:
            if isinstance(node, dict):
                try:
                    node = node[segment]
                except KeyError:
                    return
            else:
                return

        if not isinstance(node, dict):
            return node
