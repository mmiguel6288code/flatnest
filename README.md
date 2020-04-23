# flatnest

[View API documentation](http://htmlpreview.github.io/?https://github.com/mmiguel6288code/flatnest/blob/master/docs/flatnest/index.html)

This package provides:

1. Provides generators to traverse nested list structures either depth-first or breadth-first.
2. Extraction of structural information from a nested list structure into a string structure pattern which can then be used in conjunction with the flattened list to reconstruct the original nested list structure.
3. Conversion between a flat index and its corresponding sequence of nested indices (and vice versa).

There are two types of patterns: depth-first search (DFS) patterns and breadth-first search (BFS) patterns.
DFS patterns have square brackets in them and look roughly like python list literals. There are no commas and numbers represent the number of elements in the nested structure at that level.

BFS patterns use the &ast; and | symbols. The &ast; symbol is viewed sort of like a wildcard placeholder indicating that there are a number of child nodes at a lower level present in that spot.
The | symbol indicates the current level of nest structure specification is done, and should be followed by the next level of specification that corresponds to the earliest &ast; that hasn't yet been specified.

So for example, '1[2[1]3]3[2]' is a DFS pattern.
At the top level of this structure are the following 4 items:

- 1
- [2[1]3]
- 3
- [2]

In BFS form, the first level is represented as '1&ast;3&ast;'.
The first &ast; to be processed is [2[1]3] which consists of the following 3 items:

- 2
- [1]
- 3

In BFS form, this is represented as '2&ast;3'

The BFS pattern at this point (not finished yet) is '1&ast;3&ast;|2&ast;3'

The next unspecified level is the second &ast; in the pattern so far which represents [2]:

This has just the one item:

- 2

The BFS pattern at this point (not finished yet) is '1&ast;3&ast;|2&ast;3|2'
The final unspecified level is the third &ast;, which represents [1].

The final BFS pattern is '1&ast;3&ast;|2&ast;3|2|1'

This pattern defines an identical nested list structure to the DFS version of it, which is '1[2[1]3]3[2]'.
What is different between these two cases is the order of the flattened list.

The order of a DFS flattened list would be essentially the order the items would be written in a python list literal representation.

The order of a BFS flattened list places shallowly located items up front and deeply nested items in the back.

As a simple example, consider:

```
>>> flatten([0,1,2,3,[4,5],6,7,8,9])
('4[2]4', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
>>> flatten([0,1,2,3,[4,5],6,7,8,9],bfs)
('4*4|2', [0, 1, 2, 3, 6, 7, 8, 9, 4, 5])
```

In the BFS version, the more deeply nested items 4, and 5 are placed as the end, although the nested structure is identical.

