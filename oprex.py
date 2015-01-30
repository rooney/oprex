import regex, argparse
from ply import lex, yacc


def oprex(source_code):
    source_code = check_input(source_code)
    lexer = build_lexer(source_code)
    result = parse(lexer=lexer)
    return result


class OprexSyntaxError(Exception):
    def __init__(self, lineno, msg):
        if lineno:
            Exception.__init__(self, 'Line %d: %s' % (lineno, msg))
        else:
            Exception.__init__(self, msg)


def check_input(source_code):
    source_lines = source_code.split('\n')
    numlines = len(source_lines)

    # we require the oprex source code to have leading and trailing empty lines
    # to make proper look of indentation when it is a triple-quotes string
    if source_lines[0].strip():
        raise OprexSyntaxError(1, 'First line must be blank, not: ' + source_lines[0])
    if source_lines[-1].strip():
        raise OprexSyntaxError(numlines, 'Last line must be blank, not: ' + source_lines[-1])    
    return source_code


# The followings are PLY-related

tokens = (
    'EQUALS',
    'INDENT',
    'LITERAL',
    'NEWLINE',
    'QUEST',
    'SLASH',
    'VARIABLE',
)

t_ignore = '' # oprex is whitespace-significant, no ignored characters


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


def t_NEWLINE(t):
    r'([ \t]*\n)+'
    t.lexer.lineno += t.lexer.lexmatch.group(0).count('\n')
    return t


class Variable(str):
    pass

def t_VARIABLE(t):
    r'[A-Za-z0-9_]+'

    name = t.value
    if regex.match('[0-9_]', name):
        raise OprexSyntaxError(t.lineno, 'Illegal variable name (must start with a letter): ' + name)
    if name[-1] == '_':
        raise OprexSyntaxError(t.lineno, 'Illegal variable name (must not end with underscore): ' + name)
    t.value = Variable(name)
    return t


# Rules that may eat space/tab 
# should be using the function form and be put before the INDENT rule
# to make it run before INDENT

def t_EQUALS(t):
    r'[ \t]*=[ \t]*'
    return t


def t_INDENT(t):
    r'([ ]+|[\t]+)(?=(?P<indentee>.*))'
    indenter = t.value[0]
    try:
        if indenter != t.lexer.indenter:
            raise OprexSyntaxError(t.lineno, 'Cannot mix space and tab for indentation')
    except AttributeError:
        # this is the first INDENT encountered, record what character is used for indentation
        # further indentation must use the same character
        t.lexer.indenter = indenter

    indentee = t.lexer.lexmatch.group('indentee')
    if not indentee:
        return # indent requires something follows, i.e. indented empty line should not produce INDENT token
    return t


t_QUEST = r'\?'
t_SLASH = r'/'


def t_error(t):
    raise OprexSyntaxError(t.lineno, 'Unsupported syntax: ' + t.value.split('\n')[0])


def p_oprex(t):
    '''oprex : 
             | NEWLINE
             | NEWLINE expression
             | NEWLINE INDENT expression'''
    if len(t) <= 2:
        t[0] = ''
    else:
        t[0] = t[len(t)-1]


def p_expression(t):
    '''expression : VARIABLE NEWLINE definitions
                  | chain    NEWLINE definitions'''
    try:
        if isinstance(t[1], Variable):
            t[0] = t.lexer.vars[t[1]]
        else:
            t[0] = t[1] % t.lexer.vars

    except KeyError as e:
        raise OprexSyntaxError(t.lineno(0), "Variable '%s' is not defined" % e.message)


def p_chain(t):
    '''chain : SLASH cell moreCells'''
    t[0] = t[2] +t[3]


def p_cell(t):
    '''cell : VARIABLE SLASH
            | VARIABLE QUEST SLASH'''
    t[0] = '%(' + t[1] + ')s'
    optional = t[2] == '?'
    if optional:
        t[0] = '(?:%s)?+' % t[0]


def p_moreCells(t):
    '''moreCells : 
                 | cell moreCells'''
    try:
        t[0] = t[1] + t[2]
    except IndexError: # empty moreCells
        t[0] = ''


def p_definitions(t):
    '''definitions : 
                   | INDENT definition NEWLINE definitions'''


def p_definition(t):
    '''definition : VARIABLE EQUALS definition
                  | VARIABLE EQUALS expression
                  | VARIABLE EQUALS LITERAL'''
    defined_vars = t.lexer.vars
    try:
        defined_vars[t[1]]
    except KeyError:
        pass
    else:
        raise OprexSyntaxError(t.lineno(1), "Variable '%s' already defined (names must be unique within a scope)" % t[1])

    defined_vars[t[1]] = t[3]
    t[0] = t[3]


def p_error(t):
    if t is None:
        raise OprexSyntaxError(None, 'Unexpected end of input')
    errline = t.lexer.lexdata.split('\n')[t.lineno - 1]
    pointer = ' ' * (find_column(t)-1) + '^'
    raise OprexSyntaxError(t.lineno, 'Unexpected token %s\n%s\n%s' % (t.type, errline, pointer))


def find_column(t):
    last_newline = t.lexer.lexdata.rfind('\n', 0, t.lexpos)
    if last_newline < 0:
        last_newline = 0
    return t.lexpos - last_newline


lexer0 = lex.lex()
def build_lexer(source_code):
    lexer = lexer0.clone()
    lexer.vars = {}
    lexer.input(source_code)
    return lexer


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
