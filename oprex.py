# -*- coding: utf-8 -*-

import regex, argparse, codecs
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
    'CHARCLASS',
    'COLON',
    'DEDENT',
    'EQUALSIGN',
    'GLOBALMARK',
    'INDENT',
    'LITERAL',
    'LPAREN',
    'NEWLINE',
    'QUESTMARK',
    'RPAREN',
    'SLASH',
    'VARNAME',
    'WHITESPACE',
)

GLOBALMARK   = '*)'
t_LPAREN     = r'\('
t_RPAREN     = r'\)'
t_QUESTMARK  = r'\?'
t_SLASH      = r'/'
t_ignore     = '' # oprex is whitespace-significant, no ignored characters

def t_character_class(t):
    ''':.*'''
    chardefs = t.value.split(' ')
    if chardefs[0] != ':':
        raise OprexSyntaxError(t.lineno, 'Character class definition requires space after the : (colon)')
    if len(chardefs) == 1: # only colon not followed by anything
        raise OprexSyntaxError(t.lineno, 'Empty character class is not allowed')

    def try_parse(chardef, errmsg, *methods): # pass chardef to method(s) until we got something
        for method in methods:                # otherwise raise errmsg
            result = method(chardef)
            if result:
                return result
        raise OprexSyntaxError(t.lineno, errmsg)

    def single(chardef): # example: a 1 $ 久 😐
        if len(chardef) == 1:
            if chardef in ['[', ']', '^', '\\']: # need escape
                chardef = '\\' + chardef
            return chardef

    def uhex(chardef): # example: U+65 u+1F4A9
        if chardef[:2].upper() == 'U+':
            hexnum = chardef[2:]
            try:
                int(hexnum, 16)
            except ValueError:
                raise OprexSyntaxError(t.lineno, 'Syntax error %s should be U+hexnumber' % chardef)
            hexlen = len(hexnum)
            if hexlen > 8:
                raise OprexSyntaxError(t.lineno, 'Syntax error %s out of range' % chardef)
            if hexlen <= 4:
                return unicode(r'\u' + ('0' * (4-hexlen) + hexnum))
            else:
                return unicode(r'\U' + ('0' * (8-hexlen) + hexnum))

    def include(chardef): # example: +upper +!lower
        if chardef.startswith('+!'):
            return chardef[2:], True # varname, negation
        if chardef.startswith('+'):
            return chardef[1:], False

    def by_prop(chardef): # example: /Alphabetic /Script=Latin /InBasicLatin /!IsCyrillic /Script!=Cyrillic /!Script=Cyrillic
        if chardef.startswith('/'):
            return r'\%s{%s}' % ('P' if '!' in chardef else 'p', chardef[1:].replace('!', '', 1))

    def by_name(chardef): # example: :TRUE :CHECK_MARK :BALLOT_BOX_WITH_CHECK
        if chardef.startswith(':'): # must be in uppercase, using underscores rather than spaces
            if not chardef.isupper(): 
                raise OprexSyntaxError(t.lineno, 'Character name must be in uppercase')
            return r'\N{%s}' % chardef[1:].replace('_', ' ')

    def range(chardef): # example: A..Z U+41..U+4F :LEFTWARDS_ARROW..:LEFT_RIGHT_OPEN-HEADED_ARROW
        if '..' in chardef:
            errmsg = 'Invalid range: ' + chardef
            bounds = chardef.split('..')
            if len(bounds) != 2 or bounds[0] == '' or bounds[1] == '':
                raise OprexSyntaxError(t.lineno, errmsg)
            lower_bound = try_parse(bounds[0], errmsg, single, uhex, by_name)
            upper_bound = try_parse(bounds[1], errmsg, single, uhex, by_name)
            return lower_bound + '-' + upper_bound

    result = []
    processed = []
    for chardef in chardefs[1:]:
        if not chardef: # multiple spaces for separator is ok
            continue
        if chardef in processed:
            raise OprexSyntaxError(t.lineno, 'Duplicate character in character class definition: ' + chardef)
        compiled = try_parse(chardef, 'Not a valid character class keyword: ' + chardef, 
            range, single, uhex, by_prop, by_name, include)
        if isinstance(compiled, basestring):
            try:
                test = compiled
                if test[:2] not in ['\\p', '\\P']:
                    test = '[' + test + ']' 
                regex.compile(test)
            except Exception as e:
                msg = '%s compiles to %s which is rejected by the regex module with error message: %s'
                raise OprexSyntaxError(t.lineno, msg % (chardef, compiled, e.msg if hasattr(e, 'msg') else e.message))
        result.append(compiled)
        processed.append(chardef)

    t.type, t.value = 'COLON', ':'
    t.extra_tokens = [ExtraToken(t, 'CHARCLASS', result)]
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


class Variable(namedtuple('Variable', 'name value lineno charclass')):
    __slots__ = ()
    def __str__(self):
        return self.value


class VariableLookup:
    names = []
    fmt = ''
    def add(self, name, fmt):
        self.names.append(name)
        self.fmt = fmt + self.fmt
        return self


def t_VARNAME(t):
    r'[A-Za-z0-9_]+'
    name = t.value
    if regex.match('[0-9_]', name):
        raise OprexSyntaxError(t.lineno, 'Illegal name (must start with a letter): ' + name)
    if name[-1] == '_':
        raise OprexSyntaxError(t.lineno, 'Illegal name (must not end with underscore): ' + name)
    return t


# Rules that contain space/tab should be written in function form and be put 
# before the t_linemark rule to make PLY calls them first.
# Otherwise t_linemark will turn the spaces/tabs into WHITESPACE token.

def t_EQUALSIGN(t):
    r'[ \t]*=[ \t]*'
    return t


def t_linemark(t):
    r'[ \t\n]+(\*\)[ \t]*)*'
    lines = t.value.split('\n')
    num_newlines = len(lines) - 1
    if num_newlines == 0:
        if GLOBALMARK in t.value: # globalmark must be put at the beginning of a line, i.e. requires newline
            raise OprexSyntaxError(t.lexer.lineno, 'Syntax error: ' + t.lexer.source_lines[t.lexer.lineno-1])
        t.type = 'WHITESPACE'
        return t
    else:
        t.type = 'NEWLINE'
        t.lexer.lineno += num_newlines

    # the whitespace after the last newline is indentation
    indentation = lines[-1]

    num_globalmarks = indentation.count(GLOBALMARK)
    if endpos(t) == len(t.lexer.lexdata) and not num_globalmarks:
        # this is a just-before-the-end-of-input whitespace
        # no further processing needed
        return t

    # indentation may generate extra tokens:
    # + GLOBALMARK if it contains globalmark
    # + INDENT if its depth is more than previous line's, DEDENT(s) if less
    t.extra_tokens = deque()

    if indentation:
        indent_using_space = ' ' in indentation
        indent_using_tab = '\t' in indentation
        if indent_using_space and indent_using_tab:
            raise OprexSyntaxError(t.lexer.lineno, 'Cannot mix space and tab for indentation')

        if num_globalmarks:
            if num_globalmarks != 1:
                raise OprexSyntaxError(t.lexer.lineno, 'Syntax error: ' + indentation)
            if not indentation.startswith(GLOBALMARK):
                raise OprexSyntaxError(t.lexer.lineno, "The GLOBALMARK %s must be put at the line's beginning" % GLOBALMARK)
            if len(indentation) == len(GLOBALMARK):
                raise OprexSyntaxError(t.lexer.lineno, 'Indentation required after GLOBALMARK ' + GLOBALMARK)
            indentation = indentation.replace(GLOBALMARK, (' ' * len(GLOBALMARK)) if indent_using_space else '')
            t.extra_tokens.append(ExtraToken(t, 'GLOBALMARK', GLOBALMARK))

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

    # else, there's indentation depth change
    if indentlen > prev: # deeper indentation, start of a new scope
        t.extra_tokens.appendleft(ExtraToken(t, 'INDENT'))
        t.lexer.indent_stack.append(indentlen)
        return t

    if indentlen < prev: # end of one or more scopes
        while indentlen < prev: # close all scopes having deeper indentation
            t.extra_tokens.appendleft(ExtraToken(t, 'DEDENT'))
            t.lexer.indent_stack.pop()
            prev = t.lexer.indent_stack[-1]
        if indentlen != prev: # the indentation tries to return to a nonexistent level
            raise OprexSyntaxError(t.lexer.lineno, 'Indentation error')
        return t 


def t_error(t):
    raise OprexSyntaxError(t.lineno, 'Unsupported syntax: ' + t.value.split('\n')[0])


def endpos(t):
    return t.lexpos + len(t.value)
    

def p_oprex(t):
    '''oprex : 
             | WHITESPACE
             | NEWLINE
             | NEWLINE        expression
             | NEWLINE INDENT expression DEDENT'''
    if len(t) == 3:
        expression = t[2]
    elif len(t) == 5:
        expression = t[3]
    else:
        expression = ''
    t[0] = expression


def check_unused_variable(t, lookups):
    try:
        definitions = t[4]
    except IndexError:
        pass
    else:
        for var in definitions:
            if var.name not in lookups:
                raise OprexSyntaxError(var.lineno, "'%s' is defined but not used (by its parent expression)" % var.name)
        t.lexer.scopes.pop()


def p_expression(t):
    '''expression : lookup NEWLINE
                  | lookup NEWLINE beginscope definitions DEDENT'''
    lookup = t[1]
    current_scope = t.lexer.scopes[-1]
    try:
        result = lookup.fmt % current_scope
    except KeyError as e:
        raise OprexSyntaxError(t.lineno(0), "'%s' is not defined" % e.message)

    check_unused_variable(t, lookup.names)
    t[0] = result


def p_lookup(t):
    '''lookup : VARNAME
              | SLASH cells'''
    if t[1] == '/':
        lookup = t[2]
    else:
        varname = t[1]
        lookup = VariableLookup()
        lookup.add(varname, '%(' + varname + ')s')
    t[0] = lookup


def p_cells(t):
    '''cells : cell SLASH
             | cell SLASH cells'''
    varname, fmt = t[1]
    try:
        lookup = t[3]
    except IndexError:
        lookup = VariableLookup()
    t[0] = lookup.add(varname, fmt)


def p_cell(t):
    '''cell : VARNAME
            | VARNAME QUESTMARK
            | LPAREN VARNAME RPAREN
            | LPAREN VARNAME RPAREN QUESTMARK
            | LPAREN VARNAME QUESTMARK RPAREN'''
    if t[1] == '(':
        varname = t[2]
    else:
        varname = t[1]

    optional, capture = {
        2 : (False, False),
        3 : (True,  False),
        4 : (False, True),
        5 : (True,  True),
    }[len(t)]

    fmt = '%(' + varname + ')s'
    if capture and optional:
        optional_capture = t[4] == '?'
        if optional_capture:
            fmt = '(?<%s>%s)?+' % (varname, fmt)
        else: # capture optional
            fmt = '(?<%s>(?:%s)?+)' % (varname, fmt)

    elif capture and not optional:
        fmt = '(?<%s>%s)' % (varname, fmt)
        
    elif optional and not capture:
        fmt = '(?:%s)?+' % fmt

    t[0] = varname, fmt


def p_beginscope(t):
    '''beginscope : INDENT'''
    current_scope = t.lexer.scopes[-1]
    t.lexer.scopes.append(current_scope.copy())


def p_definitions(t):
    '''definitions : definition
                   | definition definitions'''
    try:
        variables = t[1] + t[2]
    except IndexError:
        variables = t[1]
    t[0] = variables


def p_definition(t):
    '''definition : assignment
                  | GLOBALMARK assignment'''

    def define(variables, scope):
        for var in variables:
            try:
                already_defined = scope[var.name]
            except KeyError:
                scope[var.name] = var
            else:
                raise OprexSyntaxError( t.lineno(1), 
                    "Names must be unique within a scope, '%s' is already defined (previous definition at line %d)" % (
                        var.name, already_defined.lineno
                    ))

    has_globalmark = t[1] == GLOBALMARK
    if has_globalmark:
        variables = t[2]
        for scope in t.lexer.scopes:
            define(variables, scope) # global variable, define in all scopes
    else:
        variables = t[1]
        current_scope = t.lexer.scopes[-1] 
        define(variables, current_scope) # non-global, define in current scope only
    t[0] = variables


def p_assignment(t):
    '''assignment : VARNAME EQUALSIGN assignment
                  | VARNAME EQUALSIGN expression
                  | VARNAME EQUALSIGN LITERAL   NEWLINE
                  | VARNAME COLON     charclass'''
    varname = t[1]
    charclass = t[2] == ':'
    lineno = t.lineno(1)
    if isinstance(t[3], list): # t[3] is another assignment
        variables = t[3]
        value = variables[0].value
    else:
        variables = []
        value = t[3]
    variables.append(Variable(varname, value, lineno, charclass))
    t[0] = variables


def p_charclass(t):
    '''charclass : CHARCLASS NEWLINE
                 | CHARCLASS NEWLINE beginscope definitions DEDENT'''
    charclass = t[1]
    lookups = []
    current_scope = t.lexer.scopes[-1]

    def interpolate(char):
        if isinstance(char, tuple): # lookup
            varname, negation = char
            lookups.append(varname)
            try:
                var = current_scope[varname]
            except KeyError:
                raise OprexSyntaxError(t.lineno(0), "Cannot include '%s': not defined" % varname)
            if not var.charclass:
                raise OprexSyntaxError(t.lineno(0), "Cannot include '%s': not a character class" % varname)
            char = var.value
            if negation:
                char = '[^' + char[1:]
        return char

    charclass = map(interpolate, charclass)
    check_unused_variable(t, lookups)
    t[0] = '[' + ''.join(charclass) + ']'


def p_error(t):
    if t is None:
        raise OprexSyntaxError(None, 'Unexpected end of input')

    if t.type == 'INDENT':
        raise OprexSyntaxError(t.lineno, 'Unexpected INDENT')

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
                extra_dedent = LexToken('DEDENT', 'EOF', len(lexer.source_lines), len(lexer.lexdata), lexer)
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
    lexer.indent_stack = [0]  # for keeping track of indentation levels
    lexer.source_lines = source_lines
    lexer.input('\n'.join(source_lines)) # all newlines are now just \n, simplifying the lexer
    lexer.scopes = [{}]
    return CustomLexer(lexer)


parser = yacc.yacc()
def parse(lexer):
    # always use V1, UNICODE, and MULTILINE
    return '(?umV1)' + parser.parse(lexer=lexer, tracking=True)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('path/to/source/file')
    argparser.add_argument('--encoding', help='encoding of the source file')
    args = argparser.parse_args()

    source_file = getattr(args, 'path/to/source/file')
    default_encoding = 'utf-8'
    encoding = args.encoding or default_encoding

    with codecs.open(source_file, 'r', encoding) as f:
        source_code = f.read()

    print oprex(source_code)
