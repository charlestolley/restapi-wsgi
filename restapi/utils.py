def LazySplit (s, delim):
    """A generator to split a string into substrings

    Args:
        s: some string
        delim: the delimiter to use to split s

    Yields:
        a tuple (start, end), where start is the index of the first character
        of the substring, and end is the index after the last character.

    Examples:
        >>> print([i for i in LazySplit("/path/to/file", "/")])
        [(0, 0), (1, 5), (6, 8), (9, 13)]
    """
    end = -1
    while end < len(s):
        start = end + 1
        end = s.find(delim, start)

        if end < 0:
            end = len(s)

        yield start, end
