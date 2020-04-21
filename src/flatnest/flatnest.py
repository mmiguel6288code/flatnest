"""
This module converts to/from a nested structure (e.g. list of lists of lists of ... of values) and a (nest pattern, flat list) tuple

The nest pattern is a string consisting solely of square brackets and digits.
A number represents the number of consecutive values at the current level of the nested structure.
An opening square bracket represents entering a deeper level of nesting.
A closing square bracket represents leaving a deper level of nesting.
The square brackets at the top level (would be first and last characters of every pattern) are omitted.
"""
def flatten(nested_structure,algorithm='DFS'):
    """
    The flatten function takes a nested data structure (list of lists of lists etc) and returns a nest pattern that stores the nesting information as well as a flattend version (list of values).

    >>> flatten([1,'abc',[0,[1,1,[5]],'def'],9,10,11])
    ('2[1[2[1]]1]3',[1, 'abc', 0, 1, 1, 5, 'def', 9, 10, 11])
    """
    flat_list = []
    nest_pattern_list = []
    stack = [[nested_list,0]]
    while len(stack) > 0:
        target,pos = stack[-1]
        if pos >= len(target):
            stack.pop(-1)
            structure_pattern.append(']')
        else:
            item = target[pos]
            stack[-1][1] += 1
            if isinstance(item,(list,tuple)):
                stack.append([item,0])
                structure_pattern.append('[')
            else:
                data_stream.append(item)
                structure_pattern.append('.')
    structure_pattern.pop(-1) #remove trailing ]
    return data_stream,''.join(structure_pattern)

def deflatten(structure_pattern,data_stream,algorithm='DFS'):
    """
    The deflatten function takes a structure pattern flat and a data stream (list of values), and produces a nested data structure according to those inputs.
    This is the inverse function of flatten()
    >>> deflatten('..[.[..[.]].]...',[1, 'abc', 0, 1, 1, 5, 'def', 9, 10, 11])
    [1, 'abc', [0, [1, 1, [5]], 'def'], 9, 10, 11]
    """
    data_structure = []
    stack = [data_structure]
    pos = 0
    for token in structure_pattern:
        if token == '[':
            new_sublist = []
            stack[-1].append(new_sublist)
            stack.append(new_sublist)
        elif token == ']':
            stack.pop(-1)
        elif token == '.':
            stack[-1].append(data_stream[pos])
            pos += 1
    return data_structure

def get_stream_index(structure_pattern,structure_index):
    """
    Translates the sequence of indices identifying an item  in a hierarchy
    to the index identifying the same item in the flattened data stream.
    The structure indices must point to a value, not a list.
    >>> get_stream_index('..[[[.]..].].',[0])
    0
    >>> get_stream_index('..[[[.]..].].',[2,0,0,0])
    2
    >>> get_stream_index('..[[[.]..].].',[2,1])
    5
    """
    structure_index = list(structure_index)
    stream_index = 0 
    current_structure_index  = [0] 
    for p in structure_pattern:
        if p == '[':
            if current_structure_index >= structure_index:
                raise Exception('Provided structure_index does not point to a non-list element')
            current_structure_index.append(0)
        elif p == ']':
            if current_structure_index >= structure_index:
                raise Exception('Provided structure_index does not point to a non-list element')
            current_structure_index.pop(-1)
            current_structure_index[-1] += 1
        elif p == '.':
            if current_structure_index == structure_index:
                return stream_index
            stream_index += 1
            current_structure_index[-1] += 1
        else:
            raise Exception('Invalid character in structure pattern: %s' % repr(p))

def get_structure_index(structure_pattern,stream_index):
    """
    Translates the stream index into a sequence of structure indices identifying an item in a hierarchy whose structure is specified by the provided structure pattern.
    >>> get_structure_index('...',1)
    [1]
    >>> get_structure_index('.[.].',1)
    [1, 0]
    >>> get_structure_index('.[[...],..].',1)
    [1, 0, 0]
    >>> get_structure_index('.[[...]...].',2)
    [1, 0, 1]
    >>> get_structure_index('.[[...]...].',3)
    [1, 0, 2]
    >>> get_structure_index('.[[...]...].',4)
    [1, 1]
    >>> get_structure_index('.[[...]...].',5)
    [1, 2]
    >>> get_structure_index('.[[...]...].',6)
    [1, 3]
    >>> get_structure_index('.[[...]...].',7)
    [2]
    """
    structure_index = [0]
    current_stream_index = 0
    for p in structure_pattern:
        if p == '[':
            structure_index.append(0)
        elif p == '.':
            if current_stream_index == stream_index:
                return structure_index
            structure_index[-1] += 1
            current_stream_index += 1
        elif p == ']':
            structure_index.pop(-1)
            structure_index[-1] += 1
        else:
            raise Exception('Invalid character in structure pattern: %s' % repr(p))
    raise Exception('Provided stream index does not exist in the provided structure pattern')
