import regex, argparse
from ply import lex, yacc
from collections import namedtuple, deque


def oprex(source_code):
    source_code = check_input(source_code)
    lexer = build_lexer(source_code)
    result = parse(lexer=lexer)
    return result


class OprexSyntaxError(Exception):
    def __init__(self, lineno, msg):
        if lineno:
            Exception.__init__(self, '\nLine %d: %s' % (lineno, msg))
        else:
            Exception.__init__(self, '\n' + msg)


def check_input(source_code):
    # oprex requires the source code to have leading and trailing blank lines to make
    # "proper look of indentation" when it is a triple-quoted string
    source_lines = regex.split('\r?\n', source_code)
    if source_lines[0].strip():
        raise OprexSyntaxError(1, 'First line must be blank, not: ' + source_lines[0])
    if source_lines[-1].strip():
        numlines = len(source_lines)
        raise OprexSyntaxError(numlines, 'Last line must be blank, not: ' + source_lines[-1])

    return '\n'.join(source_lines) # all newlines are now just \n, simplifying the lexer


Token = namedtuple('Token', 'type value lineno lexpos')
INDENT = Token('INDENT', None, 0, 0)
DEDENT = Token('DEDENT', None, 0, 0)

tokens = (
    'CHARCLASS',
    'CLOSEPAREN',
    'COLON',
    'DEDENT',
    'EQUALSIGN',
    'INDENT',
    'LITERAL',
    'NEWLINE',
    'OPENPAREN',
    'QUESTMARK',
    'SLASH',
    'VARNAME',
    'WHITESPACE',
)

t_ignore = '' # oprex is whitespace-significant, no ignored characters


def t_COLON(t):
    ''':.*'''
    chars = t.value.split(' ')
    if chars[0] != ':':
        raise OprexSyntaxError(t.lineno, 'Character class definition requires space after the : (colon)')
    if len(chars) == 1:
        raise OprexSyntaxError(t.lineno, 'Empty character class is not allowed')

    charclass = []
    for char in chars[1:]:
        if not char: # multiple spaces for separator is ok
            continue
        if len(char) > 1:
            raise OprexSyntaxError(t.lineno, 'Invalid character in character class definition: ' + char + ' (each character must be len==1)')
        if char in charclass:
            raise OprexSyntaxError(t.lineno, 'Duplicate character in character class definition: ' + char)
        charclass.append(char)
    charclass = '[' + ''.join(charclass) + ']'
    t.extra_tokens = [Token('CHARCLASS', charclass, t.lineno, t.lexpos)]
    return t


def t_LITERAL(t):
    r"""(?:'|")(.*)"""
    value = t.value.strip()
    if len(value) < 2 or value[0] != value[-1]:
        raise OprexSyntaxError(t.lineno, 'Missing closing quote: ' + value)

    t.value = regex.escape(
        value[1:-1], # remove the surrounding quotes
        special_only=True,
    )
    return t


Variable = namedtuple('Variable', 'name type capture')

def t_VARNAME(t):
    r'[A-Za-z0-9_]+'

    name = t.value
    if regex.match('[0-9_]', name):
        raise OprexSyntaxError(t.lineno, 'Illegal variable name (must start with a letter): ' + name)
    if name[-1] == '_':
        raise OprexSyntaxError(t.lineno, 'Illegal variable name (must not end with underscore): ' + name)
    return t


# Rules that contain space/tab should be written in function form and be put 
# before the t_WHITESPACE rule to make them get inspected first

def t_EQUALSIGN(t):
    r'[ \t]*=[ \t]*'
    return t


def t_WHITESPACE(t):
    r'[ \t\n]+'
    lines = t.value.split('\n')
    num_newlines = len(lines) - 1
    if not num_newlines: # plain regular whitespace
        return t

    # newline-containing whitespace

    t.type = 'NEWLINE'
    t.lexer.lineno += num_newlines
    if t.lexpos + len(t.value) == len(t.lexer.lexdata):
        # this whitespace is just before the end of input
        # no further processing needed
        return t

    # the whitespace after the last newline is indentation
    indentation = lines[-1]
    if indentation:
        if ' ' in indentation and '\t' in indentation:
            raise OprexSyntaxError(t.lexer.lineno, 'Cannot mix space and tab for indentation')

        indentchar = indentation[0]
        try:
            if indentchar != t.lexer.indentchar:
                raise OprexSyntaxError(t.lexer.lineno, 'Cannot mix space and tab for indentation')
        except AttributeError:
            # this is the first indent encountered, record whether it uses space or tab,
            # further indents must use the same character
            t.lexer.indentchar = indentchar
        indentlen = len(indentation)

    else:
        indentlen = 0

    # compare with previous indentation
    prev = t.lexer.indent_stack[-1]
    if indentlen == prev: # indentation of same depth, no special token needed
        return t

    # indentation depth change, either start of a new block (INDENT) or end of block (DEDENT)

    if indentlen > prev: # deeper indentation, start of a new block
        t.extra_tokens = [INDENT]
        t.lexer.indent_stack.append(indentlen)
        return t

    if indentlen < prev: # end of one or more blocks
        t.extra_tokens = []
        while indentlen < prev: # close all blocks with deeper indentation
            t.extra_tokens.append(DEDENT)
            t.lexer.indent_stack.pop()
            prev = t.lexer.indent_stack[-1]
        if indentlen != prev: # the indentation tries to return to a nonexistent level
            raise OprexSyntaxError(t.lexer.lineno, 'Indentation error')
        return t 

t_CLOSEPAREN = r'\)'
t_OPENPAREN  = r'\('
t_QUESTMARK  = r'\?'
t_SLASH      = r'/'


def t_error(t):
    raise OprexSyntaxError(t.lineno, 'Unsupported syntax: ' + t.value.split('\n')[0])


def p_oprex(t):
    '''oprex : 
             | WHITESPACE
             | NEWLINE
             | NEWLINE        expression
             | NEWLINE INDENT expression DEDENT'''
    if len(t) == 3:
        t[0] = t[2]
    elif len(t) == 5:
        t[0] = t[3]
    else:
        t[0] = ''


def p_expression(t):
    '''expression : VARNAME              NEWLINE
                  | VARNAME              NEWLINE indent definitions DEDENT
                  | SLASH cell moreCells NEWLINE
                  | SLASH cell moreCells NEWLINE indent definitions DEDENT'''
    vars_in_scope = t.lexer.vars_stack[-1]
    try:
        if t[1] == '/':
            t[0] = (t[2] + t[3]) % vars_in_scope
        else:
            t[0] = vars_in_scope[t[1]]

    except KeyError as e:
        raise OprexSyntaxError(t.lineno(0), "Variable '%s' is not defined" % e.message)
    t.lexer.vars_stack.pop()


def p_indent(t):
    '''indent : INDENT'''
    vars_in_scope = t.lexer.vars_stack[-1]
    t.lexer.vars_stack.append(vars_in_scope.copy())


def p_cell(t):
    '''cell : VARNAME SLASH
            | VARNAME QUESTMARK SLASH
            | OPENPAREN VARNAME CLOSEPAREN SLASH
            | OPENPAREN VARNAME CLOSEPAREN QUESTMARK SLASH
            | OPENPAREN VARNAME QUESTMARK CLOSEPAREN SLASH'''
    varname, optional, capture = {
        3 : (t[1], False, False),
        4 : (t[1], True,  False),
        5 : (t[2], False, True),
        6 : (t[2], True,  True),
    }[len(t)]

    if optional and capture:
        if t[3] == '?':
            raise OprexSyntaxError(
                t.lineno(3),
                "'/(...?)/' is not supported. To 'capture optional', put the optional part in a subexpression variable, then capture the subexpression."
            )
    result = '%(' + varname + ')s'
    if capture:
        result = '(?<%s>%s)' % (varname, result)
        if optional:
            result += '?+'
    elif optional:
        result = '(?:%s)?+' % result
    t[0] = result


def p_moreCells(t):
    '''moreCells : 
                 | cell moreCells'''
    try:
        t[0] = t[1] + t[2]
    except IndexError: # empty production
        t[0] = ''


def p_definitions(t):
    '''definitions : 
                   | definition definitions'''


def p_definition(t):
    '''definition : assignment definition
                  | assignment expression
                  | assignment CHARCLASS NEWLINE
                  | assignment LITERAL   NEWLINE'''
    varname = t[1]
    value = t[2]
    t.lexer.vars_stack[-1][varname] = value
    t[0] = value


def p_assignment(t):
    '''assignment : VARNAME EQUALSIGN
                  | VARNAME COLON'''
    varname = t[1]
    defined_vars = t.lexer.vars_stack[-1]
    try:
        defined_vars[varname]
    except KeyError:
        pass
    else:
        raise OprexSyntaxError(t.lineno(-1), "Variable '%s' is already defined (names must be unique within a scope)" % varname)
    t[0] = varname


def p_error(t):
    if t is None:
        raise OprexSyntaxError(None, 'Unexpected end of input')
    errline = t.lexer.lexdata.split('\n')[t.lineno - 1]
    pointer = ' ' * (find_column(t)-1) + '^'
    raise OprexSyntaxError(t.lineno, 'Unexpected %s\n%s\n%s' % (t.type, errline, pointer))


def find_column(t):
    last_newline = t.lexer.lexdata.rfind('\n', 0, t.lexpos)
    if last_newline < 0:
        last_newline = 0
    return t.lexpos - last_newline


class CustomLexer:
    def __init__(self, real_lexer):
        self.__dict__ = real_lexer.__dict__
        self.real_lexer = real_lexer
        self.extras_queue = deque([])

    def get_next_token(self):
        try:
            return self.extras_queue.popleft()
        except IndexError:
            token = self.real_lexer.token()
            if token:
                if hasattr(token, 'extra_tokens'):
                    self.extras_queue.extend(token.extra_tokens)
                return token
            else:
                num_undedented = len(self.real_lexer.indent_stack) - 1
                self.extras_queue.extend([DEDENT] * num_undedented)
                self.extras_queue.append(None)
                return self.extras_queue.popleft()

    def token(self):
        token = self.get_next_token()
        # print token
        return token


lexer0 = lex.lex()
def build_lexer(source_code):
    lexer = lexer0.clone()
    lexer.indent_stack = [0]
    lexer.input(source_code)
    lexer.vars_stack = [{}]
    return CustomLexer(lexer)


parser = yacc.yacc()
def parse(lexer):
    return parser.parse(lexer=lexer, tracking=True)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('path/to/source/file')
    args = argparser.parse_args()
    source_file = getattr(args, 'path/to/source/file')
    with open(source_file, 'r') as f:
        source_code = f.read() 
    print oprex(source_code)
