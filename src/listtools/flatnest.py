"""
This module converts to/from a nested structure (e.g. list of lists of lists of ... of values) and a (nest pattern, flat list) tuple

The nest pattern is a string consisting solely of square brackets and digits.
A number represents the number of consecutive values at the current level of the nested structure.
An opening square bracket represents entering a deeper level of nesting.
A closing square bracket represents leaving a deper level of nesting.
The square brackets at the top level (would be first and last characters of every pattern) are omitted.
"""

import re
from collections import deque
from enum import Enum
class NestDirective(Enum):
    DFS_PUSH=1
    DFS_POP=2
    BFS_QUEUE=3
    BFS_SERVE=4
directive_token_map = {
        NestDirective.DFS_PUSH: '[',
        NestDirective.DFS_POP: ']',
        NestDirective.BFS_QUEUE: '*',
        NestDirective.BFS_SERVE: '|',
        }
#invert the directive_token_map dict
token_directive_map = {token:directive for directive,token in directive_token_map.items()}

def dfs(nested_structure,include_nest_directives=False):
    """
    Implements a depth-first-search traversal of a nested list structure

    >>> list(dfs([1,[2,3,[4,5,[6,7],8,9],10,11],12]))
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    """
    stack = deque([[nested_structure,0]])
    while len(stack) > 0:
        tree,pos = stack[-1]
        while pos < len(tree):
            item = tree[pos]
            pos += 1
            if isinstance(item,(list,tuple)):
                if include_nest_directives:
                    yield NestDirective.DFS_PUSH
                stack[-1][1] = pos
                stack.append([item,0])
                break
            else:
                yield item
        if pos == len(tree):
            if len(stack) > 1 and include_nest_directives:
                yield NestDirective.DFS_POP
            stack.pop()
def bfs(nested_structure,include_nest_directives=False):
    """
    Implements a breadth-first-search traversal of a nested list structure
    
    >>> list(bfs([1,[2,3,[4,5,[6,7],8,9],10,11],12]))
    [1, 12, 2, 3, 10, 11, 4, 5, 8, 9, 6, 7]
    """
    queue = deque([nested_structure])
    while len(queue) > 0:
        tree = queue.popleft()
        for item in tree:
            if isinstance(item,(list,tuple)):
                if include_nest_directives:
                    yield NestDirective.BFS_QUEUE
                queue.append(item)
            else:
                yield item
        if len(queue) > 0 and include_nest_directives:
            yield NestDirective.BFS_SERVE


def flatten(nested_structure,algorithm=dfs):
    """
    Traverses the nested structure according to the algorithm.
    Produces a structure pattern string and a flat list

    The structure pattern can be combined with the flat list to reconstruct the additional structure using the deflatten function
    The flat list corresponds to the order of traversal in the provided algorithm parameter

    
    >>> flatten([1,[2,3,[4,5,[6,7],8,9],10,11],12])
    ('1[2[2[2]2]2]1', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

    >>> flatten([1,[2,3,[4,5,[6,7],8,9],10,11],12],bfs)
    ('1*1|2*2|2*2|2', [1, 12, 2, 3, 10, 11, 4, 5, 8, 9, 6, 7])

    """
    if algorithm not in [dfs,bfs]:
        raise Exception('algorithm must be either the function dfs or the function bfs')
    pattern_list = []
    flat_list = []
    consecutive_item_count = 0
    for item in algorithm(nested_structure,include_nest_directives=True):
        if isinstance(item,NestDirective):
            if consecutive_item_count > 0:
                pattern_list.append(str(consecutive_item_count))
            consecutive_item_count = 0
            pattern_list.append(directive_token_map[item])
        else:
            consecutive_item_count += 1
            flat_list.append(item)
    if consecutive_item_count > 0:
        pattern_list.append(str(consecutive_item_count))
    structure_pattern = ''.join(pattern_list)
    return (structure_pattern,flat_list)

def parse_pattern(structure_pattern):
    """
    Splits the structure pattern into integers and nest directive enum values
    """
    return [(token_directive_map[token] if token in token_directive_map else int(token)) for token in re.split('(['+re.escape(''.join(directive_token_map.values()))+'])',structure_pattern)]

def deflatten(structure_pattern,flat_list):
    """
    Given a structure pattern and a flat list, construct a nested list structure

    >>> deflatten('1[2[2[2]2]2]1', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    [1, [2, 3, [4, 5, [6, 7], 8, 9], 10, 11], 12]

    >>> deflatten('1*1|2*2|2*2|2', [1, 12, 2, 3, 10, 11, 4, 5, 8, 9, 6, 7])
    [1, [2, 3, [4, 5, [6, 7], 8, 9], 10, 11], 12]

    """

    structure_directives = parse_pattern(structure_pattern)

    stackqueue = deque()
    nested_structure = []
    top_nested_structure = nested_structure
    flat_position = 0
    alg = None
    for directive in structure_directives:
        if directive is NestDirective.DFS_PUSH:
            if alg is bfs:
                raise Exception('Structure pattern contains both dfs and bfs tokens')
            alg = dfs
            stackqueue.append(nested_structure)
            nested_structure = []
            stackqueue[-1].append(nested_structure)
        elif directive is NestDirective.DFS_POP: 
            if alg is bfs:
                raise Exception('Structure pattern contains both dfs and bfs tokens')
            alg = dfs
            nested_structure = stackqueue.pop()
        elif directive is NestDirective.BFS_QUEUE: 
            if alg is dfs:
                raise Exception('Structure pattern contains both dfs and bfs tokens')
            alg = bfs
            subtree = []
            stackqueue.append(subtree)
            nested_structure.append(subtree)
        elif directive is NestDirective.BFS_SERVE: 
            if alg is dfs:
                raise Exception('Structure pattern contains both dfs and bfs tokens')
            alg = bfs
            nested_structure = stackqueue.popleft()
        else:
            #is a number -> consume that many items
            if flat_position + directive <= len(flat_list):
                nested_structure.extend(flat_list[flat_position:flat_position+directive])
                flat_position += directive
            else:
                raise Exception('structure_pattern implies more values than flat_list contains')
    if flat_position < len(flat_list):
        raise Exception('flat_list has more data than structure_pattern implies')
    if len(stackqueue) != 0:
        raise Exception('Structure pattern contains either imbalanced directive tokens')
    return top_nested_structure

def get_nest_indices(structure_pattern,flat_index):
    """
    Given a structure pattern and an index into the flat list, return the corresponding sequence of indices identifying the position in the nested structure.

    A negative flat index works from the end of the flat list

    >>> get_nest_indices('1[2[2[2]2]2]1',0)
    [0]
    >>> get_nest_indices('1[2[2[2]2]2]1',1)
    [1, 0]
    >>> get_nest_indices('1[2[2[2]2]2]1',2)
    [1, 1]
    >>> get_nest_indices('1[2[2[2]2]2]1',3)
    [1, 2, 0]
    >>> get_nest_indices('1[2[2[2]2]2]1',4)
    [1, 2, 1]
    >>> get_nest_indices('1[2[2[2]2]2]1',5)
    [1, 2, 2, 0]
    >>> get_nest_indices('1[2[2[2]2]2]1',6)
    [1, 2, 2, 1]
    >>> get_nest_indices('1[2[2[2]2]2]1',10)
    [1, 4]
    >>> get_nest_indices('1[2[2[2]2]2]1',11)
    [2]

    """
    nest_indices = [0]
    current_flat_index = 0
    nest_queue = []
    structure_directives = parse_pattern(structure_pattern)
    alg = None
    if flat_index < 0:
        flat_index += sum(item for item in structure_directives if isinstance(item,int))
    for directive in structure_directives:
        if directive is NestDirective.DFS_PUSH:
            if alg is bfs:
                raise Exception('Structure pattern contains both dfs and bfs tokens')
            alg = dfs
            nest_indices.append(0)
        elif directive is NestDirective.DFS_POP: 
            if alg is bfs:
                raise Exception('Structure pattern contains both dfs and bfs tokens')
            alg = dfs
            nest_indices.pop()
            nest_indices[-1] += 1
        elif directive is NestDirective.BFS_QUEUE: 
            if alg is dfs:
                raise Exception('Structure pattern contains both dfs and bfs tokens')
            alg = bfs
            nest_queue.append(nest_indices[:])
            nest_indices[-1] += 1
            

        elif directive is NestDirective.BFS_SERVE: 
            if alg is dfs:
                raise Exception('Structure pattern contains both dfs and bfs tokens')
            nest_indices = nest_queue.popleft()
            nest_indices.append(0)
        else:
            #is a number 
            if current_flat_index <= flat_index < (current_flat_index + directive):
                nest_indices[-1] += (flat_index-current_flat_index)
                return nest_indices
            else:
                current_flat_index += directive
                nest_indices[-1] += directive
    raise Exception('flat index exceeds size implied by structure pattern')




def get_flat_index(structure_pattern,nest_indices):
    """
    Given a structure pattern and a sequence of indices into the nested structure, return the corresponding flat list index

    >>> get_flat_index('1[2[2[2]2]2]1',[0])
    0
    >>> get_flat_index('1[2[2[2]2]2]1',[1,0])
    1
    >>> get_flat_index('1[2[2[2]2]2]1',[1,1])
    2
    >>> get_flat_index('1[2[2[2]2]2]1',[1,2,0])
    3
    >>> get_flat_index('1[2[2[2]2]2]1',[1,2,1])
    4
    >>> get_flat_index('1[2[2[2]2]2]1',[1,2,2,0])
    5
    >>> get_flat_index('1[2[2[2]2]2]1',[1,2,2,1])
    6
    >>> get_flat_index('1[2[2[2]2]2]1',[1,4])
    10
    >>> get_flat_index('1[2[2[2]2]2]1',[2])
    11

    """
    current_nest_indices = [0]
    flat_index = 0
    nest_queue = []
    structure_directives = parse_pattern(structure_pattern)
    alg = None
    for directive in structure_directives:
        if directive is NestDirective.DFS_PUSH:
            if alg is bfs:
                raise Exception('Structure pattern contains both dfs and bfs tokens')
            alg = dfs
            current_nest_indices.append(0)
        elif directive is NestDirective.DFS_POP: 
            if alg is bfs:
                raise Exception('Structure pattern contains both dfs and bfs tokens')
            alg = dfs
            current_nest_indices.pop()
            current_nest_indices[-1] += 1
        elif directive is NestDirective.BFS_QUEUE: 
            if alg is dfs:
                raise Exception('Structure pattern contains both dfs and bfs tokens')
            alg = bfs
            nest_queue.append(current_nest_indices[:])
            current_nest_indices[-1] += 1

        elif directive is NestDirective.BFS_SERVE: 
            if alg is dfs:
                raise Exception('Structure pattern contains both dfs and bfs tokens')
            current_nest_indices = nest_queue.popleft()
            current_nest_indices.append(0)
        else:
            #is a number 
            if current_nest_indices[:-1] == nest_indices[:-1] and (current_nest_indices[-1] <= nest_indices[-1] < (current_nest_indices[-1]+directive)):
                return flat_index + (nest_indices[-1] - current_nest_indices[-1])
            else:
                current_nest_indices[-1] += directive
                flat_index += directive
    raise Exception('The provided nest indices do not exist in the structure pattern')
