class Path:
    class Iterator:
        def __init__ (self, path):
            self.path = path
            self.start = 0
            self.end = None

        def __next__ (self):
            if self.start >= len(self.path):
                raise StopIteration()

            self.end = self.path.find("/", self.start)

            if self.end < 0:
                self.end = len(self.path)

            result = (self.start, self.end)
            self.start = self.end + 1
            return result

    def __init__ (self, path):
        self.path = path

    def __iter__ (self):
        return self.Iterator(self.path)
