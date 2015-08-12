# -*- coding: utf-8 -*-

import argparse, codecs, unicodedata, regex as regexlib
from ply import lex, yacc
from collections import namedtuple, deque


def oprex(source_code):
    source_lines = sanitize(source_code)
    lexer = build_lexer(source_lines)
    result = parse(lexer=lexer)
    cleanup(lexer=lexer)
    return result


class OprexError(Exception):
    def __init__(self, lineno, msg):
        msg = msg.replace('\t', ' ')
        if lineno:
            msg = 'Line %d: %s' % (lineno, msg)
        Exception.__init__(self, '\n' + msg)

class OprexSyntaxError(OprexError): pass
class OprexInternalError(OprexError): pass


def sanitize(source_code):
    # oprex requires the source code to have leading and trailing blank lines to make
    # "proper look of indentation" when it is a triple-quoted string

    def is_blank_or_comments_only(line):
        non_comments = line.split('--')[0]
        return non_comments.strip() == ''

    source_lines = regexlib.split('\r?\n', source_code)
    first_line = source_lines[0]
    last_line = source_lines[-1]

    if not is_blank_or_comments_only(first_line):
        raise OprexSyntaxError(1, 'First line must be blank, not: ' + first_line)
    if not is_blank_or_comments_only(last_line):
        raise OprexSyntaxError(len(source_lines), 'Last line must be blank, not: ' + last_line)

    # at this point, first and last lines are ensured to be blanks/comments only
    # we'll make them really empty so regex-for-comments does not need take into consideration first/last-line comments
    source_lines[0] = source_lines[-1] = ''
    return source_lines


states = (
    ('CHARCLASS',  'exclusive'),
    ('LOOKAROUND', 'inclusive'),
    ('ORBLOCK',    'inclusive'),
)
LexToken = namedtuple('LexToken', 'type value lineno lexpos lexer')
ExtraToken = lambda t, type, value=None, lexpos=None: LexToken(type, value or t.value, t.lexer.lineno, lexpos or t.lexpos, t.lexer)
reserved = {
    '_' : 'UNDERSCORE',
}
tokens = [
    'AT',
    'BAR',
    'BEGIN_LOOKAROUND',
    'BEGIN_ORBLOCK',
    'CHAR',
    'COLON',
    'DEDENT',
    'DOT',
    'END_OF_LOOKAROUND',
    'END_OF_ORBLOCK',
    'EQUALSIGN',
    'EXCLAMARK',
    'FAIL',
    'FLAGSET',
    'GLOBALMARK',
    'GT',
    'INDENT',
    'NUMBER',
    'LBRACKET',
    'LPAREN',
    'LT',
    'MINUS',
    'NEWLINE',
    'NON',
    'OF',
    'PLUS',
    'QUESTMARK',
    'RBRACKET',
    'RPAREN',
    'SLASH',
    'STRING',
    'VARNAME',
    'WHITESPACE',
] + reserved.values()

GLOBALMARK   = '*)'
t_AT         = r'\@'
t_BAR        = r'\|'
t_DOT        = r'\.'
t_EQUALSIGN  = r'\='
t_EXCLAMARK  = r'\!'
t_GT         = r'\>'
t_LBRACKET   = r'\['
t_LPAREN     = r'\('
t_LT         = r'\<'
t_MINUS      = r'\-'
t_NUMBER     = r'\d+'
t_PLUS       = r'\+'
t_QUESTMARK  = r'\?'
t_RBRACKET   = r'\]'
t_RPAREN     = r'\)'
t_SLASH      = r'\/'
t_ignore = '' # oprex is whitespace-significant, no ignored characters


ESCAPE_SEQUENCE_RE = regexlib.compile(r'''\\
    ( .
    | N\{[^}]++\} # Unicode character name
    | U\d{8}      # 8-digit hex escapes
    | u\d{4}      # 4-digit hex escapes
    | x\d{2}      # 2-digit hex escapes
    | [0-7]{1,3}  # Octal escapes
    )''', regexlib.VERBOSE)


OVERESCAPED_RE = regexlib.compile(r'''\\\\
    ( \\\\          # Escaped backslash
    | ['"abfnrtv]   # Single-character escapes
    | N\\\{[^}]++\} # Unicode character name
    | U\d{8}        # 8-digit hex escapes
    | u\d{4}        # 4-digit hex escapes
    | x\d{2}        # 2-digit hex escapes
    | [0-7]{1,3}    # Octal escapes
    )''', regexlib.VERBOSE)


class Variable(namedtuple('Variable', 'name value lineno')):
    __slots__ = ()
    def is_builtin(self):
        return self.lineno == 0


class VariableDeclaration:
    __slots__ = ('varname lineno capture')
    def __init__(self, varname, lineno, capture):
        self.varname = varname
        self.lineno  = lineno
        self.capture = capture


class VariableLookup(namedtuple('VariableLookup', 'varname lineno optional')):
    __slots__ = ()

class NegatedLookup(namedtuple('NegatedLookup', 'varname lineno optional')):
    __slots__ = ()

class Backreference(namedtuple('Backreference', 'varname lineno optional')):
    __slots__ = ()

class CaptureCondition(namedtuple('CaptureCondition', 'varname lineno')):
    __slots__ = ()

class Quantifier(namedtuple('Quantifier', 'base modifier')):
    __slots__ = ()

class Assignment(namedtuple('Assignment', 'declarations value lineno')):
    __slots__ = ()


class Block(namedtuple('Block', 'variables starting_lineno')):
    __slots__ = ()
    def check_unused_vars(self, useds):
        for var in self.variables:
            if var.name not in useds:
                raise OprexSyntaxError(var.lineno, "'%s' is defined but not used (by its parent expression)" % var.name)


class Scope(dict):
    types = ('ROOTSCOPE', 'BLOCKSCOPE', 'FLAGSCOPE')
    ROOTSCOPE, BLOCKSCOPE, FLAGSCOPE = range(3)
    __slots__ = ('starting_lineno', 'type')
    def __init__(self, type, starting_lineno, parent_scope):
        self.starting_lineno = starting_lineno
        self.type = type
        if parent_scope:
            self.update(parent_scope)


class Flagset(unicode):
    __slots__ = ('turn_ons', 'turn_offs')
    all_flags = {}
    scopeds = {
        'dotall'     : 's',
        'fullcase'   : 'f',
        'ignorecase' : 'i',
        'multiline'  : 'm',
        'verbose'    : 'x',
        'word'       : 'w',
    }
    globals = {
        'ascii'        : 'a',
        'bestmatch'    : 'b',
        'enhancematch' : 'e',
        'locale'       : 'L',
        'reverse'      : 'r',
        'unicode'      : 'u',
        'version0'     : 'V0',
        'version1'     : 'V1',
    }
    def __new__(cls, turn_ons, turn_offs):
        if turn_offs:
            flags = turn_ons + '-' + turn_offs
        else:
            flags = turn_ons
        flagset = unicode.__new__(cls, flags)
        flagset.turn_ons = turn_ons
        flagset.turn_offs = turn_offs
        return flagset
        
Flagset.all_flags.update(Flagset.scopeds)
Flagset.all_flags.update(Flagset.globals)


class Expr:
    def __init__(self, **attribs):
        self.__dict__.update(attribs)

    def apply(self, scope):
        # return regex, references
        raise NotImplemented


class Regex(unicode):
    __slots__ = ('base_value', 'grouped', 'quantifier')
    def __new__(cls, base_value, modifier=None): # modifier can be one of: quantifier, scoped flags, or grouping
        value = base_value
        grouped = False
        quantifier = None
        if modifier:
            if modifier.startswith('(?'): # scoped flags/grouping -- without the closing paren
                value = modifier + base_value + ')' # add the closing paren
                grouped = True
            else: # modifier is quantifier
                quantifier = modifier
                value += quantifier
        expr = unicode.__new__(cls, value)
        expr.base_value = base_value
        expr.grouped = grouped
        expr.quantifier = quantifier
        return expr

    def apply(self, scope):
        return self, []


class Alternation(Regex):
    __slots__ = ('grouping_unnecessary',)
    def __new__(cls, subexpressions, is_atomic):
        alternation = Regex.__new__(cls, '|'.join(subexpressions), modifier='(?>' if is_atomic else None)
        alternation.grouping_unnecessary = is_atomic or len(subexpressions) == 1
        return alternation


class CharClass(Regex):
    __slots__ = ('is_set_op',)
    escapes = {
        '['  : '\\[',
        ']'  : '\\]',
        '^'  : '\\^',
        '-'  : '\\-',
        '\\' : '\\\\',
    }
    def __new__(cls, value, is_set_op):
        if value.startswith('[') and value.endswith(']') and value != '[ ]':
            if len(value) == 3 or ESCAPE_SEQUENCE_RE.fullmatch(value[1:-1]):
                value = value[1:-1]
        if len(value) == 1:
            value = regexlib.escape(value, special_only=True)
        value = {
            r'[^\d]' : r'\D',
            r'[^\D]' : r'\d',
            r'[^\s]' : r'\S',
            r'[^\S]' : r'\s',
            r'[^\w]' : r'\W',
            r'[^\W]' : r'\w',
            r'[^\$]' : r'[^$]',
            r'[^\.]' : r'[^.]',
            r'[^\|]' : r'[^|]',
            r'[^\?]' : r'[^?]',
            r'[^\*]' : r'[^*]',
            r'[^\+]' : r'[^+]',
            r'[^\(]' : r'[^(]',
            r'[^\)]' : r'[^)]',
            r'[^\{]' : r'[^{]',
            r'[^\}]' : r'[^}]',
            r'\-'    :  '-',
        }.get(value, value)
        charclass = Regex.__new__(cls, value)
        charclass.is_set_op = is_set_op
        return charclass
    
    def negated(self):
        if self.startswith('[^'):
            negated_value = self.replace('[^', '[', 1)
        elif self.startswith('['):
            negated_value = self.replace('[', '[^', 1)
        elif self.startswith(r'\p{'):
            negated_value = self.replace(r'\p{', r'\P{', 1)
        elif self.startswith(r'\P{'):
            negated_value = self.replace(r'\P{', r'\p{', 1)
        elif self == '-':
            negated_value = r'[^\-]'
        else:
            negated_value = '[^%s]' % self
        return CharClass(value=negated_value, is_set_op=self.is_set_op)


class CCItem(namedtuple('CCItem', 'source type value')):
    __slots__ = ()
    op_types = ('unary', 'binary')
    UNARY_OP, BINARY_OP = range(2)

    @staticmethod
    def token(t, type, value):
        source = t.value
        if type not in ('include', 'op'): # testing these types requires parser context
            try:
                regexlib.compile('[' + value + ']')
            except regexlib.error as e:
                raise OprexSyntaxError(t.lineno, 
                    '%s compiles to %s which is rejected by the regex engine with error message: %s' % (source, value, e.message))
        t.type = 'CHAR'
        t.value = CCItem(source, type, value)
        return t


Builtin   = lambda name, value, modifier=None: Variable(name, Regex(value, modifier), lineno=0)
BuiltinCC = lambda name, value:                Variable(name, CharClass(value, is_set_op=False), lineno=0)
BUILTINS  = [
    BuiltinCC('alpha',         r'[a-zA-Z]'),
    BuiltinCC('upper',         r'[A-Z]'),
    BuiltinCC('lower',         r'[a-z]'),
    BuiltinCC('alnum',         r'[a-zA-Z0-9]'),
    BuiltinCC('padchar',       r'[ \t]'),
    BuiltinCC('backslash',     r'\\'),
    BuiltinCC('tab',           r'\t'),
    BuiltinCC('digit',         r'\d'),
    BuiltinCC('whitechar',     r'\s'),
    BuiltinCC('wordchar',      r'\w'),
    Builtin('BOW',             r'\m'),
    Builtin('EOW',             r'\M'),
    Builtin('WOB',             r'\b'),
    Builtin('non-WOB',         r'\B'),
    Builtin('BOS',             r'\A'),
    Builtin('EOS',             r'\Z'),
    Builtin('uany',            r'\X'),
    Builtin('FAIL!',           r'', modifier='(?!'),
]
FLAG_DEPENDENT_BUILTINS = dict(
    m = { # MULTILINE
        True  : [
            Builtin('BOL', '^'),
            Builtin('EOL', '$'),
        ],
        False : [
            Builtin('BOL', '^', modifier='(?m:'),
            Builtin('EOL', '$', modifier='(?m:'),
        ],
    },
    s = { # DOTALL
        True  : [
            Builtin('any',          '.'),
            Builtin('non-linechar', '.', modifier='(?-s:'),
        ],
        False : [
            Builtin('any',          '.', modifier='(?s:'),
            Builtin('non-linechar', '.'),
        ],
    },
    w = { # WORD
        True  : [
            BuiltinCC('linechar', r'[\r\n\x0B\x0C]'),
        ],
        False : [
            BuiltinCC('linechar', r'\n'),
        ],
    },
    x = { # VERBOSE
        True  : [
            BuiltinCC('space',  '[ ]'),
        ],
        False : [
            BuiltinCC('space',  ' '),
        ],
    },
)
DEFAULT_FLAGS = 'w'
for flag in FLAG_DEPENDENT_BUILTINS:
    for var in FLAG_DEPENDENT_BUILTINS[flag][flag in DEFAULT_FLAGS]:
        BUILTINS.append(var)

def flags_redef_builtins(flags, flag_dependent_builtins, scope):
    for flag in FLAG_DEPENDENT_BUILTINS:
        if flag in flags:
            for var in flag_dependent_builtins[flag][flag in flags.turn_ons]:
                scope[var.name] = var


def t_COLON(t):
    r''':'''
    t.lexer.start_mode('CHARCLASS')
    return t


def t_CHARCLASS_DOT(t):
    r'''\.'''
    return t


def t_CHARCLASS_op(t):
    '''not:|not|and'''
    return CCItem.token(t, 'op', {
        'not:' : '^',
        'not'  : '--',
        'and'  : '&&',
    }[t.value])


def t_CHARCLASS_varname(t):
    r'''\w{2,}'''
    return CCItem.token(t, 'include', VariableLookup(t.value, t.lineno, optional=False))


def t_CHARCLASS_include(t):
    r'''\+\w+'''
    return CCItem.token(t, 'include', VariableLookup(t.value[1:], t.lineno, optional=False))


def t_CHARCLASS_prop(t):
    r'''/\w+(=\w+)?'''
    return CCItem.token(t, 'prop', '\p{%s}' % t.value[1:])


def t_CHARCLASS_name(t):
    r''':[\w-]+'''
    return CCItem.token(t, 'name', '\N{%s}' % t.value[1:].replace('_', ' '))


def t_CHARCLASS_escape(t):
    r'''(?x)\\
    ( [\\abfnrtv]    # Single-character escapes
    | N\{[^}]+\}     # Unicode character name
    | U[a-fA-F\d]{8} # 8-digit hex escapes
    | u[a-fA-F\d]{4} # 4-digit hex escapes
    | x[a-fA-F\d]{2} # 2-digit hex escapes 
    | [0-7]{1,3}     # Octal escapes
    )(?=[\s.])'''
    return CCItem.token(t, 'escape', t.value)


def t_CHARCLASS_bad_escape(t):
    r'''\\\S+'''
    raise OprexSyntaxError(t.lineno, 'Bad escape sequence: ' + t.value)


def t_CHARCLASS_literal(t):
    r'''\S'''
    return CCItem.token(t, 'literal', CharClass.escapes.get(t.value, t.value))


def t_FLAGSET(t):
    r'\([- \t\w]+\)'
    flags = t.value[1:-1] # exclude the surrounding ( )
    flags = flags.split(' ') # will contain empty strings in case of consecutive spaces, so...
    flags = filter(lambda flag: flag, flags) # ...exclude empty strings
    turn_ons = ''
    turn_offs = ''
    for flag in flags:
        try:
            if flag.startswith('-'):
                turn_offs += Flagset.all_flags[flag[1:]]
            else:
                turn_ons += Flagset.all_flags[flag]
        except KeyError:
            raise OprexSyntaxError(t.lineno, "Unknown flag '%s'. Supported flags are: %s" % (flag, ' '.join(sorted(Flagset.all_flags.keys()))))

    flags = Flagset(turn_ons, turn_offs)
    try:
        test = '(?%s)' % flags
        if 'V' in flags:
            regexlib.compile(test)
        else:
            regexlib.compile('(?V1)' + test)
    except Exception as e:
        raise OprexSyntaxError(t.lineno, '%s compiles to %s which is rejected by the regex engine with error message: %s' % 
            (t.value, test, str(e.message)))
    else:
        t.type = 'LPAREN'
        t.extra_tokens = [ExtraToken(t, 'FLAGSET', value=flags), ExtraToken(t, 'RPAREN')]
    return t


def t_BEGIN_LOOKAROUND(t):
    r'''<@>'''
    if t.lexer.mode != 'INITIAL':
        raise OprexSyntaxError(t.lineno, t.lexer.mode + ' cannot contain LOOKAROUND')
    t.lexer.start_mode('LOOKAROUND')
    t.lexer.barpos = None
    t.lexer.lookaround_parent_indent_depth = t.lexer.indent_stack[-1]
    return t


def t_BEGIN_ORBLOCK(t):
    r'''(<<\|)|(@\|)'''
    if t.lexer.mode != 'INITIAL':
        raise OprexSyntaxError(t.lineno, t.lexer.mode + ' cannot contain ORBLOCK')
    t.lexer.start_mode('ORBLOCK')
    t.lexer.barpos = find_column(t) + len(t.value) - 1
    return t


def restore_overescaped(match):
    match = match.group(1)
    if match.startswith('N'):
        charname = match[3:-2]
        unicodedata.lookup(charname) # raise KeyError if undefined character name
        return '\\N{' + charname + '}'
    else:
        return {
            'a'    : '\\x07',
            'b'    : '\\x08',
            'f'    : '\\x0C',
            'v'    : '\\x0B',
        }.get(match, '\\' + match)


def t_STRING(t):
    r'''("(\\.|[^"\\])*")|('(\\.|[^'\\])*')''' # single- or double-quoted string, with escape-quote support
    value = t.value[1:-1] # remove the surrounding quotes
    value = value.replace('\\"', '"').replace("\\'", "'") # apply escaped quotes
    value = regexlib.escape(value, special_only=True)
    try:
        t.value = OVERESCAPED_RE.sub(restore_overescaped, value)
    except KeyError as e:
        raise OprexSyntaxError(t.lineno, e.message)
    else:
        return t


## NON and FAIL must be before VARNAME otherwise VARNAME will be produced instead

def t_NON(t):
    'non-'
    return t

def t_FAIL(t):
    'FAIL!'
    return t

def t_VARNAME(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    t.type = reserved.get(t.value, 'VARNAME')
    return t


# Rules that contain space/tab should be written in function form and be put 
# before the t_linemark rule to make PLY calls them first.
# Otherwise t_linemark will turn the spaces/tabs into WHITESPACE token.


def t_INITIAL_ORBLOCK_OF(t):
    r'[ \t]+of(?=[ \t:])(?![ \t]+(--|\n))' # without this, WHITESPACE VARNAME will be produced instead, requiring making "of" a reserved keyword
    t.type = 'WHITESPACE'
    t.extra_tokens = [ExtraToken(t, 'OF', lexpos=t.lexpos + t.value.index('of'))]
    return t


def t_ANY_comments_whitespace(t):
    r'''(?mx)
    (
        [ \t\n]+
        (--.*)?  # comments
    )+
    (
        \*\)     # globalmark
        [ \t]*
    )*
    '''
    lines = t.value.split('\n')
    indentation = lines[-1]
    is_finale = endpos(t) == len(t.lexer.lexdata)
    if is_finale: # effectively no indentation
        indentation = ''

    has_globalmark = GLOBALMARK in indentation
    num_newlines = len(lines) - 1
    has_empty_line = num_newlines > 1
    t.lexer.lineno += num_newlines

    t.extra_tokens = []
    def add_extras():
        if add_extras.END_OF_ORBLOCK:
            t.extra_tokens.append(ExtraToken(t, 'END_OF_ORBLOCK'))
        if add_extras.END_OF_LOOKAROUND:
            t.extra_tokens.append(ExtraToken(t, 'END_OF_LOOKAROUND'))
        if add_extras.INDENT:
            t.extra_tokens.append(ExtraToken(t, 'INDENT'))
        for _ in range(add_extras.DEDENT):
            t.extra_tokens.append(ExtraToken(t, 'DEDENT'))
        if add_extras.GLOBALMARK:
            t.extra_tokens.append(ExtraToken(t, 'GLOBALMARK', GLOBALMARK))

    add_extras.END_OF_ORBLOCK = False
    add_extras.END_OF_LOOKAROUND = False
    add_extras.INDENT = False
    add_extras.DEDENT = 0
    add_extras.GLOBALMARK = False

    if num_newlines == 0:
        if GLOBALMARK in t.value: # globalmark must be put at the beginning of a line, i.e. requires newline
            raise OprexSyntaxError(t.lexer.lineno, 'Syntax error: ' + t.lexer.source_lines[t.lexer.lineno-1])
        else:
            t.type = 'WHITESPACE'
            return t

    # else, num_newlines > 0
    t.type = 'NEWLINE'
    if t.lexer.mode == 'CHARCLASS': # NEWLINE ends the charclass-mode
        t.lexer.end_mode('CHARCLASS')

    if is_finale or has_empty_line: # empty line ends ORBLOCK/LOOKAROUND
        if t.lexer.mode == 'ORBLOCK':
            add_extras.END_OF_ORBLOCK = True
            t.lexer.end_mode('ORBLOCK')
        elif t.lexer.mode == 'LOOKAROUND':
            add_extras.END_OF_LOOKAROUND = True
            t.lexer.end_mode('LOOKAROUND')

    def check_indentation_char():
        if indentation == GLOBALMARK:
            raise OprexSyntaxError(t.lexer.lineno, 'Syntax error: ' + indentation)

        indent_using_space = ' ' in indentation
        indent_using_tab = '\t' in indentation
        if indent_using_space and indent_using_tab:
            raise OprexSyntaxError(t.lexer.lineno, 'Cannot mix space and tab for indentation')

        indentchar = ' ' if indent_using_space else '\t'
        try: # all indentations must use the same character
            if indentchar != t.lexer.indentchar:
                raise OprexSyntaxError(t.lexer.lineno, 'Inconsistent indentation character')
        except AttributeError: # this is the first indent encountered, record whether it uses space or tab -- further indents must use the same character
            t.lexer.indentchar = indentchar

    def strip_globalmark():
        if indentation.count(GLOBALMARK) > 1:
            raise OprexSyntaxError(t.lexer.lineno, 'Syntax error: ' + indentation)
        if not indentation.startswith(GLOBALMARK):
            raise OprexSyntaxError(t.lexer.lineno, "The GLOBALMARK %s must be put at the line's beginning" % GLOBALMARK)
        return indentation.replace(GLOBALMARK, '  ' if t.lexer.indentchar == ' ' else '')

    def produce_INDENT_DEDENT():
        indentlen = len(indentation)
        prev = t.lexer.indent_stack[-1]
        if indentlen == prev: # no change in indentation depth
            return

        # else, there's indentation depth change
        if indentlen > prev: # deeper indentation, start of a new scope
            add_extras.INDENT = True
            t.lexer.indent_stack.append(indentlen)
            return

        if indentlen < prev: # end of one or more scopes
            while indentlen < prev: # close all scopes having deeper indentation
                add_extras.DEDENT += 1
                t.lexer.indent_stack.pop()
                prev = t.lexer.indent_stack[-1]
            if indentlen != prev: # the indentation tries to return to a nonexistent level
                raise OprexSyntaxError(t.lexer.lineno, 'Indentation error')

    if indentation:
        check_indentation_char()
        if has_globalmark:
            add_extras.GLOBALMARK = True
            indentation = strip_globalmark()

    if t.lexer.mode == 'INITIAL':
        produce_INDENT_DEDENT()

    add_extras()
    return t


def t_ANY_error(t):
    raise OprexSyntaxError(t.lineno, 'Syntax error at or near: ' + t.value.split('\n')[0])


def endpos(t):
    return t.lexpos + len(t.value)
    

def p_oprex(t):
    '''oprex : 
             | WHITESPACE
             | NEWLINE
             | NEWLINE        root_expression
             | NEWLINE INDENT root_expression DEDENT'''
    if len(t) == 3:
        flags, expression = t[2]
    elif len(t) == 5:
        flags, expression = t[3]
    else:
        flags = expression = ''

    for flag in DEFAULT_FLAGS:
        if flag not in flags:
            flags = flag + flags

    if 'V' not in flags: # use V1 by default
        flags = 'V1' + flags # put at the front so it can easily be trimmed-out if unwanted

    t[0] = '(?%s)%s' % (flags, expression)


def p_root_expression(t):
    '''root_expression : global_flags
                       | expression
                       | global_flags expression'''
    if len(t) == 3:
        flags = t[1]
        expression = t[2]
    elif len(t) == 2:
        if isinstance(t[1], Regex):
            expression = t[1]
            flags = ''
        elif isinstance(t[1], Flagset):
            flags = t[1]
            expression = ''

    t[0] = flags, expression


def p_global_flags(t):
    '''global_flags : LPAREN FLAGSET RPAREN NEWLINE'''
    flags = t[2]
    root_scope = t.lexer.scopes[0]
    if 'u' in flags.turn_ons: 
        root_scope.update(
            alpha    = Variable('alpha',    CharClass(r'\p{Alphabetic}',                 is_set_op=False), lineno=0),
            upper    = Variable('upper',    CharClass(r'\p{Uppercase}',                  is_set_op=False), lineno=0),
            lower    = Variable('lower',    CharClass(r'\p{Lowercase}',                  is_set_op=False), lineno=0),
            alnum    = Variable('alnum',    CharClass(r'\p{Alphanumeric}',               is_set_op=False), lineno=0),
            linechar = Variable('linechar', CharClass(r'[\r\n\x0B\x0C\x85\u2028\u2029]', is_set_op=False), lineno=0),
        )
        t.lexer.flag_dependent_builtins = FLAG_DEPENDENT_BUILTINS.copy()
        t.lexer.flag_dependent_builtins['w'] = t.lexer.flag_dependent_builtins['w'].copy()
        t.lexer.flag_dependent_builtins['w'][True] = [
            root_scope['linechar']
        ]
    flags_redef_builtins(
        flags = flags, 
        flag_dependent_builtins = t.lexer.flag_dependent_builtins, 
        scope = root_scope,
    )
    t[0] = flags


def p_expression(t):
    '''expression : expr optional_subblock'''
    expr = t[1]
    current_scope = t.lexer.scopes[-1]
    expression, references = expr.apply(current_scope)
    reffed_varnames = set()
    for ref in references:
        if isinstance(ref, Backreference):
            t.lexer.references.append(ref)
        else:
            reffed_varnames.add(ref.varname)

    optional_subblock_cleanup(t.lexer, t[2], reffed_varnames)
    t[0] = expression


def p_expr(t):
    '''expr : string_expr
            | lookup_expr
            | orblock_expr
            | flagged_expr
            | lookaround_expr
            | quantified_expr
            | numrange_shortcut'''
    t[0] = t[1]


def p_string_expr(t):
    '''string_expr :       STRING       NEWLINE
                   |       STRING str_b NEWLINE
                   | str_b STRING       NEWLINE
                   | str_b STRING str_b NEWLINE'''
    t[0] = Regex(''.join(t[1:-1]))


def p_str_b(t):
    '''str_b : DOT
             | UNDERSCORE'''
    t[0] = {
        '.'  : '\\b',
        '_'  : '\\B',
    }[t[1]]
    
    
def p_numrange_shortcut(t):
    '''numrange_shortcut : STRING DOT DOT STRING NEWLINE'''
    low = t[1]
    high = t[4]
            
    # check bad format
    for fmt in (low, high):
        if not regexlib.fullmatch(r'o*\d+', fmt):
            raise OprexSyntaxError(t.lineno(0), 'Bad number-range format: ' + fmt)
        if regexlib.match(r'o+0+\d+', fmt):
            raise OprexSyntaxError(t.lineno(0), 'Bad number-range format: %s (ambiguous leading-zero spec)' % fmt)
    
    o_led     = lambda str: str.startswith('o')
    zero_led  = lambda str: str.startswith('0') and str != '0'
    all_zero  = lambda str: all(digit == '0' for digit in str)
    all_nine  = lambda str: all(digit == '9' for digit in str)
    is_powten = lambda str: all(digit == '0' for digit in str[1:]) and str[0] == '1'
    
    # using zero-led/o-led format? len(low) must be == len(high)
    if zero_led(low) or zero_led(high) or o_led(low) or o_led(high):
        if len(low) != len(high):
            raise OprexSyntaxError(t.lineno(0), 
                "Bad number-range format: '%s'..'%s' (lengths must be the same if using leading-zero/o format)" % (low, high))
        
    # zero-led/o-led cannot be mixed
    if zero_led(low) and o_led(high) or o_led(low) and zero_led(high):
        raise OprexSyntaxError(t.lineno(0),
            "Bad number-range format: '%s'..'%s' (one cannot be o-led while the other is zero-led)" % (low, high))
        
    # if low > high, swap
    if int(low.lstrip('o')) > int(high.lstrip('o')):
        low, high = high, low
    
    # extract out the o's
    num_high_o = high.count('o')
    num_low_o = low.count('o')
    o_led = num_low_o > 0
    if o_led:
        o_maxdigits = len(high)
    high = high.lstrip('o')
    low = low.lstrip('o')
                
    def gen(low, high):
        len_low  = len(low)
        len_high = len(high)
        low_magnitude  = len_low - 1
        high_magnitude = len_high - 1
        
        def gen_opt_zeros(filled_length):
            if (not o_led
                or len_low == len_high
                or filled_length == o_maxdigits):
                return ''
            return '0{,%d}+' % (o_maxdigits - filled_length)
        
        def gen_all(bounds):
            subsets = []
            while bounds:
                subhigh = bounds.pop()
                sublow = bounds.pop()
                if int(sublow) <= int(subhigh):
                    subsets.append(gen_opt_zeros(len(sublow)) + gen(sublow, subhigh))
            return '(?>%s)' % '|'.join(subsets)
            
        if low == high:
            return low
        if len_low == len_high:
            if len_low == 1:
                return '[%s-%s]' % (low, high)
            if low[0] == high[0]:
                return low[0] + gen(low[1:], high[1:])
            if all_zero(low) and all_nine(high):
                return r'\d{%d}' % len_low
            if all_zero(low[1:]) and all_nine(high[1:]):
                return r'[%s-%s]\d{%d}' % (low[0], high[0], low_magnitude)
            
            bounds = []
            bounds.append(low)
            if not all_zero(low[1:]):
                bounds.append(low[0] + '9' * low_magnitude)
                bounds.append(str(int(low[0]) + 1) + '0' * low_magnitude)
            if not all_nine(high[1:]):
                bounds.append(str(int(high[0]) - 1) + '9' * high_magnitude)
                bounds.append(high[0] + '0' * high_magnitude)
            bounds.append(high)
            return gen_all(bounds)
        
        else:
            assert(len_low < len_high)
            if not o_led:
                if all_nine(high):
                    if is_powten(low):
                        return r'[1-9]\d{%d,%d}+' % (low_magnitude, high_magnitude)
                    if low == '0':
                        return '(?>%s)' % (gen('1', high) + '|0')
                    
            bounds = []
            bounds.append(low)
            if not is_powten(low):
                bounds.append('9' * len_low)
                bounds.append('1' + '0' * len_low)
            if o_led:
                for i in range(len_low, len_high):
                    bounds.append('9' * i)
                    bounds.append('1' + '0' * i)
            if not all_nine(high):
                bounds.append('9' * high_magnitude)
                bounds.append('1' + '0' * high_magnitude)
            bounds.append(high)
            return gen_all(bounds)
    
    value = gen(low, high)
    if num_high_o == num_low_o:
        opt_zeros = '0{,%d}' % num_high_o
        value = opt_zeros + value
    
    t[0] = Regex(value
        .replace('[0-9]', r'\d')
        .replace('{0,1}', '?')
        .replace('{,1}' , '?')
        .replace('{1}'  , '')
    )


class QuantifiedExpr(Expr):
    def apply(self, scope):
        regex, refs = self.quantified.apply(scope)
        regex = quantify(regex, quantifier=self.quantifier)
        return regex, refs


def p_quantified_expr(t):
    '''quantified_expr : quantifier WHITESPACE expr
                       | quantifier COLON      charclass'''
    t[0] = QuantifiedExpr(quantifier=t[1], quantified=t[3])


def p_quantifier(t):
    '''quantifier : repeat_N_times
                  | repeat_range'''
    quant = t[1]
    base = {
        '{1}'   : '',
        '{,}'   : '*',
        '{0,}'  : '*',
        '{1,}'  : '+',
        '{,1}'  : '?',
        '{0,1}' : '?',
    }.get(quant.base, quant.base)
    modifier = quant.modifier if base else ''
    t[0] = base + modifier


def p_repeat_N_times(t):
    '''repeat_N_times : AT NUMBER of
                      |    NUMBER of'''
    number = t[1] if t[1] != '@' else t[2]
    t[0] = Quantifier(base=('{%s}' % number), modifier='')


def p_repeat_range(t):
    '''repeat_range : AT numrange of
                    |    numrange backtrack MINUS of
                    |    NUMBER   backtrack PLUS  DOT DOT of
                    |    NUMBER   backtrack PLUS  DOT DOT NUMBER of'''
    possessive = len(t) == 4 # the first form above
    greedy     = len(t) == 5 # the second form
    lazy       = not possessive and not greedy # third & fourth forms

    if possessive:
        min, max = t[2]
    elif greedy:
        min, max = t[1]
    else: # lazy
        min = t[1]
        max = t[6] if len(t) == 8 else ''

    if not min:
        min = '0'
    if max and int(max) <= int(min):
        raise OprexSyntaxError(t.lineno(0), 'Repeat max must be > min')

    t[0] = Quantifier(
        base='{%s,%s}' % ('' if min == '0' else min, max),
        modifier='+' if possessive else '?' if lazy else ''
    )


def p_backtrack(t):
    '''backtrack : WHITESPACE LT LT'''


def p_of(t):
    '''of : WHITESPACE OF'''


def p_numrange(t):
    '''numrange : NUMBER DOT DOT
                | NUMBER DOT DOT NUMBER'''
    min = t[1]
    try:
        max = t[4]
    except IndexError:
        max = ''
    t[0] = min, max


def quantify(expr, quantifier):
    if quantifier == '{0}' or expr == '':
        return Regex('')
    if quantifier == '{1}' or quantifier == '':
        return expr

    def merge_quantifiers():
        try:
            return {               
                 '? of +'  : '*' ,  ## The purpose of this is so we can write x* as (x+)? e.g.
                '?+ of ++' : '*+',  ##     digits?
                '?? of +?' : '*?',  ##         digits = 1.. of digit
                 '? of ++' : '*+',  ## without making the regex output suboptimal
                 '? of +?' : '*?',
            }[quantifier + ' of ' + expr.quantifier]
        except KeyError: # not a "? of +" operation, try merge repeats e.g.
            n1 = int(expr.quantifier.strip('{').strip('}')) # colorhex = 3 of byte
            n2 = int(     quantifier.strip('{').strip('}')) #     byte = 2 of hex
            return '{%d}' % (n1 * n2)                       # --> optimize "hex{2}{3}" into "hex{6}"

    def strip_old_quantifier():
        return expr.base_value

    def put_in_group():
        unneeded = (
            expr.grouped # already
            or len(expr) == 1
            or isinstance(expr, CharClass)
            or ESCAPE_SEQUENCE_RE.fullmatch(expr)
        )
        if unneeded:
            return expr # unchanged
        else:
            return '(?:%s)' % expr

    try:
        return Regex(strip_old_quantifier(), modifier=merge_quantifiers())
    except:
        return Regex(put_in_group(), modifier=quantifier)


class FlaggedExpr(Expr):
    def apply(self, scope):
        flagscope = Scope(                   # this scope is created manually
            type = Scope.FLAGSCOPE,          # i.e. not using lexer.begin_a_scope()
            starting_lineno = self.flagline, # i.e. not appended into lexer.scopes
            parent_scope = scope,            # so, no cleanup/lexer.end_a_scope() needed
        )
        flags_redef_builtins(                                                                      
            flags = self.flags, 
            flag_dependent_builtins = self.flag_dependent_builtins, 
            scope = flagscope,
        )
        regex, references = self.expr.apply(flagscope)
        regex = Regex(regex, modifier='(?%s:' % self.flags)
        return regex, references


def p_flagged_expr(t):
    '''flagged_expr : scoped_flags expr'''
    t[0] = FlaggedExpr(
        expr = t[2],
        flags = t[1], 
        flagline = t.lineno(1),
        flag_dependent_builtins = t.lexer.flag_dependent_builtins,
    )


def p_scoped_flags(t):
    '''scoped_flags : LPAREN FLAGSET RPAREN WHITESPACE'''
    flags = t[2]
    for flag_name, global_flag in Flagset.globals.iteritems():
        if global_flag in flags.turn_ons:
            raise OprexSyntaxError(t.lineno(2), "'%s' is a global flag and must be set using global flag syntax, not scoped." % flag_name)
    t[0] = flags


class OrBlockExpr(Expr):
    def apply(self, scope):
        subexpressions = []
        references = []
        for or_item in self.items:
            expression, refs = or_item.apply(scope)
            subexpressions.append(expression)
            references.extend(refs)
        return Alternation(subexpressions, self.is_atomic), references


def p_orblock_expr(t):
    '''orblock_expr : BEGIN_ORBLOCK NEWLINE oritems END_OF_ORBLOCK'''
    t[0] = OrBlockExpr(
        is_atomic = t[1].startswith('@'),
        items = t[3],
    )


OrItems = deque


def p_oritems(t):
    '''oritems : oritem
               | oritem oritems'''
    try:
        oritems = t[2]
    except IndexError:
        oritems = OrItems()
        
    if isinstance(t[1], ConditionalExpr):
        try:
            t[1].else_expr = oritems.popleft()
        except IndexError:
            raise OprexSyntaxError(t.lineno(1), 'The last branch of OR-block must not be conditional')
    
    oritems.appendleft(t[1])    
    t[0] = oritems
    

def p_oritem(t):
    '''oritem : or condition WHITESPACE QUESTMARK WHITESPACE expr
              | or condition WHITESPACE QUESTMARK NEWLINE
              | or expr
              | or NEWLINE''' # --> allow the alternation to match empty string
    t_last = t[len(t)-1]
    expr = t_last if isinstance(t_last, Expr) else Regex('')
    if len(t) > 3:
        t[0] = ConditionalExpr(condition=t[2], then_expr=expr)
    else:
        t[0] = expr


class ConditionalExpr(Expr):
    def apply(self, scope):
        then_regex, then_refs = self.then_expr.apply(scope)
        else_regex, else_refs = self.else_expr.apply(scope)
        refs = []
        refs.extend(then_refs)
        refs.extend(else_refs)
        value = '(%s)%s' % (self.condition.varname, then_regex)
        if else_regex:
            value += '|' + else_regex
        return Regex(value, modifier='(?'), refs


def p_condition(t):
    '''condition : LBRACKET VARNAME RBRACKET'''
    t[0] = CaptureCondition(varname=t[2], lineno=t.lineno(2))
    t.lexer.references.append(t[0])
    
    
def p_or(t):
    '''or : BAR'''
    barpos = find_column(t, 1)
    if barpos != t.lexer.barpos:
        raise OprexSyntaxError(t.lineno(1), 'Misaligned OR')


class LookaroundExpr(Expr):
    def apply(self, scope):
        subexpressions = []
        references = []

        for lookitem in self.items:
            expression, refs = lookitem.expr.apply(scope)
            subexpressions.append(Regex(expression, modifier=lookitem.type))
            references.extend(refs)

        regex = Regex(''.join(subexpressions))
        return regex, references


def p_lookaround_expr(t):
    '''lookaround_expr : BEGIN_LOOKAROUND NEWLINE lookitems END_OF_LOOKAROUND'''
    t[0] = LookaroundExpr(items=t[3])


LookItems = deque


def p_lookitems(t):
    '''lookitems : lookitem NEWLINE
                 | lookitem NEWLINE lookitems'''
    try:
        t[0] = t[3]
    except IndexError:
        t[0] = LookItems()
    t[0].appendleft(LookItem(*t[1]))


class LookItem(namedtuple('LookItem', 'type expr')):   
    __slots__ = ()


def p_lookitem(t):
    '''lookitem : BAR           lookup GT
                | BAR EXCLAMARK lookup GT
                | LT            lookup BAR
                | LT  EXCLAMARK lookup BAR
                | BAR           lookup BAR'''
    last = len(t)-1
    lookup_expr = t[len(t)-2]
    is_lookahead = t[last] == '>'
    is_lookbehind = t[1] == '<'
    is_negative = t[2] == '!'

    def check_alignment():
        def check(index):
            barpos = find_column(t, index)
            if barpos != t.lexer.barpos:
                raise OprexSyntaxError(t.lineno(0), 'Misaligned |')

        if t.lexer.barpos is None: # the lookaround just started, this is the first item
            t.lexer.barpos = find_column(t, last if t[last] == '|' else 1)
        else:
            if is_lookahead:
                check(1)
            elif is_lookbehind:
                check(last)
            else:
                check(1)
                t.lexer.barpos = find_column(t, last)

    def check_indentation():
        indent_depth = find_column(t, 1)
        if indent_depth <= t.lexer.lookaround_parent_indent_depth: # might look confusing
            raise OprexSyntaxError(t.lineno(1), 'needs deeper indentation')

    check_alignment()
    check_indentation()

    if is_lookahead:
        if is_negative:
            t[0] = '(?!', lookup_expr
        else:
            t[0] = '(?=', lookup_expr
    elif is_lookbehind:
        if is_negative:
            t[0] = '(?<!', lookup_expr
        else:
            t[0] = '(?<=', lookup_expr
    else: # the base expr
        t[0] = '', lookup_expr


class LookupExpr(Expr):
    def apply(self, scope):
        is_single_lookup = len(self.items) == 1

        def resolve(lookup):
            def var_lookup():
                if lookup.varname in scope:
                    return scope[lookup.varname].value
                elif lookup.varname in self.ongoing_declarations:
                    self.ongoing_declarations[lookup.varname].capture = True
                    return Regex('(?&%s)%s' % (lookup.varname, lookup.optional)) 
                else:
                    raise OprexSyntaxError(lookup.lineno, "'%s' is not defined" % lookup.varname)

            def negated_lookup():
                try:
                    return scope['non-' + lookup.varname].value
                except KeyError:
                    value = var_lookup()
                if isinstance(value, CharClass):
                    return value.negated()
                else:
                    raise OprexSyntaxError(lookup.lineno, "'non-%s': '%s' is not a character-class" % (lookup.varname, lookup.varname))

            if isinstance(lookup, Backreference): 
                return Regex('(?P=%s)%s' % (lookup.varname, lookup.optional))
            elif isinstance(lookup, NegatedLookup):
                value = negated_lookup()
            elif isinstance(lookup, VariableLookup):
                value = var_lookup()

            if lookup.optional:
                return quantify(value, quantifier=lookup.optional)
            elif isinstance(value, Alternation) and not value.grouping_unnecessary and not is_single_lookup:
                return Regex(value, modifier='(?:')
            else:
                return value

        if is_single_lookup:
            regex = resolve(self.items[0])
        else:
            regex = Regex(''.join(map(resolve, self.items)))
        if self.atomize:
            regex = Regex(regex, modifier='(?>')
        return regex, self.items


def p_lookup_expr(t):
    '''lookup_expr : lookup NEWLINE'''
    t[0] = t[1]


def p_lookup(t):
    '''lookup :             lookup_item
              | chain_begin lookup_chain chain_end'''
    if len(t) == 2:
        items = [t[1]]
        atomize = False
    else:
        atomize = t[1].startswith('@')
        items = t[2]

        def sugar_for(varname):
            return VariableLookup(varname, t.lineno(0), optional=False)

        if t[1].endswith('//'):
            items.appendleft(sugar_for('BOL'))
        elif t[1].endswith('./'):
            items.appendleft(sugar_for('BOS'))

        if t[3] == '/':
            items.append(sugar_for('EOL'))
        elif t[3] == '.':
            items.append(sugar_for('EOS'))

    t[0] = LookupExpr(items=items, atomize=atomize, ongoing_declarations=t.lexer.ongoing_declarations)


def p_chain_begin(t):
    '''chain_begin : AT SLASH SLASH
                   | AT  DOT  SLASH
                   | AT       SLASH
                   |    SLASH SLASH
                   |     DOT  SLASH
                   |          SLASH'''
    t[0] = ''.join(t[1:])


def p_chain_end(t):
    '''chain_end : SLASH
                 | DOT
                 | '''
    try:
        t[0] = t[1]
    except IndexError:
        t[0] = ''


LookupChain = deque


def p_lookup_chain(t):
    '''lookup_chain : lookup_item SLASH
                    | lookup_item SLASH lookup_chain'''
    try:
        t[0] = t[3]
    except IndexError:
        t[0] = LookupChain()
    t[0].appendleft(t[1])


def p_lookup_item(t):
    '''lookup_item : lookup_type
                   | lookup_type QUESTMARK'''
    LookupClass, varname = t[1]
    has_questmark = len(t) == 3
    t[0] = LookupClass(varname, t.lineno(1), optional='?' if has_questmark else '')


def p_lookup_type(t):
    '''lookup_type : variable_lookup
                   | negated_lookup
                   | backreference'''
    t[0] = t[1]


def p_variable_lookup(t):
    '''variable_lookup : VARNAME
                       | FAIL'''
    t[0] = VariableLookup, t[1]


def p_negated_lookup(t):
    '''negated_lookup : NON VARNAME'''
    t[0] = NegatedLookup, t[2]


def p_backreference(t):
    '''backreference : EQUALSIGN VARNAME'''
    t[0] = Backreference, t[2]


class CharClassExpr(Expr):
    def apply(self, scope):
        items = self.items

        def check_op(op, index):
            is_first = index == 0
            is_last = index == len(items)-1
            prefix = is_first and not is_last
            infix = not is_first and not is_last

            op_type, valid_placement = {
                'not:': (CCItem.UNARY_OP, prefix),
                'not' : (CCItem.BINARY_OP, infix),
                'and' : (CCItem.BINARY_OP, infix),
            }[op.source]

            if not valid_placement:
                raise OprexSyntaxError(self.lineno, "Invalid use of %s '%s' operator" % (CCItem.op_types[op_type], op.source))
            
            if op_type == CCItem.BINARY_OP: # binary ops require the previous item to be non-op
                prev_item = items[index-1]
                if prev_item.type == 'op':
                    raise OprexSyntaxError(self.lineno,  "Bad set operation '%s %s'" % (prev_item.source, op.source))              

        includes = []
        has_range = False
        has_set_op = False
        for index, item in enumerate(items):
            if item.type == 'include':
                includes.append(item.value)
            elif item.type == 'op':
                check_op(item, index)
                has_set_op = True
            elif item.type == 'range':
                has_range = True

        def lookup(varname):
            try:
                var = scope[varname]
            except KeyError as e:
                raise OprexSyntaxError(self.lineno, "Cannot include '%s': not defined" % e.message)
            if not isinstance(var.value, CharClass):
                raise OprexSyntaxError(self.lineno, "Cannot include '%s': not a character class" % varname)
            else:
                return var.value

        def value_or_lookup(item):
            value = item.value
            if isinstance(value, VariableLookup):
                value = lookup(value.varname)
                if value.startswith('[') and not value.is_set_op: # remove nested [] unless it's set-operation
                    value = value[1:-1]
                elif value == '-': # inside character class, dash needs to be escaped
                    value = r'\-'
                elif len(value) == 2 and value[0] == '\\' and value[1] in '$.|?*+(){}': # remove unnecessary escape
                    value = value[1]
            return value

        if len(items) == 1 and items[0].type == 'include': # simple aliasing
            regex = lookup(items[0].value.varname)
        elif len(items) == 2 and items[0].source == 'not:' and items[1].type == 'include': # simple negation
            regex = lookup(items[1].value.varname).negated()
        else:
            value = ''.join(map(value_or_lookup, items))
            if len(items) == 2 and value.startswith(r'^\p{'): # convert ^\p{something} to \P{something}
                value = value.replace(r'^\p{', r'\P{', 1)
            elif len(items) > 1 or has_range:
                value = '[' + value + ']'
            regex = CharClass(value, is_set_op=has_set_op)

        return regex, includes


def p_charclass(t):
    '''charclass : charitems NEWLINE'''
    t[0] = CharClassExpr(items=t[1], lineno=t.lineno(1))


def p_charitems(t):
    '''charitems : WHITESPACE charitem
                 | WHITESPACE charitem charitems'''
    try:
        t[0] = t[3]
    except IndexError:
        t[0] = deque()
    t[0].appendleft(t[2])


def p_charitem(t):
    '''charitem : ranged_char
                | single_char
                | period_char'''
    t[0] = t[1]


def p_ranged_char(t):
    '''ranged_char : CHAR DOT DOT CHAR'''
    L_source, L_type, L_value = t[1]
    R_source, R_type, R_value = t[4]
    source = '%s..%s' % (L_source, R_source)
    value = '%s-%s' % (L_value, R_value)

    for type in (L_type, R_type):
        if type in ('include', 'prop'):
            raise OprexSyntaxError(t.lineno(0), 'Invalid character range: ' + source)
    try:
        regexlib.compile('[%s]' % value)
    except regexlib.error as e:
        raise OprexSyntaxError(t.lineno(0), 
            '%s compiles to [%s] which is rejected by the regex engine with error message: %s' % (source, value, e.message))

    t[0] = CCItem(source, 'range', value)


def p_period_char(t):
    '''period_char : DOT'''
    t[0] = CCItem('.', 'literal', '.')


def p_single_char(t):
    '''single_char : CHAR'''
    t[0] = t[1]


def p_optional_subblock(t):
    '''optional_subblock : begin_subblock definitions end_subblock
                         |'''
    if len(t) > 1:
        t[0] = Block(
            variables = t[2],
            starting_lineno = t.lineno(0),
        )


def p_begin_subblock(t):
    '''begin_subblock : INDENT'''
    t.lexer.begin_a_scope(type=Scope.BLOCKSCOPE)


def p_end_subblock(t):
    '''end_subblock : DEDENT'''
    # we don't end_a_scope() immediately after seeing a DEDENT because the block owner (parent expression) needs the variable(s) defined in the block


def optional_subblock_cleanup(lexer, subblock, reffed_varnames):
    if subblock:
        subblock.check_unused_vars(useds=reffed_varnames)
        lexer.end_a_scope(Scope.BLOCKSCOPE, at=subblock.starting_lineno)


def p_definitions(t):
    '''definitions : definition
                   | definition definitions'''
    try:
        t[0] = t[1] + t[2]
    except IndexError:
        t[0] = t[1]


def p_definition(t):
    '''definition : assignment
                  | GLOBALMARK assignment'''
    if t[1] == GLOBALMARK:
        assignment = t[2]
        scopes = t.lexer.scopes # global variable, define in all scopes
    else:
        assignment = t[1]
        scopes = t.lexer.scopes[-1:] # non-global, define in the deepest (current) scope only

    def variable_from(declaration):
        def make_var():
            varname = declaration.varname
            value = assignment.value
            if declaration.capture:
                value = Regex(value, modifier='(?P<%s>' % varname)
                t.lexer.capture_names.add(varname)
            return Variable(varname, value, assignment.lineno)

        var = make_var()
        try: # check the deepest scope for varname (every scope supersets its parent, so checking only the deepeset is sufficient)
            prev_def = scopes[-1][var.name]
        except KeyError: # not already defined, OK to define it
            for scope in scopes:
                scope[var.name] = var
        else: # already defined
            raise OprexSyntaxError(t.lineno(1),
                "'%s' is a non-redefinable built-in variable" % var.name
                if prev_def.is_builtin() else
                    "Names must be unique within a scope, '%s' is already defined (previous definition at line %d)"
                        % (var.name, prev_def.lineno))
        return var

    list_of_variables = map(variable_from, assignment.declarations)
    t[0] = list_of_variables


def p_assignment(t):
    '''assignment : declaration equals assignment
                  | declaration equals expression
                  | declaration COLON  charclass  optional_subblock'''
    declaration = t[1]
    lineno = t.lineno(1)
    del t.lexer.ongoing_declarations[declaration.varname]
    if isinstance(t[3], Assignment):
        assignment = t[3]
        assignment.declarations.append(declaration)
    else:
        if isinstance(t[3], Regex):
            value = t[3]
        elif isinstance(t[3], CharClassExpr):
            current_scope = t.lexer.scopes[-1]
            value, lookups = t[3].apply(current_scope)
            optional_subblock_cleanup(t.lexer, t[4], reffed_varnames=[lookup.varname for lookup in lookups])
        assignment = Assignment([declaration], value, lineno)
    t[0] = assignment


def p_equals(t):
    '''equals :            EQUALSIGN
              | WHITESPACE EQUALSIGN
              |            EQUALSIGN WHITESPACE
              | WHITESPACE EQUALSIGN WHITESPACE'''


def p_declaration(t):
    '''declaration :          VARNAME
                   | LBRACKET VARNAME RBRACKET'''
    capture = t[1] == '['
    varname = t[2] if capture else t[1]
    try:
        ongoing = t.lexer.ongoing_declarations[varname]
    except KeyError: # no parent declaration with the same name, safe to declare
        declaration = VariableDeclaration(varname, t.lineno(0), capture)
        t.lexer.ongoing_declarations[varname] = declaration
        t[0] = declaration
    else:
        raise OprexError(t.lineno(0), 
            "Names must be unique within a scope, '%s' is already declared (previous declaration at line %d)" % (varname, ongoing.lineno)
        )


def p_error(t):
    if t is None:
        raise OprexSyntaxError(None, 'Unexpected end of input')

    errmsg = 'Unexpected %s' % t.type
    if t.lexer.mode in ('ORBLOCK', 'LOOKAROUND') and t.type == 'VARNAME':
        errmsg += ' (forgot to close %s?)' % t.lexer.mode

    if t.type not in ('INDENT', 'END_OF_ORBLOCK', 'END_OF_LOOKAROUND'):
        errline = t.lexer.source_lines[t.lineno - 1]
        pointer = ' ' * (find_column(t)-1) + '^'
        errmsg += '\n' + errline
        errmsg += '\n' + pointer

    raise OprexSyntaxError(t.lineno, errmsg)


def find_column(t, index=None):
    lexpos = t.lexpos(index) if index else t.lexpos
    last_newline = t.lexer.lexdata.rfind('\n', 0, lexpos)
    if last_newline < 0:
        last_newline = 0
    return lexpos - last_newline


lexer0 = lex.lex()
def build_lexer(source_lines):
    lexer = CustomLexer(lexer0.clone())
    lexer.source_lines = source_lines
    lexer.input('\n'.join(source_lines)) # all newlines are now just \n, simplifying the lexer
    lexer.indent_stack = [0] # for keeping track of indentation depths
    lexer.ongoing_declarations = {}
    lexer.capture_names = set()
    lexer.references = []
    lexer.flag_dependent_builtins = FLAG_DEPENDENT_BUILTINS

    root_scope = Scope(type=Scope.ROOTSCOPE, starting_lineno=0, parent_scope=None)
    for var in BUILTINS:
        root_scope[var.name] = var
    lexer.scopes = [root_scope]

    return lexer


class CustomLexer:
    def __init__(self, real_lexer):
        self.__dict__ = real_lexer.__dict__
        self.real_lexer = real_lexer
        real_lexer.start_mode = self.start_mode
        real_lexer.end_mode = self.end_mode
        self.tokens = deque()
        self.modes = []
        self.start_mode('INITIAL')

    def token(self):
        token = self.get_next_token()
        #print token
        return token

    def get_next_token(self):
        try:
            return self.tokens.popleft()
        except IndexError:
            lexer = self.real_lexer
            token = lexer.token()
            if token:
                self.tokens.append(token)
                if hasattr(token, 'extra_tokens'):
                    self.tokens.extend(token.extra_tokens)
            else:
                extra_dedent = LexToken('DEDENT', 'EOF', len(lexer.source_lines), len(lexer.lexdata), lexer)
                num_undedented = len(lexer.indent_stack) - 1
                self.tokens.extend([extra_dedent] * num_undedented)
                self.tokens.append(None)
            return self.get_next_token()

    def input(self, input_str):
        self.real_lexer.input(input_str)

    def start_mode(self, mode):
        self.mode = mode
        self.modes.append(mode)
        self.real_lexer.push_state(mode)

    def end_mode(self, mode):
        if mode != self.mode:
            raise OprexInternalError(self.lineno, "Trying to end mode '%s' but current mode is '%s'" % (mode, self.mode))
        self.modes.pop()
        self.mode = self.modes[-1]
        self.real_lexer.pop_state()

    def begin_a_scope(self, type):
        current_scope = self.scopes[-1]
        new_scope = Scope(type=type, starting_lineno=self.lineno, parent_scope=current_scope)
        self.scopes.append(new_scope)
        return new_scope

    def end_a_scope(self, type, at):
        removed_scope = self.scopes.pop()
        if type != removed_scope.type or at != removed_scope.starting_lineno:
            raise OprexInternalError(self.lineno, 'end-of-scope for type=%s line=%d, but active scope is type=%s line=%d' % 
                (Scope.types[type], at, Scope.types[removed_scope.type], removed_scope.starting_lineno))


parser = yacc.yacc()
def parse(lexer):
    return unicode(parser.parse(lexer=lexer, tracking=True))


def cleanup(lexer):
    def check_captures():
        for ref in lexer.references:
            if ref.varname not in lexer.capture_names:
                errmsg = "Bad %s: '%s' is not defined/not a capturing group" % (ref.__class__.__name__, ref.varname)
                raise OprexSyntaxError(ref.lineno, errmsg)

    def check_unclosed_scope():
        for scope in lexer.scopes:
            if scope.type != Scope.ROOTSCOPE:
                raise OprexInternalError(lexer.lineno, 'Unclosed scope type=%s line=%d' % (Scope.types[scope.type], scope.starting_lineno))

    check_captures()
    check_unclosed_scope()


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('path/to/source/file')
    argparser.add_argument('--encoding', help='encoding of the source file')
    args = argparser.parse_args()

    source_file = getattr(args, 'path/to/source/file')
    default_encoding = 'utf-8'
    encoding = args.encoding or default_encoding

    with codecs.open(source_file, 'r') as f:
        source_code = f.read()

    print oprex(source_code)
