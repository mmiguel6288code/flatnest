import ast, os.path, os.path
from importlib.util import find_spec
from enum import Enum

class CodeType(Enum):
    PACKAGE=1
    MODULE=2
    CLASS=3
    FUNCTION=4
    ASYNCFUNCTION=5
ast_map = {ast.ClassDef:CodeType.CLASS,ast.FunctionDef:CodeType.FUNCTION,ast.AsyncFunctionDef:CodeType.ASYNCFUNCTION}

def ast_code_filter(ast_node):
    """
    Returns True if the given ast node represents a code context
    """
    return isinstance(ast_node,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef))

def ast_flatten(ast_lineage,result=None):
    if result is None:
        result = []
    if not isinstance(ast_lineage,list):
        ast_lineage = [ast_lineage]
    result.append(ast_lineage)
    for child_node in ast.iter_child_nodes(ast_lineage[-1]):
        ast_flatten(ast_lineage+[child_node],result)
    return result

def code_tree(importable_name):
    spec = find_spec(importable_name)
    if os.path.basename(spec.origin).lower() == '__init__.py':
        return PackageTree(spec.origin)
    else:
        return ModuleTree(spec.origin)
class CodeTree():
    def lineage(self):
        result = [self]
        parent = self.parent
        while parent is not None:
            result.append(parent)
            parent = parent.parent
        return result[::-1]

class PackageTree(CodeTree):
    def __init__(self,origin,parent=None):
        self.origin = origin
        self.parent = parent
        self.module_tree = ModuleTree(origin,parent=self)
        self.subtree = {}
        self.code_type = CodeType.MODULE
        dirname = os.path.dirname(origin)
        self.name = os.path.basename(dirname)
        for item in sorted(os.listdir(dirname)):
            item_path = os.path.join(dirname,item)
            if os.path.isdir(item_path):
                if os.path.exists(os.path.join(item_path,'__init__.py')):
                    self.subtree[item] = PackageTree(item_path,parent=self)
            elif os.path.splitext(item.lower())[1] in ['.py','.pyw']:
                if item != '__init__.py':
                    mt = ModuleTree(item_path,parent=self)
                    self.subtree[mt.name] = mt
    def code_type(self):
        return 'package'


    def walk(self):
        yield self.module_tree
        yield from self.module_tree.walk()
        for child in self.subtree.values():
            yield child
            yield from child.walk()
    def __repr__(self):
        return 'PackageTree(%s)' % (self.name)
    def __str__(self):
        return repr(self)

class ModuleTree(CodeTree):
    def __init__(self,origin,parent=None):
        self.origin = origin
        with open(origin,'r') as f:
            self.origin_content = f.read()
        self.ast_node = ast.parse(self.origin_content,origin,'exec')
        self.name = os.path.splitext(os.path.basename(origin))[0]
        self.ast_lineage = []
        self.code_tree = self
        self.code_type = CodeType.MODULE
        self.subtree = {}
        self.parent = parent
        self.flat_ast = ast_flatten(self.ast_node)
        for index,ast_lineage in enumerate(self.flat_ast):
            if ast_code_filter(ast_lineage[-1]):
                self._insert(ast_lineage[-1],ast_lineage[:-1],index)

    def walk(self):
        for child in self.subtree.values():
            yield child
            yield from child.walk()
        
    def _insert(self,ast_node,ast_lineage,index):
        name = ast_node.name
        code_lineage = [ancestor_ast_node.name for ancestor_ast_node in ast_lineage if ast_code_filter(ancestor_ast_node)]
        target = self
        for ancestor_code_node_name in code_lineage:
            if ancestor_code_node_name in target.subtree:
                target = target.subtree[ancestor_code_node_name]
            else:
                target.subtree[ancestor_code_node_name] = CodeNode(
                        code_tree=self,name=ancestor_code_node_name,parent=target,ast_node=...,ast_lineage=...,
                        index=index,
                        )
                target = target.subtree[ancestor_code_node_name]
        if name in target.subtree:
            target = target.subtree[name]
            if target.ast_node is ... and target.ast_lineage is ...:
                target.ast_node = ast_node
                target.ast_lineage = ast_lineage
            else:
                raise Exception('Error constructing tree for %s' % '.'.join(code_lineage+[name]))
        else:
            target = CodeNode(code_tree=self,name=name,parent=target,ast_node=ast_node,ast_lineage=ast_lineage,index=index)
            target.parent.subtree[name] = target
    def __repr__(self):
        return 'ModuleTree(%s)' % (self.name)
    def __str__(self):
        return repr(self)

class CodeNode(CodeTree):
    def __init__(self,code_tree,name,parent,ast_node,ast_lineage,index):
        self.code_tree = code_tree
        self.name = name
        self.parent = parent 
        self.ast_node = ast_node
        self.ast_lineage = ast_lineage
        self.index = index
        self.code_type = ast_map[type(ast_node)]
        self.subtree = {}
    def walk(self):
        for child in self.subtree.values():
            yield child
            yield from child.walk()
    def __repr__(self):
        return 'CodeNode(%s,%s)' % (self.name,self.code_type)
    def __str__(self):
        return repr(self)
    def prev_node(self):
        if self.index > 0:
            return self.code_tree.flat_ast[self.index-1]
        else:
            return None
    def next_node(self):
        if self.index < len(self.code_tree.flat_ast)-1:
            return self.code_tree.flat_ast[self.index+1]
        else:
            return None

if __name__ == '__main__':
    import os
    os.environ['PYTHONINSPECT'] = '1'
    os.chdir('/home/mtm/projects/ptkcmd/src')
    ct = code_tree('ptkcmd')
    for c in ct.walk():
        print('.'.join(item.name for item in c.lineage()) + ' (' + str(c.code_type) + ')')
