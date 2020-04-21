import ast, os, os.path, inspect
from importlib.util import find_spec
from enum import Enumeration

class NoTargetError(Exception): pass

def resolve(target,path=None):
    orig_cwd = os.getcwd() 
    try:
        if path is not None:
            os.chdir(path)

        outer_target_list = target.split('.')
        inner_target_list = []
        spec = None
        while len(outer_target_list) > 0:
            spec = find_spec('.'.join(outer_target_list))
            if spec is not None:
                break
            else:
                inner_target_list.insert(0,outer_target_list.pop(-1))
        if spec is None:
            raise NoTargetError('Target %s could not be found' % target)
    finally:
        if path is not None:
            os.chdir(orig_cwd)
    outer_target_list = outer_target_list
    inner_target_list = inner_target_list

    #self.spec is defined
    #self.outer_target_list is the portion of the target path composed of package and module names
    #self.inner_target_list is the portion of the target path composed of class and function names

    if self.spec.origin.lower().endswith('__init__.py'):
        #package
        return Package(target,spec)
    elif len(self.inner_target_list) == 0:
        #module
        return Module(target,spec)
    else:
        ast_node,ast_lineage = ast_get(spec.origin,inner_target_list)
        if ast_node is None:
            raise NoTargetError('Target %s could not be found' % target)
        
        if isinstance(ast_node,ast.FunctionDef):
            return Function(target,spec,ast_node,ast_lineage)
        elif isinstance(ast_node,ast.ClassDef):
            return Class(target,spec,ast_node,ast_lineage)
        elif isinstance(ast_node,ast.AsyncFunctionDef):
            return AsyncFunctionDef(target,spec,ast_node,ast_lineage)
        else:
            raise Exception('Unexpected ast node type: %s' % repr(ast_node))


def ast_code_get(origin,inner_target_list):
    """
    Gets an ast object representing the provided code context lineage in inner_target_list
    origin is the source code file
    """
    ast_module = ast_parse(origin)
    for ast_lineage,nodes in ast_walk(ast_module):
        code_ast_lineage = get_code_ast_lineage(ast_lineage)
        ast_lineage_len = len(code_ast_lineage)
        if inner_target_list[:ast_lineage_len] == code_ast_lineage:
            if len(inner_target_list) == ast_lineage_len:
                return ast_lineage[-1],ast_lineage[:-1]
        else:
            del nodes[:] #do not further traverse this path
    return None,None

def ast_code_tree(origin):
    code_tree = {}
    ast_module = ast_parse(origin)
    for ast_lineage,nodes in ast_walk(ast_module):
        code_ast_lineage = tuple(get_code_ast_lineage(ast_lineage))
        code_ast_lineages.add(code_ast_line
        ast_lineage_len = len(code_ast_lineage)
        if inner_target_list[:ast_lineage_len] == code_ast_lineage:
            if len(inner_target_list) == ast_lineage_len:
                return ast_lineage[-1],ast_lineage[:-1]
        else:
            del nodes[:] #do not further traverse this path
    return None,None

class SourceRunner():
    def __init__(self,target,spec,ast_node,ast_lineage):
        self.target = target
        self.spec = spec
        self.ast_node = ast_node
        self.ast_lineage = ast_lineage
class OuterRunner(SourceRunner):
    """
    SourceRunner object for a package or a module
    """
    def __init__(self,target,spec):
        target = target
        spec = spec
        ast_node = ast_parse(spec.origin)
        ast_lineage = []
        super().__init__(target,spec,ast_node,ast_lineage)
class InnerRunner(SourceRunner):
    """
    SourceRunner object for a function, class, or async function
    """
    def __init__(self,target,spec,ast_node,ast_lineage):
        target = target
        spec = spec
        ast_node = ast_node
        ast_lineage = ast_lineage
        super().__init__(target,spec,ast_node,ast_lineage)
class Package(OuterRunner):
    ...
class Module(SourceRunner):
    ...
class Class(InnerRunner):
    ...
class Function(InnerRunner):
    ...
class AsyncFUnction(InnerRunner):
    ...





