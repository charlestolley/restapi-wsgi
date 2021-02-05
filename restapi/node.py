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

    def __init__ (self):
        self.children = {}
        self.endpoint = None
        self.varname = None
        self.variable = None

    def add (self, name, child=None):
        """Add a subtree with the given name

        Args:
            name: the segment of the path corresponding to the new subtree
            child: some object (usually Node-like) representing the new subtree.
                If child is None, the function will create a new child.

        Returns:
            the newly added child object

        Raises:
            RuntimeError: indicates incorrect use of this function
            ValueError: name already identifies an existing subtree
        """
        if name.startswith("<") and name.endswith(">"):
            if self.variable is None:
                self.varname = name[1:-1]
                self.variable = child if child is not None else Node()
                return self.variable
            else:
                raise RuntimeError("Attempted to add path variable twice")
        elif name in self.children:
            raise ValueError("name already in use: \"{}\"".format(name))

        if child is None:
            child = Node()

        self.children[name] = child
        return child

    def get (self, name):
        """Fetch the subtree of the given name

        Args:
            name: The name of the subtree

        Returns:
            an object representing the subtree, or None, if name is not found

        Raises:
            ValueError: If you use angle-bracket-enclosed path variables, you
                must always use the same name for the variable of a particular
                Node. This error indicates that a path was added that violated
                this rule.
        """
        if name.startswith("<") and name.endswith(">"):
            name = name[1:-1]
            if self.varname is not None and name != self.varname:
                msg = "Path variable names do not match: \"{}\", \"{}\""
                raise ValueError(msg.format(self.varname, name))

            return self.variable

        try:
            return self.children[name]
        except KeyError:
            if self.variable is not None:
                return Variable(self.varname, name, self.variable)

class Variable:
    """Wrapper for a Node object reached by traversing a path variable

    Usage of this object is identical to that of Node. They are distinguished
    by the presence of the "value" attribute.

    Attributes:
        name: the angle-bracket-enclosed variable name given to define the path
            that led to this variable (angle brackets have been removed)
        value: the value of this variable, extracted from the requested URL
        node: the wrapped Node
    """

    def __init__ (self, name, value, node):
        self.name = name
        self.value = value
        self.node = node

    def add (self, *args, **kwargs):
        return self.node.add(*args, **kwargs)

    def get (self, *args, **kwargs):
        return self.node.get(*args, **kwargs)

    @property
    def endpoint (self):
        return self.node.endpoint
