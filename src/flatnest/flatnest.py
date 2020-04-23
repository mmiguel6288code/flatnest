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
    return [(token_directive_map[token] if token in token_directive_map else int(token)) for token in re.split('(['+re.escape(''.join(directive_token_map.values()))+'])',structure_pattern) if token != '']

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
        raise Exception('Structure pattern contains imbalanced directive tokens')
    return top_nested_structure

def get_nested_indices(structure_pattern,flat_index):
    """
    Given a structure pattern and an index into the flat list, return the corresponding sequence of indices identifying the position in the nested structure.

    A negative flat index works from the end of the flat list

    >>> get_nested_indices('1[2[2[2]2]2]1',0)
    [0]
    >>> get_nested_indices('1[2[2[2]2]2]1',1)
    [1, 0]
    >>> get_nested_indices('1[2[2[2]2]2]1',2)
    [1, 1]
    >>> get_nested_indices('1[2[2[2]2]2]1',3)
    [1, 2, 0]
    >>> get_nested_indices('1[2[2[2]2]2]1',4)
    [1, 2, 1]
    >>> get_nested_indices('1[2[2[2]2]2]1',5)
    [1, 2, 2, 0]
    >>> get_nested_indices('1[2[2[2]2]2]1',6)
    [1, 2, 2, 1]
    >>> get_nested_indices('1[2[2[2]2]2]1',10)
    [1, 4]
    >>> get_nested_indices('1[2[2[2]2]2]1',11)
    [2]

    """
    nest_indices = [0]
    current_flat_index = 0
    nest_queue = deque()
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
    nest_queue = deque()
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

def convert_dfs_to_bfs(dfs_pattern):
    """
    This function takes a pattern corresponding to a depth-first search and produces the corresponding breadth-first search pattern

    >>> convert_dfs_to_bfs('1[2[1]3]3[2]')
    '1*3*|2*3|2|1'

    """
    start = []
    under_construction = deque([start])
    level = 0
    final_positions = [deque([start])]
    for token in re.split('(['+re.escape(''.join(directive_token_map.values()))+'])',dfs_pattern):
        if token == '':
            continue
        if token in token_directive_map:
            directive = token_directive_map[token]
            if directive is NestDirective.DFS_PUSH:
                under_construction[-1].append(directive_token_map[NestDirective.BFS_QUEUE])
                new_item = []
                under_construction.append(new_item)
                while level >= len(final_positions):
                    final_positions.append(deque())
                final_positions[level].append(new_item)
                level += 1
            elif directive is NestDirective.DFS_POP:
                under_construction.pop()
                level -= 1
            else:
                raise Exception('Provided pattern has bfs tokens in it')
        else:
            under_construction[-1].append(token)
    if len(under_construction) != 1:
        raise Exception('Structure pattern contains imbalanced directive tokens')

    serve = directive_token_map[NestDirective.BFS_SERVE]
    return serve.join([serve.join([''.join(region) for region in level_group]) for level_group in final_positions])

def convert_bfs_to_dfs(bfs_pattern):
    """
    This function takes a pattern corresponding to a breadth-first search and produces the corresponding depth-first search pattern

    >>> convert_bfs_to_dfs('1*3*|2*3|2|1')
    '1[2[1]3]3[2]'

    """
    top = []
    target = top
    queue = deque()
    almost_done = deque()
    for token in re.split('(['+re.escape(''.join(directive_token_map.values()))+'])',bfs_pattern):
        if token == '':
            continue
        if token in token_directive_map:
            directive = token_directive_map[token]
            if directive is NestDirective.BFS_QUEUE:
                target.append(directive_token_map[NestDirective.DFS_PUSH])
                inner = []
                target.append(inner)
                queue.append(inner)
                target.append(directive_token_map[NestDirective.DFS_POP])
            elif directive is NestDirective.BFS_SERVE:
                almost_done.append(target)
                target = queue.popleft()
            else:
                raise Exception('Provided pattern has dfs tokens in it')
        else:
            target.append(token)
    if len(queue) > 0:
        raise Exception('Structure pattern contains imbalanced directive tokens')
    while len(almost_done) > 0:
        region = almost_done.pop()
        copy = list(region)
        del region[:]
        for item in copy:
            if isinstance(item,list):
                region.extend(item)
            else:
                region.append(item)

    return ''.join(top)
def is_bfs_pattern(pattern):
    """
    Checks if a given pattern can be interpreted as a breadth-first search pattern
    """
    return not directive_token_map[NestDirective.DFS_PUSH] in pattern and not directive_token_map[NestDirective.DFS_POP] in pattern
def is_dfs_pattern(pattern):
    """
    Checks if a given pattern can be interpreted as a depth-first search pattern
    """
    return not directive_token_map[NestDirective.BFS_QUEUE] in pattern and not directive_token_map[NestDirective.BFS_SERVE] in pattern
def as_bfs_pattern(pattern):
    """
    Converts a pattern to a breadth-first search pattern
    """
    if is_bfs_pattern(pattern):
        return pattern
    return convert_dfs_to_bfs(pattern)
def as_dfs_pattern(pattern):
    """
    Converts a pattern to a depth-first search pattern
    """
    if is_dfs_pattern(pattern):
        return pattern
    return convert_bfs_to_dfs(pattern)

def convert_flat_index_dfs_to_bfs(pattern,dfs_flat_index):
    """
    Calculates a bfs flat index from a dfs one
    >>> convert_flat_index_dfs_to_bfs('1[2[1]3]3[2]',3)
    11

    """
    dfs_pattern = as_dfs_pattern(pattern)
    nest_indices = get_nested_indices(dfs_pattern,dfs_flat_index)
    bfs_pattern = convert_dfs_to_bfs(dfs_pattern)
    return get_flat_index(bfs_pattern,nest_indices)
def convert_flat_index_bfs_to_dfs(pattern,bfs_flat_index):
    """
    Calculates a dfs flat index from a bfs one
    >>> convert_flat_index_bfs_to_dfs('1[2[1]3]3[2]',11)
    3
    """
    bfs_pattern = as_bfs_pattern(pattern)
    nest_indices = get_nested_indices(bfs_pattern,bfs_flat_index)
    dfs_pattern = convert_bfs_to_dfs(bfs_pattern)
    return get_flat_index(dfs_pattern,nest_indices)
