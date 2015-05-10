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
        msg = msg.replace('\t', ' ')
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
    'BACKTRACK',
    'CHARCLASS',
    'COLON',
    'DEDENT',
    'DOT',
    'EQUALSIGN',
    'EXCLAMARK',
    'GLOBALMARK',
    'INDENT',
    'NUMBER',
    'LPAREN',
    'MINUS',
    'NEWLINE',
    'PLUS',
    'QUESTMARK',
    'RPAREN',
    'SLASH',
    'STRING',
    'VARNAME',
    'WHITESPACE',
)

GLOBALMARK   = '*)'
t_BACKTRACK  = r'\<\<'
t_DOT        = r'\.'
t_EXCLAMARK  = r'\!'
t_LPAREN     = r'\('
t_MINUS      = r'\-'
t_NUMBER     = r'\d+'
t_PLUS       = r'\+'
t_QUESTMARK  = r'\?'
t_RPAREN     = r'\)'
t_SLASH      = r'\/'
t_ignore     = '' # oprex is whitespace-significant, no ignored characters


class Assignment(namedtuple('Assignment', 'varnames value lineno')):
    __slots__ = ()

class Lookup(namedtuple('Lookup', 'varname optional capture')):
    __slots__ = ()

class Variable(namedtuple('Variable', 'name value lineno')):
    __slots__ = ()
    def is_builtin(self):
        return self.lineno == 0

class Quantifier(namedtuple('Quantifier', 'base modifier')):
    __slots__ = ()

class Quantification(unicode):
    __slots__ = ('quantified', 'quantifier')
    def __new__(cls, quantified, quantifier):
        quantification = unicode.__new__(cls, quantified + quantifier)
        quantification.quantified = quantified
        quantification.quantifier = quantifier
        return quantification

class CharClass(unicode):
    __slots__ = ('for_import', 'need_brackets')
    escapes = {
        '['  : '\\[',
        ']'  : '\\]',
        '^'  : '\\^',
        '-'  : '\\-',
        '\\' : '\\\\',
        '{'  : '{{',
        '}'  : '}}',
    }
    def __new__(cls, value, for_import, need_brackets):
        charclass = unicode.__new__(cls, value)
        charclass.for_import = for_import
        charclass.need_brackets = need_brackets
        return charclass


def t_character_class(t):
    ''':.*'''
    chardefs = t.value.strip().split(' ')
    if chardefs[0] != ':':
        raise OprexSyntaxError(t.lineno, 'Character class definition requires space after the : (colon)')

    del chardefs[0] # no need to process the colon
    if not chardefs:
        raise OprexSyntaxError(t.lineno, 'Empty character class is not allowed')

    includes = set()
    t.contains_setop = False
    t.need_brackets = len(chardefs) > 1 # single-membered? brackets not needed
    t.counter = 0

    def try_parse(chardef, *functions):
        for fn in functions:
            result = fn(chardef)
            if result:
                return result, fn
        return None, None

    def single(chardef): # example: a 1 $ 久 😐
        if len(chardef) == 1:
            return CharClass.escapes.get(chardef, chardef)

    def uhex(chardef): # example: U+65 U+1F4A9
        if chardef.startswith('U+'):
            hexnum = chardef[2:]
            try:
                int(hexnum, 16)
            except ValueError:
                raise OprexSyntaxError(t.lineno, 'Syntax error %s should be U+hexadecimal' % chardef)
            hexlen = len(hexnum)
            if hexlen > 8:
                raise OprexSyntaxError(t.lineno, 'Syntax error %s out of range' % chardef)
            if hexlen <= 4:
                return unicode('\\u' + ('0' * (4-hexlen) + hexnum))
            else:
                return unicode('\\U' + ('0' * (8-hexlen) + hexnum))

    def include(chardef): # example: +alpha +digit
        if regex.match('\\+[a-zA-Z]\\w*+(?<!_)$', chardef):
            varname = chardef[1:]
            includes.add(varname)
            return '{%s.value.for_import}' % varname

    def by_prop(chardef): # example: /Alphabetic /Script=Latin /InBasicLatin /IsCyrillic
        if regex.match('/\\w+', chardef):
            prop = chardef[1:]
            return '\\p{{%s}}' % prop

    def by_name(chardef):           # example: :TRUE :CHECK_MARK :BALLOT_BOX_WITH_CHECK
        if chardef.startswith(':'): # must be in uppercase, using underscores rather than spaces
            if not chardef.isupper(): 
                raise OprexSyntaxError(t.lineno, 'Character name must be in uppercase')
            name = chardef[1:].replace('_', ' ')
            return '\\N{{%s}}' % name

    def range(chardef): # example: A..Z U+41..U+4F :LEFTWARDS_ARROW..:LEFT_RIGHT_OPEN-HEADED_ARROW
        if '..' in chardef:
            t.need_brackets = True
            try:
                range_from, range_to = chardef.split('..')
                from_val, _ = try_parse(range_from, single, uhex, by_name)
                to_val, _   = try_parse(range_to, single, uhex, by_name)
                return from_val + '-' + to_val
            except (TypeError, ValueError):
                raise OprexSyntaxError(t.lineno, 'Invalid character range: ' + chardef)

    def set_operation(chardef): # example: +alpha and +digit not +hex
        if chardef in ('not:', 'and', 'not'):
            t.contains_setop = True
            is_first = t.counter == 1
            is_last = t.counter == len(chardefs)
            prefix = is_first and not is_last
            infix = not (is_first or is_last)
            type, valid_placement, translation = {
                'not:': ('unary',  prefix, '^'),
                'not' : ('binary', infix,  '--'),
                'and' : ('binary', infix,  '&&'),
            }[chardef]
            if valid_placement:
                return translation
            else:
                raise OprexSyntaxError(t.lineno, "Incorrect use of %s '%s' operator" % (type, chardef))

    seen = set()
    def compilable(chardef):
        t.counter += 1
        if chardef == '':
            return False
        if chardef in seen:
            raise OprexSyntaxError(t.lineno, 'Duplicate item in character class definition: ' + chardef)
        else:
            seen.add(chardef)
            return True

    def compile(chardef):
        compiled, type = try_parse(chardef, range, single, uhex, by_prop, by_name, include, set_operation)
        if not compiled:
            raise OprexSyntaxError(t.lineno, 'Not a valid character class keyword: ' + chardef)
        test(compiled, type)
        return compiled

    def test(result, type):
        if type in (include, set_operation): # includes are variable names -- not testable at this point
            return                           # set operators (e.g. and, not) are not testable by itself
                                             # so just skip test for those cases
        test = curlies_escaped = result.replace('{{', '{').replace('}}', '}')
        if type != by_prop:
            test = '[' + test + ']' 
        try:
            regex.compile(test)
        except Exception as e:
            msg = '%s compiles to %s which is rejected by the regex module with error message: %s'
            raise OprexSyntaxError(t.lineno, msg % (chardef, curlies_escaped, e.msg if hasattr(e, 'msg') else e.message))

    value = ''.join([
        compile(chardef)
        for chardef in chardefs
        if compilable(chardef)
    ])
    if len(chardefs) == 2 and value.startswith('^\\p{'): # convert ^\p{something} to \P{something}
        value = value.replace('^\\p{', '\\P{', 1)
        t.need_brackets = t.contains_setop = False
    if t.contains_setop: # set operation must be bracketed even when nested
        value = '[' + value + ']'

    t.type = 'COLON'
    t.extra_tokens = [ExtraToken(t, 'CHARCLASS', (value, includes, t.need_brackets))]
    return t


def t_STRING(t):
    r"""('|")(.*)"""
    value = t.value.strip()
    if len(value) < 2 or value[0] != value[-1]:
        raise OprexSyntaxError(t.lineno, 'Missing closing quote: ' + value)

    t.value = regex.escape(
        value[1:-1], # remove the surrounding quotes
        special_only=True,
    )
    return t


def t_VARNAME(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    name = t.value
    if name.startswith('_'):
        raise OprexSyntaxError(t.lineno, 'Illegal name (must start with a letter): ' + name)
    if name.endswith('_'):
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
    if indentlen == prev: # no change indentation depth change
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
    raise OprexSyntaxError(t.lineno, 'Syntax error at or near: ' + t.value.split('\n')[0])


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


def p_expression(t):
    '''expression : repeat_expr
                  | string_expr
                  | lookup_expr'''
    t[0] = t[1]


def p_repeat_expr(t):
    '''repeat_expr : quantifier WHITESPACE expression
                   | quantifier COLON      charclass'''
    t[0] = quantify(quantified=t[3], quantifier=t[1])


def p_string_expr(t):
    '''string_expr : STRING NEWLINE optional_block'''
    check_unused_vars(t, optional_block=t[3], referenced_vars=())
    t[0] = t[1]


def p_lookup_expr(t):
    '''lookup_expr : lookup             NEWLINE optional_block
                   | SLASH lookup_chain NEWLINE optional_block'''

    referenced_vars = set()
    current_scope = t.lexer.scopes[-1]
    def resolve_variable(varname):
        referenced_vars.add(varname)
        try:
            return current_scope[varname].value
        except KeyError as e:
            raise OprexSyntaxError(t.lineno(0), "'%s' is not defined" % e.message)

    def resolve_lookup(lookup):
        value = resolve_variable(lookup.varname)
        if lookup.optional:
            value = merge_quantifier(value, lookup.optional)
        if lookup.capture:
            value = lookup.capture % value
        return value

    def merge_quantifier(expr, optionality):
        if not isinstance(expr, Quantification):
            return quantify(expr, optionality)
        try:
            return expr.quantified + {
                '++ ?+' : '*+',
                '*+ ?+' : '*+',
                '+? ??' : '*?',
                '*? ??' : '*?',
                '+ ?'   : '*' ,
                '* ?'   : '*' ,
            }[expr.quantifier + ' ' + optionality]
        except KeyError:
            return '(?:%s)%s' % (expr, optionality)

    if t[1] == '/': # lookup chain
        t[0] = ''.join(map(resolve_lookup, t[2]))
    else: # single lookup
        t[0] = resolve_lookup(t[1])
    check_unused_vars(t, optional_block=t[len(t)-1], referenced_vars=referenced_vars)


def p_quantifier(t):
    '''quantifier : repeat_N_times
                  | repeat_range
                  | optionalize'''
    quant = t[1]
    base = {
        '{1}'   : '',
        '{,}'   : '*',
        '{0,}'  : '*',
        '{1,}'  : '+',
        '{0,1}' : '?',
    }.get(quant.base, quant.base)
    modifier = quant.modifier if base else ''
    t[0] = base + modifier


def p_repeat_N_times(t):
    '''repeat_N_times : NUMBER of'''
    t[0] = Quantifier(base=('{%s}' % t[1]), modifier='')


def p_repeat_range(t):
    '''repeat_range : numrange of
                    | numrange WHITESPACE BACKTRACK MINUS of
                    | NUMBER   WHITESPACE BACKTRACK PLUS  DOT DOT of
                    | NUMBER   WHITESPACE BACKTRACK PLUS  DOT DOT NUMBER of'''
    possessive = len(t) == 3 # the first form above
    greedy     = len(t) == 6 # the second form
    lazy       = not possessive and not greedy # third & fourth forms
    
    if lazy:
        min = t[1]
        max = t[7] if len(t) == 9 else ''
    else:
        min, max = t[1]

    if not min:
        min = '0'
    if max and int(max) <= int(min):
        raise OprexSyntaxError(t.lineno(0), 'Repeat max must be > min')
    if min == '0':
        min = ''

    t[0] = Quantifier(
        base='{%s,%s}' % (min, max),
        modifier='+' if possessive else '?' if lazy else ''
    )


def p_optionalize(t):
    '''optionalize : optional of'''
    opt = t[1]
    t[0] = Quantifier(base=opt[0], modifier=opt[1:])


def p_numrange(t):
    '''numrange :        DOT DOT
                | NUMBER DOT DOT
                |        DOT DOT NUMBER
                | NUMBER DOT DOT NUMBER'''
    def number_or_empty(str):
        return str if str != '.' else ''
    min = number_or_empty(t[1])
    max = number_or_empty(t[len(t)-1])
    t[0] = min, max


def p_of(t):
    '''of : WHITESPACE VARNAME'''
    if t[2] != 'of': # we do this (rather than defining OF token/reserving 'of' as keyword) to allow having variable named 'of'
        raise OprexSyntaxError(t.lineno(0), "Expected 'of' but instead got: " + t[2])


def p_lookup_chain(t):
    '''lookup_chain : lookup SLASH
                    | lookup SLASH lookup_chain'''
    try:
        t[0] = t[3]
    except IndexError:
        t[0] = deque()
    t[0].appendleft(t[1])


def p_lookup(t):
    '''lookup : simple_lookup
              | captured_lookup
              | captured_optional_lookup'''
    t[0] = t[1]


def p_simple_lookup(t):
    '''simple_lookup : VARNAME
                     | VARNAME optional'''
    try:
        optional = t[2]
    except IndexError:
        optional = ''
    t[0] = Lookup(varname=t[1], optional=optional, capture=False)


def p_captured_lookup(t):
    '''captured_lookup : LPAREN VARNAME RPAREN
                       | LPAREN VARNAME RPAREN optional'''
    varname = t[2]
    capture = '(?<' + varname + '>%s)'
    if len(t) > 4:
        capture += t[4]
    t[0] = Lookup(varname, optional=False, capture=capture)


def p_captured_optional_lookup(t):
    '''captured_optional_lookup : LPAREN VARNAME optional RPAREN'''
    varname = t[2]
    optional = t[3]
    capture = '(?<' + varname + '>%s)'
    t[0] = Lookup(varname, optional, capture)


def p_optional(t):
    '''optional : QUESTMARK
                | QUESTMARK QUESTMARK
                | QUESTMARK EXCLAMARK'''
    possessive = len(t) == 2
    lazy = not possessive and t[2] == '?'
    greedy = not possessive and t[2] == '!'
    t[0] = '?+' if possessive else '??' if lazy else '?'


def p_optional_block(t):
    '''optional_block : begin_block definitions end_block
                      |'''
    if len(t) > 1:
        t[0] = t[2]


def p_begin_block(t):
    '''begin_block : INDENT'''
    current_scope = t.lexer.scopes[-1]
    t.lexer.scopes.append(current_scope.copy())


def p_end_block(t):
    '''end_block : DEDENT'''


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

    def define(varname):
        var = Variable(varname, assignment.value, assignment.lineno)
        try: # check the deepest scope for varname (every scope supersets its parent scope, so...
            already_defined = scopes[-1][varname] # ...checking only the deepeset is sufficient)
        except KeyError: # not already defined, OK to define it
            for scope in scopes:
                scope[varname] = var
        else: # already defined
            raise OprexSyntaxError(t.lineno(1),
                "'%s' is a built-in variable and cannot be redefined" % var.name
                if already_defined.is_builtin() else
                "Names must be unique within a scope, '%s' is already defined (previous definition at line %d)"
                    % (varname, already_defined.lineno))
        return var
    t[0] = map(define, assignment.varnames)


def p_assignment(t):
    '''assignment : VARNAME EQUALSIGN assignment
                  | VARNAME EQUALSIGN expression
                  | VARNAME COLON     charclass'''
    varname = t[1]
    lineno = t.lineno(1)
    if isinstance(t[3], Assignment):
        assignment = t[3]
        assignment.varnames.append(varname)
    else:
        value = t[3]
        assignment = Assignment([varname], value, lineno)
    t[0] = assignment


def p_charclass(t):
    '''charclass : CHARCLASS NEWLINE optional_block'''
    value, includes, t.need_brackets = t[1]
    current_scope = t.lexer.scopes[-1]
    optional_block = t[3]
    if optional_block:
        for var in optional_block:
            if var.name not in includes:
                raise OprexSyntaxError(var.lineno, "'%s' is defined but not used (by its parent character class definition)" % var.name)
            if not isinstance(var.value, CharClass):
                raise OprexSyntaxError(t.lineno(0), "Cannot include '%s': not a character class" % var.name)
            if var.value.need_brackets and not var.value.for_import.startswith('['):
                t.need_brackets = True
        t.lexer.scopes.pop()

    try:
        value = value.format(**current_scope)
    except KeyError as e:
        raise OprexSyntaxError(t.lineno(0), "Cannot include '%s': not defined" % e.message)

    for_import = value
    if t.need_brackets and not value.startswith('['):
        value = '[' + value + ']'
    if len(value) == 1:
        value = regex.escape(value, special_only=True)

    t[0] = CharClass(value, for_import, t.need_brackets)


def p_error(t):
    if t is None:
        raise OprexSyntaxError(None, 'Unexpected end of input')

    if t.type == 'INDENT':
        raise OprexSyntaxError(t.lineno, 'Unexpected INDENT')

    errline = t.lexer.source_lines[t.lineno - 1]
    pointer = ' ' * (find_column(t)-1) + '^'
    raise OprexSyntaxError(t.lineno, 'Unexpected %s\n%s\n%s' % (t.type, errline, pointer))


def check_unused_vars(t, optional_block, referenced_vars):
    if optional_block:
        for var in optional_block:
            if var.name not in referenced_vars:
                raise OprexSyntaxError(var.lineno, "'%s' is defined but not used (by its parent expression)" % var.name)
        t.lexer.scopes.pop()


def find_column(t):
    last_newline = t.lexer.lexdata.rfind('\n', 0, t.lexpos)
    if last_newline < 0:
        last_newline = 0
    return t.lexpos - last_newline


def quantify(quantified, quantifier):
    if not quantified:
        return ''
    if not quantifier:
        return quantified
    if len(quantified) > 1 and not isinstance(quantified, CharClass): # needs grouping
        quantified = '(?:%s)' % quantified
    return Quantification(quantified, quantifier)


class CustomLexer:
    def __init__(self, real_lexer):
        self.__dict__ = real_lexer.__dict__
        self.real_lexer = real_lexer
        self.tokens = deque()

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
    lexer.scopes = [{ # built-in variables                                     # lineno=0 --> builtin
        'alpha' : Variable('alpha', CharClass('[a-zA-Z]',    'a-zA-Z',    True), lineno=0),
        'upper' : Variable('upper', CharClass('[A-Z]',       'A-Z',       True), lineno=0),
        'lower' : Variable('lower', CharClass('[a-z]',       'a-z',       True), lineno=0),
        'digit' : Variable('digit', CharClass('[0-9]',       '0-9',       True), lineno=0),
        'alnum' : Variable('alnum', CharClass('[a-zA-Z0-9]', 'a-zA-Z0-9', True), lineno=0),
    }]
    return CustomLexer(lexer)


parser = yacc.yacc()
def parse(lexer):
    # always use V1, UNICODE, and MULTILINE
    return '(?umV1)' + unicode(parser.parse(lexer=lexer, tracking=True))


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
