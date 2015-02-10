import regex, argparse
from ply import lex, yacc
from collections import namedtuple, deque


def oprex(source_code):
    source_lines = sanitize(source_code)
    lexer = build_lexer(source_lines)
    result = parse(lexer=lexer)
    return result


class OprexSyntaxError(Exception):
    def __init__(self, lineno, msg):
        if lineno:
            Exception.__init__(self, '\nLine %d: %s' % (lineno, msg))
        else:
            Exception.__init__(self, '\n' + msg)


def sanitize(source_code):
    # oprex requires the source code to have leading and trailing blank lines to make
    # "proper look of indentation" when it is a triple-quoted string
    source_lines = regex.split('\r?\n', source_code)
    if source_lines[0].strip():
        raise OprexSyntaxError(1, 'First line must be blank, not: ' + source_lines[0])
    if source_lines[-1].strip():
        numlines = len(source_lines)
        raise OprexSyntaxError(numlines, 'Last line must be blank, not: ' + source_lines[-1])
    return source_lines


LexToken = namedtuple('LexToken', 'type value lineno lexpos lexer')
ExtraToken = lambda t, type, value=None: LexToken(type, value or t.value, t.lexer.lineno, t.lexpos, t.lexer)
tokens = (
    'BEGINSCOPE',
    'CHARCLASS',
    'CLOSEPAREN',
    'COLON',
    'ENDSCOPE',
    'EQUALSIGN',
    'GLOBALMARK',
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
    value = '[' + ''.join(charclass) + ']'
    t.extra_tokens = [ExtraToken(t, 'CHARCLASS', value)]
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


class Variable(namedtuple('Variable', 'name value lineno')):
    __slots__ = ()
    def __str__(self):
        return self.value


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
    r'[ \t\n]+[* \t]*'
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

    # indentation may contain "make this variable global" marker (an asterisk at the beginning of line)
    # indentation depth may change compared to previous line
    # these may generate one or more extra tokens of GLOBALMARK, BEGINSCOPE, and ENDSCOPE
    t.extra_tokens = deque()

    if indentation:
        indent_using_space = ' ' in indentation
        indent_using_tab = '\t' in indentation
        if indent_using_space and indent_using_tab:
            raise OprexSyntaxError(t.lexer.lineno, 'Cannot mix space and tab for indentation')

        # if any, process the "make global variable" marker (an asterisk leading the indent)
        stars = indentation.count('*')
        if stars:
            if stars != 1:
                raise OprexSyntaxError(t.lexer.lineno, 'Syntax error: ' + indentation)
            if indentation[0] != '*':
                raise OprexSyntaxError(t.lexer.lineno, '''The "make global" asterisk must be the line's first character''')
            if len(indentation) == 1:
                raise OprexSyntaxError(t.lexer.lineno, 'Indentation error')
            indentation = indentation.replace('*', ' ' if indent_using_space else '')
            t.extra_tokens.append(ExtraToken(t, 'GLOBALMARK', '*'))

        # all indentations must use the same character
        indentchar = ' ' if indent_using_space else '\t'
        try:
            if indentchar != t.lexer.indentchar:
                raise OprexSyntaxError(t.lexer.lineno, 'Inconsistent indentation character')
        except AttributeError:
            # this is the first indent encountered, record whether it uses space or tab,
            # further indents must use the same character
            t.lexer.indentchar = indentchar
        indentlen = len(indentation)

    else:
        indentlen = 0

    # compare with previous indentation
    prev = t.lexer.indent_stack[-1]
    if indentlen == prev: # no change in indentation depth
        return t

    # at this point, there's indentation depth change

    if indentlen > prev: # deeper indentation, start of a new scope
        t.extra_tokens.appendleft(ExtraToken(t, 'BEGINSCOPE'))
        t.lexer.indent_stack.append(indentlen)
        return t

    if indentlen < prev: # end of one or more scopes
        while indentlen < prev: # close all scopes having deeper indentation
            t.extra_tokens.appendleft(ExtraToken(t, 'ENDSCOPE'))
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
             | NEWLINE            expression
             | NEWLINE BEGINSCOPE expression ENDSCOPE'''
    if len(t) == 3:
        t[0] = t[2]
    elif len(t) == 5:
        t[0] = t[3]
    else:
        t[0] = ''


def p_expression(t):
    '''expression : VARNAME NEWLINE
                  | VARNAME NEWLINE                   beginscope definitions ENDSCOPE
                  | SLASH   cell    moreCells NEWLINE
                  | SLASH   cell    moreCells NEWLINE beginscope definitions ENDSCOPE'''
    if t[1] == '/':
        cell_varname, cell_format_str = t[2]
        slots, format_str = t[3]
        format_str = cell_format_str + format_str
        has_subblock = len(t) > 5
        if has_subblock:
            slots.append(cell_varname)
            defs = t[6]
    else:
        varname = t[1]
        format_str = '%(' + varname + ')s'
        has_subblock = len(t) > 3
        if has_subblock:
            slots = [varname]
            defs = t[4]

    vars_in_scope = t.lexer.vars_stack[-1]
    try:
        result = format_str % vars_in_scope
    except KeyError as e:
        raise OprexSyntaxError(t.lineno(0), "Variable '%s' is not defined" % e.message)

    if has_subblock:
        for definition in defs:
            if definition not in slots:
                raise OprexSyntaxError(t.lineno(0), "'%s' is defined but not used (by its immediate parent)" % definition)
        t.lexer.vars_stack.pop()

    t[0] = result


def p_beginscope(t):
    '''beginscope : BEGINSCOPE'''
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
    format_str = '%(' + varname + ')s'
    if capture:
        format_str = '(?<%s>%s)' % (varname, format_str)
        if optional:
            format_str += '?+'
    elif optional:
        format_str = '(?:%s)?+' % format_str
    t[0] = varname, format_str


def p_moreCells(t):
    '''moreCells : 
                 | cell moreCells'''
    try:
        cell_varname, cell_format_str = t[1]
        slots, format_str = t[2]
    except IndexError: # empty production
        slots, format_str = [], ''
    else:
        slots.append(cell_varname)
        format_str = cell_format_str + format_str
    t[0] = slots, format_str


def p_definitions(t):
    '''definitions : 
                   | definition definitions'''
    try:
        val, defs = t[1]
        defs += t[2]
    except IndexError: # empty production
        defs = []

    t[0] = defs


def p_definition(t):
    '''definition : assignment definition
                  | assignment expression
                  | assignment CHARCLASS NEWLINE
                  | assignment LITERAL   NEWLINE'''
    varname, is_global = t[1]
    if isinstance(t[2], tuple): # t[2] is another definition
        value, defs = t[2]
    else:
        value, defs = t[2], []
    defs.append(varname)

    lineno = t.lineno(1)
    if is_global:
        for scope in t.lexer.vars_stack:
            scope[varname] = Variable(varname, value, lineno)
    else:
        vars_in_scope = t.lexer.vars_stack[-1]
        vars_in_scope[varname] = Variable(varname, value, lineno)

    t[0] = value, defs


def p_assignment(t):
    '''assignment : VARNAME EQUALSIGN
                  | VARNAME COLON
                  | GLOBALMARK VARNAME EQUALSIGN
                  | GLOBALMARK VARNAME COLON'''
    if t[1] == '*':
        varname = t[2]
        is_global = True
    else:
        varname = t[1]
        is_global = False

    vars_in_scope = t.lexer.vars_stack[-1]
    try:
        already_defined = vars_in_scope[varname]
    except KeyError:
        pass
    else:
        raise OprexSyntaxError(t.lineno(-1), "Names must be unique within a scope, '%s' is already defined (previous definition at line %d)" % (varname, already_defined.lineno))
    t[0] = varname, is_global


def p_error(t):
    if t is None:
        raise OprexSyntaxError(None, 'Unexpected end of input')

    if t.type == 'BEGINSCOPE':
        raise OprexSyntaxError(t.lineno, 'Unexpected BEGINSCOPE (indentation error?)')

    errline = t.lexer.source_lines[t.lineno - 1]
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
        self.extras_queue = deque()

    def get_next_token(self):
        try:
            return self.extras_queue.popleft()
        except IndexError:
            lexer = self.real_lexer
            token = lexer.token()
            if token:
                if hasattr(token, 'extra_tokens'):
                    self.extras_queue.extend(token.extra_tokens)
                return token
            else:
                extra_dedent = LexToken('ENDSCOPE', 'EOF', len(lexer.source_lines), len(lexer.lexdata), lexer)
                num_undedented = len(lexer.indent_stack) - 1
                self.extras_queue.extend([extra_dedent] * num_undedented)
                self.extras_queue.append(None)
                return self.extras_queue.popleft()

    def token(self):
        token = self.get_next_token()
        # print token
        return token


lexer0 = lex.lex()
def build_lexer(source_lines):
    lexer = lexer0.clone()
    lexer.indent_stack = [0]
    lexer.source_lines = source_lines
    lexer.input('\n'.join(source_lines)) # all newlines are now just \n, simplifying the lexer
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
