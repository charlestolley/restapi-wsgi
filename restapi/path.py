class Path:
    class Iterator:
        def __init__ (self, path):
            self.path = path
            self.start = 1
            self.end = 0

        def __next__ (self):
            if self.end < 0:
                raise StopIteration()

            self.end = self.path.find("/", self.start)

            if self.end < 0:
                segment = self.path[self.start:]
            else:
                segment = self.path[self.start:self.end]
                self.start = self.end+1

            return segment

    def __init__ (self, path):
        self.path = path

    def __iter__ (self):
        return self.Iterator(self.path)

class Tree:
    def __init__ (self):
        self.root = {}

    def add (self, endpoint, path):
        node = self.root

        for segment in Path(path):
            prev = node
            node = node.setdefault(segment, {})

        prev[segment] = endpoint

    def find (self, path):
        node = self.root
        for segment in Path(path):
            if isinstance(node, dict):
                try:
                    node = node[segment]
                except KeyError:
                    return
            else:
                return

        if not isinstance(node, dict):
            return node
