class Node:
    """Represents a node in a URL path tree

    This class represents a single node in the URL path tree. Each node in the
    tree may have an associated endpoint, and may have any number of children
    nodes. An object is considered Node-like if it defines add() and get()
    functions that can be called using the same arguments given for those
    functions in this class. It should also define the endpoint attribute,
    but depending on usage, that may not be necessary.

    Attributes:
        endpoint: the resource class associated with the current path, or None
    """

    def __init__ (self, name="", parent=None):
        self.name = name
        self.parent = parent
        self.children = {}
        self.endpoint = None

    def add (self, name, child=None):
        """Add a subtree with the given name

        Args:
            name: the segment of the path corresponding to the new subtree
            child: some object (usually Node-like) representing the new subtree.
                If child is None, the function will create a new child.

        Returns:
            the newly added child object

        Raises:
            ValueError: name already identifies an existing subtree
        """
        if name in self.children:
            raise ValueError ("name already in use: \"{}\"".format(name))

        if child is None:
            child = Node (name, self)

        self.children[name] = child
        return child

    def get (self, name):
        """Fetch the subtree of the given name

        Args:
            name: The name of the subtree

        Returns:
            an object representing the subtree, or None, if name is not found
        """
        try:
            return self.children[name]
        except KeyError:
            return None
