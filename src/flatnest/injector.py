import inspect, ast, re, sys, code, readline, importlib, os, doctest, os.path
from io import StringIO
try:
    from importlib import reload
except:
    pass
try:
    input = raw_input
except NameError:
    pass

    
def get_target(target_fqn):
    """
    This function returns the target object, module object, and the module's fully qualified name based on the provided fully qualified target name.
    """
    module_fqn = target_fqn.split('.')
    while True:
        try:
            module = __import__('.'.join(module_fqn))
            break
        except ImportError:
            module_fqn.pop()
            if len(module_fqn) == 0:
                raise Exception('Could not resolve target: %s' % repr(target_fqn))
    pieces = target_fqn.split('.')
    obj = module
    for item in pieces[1:]:
        obj = getattr(obj,item)
    return obj,module,'.'.join(module_fqn)
get_target.__annotations__ = {'target_fqn':'fully qualified name of target','return':('target object','top-level target module','fully qualified name of module')}

class _ModStdout(object):
    def __init__(self,iobuf):
        self.iobuf = iobuf
    def flush(self):
        sys.__stdout__.flush()
    def writelines(self,lines):
        self.iobuf.extend(data)
        sys.__stdout__.writelines(lines)
    def write(self,data):
        self.iobuf.append(data)
        sys.__stdout__.write(data)
class _ModStderr(object):
    def __init__(self,iobuf):
        self.iobuf = iobuf
    def flush(self):
        sys.__stderr__.flush()
    def writelines(self,lines):
        self.iobuf.extend(data)
        sys.__stderr__.writelines(lines)
    def write(self,data):
        self.iobuf.append(data)
        sys.__stderr__.write(data)

def get_ast_obj(target_fqn,obj=None,module=None,module_fqn=None):
    """
    This function returns the ast object of the targeted python object
    """
    if obj is None or module is None or module_fqn is None:
        obj,module,module_fqn = get_target(target_fqn)
    importlib.reload(module)
    if inspect.ismodule(obj):
        importlib.reload(sys.modules[obj.__name__])
    else:
        importlib.reload(sys.modules[obj.__module__])
    filepath = os.path.abspath(inspect.getsourcefile(obj))
    if not filepath.startswith(os.getcwd()):
        raise Exception('Referenced file is not in the current working directory or any subfolders - this is to protect you from modifying system or site-package code: %s' % repr(filepath))
    filepath
    pieces = target_fqn.split('.')
    with open(filepath,'r') as f:
        src_lines = f.readlines()
    source = ''.join(src_lines)
    tree = ast.parse(source)
    if inspect.ismodule(obj):
        ast_obj = tree
    elif inspect.isclass(obj):
        ast_obj = [node for node in ast.walk(tree) if isinstance(node,ast.ClassDef) and node.name == pieces[-1]][0]
    elif inspect.isfunction(obj):
        ast_obj = [node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name == pieces[-1]][0]

    return ast_obj, filepath,source

class DoctestInjector(object):
    """
    This class loads a target object by its fully qualified name and parses its source code to determine how to insert docstring lines for that object.
    """
    def __init__(self,target_fqn):
        self.target_fqn = target_fqn
        obj,module,module_fqn = get_target(target_fqn)
        self.obj = obj
        self.module=module
        self.module_fqn = module_fqn
        ast_obj,self.filepath,self.original_source = get_ast_obj(target_fqn,obj,module,module_fqn)

        if isinstance(ast_obj.body[0],ast.Expr) and isinstance(ast_obj.body[0].value,ast.Str):
            #docstring already exists
            ast_doc = ast_obj.body[0]

            if hasattr(ast_doc,'end_lineno'):
                #python 3.8+
                line_index = ast_doc.end_lineno-1 #last line of docstring (line containing the ending quotes)
            else:
                #python 3.7-
                line_index = ast_doc.lineno-1 #last line of docstring (line containing the ending quotes)
            byte_index = ast_doc.col_offset
            indentation = re.search('^\\s*',src_lines[line_index]).group(0) #use docstring end line to determine indentation
            newline = re.search('[\r\n]+$',src_lines[line_index]).group(0) #use docstring end line to determine newline
            top = src_lines[:line_index+1] #include entire docstring including end line 
            bottom = src_lines[line_index+1:] #everything else
            ending = '"""'+top[-1].split('"""')[-1] #get the trailing quotes and characters after doctsring
            top[-1] = top[-1][len(indentation):-len(ending)]+newline #remove trailing from top
            bottom.insert(0,indentation+ending) #add trailing to bottom
        else:
            if len(ast_obj.body) == 1 and ast_obj.lineno == ast_obj.body[0].lineno:
                #docstring does not exist for a single-line function
                line_index = ast_obj.lineno-1 #line of function
                indentation = re.search('^\\s*',src_lines[line_index]).group(0).strip('\r\n')+'    ' #use indentation of function plus four spaces
                newline = re.search('[\r\n]+$',src_lines[line_index]).group(0) #use newline of function line
                top = src_lines[:line_index+1] #include funtion
                bottom = src_lines[ast_obj.lineno:] #everything after function
                ast_first = ast_obj.body[0] #first (and only) element in body
                byte_index = ast_first.col_offset #starting position of first element
                first_element = top[-1][byte_index:] #first element text content
                top[-1] = top[-1][:byte_index]+newline #remove first element text content from top
                bottom.insert(0,indentation+first_element) #add first element text content to bottom
                top.append(indentation+'"""'+newline) #add docstring starting quotes
                bottom.insert(0,indentation+'"""'+newline) #add docstring ending quotes
            else:
                #docstring does not exist for a multi-line function
                ast_first = ast_obj.body[0]
                line_index = ast_first.lineno-1 #line number of first element in body of definition
                byte_index = ast_first.col_offset
                indentation = re.search('^\\s*',src_lines[line_index]).group(0) #use first element line to determine indentation
                newline = re.search('[\r\n]+$',src_lines[line_index]).group(0) #use first element line to determine newline
                top = src_lines[:line_index] #everything up to but not including first element
                top.append(indentation+'"""'+newline) #add new docstring starting quotes
                bottom = src_lines[ast_obj.body[0].lineno-1:] #first element and everything after
                bottom.insert(0,indentation+'"""'+newline) #add docstring ending quotes
        self.top = top
        self.bottom = bottom
        self.indentation = indentation
        self.newline = newline
        self.middle = []
    __init__.__annotations__ = {'target_fqn':'fully qualified name of target','return':('target object','target module','fully qualified name of module')}
    def source(self):
        """
        This returns the updated source code with new inserted docstrings lines for the target object.
        """
        indented_middle = []
        last_line = None
        for line in self.middle:
            line = re.sub(self.newline,self.newline+self.indentation,line)
            if last_line is None: 
                indented_middle.append(self.indentation+line)
            else:
                indented_middle.append(line)
            last_line = line
        indented_middle[-1] = indented_middle[-1].rstrip() + self.newline #don't indent the ending triple quotes
        return ''.join(self.top+ indented_middle + self.bottom)
    def doctest_console(self):
        """
        This function runs doctests on the target file, loads the file, and enters a special interactive mode with inputs/outputs being recorded.
        When the console is done being used (via Ctrl+D), the recorded inputs/outputs will be inserted into the docstring of the target object.
        Doctests are then run for the udpated code and if there are no problems, the updated code is written to the file location.
        If there are problems, the updated code is saved to a file in the same folder as the target file but with the suffix ".failed_doctest_insert".
        """
        print('Testing doctest execution of original file')
        oldfailcount,oldtestcount = self.testmod()
        print('...done: Fail count = %d, Total count = %d' % (oldfailcount,oldtestcount))
        print('Entering interactive console')
        banner='''Doctest insertion targeting object %s within %s
Press Ctrl+D to stop writing code and incorporate session into the docstring of the targeted object
To abort this session without writing anything into the targeted file, call the exit() function
>>> from %s import * # automatic import by devshell''' % (self.target_fqn,self.filepath,self.module_fqn)
        console = code.InteractiveConsole()
        console.push('from %s import *' % (self.module_fqn))
        iobuf = self.middle
        _modstdout = _ModStdout(iobuf)
        _modstderr = _ModStderr(iobuf)
        def mod_input(prompt,iobuf=iobuf,_modstdout=_modstdout,_modstderr=_modstderr,newline=self.newline):
            sys.stdout = sys.__stdout__ #when input() is happening - need normal stdout for readline (up/down arrowkeys) to work properly
            sys.stderr = sys.__stderr__
            s = input(prompt)
            iobuf.append(prompt+s+newline)
            sys.stdout = _modstdout
            sys.stderr = _modstderr
            return s
        console.raw_input = mod_input
        #sys.stdout = _modstdout
        #sys.stderr = _modstderr
        console.interact(banner=banner)
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        if len(iobuf) == 0:
            print('No lines were written - exiting')
        else:
            print('Writing doctest lines to file')
            updated_source = self.source()
            with open(self.filepath,'w') as f:
                f.write(updated_source)
            print('Testing doctest execution of new file')
            revert = False
            try:
                newfailcount,newtestcount = self.testmod()
                print('...done: Fail count = %d (old=%d), Total count = %d (old=%d)' % (newfailcount,oldfailcount,newtestcount,oldtestcount))
            except:
                revert = True
                print('Failed to load new file - reverting back to original file')
            if revert is False and oldfailcount != newfailcount:
                revert = True
                print('Failcounts from before did not match after - reverting back to original file')
            if revert:
                with open(self.filepath,'w') as f:
                    f.write(self.original_source)
                print('Updated source code with problems located at: %s' % (self.filepath+'.failed_doctest_insert'))
                with open(self.filepath+'.failed_doctest_insert','w') as f:
                    f.write(updated_source)
            else:
                print('File successfully updated')
    def testmod(self):
        """
        This runs doctests on the target module and returns the failcount and testcount
        """
        self.module = module = reload(sys.modules[self.module_fqn])
        failcount,testcount = doctest.testmod(module)
        return failcount,testcount
def set_end_interactive(value=True):
    """
    Setting value=True will make python go into interactive mode when the script terminates.
    """
    if value:
        os.environ['PYTHONINSPECT'] = '1'
    else:
        if 'PYTHONINSPECT' in os.environ:
            del os.environ['PYTHONINSPECT']
def doctestify(target_fqn):
    """
    Start an interactive recording session for the item identified by the given fully qualified name.
    Write the recorded results to the target object's docstring and test that the doctest passes.
    """
    di = DoctestInjector(target_fqn)
    di.doctest_console()

