def LazySplit (s, char):
    end = -1
    while end < len(s):
        start = end + 1
        end = s.find(char, start)

        if end < 0:
            end = len(s)

        yield start, end
