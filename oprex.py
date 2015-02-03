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
TypeToken = lambda type: Token(type, None, 0, 0)
INDENT = TypeToken('INDENT')
DEDENT = TypeToken('DEDENT')

tokens = (
    'DEDENT',
    'EQUALSIGN',
    'INDENT',
    'LITERAL',
    'NEWLINE',
    'QUESTMARK',
    'SLASH',
    'VARIABLE',
    'WHITESPACE',
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


def t_VARIABLE(t):
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


t_QUESTMARK = r'\?'
t_SLASH = r'/'


def t_error(t):
    raise OprexSyntaxError(t.lineno, 'Unsupported syntax: ' + t.value.split('\n')[0])


def p_oprex(t):
    '''oprex : 
             | WHITESPACE
             | NEWLINE
             | NEWLINE expression
             | NEWLINE INDENT expression DEDENT'''
    if len(t) == 3:
        t[0] = t[2]
    elif len(t) == 5:
        t[0] = t[3]
    else:
        t[0] = ''


def p_expression(t):
    '''expression : VARIABLE             NEWLINE
                  | VARIABLE             NEWLINE INDENT definitions DEDENT
                  | SLASH cell moreCells NEWLINE
                  | SLASH cell moreCells NEWLINE INDENT definitions DEDENT'''
    try:
        if t[1] == '/':
            t[0] = (t[2] + t[3]) % t.lexer.vars
        else:
            t[0] = t.lexer.vars[t[1]]

    except KeyError as e:
        raise OprexSyntaxError(t.lineno(0), "Variable '%s' is not defined" % e.message)


def p_cell(t):
    '''cell : VARIABLE SLASH
            | VARIABLE QUESTMARK SLASH'''
    t[0] = '%(' + t[1] + ')s'
    optional = t[2] == '?'
    if optional:
        t[0] = '(?:%s)?+' % t[0]


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
    '''definition : VARIABLE assignment definition
                  | VARIABLE assignment expression
                  | VARIABLE assignment LITERAL NEWLINE'''
    t.lexer.vars[t[1]] = t[3]
    t[0] = t[3]


def p_assignment(t):
    '''assignment : EQUALSIGN'''
    varname = t[-1]
    defined_vars = t.lexer.vars
    try:
        defined_vars[varname]
    except KeyError:
        pass
    else:
        raise OprexSyntaxError(t.lineno(-1), "Variable '%s' is already defined (names must be unique within a scope)" % varname)


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

    def token(self):
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


lexer0 = lex.lex()
def build_lexer(source_code):
    lexer = lexer0.clone()
    lexer.indent_stack = [0]
    lexer.input(source_code)
    lexer.vars = {}
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
