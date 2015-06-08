# -*- coding: utf-8 -*-

import regex, argparse, codecs
from ply import lex, yacc
from collections import namedtuple, deque


def oprex(source_code):
    source_lines = sanitize(source_code)
    lexer = build_lexer(source_lines)
    result = parse(lexer=lexer)
    check_captures(lexer=lexer)
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
    if source_lines[0].split('--')[0].strip():
        raise OprexSyntaxError(1, 'First line must be blank, not: ' + source_lines[0])
    if source_lines[-1].split('--')[0].strip():
        numlines = len(source_lines)
        raise OprexSyntaxError(numlines, 'Last line must be blank, not: ' + source_lines[-1])
    return source_lines


LexToken = namedtuple('LexToken', 'type value lineno lexpos lexer')
ExtraToken = lambda t, type, value=None, lexpos=None: LexToken(type, value or t.value, t.lexer.lineno, lexpos or t.lexpos, t.lexer)
reserved = {
    '_' : 'UNDERSCORE',
}
tokens = [
    'AMPERSAND',
    'CHARCLASS',
    'COLON',
    'DEDENT',
    'DOT',
    'EQUALSIGN',
    'FLAGSET',
    'GLOBALMARK',
    'GT',
    'INDENT',
    'NUMBER',
    'LPAREN',
    'LT',
    'MINUS',
    'NEWLINE',
    'OF',
    'PLUS',
    'QUESTMARK',
    'RPAREN',
    'SLASH',
    'STRING',
    'VARNAME',
    'WHITESPACE',
] + reserved.values()

GLOBALMARK   = '*)'
t_AMPERSAND  = r'\&'
t_DOT        = r'\.'
t_EQUALSIGN  = r'\='
t_GT         = r'\>'
t_LPAREN     = r'\('
t_LT         = r'\<'
t_MINUS      = r'\-'
t_NUMBER     = r'\d+'
t_PLUS       = r'\+'
t_QUESTMARK  = r'\?'
t_RPAREN     = r'\)'
t_SLASH      = r'\/'
t_ignore = '' # oprex is whitespace-significant, no ignored characters


class Variable(namedtuple('Variable', 'name value lineno')):
    __slots__ = ()
    def is_builtin(self):
        return self.lineno == 0

class VariableDeclaration(namedtuple('VariableDeclaration', 'varname capture atomic')):   
    __slots__ = ()

class VariableLookup(namedtuple('VariableLookup', 'varname lineno optional')):
    __slots__ = ()

class Backreference(namedtuple('Backreference', 'varname lineno optional')):
    __slots__ = ()

class SubroutineCall(namedtuple('SubroutineCall', 'varname lineno optional')):
    __slots__ = ()

class Quantifier(namedtuple('Quantifier', 'base modifier')):
    __slots__ = ()

class Assignment(namedtuple('Assignment', 'declarations value lineno')):
    __slots__ = ()


class Expression(unicode):
    __slots__ = ('grouped', 'quantifier')
    def __new__(cls, base_value, modifier=None): # modifier can be quantifier, scoped flags, capture, or atomic group
        value = base_value
        grouped = False
        quantifier = None
        if modifier:
            if modifier.startswith('(?'): # scoped flags/capture/atomic group -- in any case it should be missing the closing paren
                value = modifier + base_value + ')' # add the closing paren
                grouped = True
            else: # modifier is quantifier
                quantifier = modifier
                value += quantifier
        expr = unicode.__new__(cls, value)
        expr.grouped = grouped
        expr.quantifier = quantifier
        return expr


class Flagset(unicode):
    __slots__ = ('turn_ons', 'turn_offs')
    all_flags = {}
    scopeds = {
        'fullcase'   : 'f',
        'ignorecase' : 'i',
        'multiline'  : 'm',
        'dotall'     : 's',
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


class CharClass(unicode):
    __slots__ = ('is_set_op',)
    escapes = {
        '['  : '\\[',
        ']'  : '\\]',
        '^'  : '\\^',
        '-'  : '\\-',
        '\\' : '\\\\',
    }
    def __new__(cls, value, is_set_op):
        charclass = unicode.__new__(cls, value)
        charclass.is_set_op = is_set_op
        return charclass

ESCAPE_SEQUENCE_RE = regex.compile(r'''
    ( \\U........      # 8-digit hex escapes
    | \\u....          # 4-digit hex escapes
    | \\x..            # 2-digit hex escapes
    | \\[0-7]{1,3}     # Octal escapes
    | \\N\{[^}]+\}     # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )''', regex.UNICODE | regex.VERBOSE)

def t_charclass(t):
    ''':.*'''
    value = t.value.split('--')[0] # parts after "--" are comments, ignore them 
    chardefs = value.split(' ') # will have empty string in case of consecutive spaces
    chardefs = filter(lambda chardef: chardef, chardefs)  # exclude empty strings
    if chardefs[0] != ':':
        raise OprexSyntaxError(t.lineno, 'Character class definition requires space after the : (colon)')
    del chardefs[0] # no need to process the colon
    if not chardefs:
        raise OprexSyntaxError(t.lineno, 'Empty character class is not allowed')

    t.counter = 0
    includes = set()

    def try_translate(chardef, *functions):
        for fn in functions:
            result = fn(chardef)
            if result:
                return result, fn.__name__

    def single(chardef): # example: a 1 $ 久 😐
        if len(chardef) == 1:
            return CharClass.escapes.get(chardef, chardef)

    def escaped(chardef): # example: \n \x61 \u0061 \U00000061
        if chardef.startswith('\\'):
            if ESCAPE_SEQUENCE_RE.match(chardef):
                return chardef
            else:
                raise OprexSyntaxError(t.lineno, 'Bad escape sequence: ' + chardef)

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
        if regex.match('\\+[a-zA-Z]\\w*+$', chardef):
            varname = chardef[1:]
            includes.add(varname)
            return VariableLookup(varname, t.lineno, optional=False)

    def by_prop(chardef): # example: /Alphabetic /Script=Latin /InBasicLatin /IsCyrillic
        if regex.match('/\\w+', chardef):
            prop = chardef[1:]
            return '\\p{%s}' % prop

    def by_name(chardef):           # example: :TRUE :CHECK_MARK :BALLOT_BOX_WITH_CHECK
        if chardef.startswith(':'): # must be in uppercase, using underscores rather than spaces
            if not chardef.isupper(): 
                raise OprexSyntaxError(t.lineno, 'Character name must be in uppercase')
            name = chardef[1:].replace('_', ' ')
            return '\\N{%s}' % name

    def range(chardef): # example: A..Z U+41..U+4F :LEFTWARDS_ARROW..:LEFT_RIGHT_OPEN-HEADED_ARROW
        if '..' in chardef:
            try:
                range_from, range_to = chardef.split('..')
                from_val, _ = try_translate(range_from, single, uhex, by_name)
                to_val, _   = try_translate(range_to, single, uhex, by_name)
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

    def translate(chardef):
        t.counter += 1
        result = try_translate(chardef, range, single, escaped, uhex, by_prop, by_name, include, set_operation)
        if not result:
            raise OprexSyntaxError(t.lineno, 'Not a valid character class keyword: ' + chardef)
        test(chardef, result)
        return result

    def test(chardef, result):
        value, type = result
        if type in ('include', 'set_operation'): # - includes are not testable at this point
            return                               # - set operators are not testable by itself
                                                 # --> so just skip test for those cases
        test = value
        if type != 'by_prop': # for some reason the regex library will not catch some errors if unicode property...
            test = '[' + test + ']' # ...is put inside brackets, so in that case we'll just skip bracketing it
        try:
            regex.compile(test)
        except regex.error as e:
            msg = '%s compiles to %s which is rejected by the regex engine with error message: %s'
            raise OprexSyntaxError(t.lineno, msg % (chardef, value, e.msg if hasattr(e, 'msg') else e.message))

    results = map(translate, chardefs)
    t.type = 'COLON'
    t.extra_tokens = [ExtraToken(t, 'CHARCLASS', (chardefs, results, includes))]
    return t


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
            regex.compile(test)
        else:
            regex.compile('(?V1)' + test)
    except Exception as e:
        raise OprexSyntaxError(t.lineno, '%s compiles to %s which is rejected by the regex engine with error message: %s' % 
            (t.value, test, str(e.message)))
    else:
        t.type = 'LPAREN'
        t.extra_tokens = [ExtraToken(t, 'FLAGSET', value=flags), ExtraToken(t, 'RPAREN')]
    return t


def t_STRING(t):
    r'''("(\\.|[^"\\])*")|('(\\.|[^'\\])*')''' # single- or double-quoted string, with escape-quote support
    value = t.value[1:-1] # remove the surrounding quotes
    value = value.replace('\\"', '"').replace("\\'", "'") # apply (unescape) escaped quotes
    value = regex.escape(value, special_only=True) # this will unnecessarily turn \ into \\
    t.value = value.replace('\\\\', '\\') # ...so, restore 
    return t


def t_VARNAME(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    t.type = reserved.get(t.value, 'VARNAME')
    return t


# Rules that contain space/tab should be written in function form and be put 
# before the t_linemark rule to make PLY calls them first.
# Otherwise t_linemark will turn the spaces/tabs into WHITESPACE token.


def t_OF(t):
    r'[ \t]+of(?=[ \t:])(?![ \t]+(--|\n))' # without this, WHITESPACE VARNAME will be produced instead, requiring making "of" a reserved keyword
    t.type = 'WHITESPACE'
    t.extra_tokens = [ExtraToken(t, 'OF', lexpos=t.lexpos + t.value.index('of'))]
    return t


def t_linemark(t):
    r'(?m)(((^|[ \t]+)--.*)|[ \t\n])+(\*\)[ \t]*)*' # comments are also captured here
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
             | NEWLINE        main_expression
             | NEWLINE INDENT main_expression DEDENT'''
    if len(t) == 3:
        flags, expression = t[2]
    elif len(t) == 5:
        flags, expression = t[3]
    else:
        flags = expression = ''

    if 'm' not in flags: # turn on MULTILINE by default
        flags = 'm' + flags
    if 'w' not in flags: # turn on WORD by default
        flags = 'w'+ flags

    flags = '(?%s)' % flags
    if 'V' not in flags: # use V1 by default, but put it in its own group, at the front, so we can easily ...
        flags = '(?V1)' + flags # trim it out of the result if unwanted (e.g. if using re rather than regex)

    try:
        regex.compile(flags)
    except Exception as e:
        raise OprexSyntaxError(t.lineno(2),  'Starting flags rejected by the regex engine with error message: ' + str(e.message))
    t[0] = flags + expression


def p_main_expression(t):
    '''main_expression : global_flagging main_expression
                       | global_flagging
                       | expression'''
    if len(t) == 3: # the first form above
        flags = t[1]
        more_flags, expression = t[2]
        flags = Flagset(
            turn_ons=flags.turn_ons + more_flags.turn_ons,
            turn_offs=flags.turn_offs + more_flags.turn_offs,
        )
    elif isinstance(t[1], Flagset): # second form (flags only)
        flags = t[1]
        expression = ''
    else: # third form (flagless expression)
        flags = Flagset(turn_ons='', turn_offs='')
        expression = t[1]

    t[0] = flags, expression


def p_global_flagging(t):
    '''global_flagging : LPAREN FLAGSET RPAREN NEWLINE'''
    flagset = t[2]
    if 'u' in flagset.turn_ons: # turning-on unicode changes some built-ins
        t.lexer.scopes[0].update(
            alpha    = Variable('alpha',    CharClass(r'\p{Alphabetic}',                 is_set_op=False), lineno=0),
            upper    = Variable('upper',    CharClass(r'\p{Uppercase}',                  is_set_op=False), lineno=0),
            lower    = Variable('lower',    CharClass(r'\p{Lowercase}',                  is_set_op=False), lineno=0),
            alnum    = Variable('alnum',    CharClass(r'\p{Alphanumeric}',               is_set_op=False), lineno=0),
            linechar = Variable('linechar', CharClass(r'[\r\n\x0B\x0C\x85\u2028\u2029]', is_set_op=False), lineno=0),
        )
    t[0] = flagset


def p_expression(t):
    '''expression : string_expr
                  | lookup_expr
                  | flagged_expr
                  | quantified_expr'''
    t[0] = t[1]


def p_string_expr(t):
    '''string_expr : string NEWLINE optional_block'''
    scope_check(t, optional_block=t[3], referenced_vars=())
    t[0] = Expression(t[1])


def p_string(t):
    '''string : boundary STRING boundary'''
    t[0] = t[1] + t[2] + t[3]


def p_boundary(t):
    '''boundary :
                | DOT
                | UNDERSCORE'''
    t[0] = {
        None : '',
        '.'  : '\\b',
        '_'  : '\\B',
    }[t[len(t)-1]]


def p_quantified_expr(t):
    '''quantified_expr : quantifier WHITESPACE expression
                       | quantifier COLON      charclass'''
    t[0] = quantify(t[3], quantifier=t[1])


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
        '{,1}'  : '?',
        '{0,1}' : '?',
    }.get(quant.base, quant.base)
    modifier = quant.modifier if base else ''
    t[0] = base + modifier


def p_repeat_N_times(t):
    '''repeat_N_times : NUMBER of'''
    number = t[1]
    t[0] = Quantifier(base=('{%s}' % number), modifier='')


def p_repeat_range(t):
    '''repeat_range : numrange of
                    | numrange backtrack MINUS of
                    | NUMBER   backtrack PLUS  DOT DOT of
                    | NUMBER   backtrack PLUS  DOT DOT NUMBER of'''
    possessive = len(t) == 3 # the first form above
    greedy     = len(t) == 5 # the second form
    lazy       = not possessive and not greedy # third & fourth forms

    if lazy:
        min = t[1]
        max = t[6] if len(t) == 8 else ''
    else:
        min, max = t[1]

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
    '''numrange :        DOT DOT
                | NUMBER DOT DOT
                |        DOT DOT NUMBER
                | NUMBER DOT DOT NUMBER'''
    def number_or_empty(str):
        return str if str != '.' else ''
    min = number_or_empty(t[1])
    max = number_or_empty(t[len(t)-1])
    t[0] = min, max


def p_optionalize(t):
    '''optionalize : QUESTMARK of'''
    t[0] = Quantifier(base='?', modifier='+')


def quantify(expr, quantifier):
    if quantifier == '{0}' or expr == '':
        return Expression('')
    if quantifier == '{1}' or quantifier == '':
        return expr

    def merge_quantifiers():
        try:
            return {               # The purpose of this is so we can write x* as (x+)? e.g.
                 '? of +'  : '*' , #     digits?
                '?+ of ++' : '*+', #         digits = 1.. of digit
                '?? of +?' : '*?', # without making the regex output suboptimal
            }[quantifier + ' of ' + expr.quantifier]
        except KeyError: # not a "? of +" operation, try merge repeats e.g.
            n1 = int(expr.quantifier.strip('{').strip('}')) # colorhex = 3 of byte
            n2 = int(     quantifier.strip('{').strip('}')) #     byte = 2 of hex
            return '{%d}' % (n1 * n2)                       # --> optimize "hex{2}{3}" into "hex{6}"

    def strip_old_quantifier():
        return expr[:-len(expr.quantifier)]

    def put_in_group():
        unneeded = (
            len(expr) == 1 or 
            len(expr) == 2 and expr[0] == '\\' or 
            isinstance(expr, CharClass) or 
            expr.grouped # already
        )
        if unneeded:
            return expr # unchanged
        else:
            return '(?:%s)' % expr

    try:
        return Expression(strip_old_quantifier(), modifier=merge_quantifiers())
    except:
        return Expression(put_in_group(), modifier=quantifier)


def p_flagged_expr(t):
    '''flagged_expr : LPAREN FLAGSET RPAREN WHITESPACE expression'''
    flags = t[2]
    for flag_name, global_flag in Flagset.globals.iteritems():
        if global_flag in flags.turn_ons:
            raise OprexSyntaxError(t.lineno(2), "'%s' is a global flag and must be set using global flag syntax, not scoped." % flag_name)
    t[0] = Expression(t[5], modifier='(?%s:' % flags)


def p_lookup_expr(t):
    '''lookup_expr : lookup             NEWLINE optional_block
                   | SLASH lookup_chain NEWLINE optional_block'''
    referenced_vars = set()
    current_scope = t.lexer.scopes[-1]
    def resolve_var(lookup):
        referenced_vars.add(lookup.varname)
        try:
            var = current_scope[lookup.varname]
        except KeyError:
            raise OprexSyntaxError(t.lineno(0), "'%s' is not defined" % lookup.varname)
        if lookup.optional:
            return quantify(var.value, quantifier=lookup.optional)
        else:
            return var.value

    def resolve(lookup):
        if isinstance(lookup, VariableLookup):
            return resolve_var(lookup)
        elif isinstance(lookup, Backreference): 
            t.lexer.backreferences.add(lookup)
            return '(?P=%s)%s' % (lookup.varname, lookup.optional)
        elif isinstance(lookup, SubroutineCall): 
            t.lexer.subroutine_calls.add(lookup)
            return '(?&%s)%s' % (lookup.varname, lookup.optional)

    if t[1] == '/': # chain of lookups
        t[0] = Expression(''.join(map(resolve, t[2])))
    else: # single lookup
        t[0] = resolve(t[1])
    scope_check(t, optional_block=t[len(t)-1], referenced_vars=referenced_vars)


def p_lookup_chain(t):
    '''lookup_chain : lookup SLASH
                    | lookup SLASH lookup_chain'''
    try:
        t[0] = t[3]
    except IndexError:
        t[0] = deque()
    t[0].appendleft(t[1])


def p_lookup(t):
    '''lookup : lookup_type
              | lookup_type QUESTMARK'''
    LookupClass, varname = t[1]
    has_questmark = len(t) == 3
    t[0] = LookupClass(varname, t.lineno(1), optional='?+' if has_questmark else '')


def p_lookup_type(t):
    '''lookup_type : variable_lookup
                   | backreference
                   | subroutine_call'''
    t[0] = t[1]


def p_variable_lookup(t):
    '''variable_lookup : VARNAME
                       | UNDERSCORE
                       | DOT'''
    t[0] = VariableLookup, t[1]


def p_backreference(t):
    '''backreference : EQUALSIGN VARNAME'''
    t[0] = Backreference, t[2]


def p_subroutine_call(t):
    '''subroutine_call : AMPERSAND VARNAME'''
    t[0] = SubroutineCall, t[2]


def p_charclass(t):
    '''charclass : CHARCLASS NEWLINE optional_block'''
    chardefs, results, includes = t[1]
    values, types = zip(*results)
    current_scope = t.lexer.scopes[-1]

    def lookup(varname):
        try:
            var = current_scope[varname]
        except KeyError as e:
            raise OprexSyntaxError(t.lineno(0), "Cannot include '%s': not defined" % e.message)
        if not isinstance(var.value, CharClass):
            raise OprexSyntaxError(t.lineno(0), "Cannot include '%s': not a character class" % varname)
        else:
            return var.value

    def value_or_lookup(value):
        if isinstance(value, VariableLookup):
            value = lookup(value.varname)
            if value.startswith('[') and not value.is_set_op: # remove nested [] unless it's set-operation
                value = value[1:-1]
            elif value == '-': # inside character class, dash needs to be escaped
                value = r'\-'
            elif len(value) == 2 and value[0] == '\\' and value[1] in '$.|?*+(){}': # remove unnecessary escape
                value = value[1]
        return value

    if len(chardefs) == 1 and 'include' in types: # simple aliasing
        t[0] = lookup(values[0].varname)
    else:
        result = ''.join(map(value_or_lookup, values))
        if result == '\\-': # no need to escape dash outside of character class
            result = '-'
        elif len(result) == 1:
            result = regex.escape(result, special_only=True)
        elif len(chardefs) == 2 and result.startswith(r'^\p{'): # convert ^\p{something} to \P{something}
            result = result.replace(r'^\p{', r'\P{', 1)
        elif len(chardefs) > 1 or 'range' in types:
            result = '[' + result + ']'
        t[0] = CharClass(result, is_set_op='set_operation' in types)

    scope_check(t, optional_block=t[3], referenced_vars=includes)


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

    def make_var(declaration, base_value):
        varname = declaration.varname
        value = base_value
        if declaration.atomic:
            value = Expression(value, modifier='(?>')
        if declaration.capture:
            value = Expression(value, modifier='(?P<%s>' % varname)
            t.lexer.captures.add(varname)
        return Variable(varname, value, assignment.lineno)

    def define(declaration):
        var = make_var(declaration, assignment.value)
        try: # check the deepest scope for varname (every scope supersets its parent, so checking only the deepeset is sufficient)
            prev_def = scopes[-1][var.name]
        except KeyError: # not already defined, OK to define it
            for scope in scopes:
                scope[var.name] = var
        else: # already defined
            raise OprexSyntaxError(t.lineno(1),
                "'%s' is a built-in variable and cannot be redefined" % var.name
                if prev_def.is_builtin() else
                    "Names must be unique within a scope, '%s' is already defined (previous definition at line %d)"
                        % (var.name, prev_def.lineno))
        return var
    t[0] = map(define, assignment.declarations)


def p_assignment(t):
    '''assignment : declaration equals assignment
                  | declaration equals expression
                  | declaration COLON  charclass'''
    declaration = t[1]
    lineno = t.lineno(1)
    if isinstance(t[3], Assignment):
        assignment = t[3]
        assignment.declarations.append(declaration)
    else:
        value = t[3]
        assignment = Assignment([declaration], value, lineno)
    t[0] = assignment


def p_equals(t):
    '''equals :            EQUALSIGN
              | WHITESPACE EQUALSIGN
              |            EQUALSIGN WHITESPACE
              | WHITESPACE EQUALSIGN WHITESPACE'''


def p_declaration(t):
    '''declaration :        VARNAME
                   | DOT    VARNAME
                   |     LT VARNAME GT
                   | DOT LT VARNAME GT'''
    capture = t[len(t)-1] == '>'
    varname = t[len(t)-2] if capture else t[len(t)-1]
    atomic  = t[1] == '.'
    t[0] = VariableDeclaration(varname, capture, atomic)


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


def scope_check(t, optional_block, referenced_vars):
    if optional_block:
        for var in optional_block:
            if var.name not in referenced_vars:
                raise OprexSyntaxError(var.lineno, "'%s' is defined but not used (by its parent expression)" % var.name)
        t.lexer.scopes.pop()


lexer0 = lex.lex()
def build_lexer(source_lines):
    lexer = lexer0.clone()
    lexer.source_lines = source_lines
    lexer.input('\n'.join(source_lines)) # all newlines are now just \n, simplifying the lexer
    lexer.indent_stack = [0] # for keeping track of indentation depths
    lexer.captures = set()
    lexer.backreferences = set()
    lexer.subroutine_calls = set()
    lexer.scopes = [{
        'alpha'     : Variable('alpha',     CharClass('[a-zA-Z]',        is_set_op=False), lineno=0),
        'upper'     : Variable('upper',     CharClass('[A-Z]',           is_set_op=False), lineno=0),
        'lower'     : Variable('lower',     CharClass('[a-z]',           is_set_op=False), lineno=0),
        'alnum'     : Variable('alnum',     CharClass('[a-zA-Z0-9]',     is_set_op=False), lineno=0),
        'digit'     : Variable('digit',     CharClass(r'\d',             is_set_op=False), lineno=0),
        'space'     : Variable('space',     CharClass(' ',               is_set_op=False), lineno=0),
        'linechar'  : Variable('linechar',  CharClass(r'[\r\n\x0B\x0C]', is_set_op=False), lineno=0),
        'whitechar' : Variable('whitechar', CharClass(r'\s',             is_set_op=False), lineno=0),
        'wordchar'  : Variable('wordchar',  CharClass(r'\w',             is_set_op=False), lineno=0),
        '.'         : Variable('.',         Expression(r'\b'),                             lineno=0),
        '_'         : Variable('_',         Expression(r'\B'),                             lineno=0),
        'SoS'       : Variable('SoS',       Expression(r'\A'),                             lineno=0),
        'EoS'       : Variable('EoS',       Expression(r'\Z'),                             lineno=0),
        'SoL'       : Variable('SoL',       Expression(r'^'),                              lineno=0),
        'EoL'       : Variable('EoL',       Expression(r'$'),                              lineno=0),
        'any'       : Variable('any',       Expression('(?s:.)'),                          lineno=0),
        'uany'      : Variable('uany',      Expression(r'\X'),                             lineno=0),
    }]
    return CustomLexer(lexer)


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


parser = yacc.yacc()
def parse(lexer):
    return unicode(parser.parse(lexer=lexer, tracking=True))


def check_captures(lexer):
    def check(type, lookups):
        for lookup in lookups:
            if lookup.varname not in lexer.captures:
                errmsg = "Invalid %s: '%s' is not defined/not a capture" % (type, lookup.varname)
                raise OprexSyntaxError(lookup.lineno, errmsg)
    check('subroutine call', lexer.subroutine_calls)
    check('backreference', lexer.backreferences)


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
