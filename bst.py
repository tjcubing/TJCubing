# Balanced binary search tree (AVL tree) implementation

class Node:

    def __init__(self, key, value=None, parent=None, left=None, right=None):
        self.key, self.value, self.parent = key, value, parent
        self.child = [left, right]
        self.balance, self.height = 0, 1

    def __str__(self) -> str:
        return f"{self.key}:{self.value}:{self.balance}" if self.value is not None else str(self.key)

    def extrema(self, i: int):
        n = self
        while n.child[i] is not None:
            n = n.child[i]
        return n

    def min(self): return self.extrema(0)

    def max(self): return self.extrema(1)

class BST:

    def __init__(self):
        self.root = None

    def __str__(self, n=None, s="", d=0) -> str:
        if d == 0: n = self.root
        if n is None: return s
        s = self.__str__(n.child[0], s, d + 1)
        s += " "*4*d + str(n) + "\n"
        s = self.__str__(n.child[1], s, d + 1)
        return s

    def min(self): return self.root.min()

    def max(self): return self.root.max()

    def __add(self, key, value, n):
        if n.child[key > n.key] is None:
            n.child[key > n.key] = Node(key, value, n)
            return
        self.__add(key, value, n.child[key > n.key])

    def add(self, key, value=None):
        if self.root is None:
            self.root = Node(key, value)
            return
        self.__add(key, value, self.root)

        n = self.find(key, value)
        self.trace_heights(n)
        self.trace(n)

    def __find(self, key, value, n):
        if key == n.key and value == n.value:
            return n

        if n.child[key > n.key] is None:
            return None

        return self.__find(key, value, n.child[key > n.key])

    def find(self, key, value=None):
        return self.__find(key, value, self.root)

    def contains(self, key, value=None) -> bool:
        return self.find(key, value) is not None

    def delete(self, key, value=None):
        n = self.find(key, value)
        # leaf node
        if n.child[0] is None and n.child[1] is None:
            # root node
            if n.parent is None:
                self.root = None
                return
            self.set_children(n.parent, n.key, None)
            to_trace = n.parent
        elif n.child[0] is None:
            if n.parent is None:
                self.root = n.child[1]
                self.root.parent = None
                return
            self.set_children(n.parent, n.key, n.child[1])
            to_trace = n.child[1]
        elif n.child[1] is None:
            if n.parent is None:
                self.root = n.child[0]
                self.root.parent = None
                return
            self.set_children(n.parent, n.key, n.child[0])
            to_trace = n.child[0]
        # two children
        else:
            temp = n.child[0].max()
            n.key, n.value = temp.key, temp.value
            self.set_children(temp.parent, temp.key, temp.child[0])
            if temp.child[0] is not None:
                self.trace_heights(temp.child[0])
            self.trace_heights(temp)
            return

        self.trace_heights(to_trace)
        self.trace(to_trace)

    def update(self, key, value, new):
        self.delete(key, value)
        self.add(new, value)

    def pop(self):
        n = self.min()
        self.delete(n.key, n.value)
        return n.key, n.value

    def set_children(self, n, key, value):
        n.child[key > n.key] = value
        if value is not None:
            value.parent = n

    def trace_heights(self, n):
        while n is not None:
            self.update_height(n)
            n = n.parent

    def update_height(self, n):
        left = n.child[0].height if n.child[0] is not None else 0
        right = n.child[1].height if n.child[1] is not None else 0
        n.height = max(left, right) + 1
        n.balance = right - left

    def trace(self, n):
        while n.parent is not None:
            p = n.parent
            # right child
            if n.key > p.key:
                if p.balance == 2:
                    (self.rotate_right_left if n.balance < 0 else self.rotate_left)(p, n)
            else:
                if p.balance == -2:
                    (self.rotate_left_right if n.balance > 0 else self.rotate_right)(p, n)
            n = p

    def rotate(self, p, n, d):
        c = n.child[d]
        p.child[d ^ 1] = c

        if c is not None:
            c.parent = p
        n.child[d] = p

        n.parent = p.parent
        if p.parent is not None:
            p.parent.child[p.key > p.parent.key] = n
        else:
            self.root = n
        p.parent = n

        # order matters: update from the bottom up
        self.update_height(p)
        self.update_height(n)

        return n

    def rotate_left(self, p, n):
        return self.rotate(p, n, 0)

    def rotate_right(self, p, n):
        return self.rotate(p, n, 1)

    def rotate_left_right(self, p, n):
        return self.rotate_right(p, self.rotate_left(n, n.child[1]))

    def rotate_right_left(self, p, n):
        return self.rotate_left(p, self.rotate_right(n, n.child[0]))

