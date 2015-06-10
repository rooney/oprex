# -*- coding: utf-8 -*-

import unittest, regex
from oprex import oprex, OprexSyntaxError

# class TestErrorHandling(unittest.TestCase):
#     def given(self, oprex_source, expect_error):
#         expect_error = '\n' + expect_error
#         try:
#             oprex(oprex_source)
#         except Exception as err:
#             got_error = err.message
#         else:
#             got_error = ''

#         if got_error != expect_error:
#             msg = 'For input: %s\n----------------------------- Got Error: -----------------------------%s\n\n-------------------------- Expected Error: ---------------------------%s'
#             raise AssertionError(msg % (
#                 oprex_source or '(empty string)', 
#                 got_error or '\n(no error)', 
#                 expect_error or '\n(no error)',
#             ))


#     def test_white_guards(self):
#         self.given('one-liner input',
#         expect_error='Line 1: First line must be blank, not: one-liner input')

#         self.given('''something in the first line
#         ''',
#         expect_error='Line 1: First line must be blank, not: something in the first line')

#         self.given('''
#         something in the last line''',
#         expect_error='Line 2: Last line must be blank, not:         something in the last line')


#     def test_unknown_symbol(self):
#         self.given('''
#             `@$%^&;{}[]\\
#         ''',
#         expect_error='Line 2: Syntax error at or near: `@$%^&;{}[]\\')


#     def test_unexpected_token(self):
#         self.given('''
#             /to/be/?
#         ''',
#         expect_error='''Line 2: Unexpected QUESTMARK
#             /to/be/?
#                    ^''')

#         self.given('''
#             root
#                 branch
#         ''',
#         expect_error='''Line 3: Unexpected NEWLINE
#                 branch
#                       ^''')

#         self.given('''
#             root
#                 root = '/'
#             root2
#         ''',
#         expect_error='''Line 4: Unexpected VARNAME
#             root2
#             ^''')

#         self.given('''
#             root
#                 root = '/'\nroot2
#         ''',
#         expect_error='Line 4: Unexpected VARNAME\nroot2\n^')

#         self.given('''
# *)          /warming/and/warming/
#         ''',
#         expect_error='Line 2: Unexpected GLOBALMARK\n*)          /warming/and/warming/\n^')

#         self.given('''
#             /greeting/world/
#                 greeting = 'hello'
#                     world = 'world'
#         ''',
#         expect_error="Line 4: 'world' is defined but not used (by its parent expression)")


#     def test_indentation_error(self):
#         self.given('''
#             /greeting/world/
#                 greeting = 'hello'
#                  world = 'world'
#         ''',
#         expect_error="Line 4: 'world' is defined but not used (by its parent expression)")

#         self.given('''
#             root
#                 branch
#                misaligned
#         ''',
#         expect_error='Line 4: Indentation error')

#         self.given('''
#                 root
#                     branch
#             hyperroot
#         ''',
#         expect_error='Line 4: Indentation error')


#     def test_correct_error_line_numbering(self):
#         self.given('''
#             /greeting/world/
#                 greeting = 'hello'

#                     world = 'world'
#         ''',
#         expect_error="Line 5: 'world' is defined but not used (by its parent expression)")

#         self.given('''

#             /greeting/world/


#                 greeting = 'hello'

#                  world = 'world'
#         ''',
#         expect_error="Line 8: 'world' is defined but not used (by its parent expression)")

#         self.given('''
#             /greeting/world/
#                 greeting = 'hello'


#                world = 'world'
#         ''',
#         expect_error='Line 6: Indentation error')

#         self.given('''
#             warming


#             *)  warming = 'global'
#         ''',
#         expect_error="Line 5: The GLOBALMARK *) must be put at the line's beginning")


#     def test_mixed_indentation(self):
#         self.given('''
#             \tthis_line_mixes_tab_and_spaces_for_indentation
#         ''',
#         expect_error='Line 2: Cannot mix space and tab for indentation')

#         self.given('''
#             /tabs/vs/spaces/
# \t\ttabs = 'this line is tabs-indented'
#                 spaces = 'this line is spaces-indented'
#         ''',
#         expect_error='Line 3: Inconsistent indentation character')


#     def test_undefined_variable(self):
#         self.given('''
#             bigfoot
#         ''',
#         expect_error="Line 2: 'bigfoot' is not defined")

#         self.given('''
#             /horses/and/unicorns/
#                 horses = 'Thoroughbreds'
#                 and = ' and '
#         ''',
#         expect_error="Line 2: 'unicorns' is not defined")

#         self.given('''
#             /unicorns/and/horses/
#                 horses = 'Thoroughbreds'
#                 and = ' and '
#         ''',
#         expect_error="Line 2: 'unicorns' is not defined")

#         self.given('''
#             unicorn
#                 unicorn = unicorn
#         ''',
#         expect_error="Line 3: 'unicorn' is not defined")


#     def test_illegal_variable_name(self):
#         self.given('''
#             101dalmatians
#                 101dalmatians = 101 of 'dalmatians'
#         ''',
#         expect_error='''Line 2: Unexpected VARNAME
#             101dalmatians
#                ^''')
        
#         self.given('''
#             /101dalmatians/
#                 101dalmatians = 101 of 'dalmatians'
#         ''',
#         expect_error='''Line 2: Unexpected NUMBER
#             /101dalmatians/
#              ^''')
        
#         self.given('''
#             /_/
#                 _ = 'underscore'
#         ''',
#         expect_error='''Line 3: Unexpected UNDERSCORE
#                 _ = 'underscore'
#                 ^''')


#     def test_duplicate_variable(self):
#         self.given(u'''
#             dejavu
#                 dejavu = 'Déjà vu'
#                 dejavu = 'Déjà vu'
#         ''',
#         expect_error="Line 4: Names must be unique within a scope, 'dejavu' is already defined (previous definition at line 3)")

#         self.given(u'''
#             dejavu
#                 dejavu = dejavu = 'Déjà vu'
#         ''',
#         expect_error="Line 3: Names must be unique within a scope, 'dejavu' is already defined (previous definition at line 3)")

#         self.given('''
#             /subject/predicate/object/
#                 subject = /article/adjective/noun/
# *)                  article = 'the'
# *)                  adjective = /speed/color/
#                         speed = 'quick'
#                         color = 'brown'
# *)                  noun = 'fox'
#                 predicate = /verb/adverb/
#                     verb = 'jumps'
#                     adverb = 'over'
#                 object = /article/adjective/noun/
#                     article = 'an'
#         ''',
#         expect_error="Line 13: Names must be unique within a scope, 'article' is already defined (previous definition at line 4)")


#     def test_unused_variable(self):
#         self.given('''
#             /alice/bob/
#                 alice = 'alice'
#                 bob = 'bob'
#                 trudy = 'trudy'
#         ''',
#         expect_error="Line 5: 'trudy' is defined but not used (by its parent expression)")

#         self.given('''
#             /alice/bob/
#                 alice = 'alice'
#                 bob = robert
#                     robert = 'bob'
#                     doe = 'doe'
#         ''',
#         expect_error="Line 6: 'doe' is defined but not used (by its parent expression)")


#     def test_unclosed_literal(self):
#         self.given('''
#             mcd
#                 mcd = 'McDonald's
#         ''',
#         expect_error='''Line 3: Unexpected VARNAME
#                 mcd = 'McDonald's
#                                 ^''')
        
#         self.given('''
#             "she said \\"Hi\\"
#         ''',
#         expect_error='Line 2: Syntax error at or near: "she said \\"Hi\\"')
        
#         self.given('''
#             quotes_mismatch
#                 quotes_mismatch = "'
#         ''',
#         expect_error="""Line 3: Syntax error at or near: "'""")


#     def test_invalid_string_escape(self):
#         self.given('''
#             '\N{KABAYAN}'
#         ''',
#         expect_error="Line 2: undefined character name 'KABAYAN'")

#         self.given(u'''
#             '\N{APOSTROPHE}'
#         ''',
#         expect_error="Line 2: Syntax error at or near: '")


#     def test_invalid_global_mark(self):
#         self.given('''
#             *)
#         ''',
#         expect_error="Line 2: The GLOBALMARK *) must be put at the line's beginning")

#         self.given('''
# *)
#         ''',
#         expect_error='Line 2: Indentation required after GLOBALMARK *)')

#         self.given('''
# *)\t
#         ''',
#         expect_error='Line 2: Unexpected GLOBALMARK\n*) \n^')

#         self.given('''
# *)warming
#         ''',
#         expect_error='Line 2: Indentation required after GLOBALMARK *)')

#         self.given('''
# *)          warming
#         ''',
#         expect_error='Line 2: Unexpected GLOBALMARK\n*)          warming\n^')

#         self.given('''
#             warming
#                 *)warming = 'global'
#         ''',
#         expect_error="Line 3: The GLOBALMARK *) must be put at the line's beginning")

#         self.given('''
#             warming
#             *)  warming = 'global'
#         ''',
#         expect_error="Line 3: The GLOBALMARK *) must be put at the line's beginning")

#         self.given('''
#             warming
#                 warming*) = 'global'
#         ''',
#         expect_error="Line 3: Syntax error at or near: *) = 'global'")

#         self.given('''
#             warming
#                 warming = global *)
#         ''',
#         expect_error="Line 3: Syntax error:                 warming = global *)")

#         self.given('''
#             warming
#                 warming = *) 'global'
#         ''',
#         expect_error="Line 3: Syntax error:                 warming = *) 'global'")

#         self.given('''
#             warming
#                 warming *) = 'global'
#         ''',
#         expect_error="Line 3: Syntax error:                 warming *) = 'global'")

#         self.given('''
#             warming
# *)          *)  warming = 'global'
#         ''',
#         expect_error='Line 3: Syntax error: *)          *)  ')

#         self.given('''
#             warming
# *)              warming*) = 'global'
#         ''',
#         expect_error="Line 3: Syntax error at or near: *) = 'global'")

#         self.given('''
#             warming
# *)              warming = global *)
#         ''',
#         expect_error="Line 3: Syntax error: *)              warming = global *)")

#         self.given('''
#             warming
#                 warming = 'global'
# *)              
#         ''',
#         expect_error="Line 4: Unexpected NEWLINE\n*)              \n                ^")

#         self.given('''
#             warming
#                 warming = 'global'
# *)
#         ''',
#         expect_error="Line 4: Indentation required after GLOBALMARK *)")

#         self.given('''
#             warming
#                 warming = 'global'
# *)              junk
#         ''',
#         expect_error="Line 4: Unexpected NEWLINE\n*)              junk\n                    ^")

#         self.given('''
#             warming
#                 warming = 'global'
# *)            *)junk
#         ''',
#         expect_error="Line 4: Syntax error: *)            *)")

#         self.given('''
#             warming
#                 warming = 'global'
# *)              *)
#         ''',
#         expect_error="Line 4: Syntax error: *)              *)")

#         self.given('''
#             warming
#                 warming = 'global'
# *)            *)
#         ''',
#         expect_error="Line 4: Syntax error: *)            *)")


#     def test_global_aliasing(self):
#         self.given('''
#             /oneoneone/oneone/one/
#                 oneoneone = /satu/uno/ichi/
#                     satu = '1'
# *)                  uno = ichi = satu
#                 oneone = /uno/ichi/
#                 one = ichi
#                     ichi: 1
#         ''',
#         expect_error="Line 8: Names must be unique within a scope, 'ichi' is already defined (previous definition at line 5)")

#         self.given('''
#             /oneoneone/oneone/one/
#                 oneoneone = /satu/uno/ichi/
#                     satu = '1'
# *)                  uno = ichi = satu
#                 oneone = /uno/ichi/
#                 one = uno
#                     uno: 1
#         ''',
#         expect_error="Line 8: Names must be unique within a scope, 'uno' is already defined (previous definition at line 5)")

#         self.given('''
#             /oneoneone/oneone/one/
#                 oneoneone = /satu/uno/ichi/
#                     satu = '1'
# *)                  uno = ichi = satu
#                 oneone = /uno/ichi/
#                 one = satu
#         ''',
#         expect_error="Line 7: 'satu' is not defined")

#         self.given('''
#             /oneoneone/oneone/one/
#                 oneoneone = /satu/uno/ichi/
# *)                  satu = '1'
#                     uno = ichi = satu
#                 one = satu
#                 oneone = /uno/ichi/
#         ''',
#         expect_error="Line 7: 'uno' is not defined")


#     def test_invalid_charclass(self):
#         self.given('''
#             empty_charclass
#                 empty_charclass:
#         ''',
#         expect_error='Line 3: Empty character class is not allowed')

#         self.given('''
#             noSpaceAfterColon
#                 noSpaceAfterColon:n o
#         ''',
#         expect_error='Line 3: Character class definition requires space after the : (colon)')

#         self.given('''
#             diphtong
#                 diphtong: ae au
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: ae')

#         self.given('''
#             miscolon
#                 miscolon: /colon/should/be/equal/sign/
#         ''',
#         expect_error='Line 3: /colon/should/be/equal/sign/ compiles to \p{colon/should/be/equal/sign/} which is rejected by the regex engine with error message: bad fuzzy constraint')

#         self.given('''
#             miscolon
#                 miscolon: 'colon should be equal sign'
#         ''',
#         expect_error="Line 3: Not a valid character class keyword: 'colon")

#         self.given('''
#             /A/a/
#                 A: a: A a
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: a:')

#         self.given('''
#             /A/a/
#                 A: a = A a
#         ''',
#         expect_error="Line 2: 'a' is not defined")

#         self.given('''
#             /A/a/
#                 A: a = A
#         ''',
#         expect_error="Line 2: 'a' is not defined")

#         self.given('''
#             /shouldBeColon/
#                 shouldBeColon = A a
#         ''',
#         expect_error='''Line 3: Unexpected VARNAME
#                 shouldBeColon = A a
#                                   ^''')

#         self.given('''
#             mixedAssignment
#                 mixedAssignment : = x
#         ''',
#         expect_error='''Line 3: Unexpected COLON
#                 mixedAssignment : = x
#                                 ^''')

#         self.given('''
#             mixedAssignment
#                 mixedAssignment := x
#         ''',
#         expect_error='Line 3: Character class definition requires space after the : (colon)')

#         self.given('''
#             mixedAssignment
#                 mixedAssignment:= x
#         ''',
#         expect_error='Line 3: Character class definition requires space after the : (colon)')

#         self.given('''
#             mixedAssignment
#                 mixedAssignment=: x
#         ''',
#         expect_error='''Line 3: Unexpected COLON
#                 mixedAssignment=: x
#                                 ^''')

#         self.given('''
#             mixedAssignment
#                 mixedAssignment =: x
#         ''',
#         expect_error='''Line 3: Unexpected COLON
#                 mixedAssignment =: x
#                                  ^''')

#         self.given('''
#             x
#                 x: /IsAwesome
#         ''',
#         expect_error='Line 3: /IsAwesome compiles to \p{IsAwesome} which is rejected by the regex engine with error message: unknown property')

#         self.given('''
#             x
#                 x: :KABAYAN_SABA_KOTA
#         ''',
#         expect_error='Line 3: :KABAYAN_SABA_KOTA compiles to \N{KABAYAN SABA KOTA} which is rejected by the regex engine with error message: undefined character name')

#         self.given(r'''
#             x
#                 x: \N{KABAYAN}
#         ''',
#         expect_error='Line 3: \N{KABAYAN} compiles to \N{KABAYAN} which is rejected by the regex engine with error message: undefined character name')

#         self.given(r'''
#             x
#                 x: \o
#         ''',
#         expect_error='Line 3: Bad escape sequence: \o')

#         self.given(r'''
#             x
#                 x: \w
#         ''',
#         expect_error='Line 3: Bad escape sequence: \w')

#         self.given(r'''
#             x
#                 x: \'
#         ''',
#         expect_error="Line 3: Bad escape sequence: \\'")

#         self.given(r'''
#             x
#                 x: \"
#         ''',
#         expect_error='Line 3: Bad escape sequence: \\"')

#         self.given(r'''
#             x
#                 x: \\
#         ''',
#         expect_error=r'Line 3: Bad escape sequence: \\')

#         self.given(r'''
#             x
#                 x: \ron
#         ''',
#         expect_error=r'Line 3: Bad escape sequence: \ron')

#         self.given(r'''
#             x
#                 x: \u123
#         ''',
#         expect_error='Line 3: Bad escape sequence: \u123')

#         self.given(r'''
#             x
#                 x: \U1234
#         ''',
#         expect_error='Line 3: Bad escape sequence: \U1234')

#         self.given(r'''
#             x
#                 x: \u12345
#         ''',
#         expect_error='Line 3: Bad escape sequence: \u12345')


#     def test_invalid_char(self):
#         self.given('''
#             x
#                 x: u1234
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: u1234')

#         self.given('''
#             x
#                 x: u+ab
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: u+ab')

#         self.given('''
#             x
#                 x: u+123z
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: u+123z')

#         self.given('''
#             x
#                 x: U+123z
#         ''',
#         expect_error='Line 3: Syntax error U+123z should be U+hexadecimal')

#         self.given('''
#             x
#                 x: U+123456789
#         ''',
#         expect_error='Line 3: Syntax error U+123456789 out of range')

#         self.given('''
#             x
#                 x: U+
#         ''',
#         expect_error='Line 3: Syntax error U+ should be U+hexadecimal')

#         self.given('''
#             x
#                 x: :YET_ANOTHER_CHARACTER_THAT_SHOULD_NOT_BE_IN_UNICODE
#         ''',
#         expect_error='Line 3: :YET_ANOTHER_CHARACTER_THAT_SHOULD_NOT_BE_IN_UNICODE compiles to \N{YET ANOTHER CHARACTER THAT SHOULD NOT BE IN UNICODE} which is rejected by the regex engine with error message: undefined character name')

#         # unicode character name should be in uppercase
#         self.given('''
#             x
#                 x: check-mark
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: check-mark')

#         self.given('''
#             x
#                 x: @omic
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: @omic')

#         self.given('''
#             x
#                 x: awe$ome
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: awe$ome')


#     def test_invalid_range(self):
#         self.given('''
#             x
#                 x: ..
#         ''',
#         expect_error='Line 3: Invalid character range: ..')

#         self.given('''
#             x
#                 x: infinity..
#         ''',
#         expect_error='Line 3: Invalid character range: infinity..')

#         self.given('''
#             x
#                 x: ..bigbang
#         ''',
#         expect_error='Line 3: Invalid character range: ..bigbang')

#         self.given('''
#             x
#                 x: bigcrunch..bigbang
#         ''',
#         expect_error='Line 3: Invalid character range: bigcrunch..bigbang')

#         self.given('''
#             x
#                 x: A...Z
#         ''',
#         expect_error='Line 3: Invalid character range: A...Z')

#         self.given('''
#             x
#                 x: 1..2..3
#         ''',
#         expect_error='Line 3: Invalid character range: 1..2..3')

#         self.given('''
#             x
#                 x: /IsAlphabetic..Z
#         ''',
#         expect_error='Line 3: Invalid character range: /IsAlphabetic..Z')

#         self.given('''
#             x
#                 x: +alpha..Z
#         ''',
#         expect_error='Line 3: Invalid character range: +alpha..Z')


#     def test_invalid_charclass_include(self):
#         self.given('''
#             x
#                 x: +1
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: +1')

#         self.given('''
#             x
#                 x: +7even
#                     7even: 7
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: +7even')

#         self.given('''
#             x
#                 x: +bang!
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: +bang!')

#         self.given('''
#             x
#                 x: ++
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: ++')

#         self.given('''
#             x
#                 x: ++
#                     +: p l u s
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: ++')

#         self.given('''
#             x
#                 x: +!awe+some
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: +!awe+some')

#         self.given('''
#             x
#                 x: +__special__
#                     __special__: x
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: +__special__')

#         self.given('''
#             x
#                 x: y
#                     y: m i s n g +
#         ''',
#         expect_error="Line 4: 'y' is defined but not used (by its parent expression)")

#         self.given('''
#             x
#                 x: +y
#                     y = 'should be a charclass'
#         ''',
#         expect_error="Line 3: Cannot include 'y': not a character class")

#         self.given(u'''
#             vowhex
#                 vowhex: +!vowel +hex
#                     vowel: a i u e o A I U E O
#                     hex: 0..9 a..f A..F
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: +!vowel')

#         self.given(u'''
#             /x/y/
#                 x = 'x'
#                 y: +x
#         ''',
#         expect_error="Line 4: Cannot include 'x': not a character class")

#         self.given(u'''
#             /plus/minus/pmz/
#                 plus: +
#                 minus = '-' -- gotcha: exactly-same output with "minus: -" but not includable 
#                 pmz: +plus +minus z
#         ''',
#         expect_error="Line 5: Cannot include 'minus': not a character class")

#         self.given(u'''
#             /plus/minus/pmz/
#                 plus: +
#                 minus = '-'
#                 pmz: +plus +dash z
#                     dash: +minus
#         ''',
#         expect_error="Line 6: Cannot include 'minus': not a character class")


#     def test_invalid_charclass_operation(self):
#         self.given(u'''
#             missing_arg
#                 missing_arg: /Alphabetic and
#         ''',
#         expect_error="Line 3: Incorrect use of binary 'and' operator")

#         self.given(u'''
#             missing_arg
#                 missing_arg: and /Alphabetic
#         ''',
#         expect_error="Line 3: Incorrect use of binary 'and' operator")

#         self.given(u'''
#             missing_arg
#                 missing_arg: /Alphabetic not
#         ''',
#         expect_error="Line 3: Incorrect use of binary 'not' operator")

#         self.given(u'''
#             missing_arg
#                 missing_arg: not /Alphabetic
#         ''',
#         expect_error="Line 3: Incorrect use of binary 'not' operator")

#         self.given(u'''
#             missing_args
#                 missing_args: and
#         ''',
#         expect_error="Line 3: Incorrect use of binary 'and' operator")

#         self.given(u'''
#             missing_args
#                 missing_args: not
#         ''',
#         expect_error="Line 3: Incorrect use of binary 'not' operator")

#         self.given(u'''
#             missing_args
#                 missing_args: not:
#         ''',
#         expect_error="Line 3: Incorrect use of unary 'not:' operator")


#     def test_invalid_quantifier(self):
#         self.given(u'''
#             3 of
#         ''',
#         expect_error='''Line 2: Unexpected VARNAME
#             3 of
#               ^''')

#         self.given(u'''
#             3 of          
#                 of = 'trailing spaces above after the "of"'
#         ''',
#         expect_error='''Line 2: Unexpected VARNAME
#             3 of          
#               ^''')

#         self.given(u'''
#             3 of -- 3 of what?
#         ''',
#         expect_error='''Line 2: Unexpected VARNAME
#             3 of -- 3 of what?
#               ^''')

#         self.given(u'''
#             3 of-- 3 of what?
#         ''',
#         expect_error='''Line 2: Unexpected VARNAME
#             3 of-- 3 of what?
#               ^''')

#         self.given(u'''
#             3 of of--
#         ''',
#         expect_error='''Line 2: Unexpected MINUS
#             3 of of--
#                    ^''')

#         self.given(u'''
#             3 alpha
#         ''',
#         expect_error='''Line 2: Unexpected VARNAME
#             3 alpha
#               ^''')

#         self.given(u'''
#             3 ofalpha
#         ''',
#         expect_error='''Line 2: Unexpected VARNAME
#             3 ofalpha
#               ^''')

#         self.given(u'''
#             3of alpha
#         ''',
#         expect_error='''Line 2: Unexpected VARNAME
#             3of alpha
#              ^''')

#         self.given(u'''
#             3 o falpha
#         ''',
#         expect_error='''Line 2: Unexpected VARNAME
#             3 o falpha
#               ^''')

#         self.given(u'''
#             3 office alpha
#         ''',
#         expect_error='''Line 2: Unexpected VARNAME
#             3 office alpha
#               ^''')

#         self.given(u'''
#             3. of alpha
#         ''',
#         expect_error='''Line 2: Unexpected WHITESPACE
#             3. of alpha
#               ^''')

#         self.given(u'''
#             3... of alpha
#         ''',
#         expect_error='''Line 2: Unexpected DOT
#             3... of alpha
#                ^''')

#         self.given(u'''
#             3+ of alpha
#         ''',
#         expect_error='''Line 2: Unexpected PLUS
#             3+ of alpha
#              ^''')

#         self.given(u'''
#             3+3 of alpha
#         ''',
#         expect_error='''Line 2: Unexpected PLUS
#             3+3 of alpha
#              ^''')

#         self.given(u'''
#             3..2 of alpha
#         ''',
#         expect_error='Line 2: Repeat max must be > min')

#         self.given(u'''
#             2..2 of alpha
#         ''',
#         expect_error='Line 2: Repeat max must be > min')

#         self.given(u'''
#             1..1 of alpha
#         ''',
#         expect_error='Line 2: Repeat max must be > min')

#         self.given(u'''
#             0..0 of alpha
#         ''',
#         expect_error='Line 2: Repeat max must be > min')

#         self.given(u'''
#             1 ..3 of alpha
#         ''',
#         expect_error='''Line 2: Unexpected DOT
#             1 ..3 of alpha
#               ^''')

#         self.given(u'''
#             1.. 3 of alpha
#         ''',
#         expect_error='''Line 2: Unexpected NUMBER
#             1.. 3 of alpha
#                 ^''')

#         self.given(u'''
#             1 .. of alpha
#         ''',
#         expect_error='''Line 2: Unexpected DOT
#             1 .. of alpha
#               ^''')

#         self.given(u'''
#             1 <<- of alpha
#         ''',
#         expect_error='''Line 2: Unexpected MINUS
#             1 <<- of alpha
#                 ^''')

#         self.given(u'''
#             1 <<+ of alpha
#         ''',
#         expect_error='''Line 2: Unexpected WHITESPACE
#             1 <<+ of alpha
#                  ^''')

#         self.given(u'''
#             1 <<+..0 of alpha
#         ''',
#         expect_error='Line 2: Repeat max must be > min')

#         self.given(u'''
#             0 <<+..0 of alpha
#         ''',
#         expect_error='Line 2: Repeat max must be > min')

#         self.given(u'''
#             1 <<+..1 of alpha
#         ''',
#         expect_error='Line 2: Repeat max must be > min')

#         self.given(u'''
#             2 <<+..2 of alpha
#         ''',
#         expect_error='Line 2: Repeat max must be > min')

#         self.given(u'''
#             2..1 <<- of alpha
#         ''',
#         expect_error='Line 2: Repeat max must be > min')

#         self.given(u'''
#             ? <<- of alpha
#         ''',
#         expect_error='''Line 2: Unexpected LT
#             ? <<- of alpha
#               ^''')


#     def test_commenting_error(self):
#         self.given(u'''
#             - this comment is missing another - prefix
#         ''',
#         expect_error='''Line 2: Unexpected MINUS
#             - this comment is missing another - prefix
#             ^''')

#         self.given(u'''
#             1 of vowel - this comment is missing another - prefix
#                 vowel: a i u e o 
#         ''',
#         expect_error='''Line 2: Unexpected WHITESPACE
#             1 of vowel - this comment is missing another - prefix
#                       ^''')

#         self.given(u'''
#             1 of vowel- this comment is missing another - prefix
#                 vowel: a i u e o 
#         ''',
#         expect_error='''Line 2: Unexpected MINUS
#             1 of vowel- this comment is missing another - prefix
#                       ^''')

#         self.given(u'''
#             1 of vowel
#                 vowel: a i u e o - this comment is missing another - prefix
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: this')

#         self.given(u'''
#             1 of vowel
#                 vowel: a i u e o- this comment is missing another - prefix
#         ''',
#         expect_error='Line 3: Not a valid character class keyword: o-')

#         self.given('''
#             /comment/-- whitespace required before the "--"
#                 comment = 'first'
#         ''',
#         expect_error='''Line 2: Unexpected MINUS
#             /comment/-- whitespace required before the "--"
#                      ^''')

#         self.given('''
#             /comment/--
#                 comment = 'first'
#         ''',
#         expect_error='''Line 2: Unexpected MINUS
#             /comment/--
#                      ^''')


#     def test_invalid_reference(self):
#         self.given(u'''
#             =missing
#         ''',
#         expect_error="Line 2: Invalid backreference: 'missing' is not defined/not a capture")

#         self.given(u'''
#             =missing?
#         ''',
#         expect_error="Line 2: Invalid backreference: 'missing' is not defined/not a capture")

#         self.given(u'''
#             &missing
#         ''',
#         expect_error="Line 2: Invalid subroutine call: 'missing' is not defined/not a capture")

#         self.given(u'''
#             /&missing/
#         ''',
#         expect_error="Line 2: Invalid subroutine call: 'missing' is not defined/not a capture")

#         self.given(u'''
#             &=invalid_mix
#         ''',
#         expect_error='''Line 2: Unexpected EQUALSIGN
#             &=invalid_mix
#              ^''')

#         self.given(u'''
#             =&invalid_mix
#         ''',
#         expect_error='''Line 2: Unexpected AMPERSAND
#             =&invalid_mix
#              ^''')

#         self.given(u'''
#             =alpha
#         ''',
#         expect_error="Line 2: Invalid backreference: 'alpha' is not defined/not a capture")

#         self.given(u'''
#             /alpha/&alpha/
#         ''',
#         expect_error="Line 2: Invalid subroutine call: 'alpha' is not defined/not a capture")

#         self.given(u'''
#             /alpha/&alpha/
#                 alpha: a..z A..Z
#         ''',
#         expect_error="Line 3: 'alpha' is a built-in variable and cannot be redefined")

#         self.given(u'''
#             /bang/=bang/
#                 bang: b a n g !
#         ''',
#         expect_error="Line 2: Invalid backreference: 'bang' is not defined/not a capture")


#     def test_invalid_boundaries(self):
#         self.given(u'''
#             /cat./
#                 cat = 'cat'
#         ''',
#         expect_error='''Line 2: Unexpected DOT
#             /cat./
#                 ^''')

#         self.given(u'''
#             /.cat/
#                 cat = 'cat'
#         ''',
#         expect_error='''Line 2: Unexpected VARNAME
#             /.cat/
#               ^''')

#         self.given(u'''
#             /cat_/
#                 cat = 'cat'
#         ''',
#         expect_error="Line 2: 'cat_' is not defined")

#         self.given(u'''
#             /cat/
#                 cat = 'cat' .
#         ''',
#         expect_error='''Line 3: Unexpected WHITESPACE
#                 cat = 'cat' .
#                            ^''')

#         self.given(u'''
#             /cat/
#                 cat = 'cat'__
#         ''',
#         expect_error='''Line 3: Unexpected VARNAME
#                 cat = 'cat'__
#                            ^''')

#         self.given(u'''
#             /_/
#                 _ = 'underscore'
#         ''',
#         expect_error='''Line 3: Unexpected UNDERSCORE
#                 _ = 'underscore'
#                 ^''')

#         self.given(u'''
#             /_./
#         ''',
#         expect_error='''Line 2: Unexpected DOT
#             /_./
#               ^''')


#     def test_invalid_flags(self):
#         self.given(u'''
#             (pirate) 'carribean'
#         ''',
#         expect_error="Line 2: Unknown flag 'pirate'. Supported flags are: ascii bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse unicode verbose version0 version1 word")
 
#         self.given(u'''
#             (-pirate) 'carribean'
#         ''',
#         expect_error="Line 2: Unknown flag '-pirate'. Supported flags are: ascii bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse unicode verbose version0 version1 word")
 
#         self.given(u'''
#             (--ignorecase) 'carribean'
#         ''',
#         expect_error="Line 2: Unknown flag '--ignorecase'. Supported flags are: ascii bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse unicode verbose version0 version1 word")
 
#         self.given(u'''
#             (unicode-ignorecase)
#             alpha
#         ''',
#         expect_error="Line 2: Unknown flag 'unicode-ignorecase'. Supported flags are: ascii bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse unicode verbose version0 version1 word")

#         self.given(u'''
#             (unicode) alpha
#         ''',
#         expect_error="Line 2: 'unicode' is a global flag and must be set using global flag syntax, not scoped.")

#         self.given(u'''
#             (ignorecase)alpha
#         ''',
#         expect_error='''Line 2: Unexpected VARNAME
#             (ignorecase)alpha
#                         ^''')

#         self.given(u'''
#             (ignorecase)
#              alpha
#         ''',
#         expect_error='Line 3: Unexpected INDENT')

#         self.given(u'''
#             (ignorecase -ignorecase) alpha
#         ''',
#         expect_error='Line 2: (ignorecase -ignorecase) compiles to (?i-i) which is rejected by the regex engine with error message: bad inline flags: flag turned on and off at position 10')
 
#         self.given(u'''
#             (-ignorecase ignorecase) alpha
#         ''',
#         expect_error='Line 2: (-ignorecase ignorecase) compiles to (?i-i) which is rejected by the regex engine with error message: bad inline flags: flag turned on and off at position 10')
 
#         self.given(u'''
#             (-ignorecase ignorecase unicode)
#             alpha
#         ''',
#         expect_error='Line 2: (-ignorecase ignorecase unicode) compiles to (?iu-i) which is rejected by the regex engine with error message: bad inline flags: flag turned on and off at position 11')
 
#         self.given(u'''
#             (-ignorecase unicode ignorecase)
#             alpha
#         ''',
#         expect_error='Line 2: (-ignorecase unicode ignorecase) compiles to (?ui-i) which is rejected by the regex engine with error message: bad inline flags: flag turned on and off at position 11')
 
#         self.given(u'''
#             (-unicode)
#             alpha
#         ''',
#         expect_error='Line 2: (-unicode) compiles to (?-u) which is rejected by the regex engine with error message: bad inline flags: cannot turn off global flag at position 9')
 
#         self.given(u'''
#             (ignorecase)
#             (-ignorecase)
#         ''',
#         expect_error='''Line 3: Unexpected NEWLINE
#             (-ignorecase)
#                          ^''')
 
#         self.given(u'''
#             (unicode ignorecase)
#             (-ignorecase)
#         ''',
#         expect_error='''Line 3: Unexpected NEWLINE
#             (-ignorecase)
#                          ^''')

#         self.given(u'''
#             (ascii unicode)
#         ''',
#         expect_error='Line 2: (ascii unicode) compiles to (?au) which is rejected by the regex engine with error message: ASCII, LOCALE and UNICODE flags are mutually incompatible')

#         self.given(u'''
#             (unicode ascii)
#         ''',
#         expect_error='Line 2: (unicode ascii) compiles to (?ua) which is rejected by the regex engine with error message: ASCII, LOCALE and UNICODE flags are mutually incompatible')

#         self.given(u'''
#             (ascii locale)
#         ''',
#         expect_error='Line 2: (ascii locale) compiles to (?aL) which is rejected by the regex engine with error message: ASCII, LOCALE and UNICODE flags are mutually incompatible')

#         self.given(u'''
#             (unicode locale)
#         ''',
#         expect_error='Line 2: (unicode locale) compiles to (?uL) which is rejected by the regex engine with error message: ASCII, LOCALE and UNICODE flags are mutually incompatible')

#         self.given(u'''
#             (version0 version1)
#         ''',
#         expect_error='Line 2: (version0 version1) compiles to (?V0V1) which is rejected by the regex engine with error message: 8448')

#         self.given(u'''
#             (version1 version0)
#         ''',
#         expect_error='Line 2: (version1 version0) compiles to (?V1V0) which is rejected by the regex engine with error message: 8448')


class TestOutput(unittest.TestCase):
    def given(self, oprex_source, expect_regex):
        default_flags = '(?V1mw)'
        regex_source = oprex(oprex_source)
        regex_source = regex_source.replace(default_flags, '', 1)
        if regex_source != expect_regex:
            msg = 'For input: %s\n---------------------------- Got Output: -----------------------------\n%s\n\n------------------------- Expected Output: ---------------------------\n%s'
            raise AssertionError(msg % (
                oprex_source or '(empty string)', 
                regex_source or '(empty string)', 
                expect_regex or '(empty string)',
            ))


    def test_empties(self):
        self.given('',
        expect_regex='')

        self.given('''
        ''',
        expect_regex='')

        self.given('''

        ''',
        expect_regex='')
        self.given('''


        ''',
        expect_regex='')


    def test_indentation(self):
        # indentation using space
        self.given('''
            /weather/warming/
                weather = 'local'
*)              warming = 'global'
        ''',
        expect_regex='localglobal')

        # indentation using tab
        self.given('''
/weather/warming/
\tweather = 'local'
*)\twarming = 'global'
        ''',
        expect_regex='localglobal')


    def test_escaping_output(self):
        self.given('''
            stars
                stars = '***'
        ''',
        expect_regex=r'\*\*\*')

        self.given('''
            add
                add: +plus
                    plus: +
        ''',
        expect_regex=r'\+')


    def test_assignment_whitespace(self):
        self.given('''
        /a/b/c/d/e/f/g/h/i/j/k/l/m/
            a='a'
            b= 'b'
            c ='c'
            d = 'd'
            e   ='e'
            f   = 'f'
            g   =   'g'
            h=  'h'
            i = 'i'
            j   =    'j'
            k =     l     =  m  = 'z'
        ''',
        expect_regex='abcdefghijzzz')

        self.given('''
            add
                add: +plus
                    plus: +
        ''',
        expect_regex=r'\+')


    def test_character_class(self):
        self.given('''
            papersize
                papersize = /series/size/
                    series: A B C
                    size: 0 1 2 3 4 5 6 7 8
        ''',
        expect_regex='[ABC][012345678]')

        self.given('''
            /A/a/
                A = a: A a
        ''',
        expect_regex='[Aa][Aa]')

        self.given('''
            /A/a/
                A = a: A a
        ''',
        expect_regex='[Aa][Aa]')

        self.given('''
            x
                x: [ ^ \\ ]
        ''',
        expect_regex='[\\[\\^\\\\\\]]')


    def test_char(self):
        self.given('''
            x
                x: /Alphabetic /Script=Latin /InBasicLatin /IsCyrillic /Script=Cyrillic
        ''',
        expect_regex='[\p{Alphabetic}\p{Script=Latin}\p{InBasicLatin}\p{IsCyrillic}\p{Script=Cyrillic}]')

        self.given('''
            x
                x: U+ab U+AB U+00ab U+00Ab
        ''',
        expect_regex='[\u00ab\u00AB\u00ab\u00Ab]')

        self.given('''
            x
                x: U+12ab U+12AB U+12Ab
        ''',
        expect_regex='[\u12ab\u12AB\u12Ab]')

        self.given('''
            x
                x: U+1234a U+1234A U+01234a
        ''',
        expect_regex='[\U0001234a\U0001234A\U0001234a]')

        self.given('''
            x
                x: :SKULL_AND_CROSSBONES :BIOHAZARD_SIGN :CANCER
        ''',
        expect_regex='[\N{SKULL AND CROSSBONES}\N{BIOHAZARD SIGN}\N{CANCER}]')


    def test_character_range_output(self):
        self.given('''
            x
                x: U+41..Z :LEFTWARDS_ARROW..:LEFT_RIGHT_OPEN-HEADED_ARROW
        ''',
        expect_regex=r'[\u0041-Z\N{LEFTWARDS ARROW}-\N{LEFT RIGHT OPEN-HEADED ARROW}]')

        self.given('''
            need_escape
                need_escape: [ ^ a - z ]
        ''',
        expect_regex=r'[\[\^a\-z\]]')


    def test_charclass_include_output(self):
        self.given(u'''
            op
                op: +add +sub +mul +div
                    add: +
                    sub: -
                    mul: * ×
                    div: / ÷ :
        ''',
        expect_regex=ur'[+\-*×/÷:]')

        self.given(u'''
            aUmlaut
                aUmlaut: +a_with_diaeresis
                    a_with_diaeresis: ä
        ''',
        expect_regex=u'ä')

        self.given(u'''
            aUmlaut
                aUmlaut: +small_a_umlaut
                    small_a_umlaut: +a_with_diaeresis
                        a_with_diaeresis: ä
        ''',
        expect_regex=u'ä')

        self.given(u'''
            aUmlaut
                aUmlaut: +a_with_diaeresis
                    a_with_diaeresis: U+E4
        ''',
        expect_regex=r'\u00E4')

        self.given(u'''
            aUmlaut
                aUmlaut: +a_with_diaeresis
                    a_with_diaeresis: :LATIN_SMALL_LETTER_A_WITH_DIAERESIS
        ''',
        expect_regex=r'\N{LATIN SMALL LETTER A WITH DIAERESIS}')

        self.given(u'''
            alphabetic
                alphabetic: +is_alphabetic
                    is_alphabetic: /Alphabetic
        ''',
        expect_regex=r'\p{Alphabetic}')

        self.given(u'''
            lowaz
                lowaz: +lowerAZ
                    lowerAZ: a..z
        ''',
        expect_regex='[a-z]')

        self.given(u'''
            /hex/
                hex: +hexx +hexy +hexz
                    hexx = hexdigit
                        hexdigit: 0..9
                    hexy = hexz = hexalpha
                        hexalpha: a..f A..F
        ''',
        expect_regex='[0-9a-fA-Fa-fA-F]')

        self.given(u'''
            /xx/dup/
                xx: x X
                dup: +xx
        ''',
        expect_regex='[xX][xX]')

        self.given(u'''
            /cc/
                cc: +yy a
                    yy: y not Y
        ''',
        expect_regex='[[y--Y]a]')

        self.given(u'''
            /cc/
                cc: a +yy
                    yy: y not Y
        ''',
        expect_regex='[a[y--Y]]')

        self.given(u'''
            /cc/
                cc: +xx +yy
                    xx: x not X
                    yy: y not Y
        ''',
        expect_regex='[[x--X][y--Y]]')

        self.given(u'''
            /cc/
                cc: +xx a +yy
                    xx: x not X
                    yy: y not Y
        ''',
        expect_regex='[[x--X]a[y--Y]]')

        self.given(u'''
            /notX/
                notX:  not: X
        ''',
        expect_regex='[^X]')

        self.given(u'''
            /not_X/
                not_X: +notX
                    notX:  not: X
        ''',
        expect_regex='[^X]')

        self.given(u'''
            /notNotX/
                notNotX: not: +notX
                    notX:  not: X
        ''',
        expect_regex='[^[^X]]')

        self.given(u'''
            /plus/minus/pmz/
                plus: +
                minus: -
                pmz: +plus +minus z
        ''',
        expect_regex='\+-[+\-z]')

        self.given(u'''
            vowhex
                vowhex: +vowel +hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_regex='[aiueoAIUEO0-9a-fA-F]')


    def test_charclass_operation_output(self):
        self.given(u'''
            xb123
                xb123: X x +hex not c..f C..D :LATIN_CAPITAL_LETTER_F +vowel and 1 2 3 /Alphabetic
                    hex: 0..9 a..f A..F
                    vowel: a i u e o A I U E O
        ''',
        expect_regex='[Xx0-9a-fA-F--c-fC-D\N{LATIN CAPITAL LETTER F}aiueoAIUEO&&123\p{Alphabetic}]')

        self.given(u'''
            allButU
                allButU: not: U
        ''',
        expect_regex='[^U]')

        self.given(u'''
            nonalpha
                nonalpha: not: /Alphabetic
        ''',
        expect_regex='\P{Alphabetic}')

        self.given(u'''
            otherz
                otherz: +nonz
                    nonz: not: z
        ''',
        expect_regex='[^z]')

        self.given(u'''
            a_or_consonant
                a_or_consonant: A a +consonant 
                    consonant: a..z A..Z not a i u e o A I U E O 
        ''',
        expect_regex='[Aa[a-zA-Z--aiueoAIUEO]]')

        self.given(u'''
            maestro
                maestro: m +ae s t r o 
                    ae: +vowel and +hex not +upper
                        hex: +digit a..f A..F 
                        vowel: a i u e o A I U E O
        ''',
        expect_regex=r'[m[aiueoAIUEO&&\da-fA-F--A-Z]stro]')


    def test_charclass_escape_output(self):
        self.given('''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_regex='[\u0061\U00000061\x61\61]')

        self.given(r'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_regex=r'[\u0061\U00000061\x61\61]')

        self.given(u'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_regex=u'[\u0061\U00000061\x61\61]')

        self.given(ur'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_regex=ur'[\u0061\U00000061\x61\61]')

        self.given(r'''
            allowed_escape
                allowed_escape: \n \r \t \a \b \v \f
        ''',
        expect_regex=r'[\n\r\t\a\b\v\f]')

        self.given(r'''
            unicode_charname
                unicode_charname: \N{AMPERSAND} :AMPERSAND
        ''',
        expect_regex='[\N{AMPERSAND}\N{AMPERSAND}]')


    def test_string_literal(self):
        self.given('''
            'lorem ipsum'
        ''',
        expect_regex='lorem ipsum')

        self.given('''
            "lorem ipsum"
        ''',
        expect_regex='lorem ipsum')

        self.given('''
            "Ron's"
        ''',
        expect_regex="Ron's")

        self.given(r'''
            'Ron\'s'
        ''',
        expect_regex="Ron's")

        self.given('''
            'Ron\\'s'
        ''',
        expect_regex="Ron's")

        self.given('''
            'said "Hi"'
        ''',
        expect_regex='said "Hi"')

        self.given(r'''
            "said \"Hi\""
        ''',
        expect_regex='said "Hi"')

        self.given(r'''
            "name:\toprex\nawesome:\tyes"
        ''',
        expect_regex='name:\\toprex\\nawesome:\\tyes')


    def test_string_interpolation(self):
        self.given('''
            /p/pXs/s/
                p = '%'
                s = 's'
                pXs = /p/X/s/
                    <X> = 'X'
        ''',
        expect_regex='%%(?P<X>X)ss')

        self.given('''
            /p/pXs/s/
                p = '%'
                s = 's'
                <pXs> = /p/X/s/
                    <X> = 'X'
        ''',
        expect_regex='%(?P<pXs>%(?P<X>X)s)s')

        self.given('''
            greeting
                greeting = 'Hello %(name)s'
        ''',
        expect_regex='Hello %\(name\)s')


        self.given('''
            message
                message = /greeting/name/
                    greeting = 'Hello%'
                    name = /salutation/first/last/
                        <salutation> = 'Sir/Madam'
                        first = 's%(first)s'
                        last  = '%(last)s'
        ''',
        expect_regex='Hello%(?P<salutation>Sir/Madam)s%\(first\)s%\(last\)s')


    def test_scoping(self):
        self.given('''
            /subject/predicate/object/
                subject = /article/adjective/noun/
                    article = 'the'
                    adjective = /speed/color/
                        speed = 'quick'
                        color = 'brown'
                    noun = 'fox'
                predicate = /verb/adverb/
                    verb = 'jumps'
                    adverb = 'over'
                object = /article/adjective/noun/
                    article = 'the'
                    adjective = 'lazy'
                    noun = 'dog'
        ''',
        expect_regex='thequickbrownfoxjumpsoverthelazydog')

        self.given('''
            /subject/predicate/object/
                subject = /article/adjective/noun/
*)                  article = 'the'
*)                  adjective = /speed/color/
                        speed = 'quick'
                        color = 'brown'
*)                  noun = 'fox'
                predicate = /verb/adverb/
                    verb = 'jumps'
                    adverb = 'over'
                object = /article/adjective/noun/
        ''',
        expect_regex='thequickbrownfoxjumpsoverthequickbrownfox')

        self.given('''
            /grosir/banana4/papaya4/
                grosir = /ciek/empat/sekawan/
                    ciek: 1
*)                  empat = sekawan: 4
                banana4 = /gedang/sekawan/
                    gedang = 'banana'
                papaya4 = /gedang/opat/
                    gedang = 'papaya'
                    opat = empat
        ''',
        expect_regex='144banana4papaya4')

        self.given('''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
                    satu = '1'
*)                  uno = ichi = satu
                oneone = /uno/ichi/
                one = satu
                    satu: 1
        ''',
        expect_regex='111111')


    def test_aliases(self):
        self.given('''
            /griffin/griffon/gryphon/alce/keythong/opinicus/
                griffin = griffon = 'protoceratops'
                gryphon = griffon
                alce = keythong = opinicus = griffin
        ''',
        expect_regex='protoceratopsprotoceratopsprotoceratopsprotoceratopsprotoceratopsprotoceratops')

        self.given('''
            /X/deadeye/ten/unknown_thing/wrong_answer/
                deadeye = X: X
                ten = X
                unknown_thing = wrong_answer = X
        ''',
        expect_regex='XXXXX')


    def test_empty_lines_ok(self):
        self.given('''

            /subject/predicate/object/

                subject = /article/adjective/noun/
                    article = 'the'
                    adjective = /speed/color/


                        speed = 'quick'
                        color = 'brown'
                    noun = 'fox'

                predicate = /verb/adverb/
                    verb = 'jumps'


                    adverb = 'over'
                object = /article/adjective/noun/
                    article = 'the'
                    adjective = 'lazy'

                    noun = 'dog'

        ''',
        expect_regex='thequickbrownfoxjumpsoverthelazydog')


    def test_captures_output(self):
        self.given('''
            /extra/extra?/
                <extra> = 'icing'
        ''',
        expect_regex='(?P<extra>icing)(?P<extra>icing)?+')

        self.given('''
            /defcon/level/
                defcon = 'DEFCON'
                <level>: 1 2 3 4 5
        ''',
        expect_regex=r'DEFCON(?P<level>[12345])')

        self.given('''
            captured?
                <captured> = /L/R/
                    <L> = 'Left'
                    <R> = 'Right'
        ''',
        expect_regex=r'(?P<captured>(?P<L>Left)(?P<R>Right))?+')

        self.given('''
            uncaptured?
                uncaptured = /L?/R/
                    <L> = 'Left'
                    <R> = 'Right'
        ''',
        expect_regex=r'(?:(?P<L>Left)?+(?P<R>Right))?+')


    def test_atomic_grouping_output(self):
        self.given('''
            /bomb?/clock/mass/number?/
                .bomb = 'bomb'
                .<clock> = 'clock'
                .mass: M A S s
                .<number>: n u m b e r
        ''',
        expect_regex=r'(?>bomb)?+(?P<clock>(?>clock))(?>[MASs])(?P<number>(?>[number]))?+')

        self.given('''
            nonatomic?
                nonatomic = /L?/R/
                    .L = 'Left'
                    .R = 'Right'
        ''',
        expect_regex=r'(?:(?>Left)?+(?>Right))?+')

        self.given('''
            /yadda/ditto/
                .<yadda> = 'yadda'
                ditto = yadda
        ''',
        expect_regex=r'(?P<yadda>(?>yadda))(?P<yadda>(?>yadda))')


    def test_builtin_output(self):
        self.given('''
            /alpha/upper/lower/digit/alnum/
        ''',
        expect_regex=r'[a-zA-Z][A-Z][a-z]\d[a-zA-Z0-9]')


    def test_quantifier_output(self):
        self.given('''
            0 of alpha
        ''',
        expect_regex='')

        self.given('''
            1 of alpha
        ''',
        expect_regex='[a-zA-Z]')

        self.given('''
            2 of alpha
        ''',
        expect_regex='[a-zA-Z]{2}')

        self.given('''
            .. of alpha
        ''',
        expect_regex='[a-zA-Z]*+')

        self.given('''
            0.. of alpha
        ''',
        expect_regex='[a-zA-Z]*+')

        self.given('''
            1.. of alpha
        ''',
        expect_regex='[a-zA-Z]++')

        self.given('''
            2.. of alpha
        ''',
        expect_regex='[a-zA-Z]{2,}+')

        self.given('''
            ..2 of alpha
        ''',
        expect_regex='[a-zA-Z]{,2}+')

        self.given('''
            0..2 of alpha
        ''',
        expect_regex='[a-zA-Z]{,2}+')

        self.given('''
            ..1 of alpha
        ''',
        expect_regex='[a-zA-Z]?+')

        self.given('''
            0..1 of alpha
        ''',
        expect_regex='[a-zA-Z]?+')

        self.given('''
            3..4 of alpha
        ''',
        expect_regex='[a-zA-Z]{3,4}+')

        self.given('''
            .. <<- of alpha
        ''',
        expect_regex='[a-zA-Z]*')

        self.given('''
            0.. <<- of alpha
        ''',
        expect_regex='[a-zA-Z]*')

        self.given('''
            1.. <<- of alpha
        ''',
        expect_regex='[a-zA-Z]+')

        self.given('''
            2.. <<- of alpha
        ''',
        expect_regex='[a-zA-Z]{2,}')

        self.given('''
            ..2 <<- of alpha
        ''',
        expect_regex='[a-zA-Z]{,2}')

        self.given('''
            0..2 <<- of alpha
        ''',
        expect_regex='[a-zA-Z]{,2}')

        self.given('''
            ..1 <<- of alpha
        ''',
        expect_regex='[a-zA-Z]?')

        self.given('''
            0..1 <<- of alpha
        ''',
        expect_regex='[a-zA-Z]?')

        self.given('''
            0 <<+..1 of alpha
        ''',
        expect_regex='[a-zA-Z]??')

        self.given('''
            3..4 <<- of alpha
        ''',
        expect_regex='[a-zA-Z]{3,4}')

        self.given('''
            0 <<+.. of alpha
        ''',
        expect_regex='[a-zA-Z]*?')

        self.given('''
            1 <<+.. of alpha
        ''',
        expect_regex='[a-zA-Z]+?')

        self.given('''
            2 <<+.. of alpha
        ''',
        expect_regex='[a-zA-Z]{2,}?')

        self.given('''
            0 <<+..1 of alpha
        ''',
        expect_regex='[a-zA-Z]??')

        self.given('''
            0 <<+..2 of alpha
        ''',
        expect_regex='[a-zA-Z]{,2}?')

        self.given('''
            1 <<+..2 of alpha
        ''',
        expect_regex='[a-zA-Z]{1,2}?')

        self.given('''
            ? of alpha
        ''',
        expect_regex='[a-zA-Z]?+')

        self.given('''
            alphas?
                alphas = 1.. of alpha
        ''',
        expect_regex='[a-zA-Z]*+')

        self.given('''
            alphas?
                alphas = .. of alpha
        ''',
        expect_regex='(?:[a-zA-Z]*+)?+')

        self.given('''
            opt_alpha?
                opt_alpha = ? of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?+)?+')

        self.given('''
            opt_alpha?
                opt_alpha = 0..1 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?+)?+')

        self.given('''
            opt_alpha?
                opt_alpha = 0..1 <<- of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?)?+')

        self.given('''
            opt_alpha?
                opt_alpha = 0 <<+..1 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]??)?+')

        self.given('''
            ? of ? of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?+)?+')

        self.given('''
            ? of 0..1 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?+)?+')

        self.given('''
            0..1 of ? of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?+)?+')

        self.given('''
            ? of 0..1 <<- of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?)?+')

        self.given('''
            0 <<+..1 of ? of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?+)??')

        self.given('''
            0..1 <<- of 0 <<+..1 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]??)?')

        self.given('''
            2 of ? of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?+){2}')

        self.given('''
            ? of 2 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{2})?+')

        self.given('''
            ? of 1..3 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{1,3}+)?+')

        self.given('''
            1..3 of ? of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?+){1,3}+')

        self.given('''
            1..3 <<- of 5..7 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{5,7}+){1,3}')

        self.given('''
            1..3 of 5..7 <<- of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{5,7}){1,3}+')

        self.given('''
            1..3 <<- of 5..7 <<- of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{5,7}){1,3}')

        self.given('''
            1 <<+..3 of 5..7 <<- of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{5,7}){1,3}?')

        self.given('''
            1..3 <<- of 5 <<+..7 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{5,7}?){1,3}')

        self.given('''
            1 <<+..3 of 5 <<+..7 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{5,7}?){1,3}?')

        self.given('''
            2 of 3..4 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{3,4}+){2}')

        self.given('''
            2 of 3..4 <<- of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{3,4}){2}')

        self.given('''
            2 of 3 <<+..4 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{3,4}?){2}')

        self.given('''
            2..3 of 4 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{4}){2,3}+')

        self.given('''
            2..3 <<- of 4 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{4}){2,3}')

        self.given('''
            2 <<+..3 of 4 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{4}){2,3}?')

        self.given('''
            css_color
                css_color = 6 of hex
                    hex: 0..9 a..f
        ''',
        expect_regex='[0-9a-f]{6}')

        self.given('''
            css_color
                css_color = 3 of 2 of hex
                    hex: 0..9 a..f
        ''',
        expect_regex='[0-9a-f]{6}')

        self.given('''
            css_color
                css_color = 3 of hexbyte
                    hexbyte = 2 of: 0..9 a..f
        ''',
        expect_regex='[0-9a-f]{6}')

        self.given('''
            DWORD_speak
                DWORD_speak = 1.. of 4 of hex
                    hex: 0..9 A..F
        ''',
        expect_regex='(?:[0-9A-F]{4})++')


    def test_commenting(self):
        self.given('''
            -- comments should be ignored
        ''',
        expect_regex='')

        self.given('''
-- comments should be ignored
        ''',
        expect_regex='')

        self.given('''
            -- comments should be ignored
            --comments should be ignored
        ''',
        expect_regex='')

        self.given('''
-- comments should be ignored
--comments should be ignored
        ''',
        expect_regex='')

        self.given('''
            --comments should be ignored
--comments should be ignored
            -- comments should be ignored
        ''',
        expect_regex='')

        self.given('''
            --comments should be ignored
-- comments should be ignored
            -- comments should be ignored
--comments should be ignored
        ''',
        expect_regex='')

        self.given('''-- first line containing comments, and only comments, is OK
        -- so is last line''',
        expect_regex='')

        self.given('''--
--      ''',
        expect_regex='')

        self.given(''' --
        --''',
        expect_regex='')

        self.given('''
            --
        ''',
        expect_regex='')

        self.given('''
--
        ''',
        expect_regex='')

        self.given('''
            ---
        ''',
        expect_regex='')

        self.given('''
            --
            --
        ''',
        expect_regex='')

        self.given('''
--
--
        ''',
        expect_regex='')

        self.given('''
            --
--
            --
        ''',
        expect_regex='')

        self.given('''
            --
--
            --
--
        ''',
        expect_regex='')

        self.given('''
            /comment/ -- should be ignored
                comment = 'first'
        ''',
        expect_regex='first')

        self.given('''
            /comment/ --should be ignored
                comment = 'first'
        ''',
        expect_regex='first')

        self.given('''
            /comment/ --
                comment = 'first'
        ''',
        expect_regex='first')

        self.given('''
-- begin
            /social_symbol/literally/literal/ --comments should be ignored
                social_symbol: @ #        -- the social media symbols
                literally = 'literally' -- string literal
                literal = literally --alias
--end
        ''',
        expect_regex='[@#]literallyliterally')


    def test_reference_output(self):
        self.given(u'''
            /bang/=bang/
                <bang>: b a n g !
        ''',
        expect_regex='(?P<bang>[bang!])(?P=bang)')
        
        self.given(u'''
            /=bang/bang/
                <bang>: b a n g !
        ''',
        expect_regex='(?P=bang)(?P<bang>[bang!])')
        
        self.given(u'''
            /bang/=bang?/
                <bang>: b a n g !
        ''',
        expect_regex='(?P<bang>[bang!])(?P=bang)?+')
        
        self.given(u'''
            /=bang?/bang/
                <bang>: b a n g !
        ''',
        expect_regex='(?P=bang)?+(?P<bang>[bang!])')

        self.given(u'''
            /bang/&bang/
                <bang>: b a n g !
        ''',
        expect_regex='(?P<bang>[bang!])(?&bang)')


    def test_wordchar_boundary_output(self):
        self.given('''
            /wordchar/./_/
        ''',
        expect_regex=r'\w\b\B')

        self.given('''
            realworld_wordchar
                realworld_wordchar: +wordchar - not +digit _
        ''',
        expect_regex=r'[\w\---\d_]')

        self.given('''
            cat
                cat = .'cat'.
        ''',
        expect_regex=r'\bcat\b')

        self.given('''
            /./cat/./
                cat = 'cat'
        ''',
        expect_regex=r'\bcat\b')

        self.given('''
            /./cat/./
                cat = .'cat'.
        ''',
        expect_regex=r'\b\bcat\b\b')

        self.given('''
            /anti/_/
                anti = 'anti'
        ''',
        expect_regex=r'anti\B')

        self.given('''
            somethingtastic
                somethingtastic = _'tastic'
        ''',
        expect_regex=r'\Btastic')

        self.given('''
            expletification
                expletification = _'bloody'_
        ''',
        expect_regex=r'\Bbloody\B')

        self.given('''
            _
        ''',
        expect_regex=r'\B')

        self.given('''
            .
        ''',
        expect_regex=r'\b')

        self.given('''
            2 of .
        ''',
        expect_regex=r'\b{2}')

        self.given('''
            bdry
                .bdry = .
        ''',
        expect_regex=r'(?>\b)')

        self.given('''
            bdry
                <bdry> = .
        ''',
        expect_regex=r'(?P<bdry>\b)')

        self.given('''
            bdries
                bdries = 1 of 2 of 3 of .
        ''',
        expect_regex=r'\b{6}')

        self.given('''
            bdries?
                bdries = 1.. of .
        ''',
        expect_regex=r'\b*+')


    def test_string_escape_output(self):
        self.given(r'''
            3.. of '\n'
        ''',
        expect_regex=r'\n{3,}+')

        self.given(r'''
            3.. of '\t'
        ''',
        expect_regex=r'\t{3,}+')

        self.given('''
            3.. of '\t'
        ''',
        expect_regex='\t{3,}+')

        self.given(r'''
            3.. of '\x61'
        ''',
        expect_regex=r'\x61{3,}+')

        self.given('''
            3.. of '\x61'
        ''',
        expect_regex='a{3,}+')

        self.given(u'''
            3.. of '\U00000061'
        ''',
        expect_regex='a{3,}+')

        self.given(r'''
            3.. of '\u0061'
        ''',
        expect_regex=r'\u0061{3,}+')

        self.given(r'''
            3.. of '\61'
        ''',
        expect_regex=r'\61{3,}+')

        self.given(u'''
            3.. of '\N{AMPERSAND}'
        ''',
        expect_regex='&{3,}+')

        self.given(r'''
            3.. of '\N{AMPERSAND}'
        ''',
        expect_regex=r'\N{AMPERSAND}{3,}+')

        self.given(r'''
            3.. of '\N{LEFTWARDS ARROW}'
        ''',
        expect_regex=r'\N{LEFTWARDS ARROW}{3,}+')

        self.given(u'''
            3.. of 'M\N{AMPERSAND}M\\\N{APOSTROPHE}s'
        ''',
        expect_regex="(?:M&M's){3,}+")

        self.given(ur'''
            3.. of 'M\N{AMPERSAND}M\N{APOSTROPHE}s'
        ''',
        expect_regex=r'(?:M\N{AMPERSAND}M\N{APOSTROPHE}s){3,}+')

        self.given(r'''
            '\a\b\f\v\t'
        ''',
        expect_regex=r'\x07\x08\x0C\x0B\t')

        self.given(r'''
            '.\w\b\s\X\n'
        ''',
        expect_regex=r'\.\\w\x08\\s\\X\n')


    def test_flagging_output(self):
        self.given('''
            (unicode)
        ''',
        expect_regex='(?V1mwu)')

        self.given('''
            (ascii version0)
        ''',
        expect_regex='(?mwaV0)')

        self.given('''
            (bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse verbose version1 word)
        ''',
        expect_regex='(?bsefiLmrxV1w)')

        self.given('''
            (multiline)
        ''',
        expect_regex='(?V1wm)')

        self.given('''
            (-multiline)
        ''',
        expect_regex='(?V1w-m)')

        self.given('''
            (-word)
        ''',
        expect_regex='(?V1m-w)')

        self.given('''
            (ignorecase)
        ''',
        expect_regex='(?V1mwi)')

        self.given('''
            (-ignorecase)
        ''',
        expect_regex='(?V1mw-i)')

        self.given('''
            (unicode ignorecase)
        ''',
        expect_regex='(?V1mwui)')

        self.given('''
            (unicode)
            (ignorecase) alpha
        ''',
        expect_regex='(?V1mwu)(?i:\p{Alphabetic})')

        self.given('''
            (unicode ignorecase)
            (-ignorecase) lower
        ''',
        expect_regex='(?V1mwui)(?-i:\p{Lowercase})')

        self.given('''
            (ignorecase) .'giga'_
        ''',
        expect_regex=r'(?i:\bgiga\B)')

        self.given('''
            (ignorecase) /super/uppers/
                super = 'super'
                uppers = (-ignorecase) 1.. of upper
        ''',
        expect_regex='(?i:super(?-i:[A-Z]++))')

        self.given('''
            hex?
                hex = (ignorecase) 1 of: +digit a..f
        ''',
        expect_regex=r'(?i:[\da-f])?+')


    def test_variable_named_of(self):
        self.given('''
            2 of of -- a variable named "of"
                of = 'of'
        ''',
        expect_regex=r'(?:of){2}')

        self.given('''
            1 of 2 of of               
                of = 'of'
        ''',
        expect_regex=r'(?:of){2}')

        self.given('''
            1 of 2 of 3 of of
                of: o f
        ''',
        expect_regex=r'[of]{6}')

        self.given('''
            2  of  /digit/of/digit/
                of: o f
        ''',
        expect_regex=r'(?:\d[of]\d){2}')

        self.given('''
            1 of 2 of '3 of alpha'
        ''',
        expect_regex=r'(?:3 of alpha){2}')


    def test_flag_dependent_charclass_output(self):
        self.given('''
            (-multiline)
            /SoL/EoL/line2/SoS/EoS/
                line2 = (multiline) /SoL/EoL/SoS/EoS/
        ''',
        expect_regex='(?V1w-m)(?m:^)(?m:$)(?m:^$\A\Z)\A\Z')

        self.given('''
            /SoL/EoL/line2/SoS/EoS/
                line2 = (-multiline) /SoL/EoL/SoS/EoS/
        ''',
        expect_regex='^$(?-m:(?m:^)(?m:$)\A\Z)\A\Z')

        self.given('''
            /SoL/EoL/SoS/EoS/line2/
                line2 = (dotall) /SoL/EoL/SoS/EoS/ -- should be unaffected
        ''',
        expect_regex='^$\A\Z(?s:^$\A\Z)')

        self.given('''
            /any/any2/any3/
                any2 = (dotall) any
                any3 = (-dotall) any
        ''',
        expect_regex='(?s:.)(?s:.)(?-s:(?s:.))')

        self.given('''
            /space/tab/spacetab2/spacetab3/
                spacetab2 = (verbose) /space/tab/
                spacetab3 = (-verbose) /space/tab/
        ''',
        expect_regex=r' \t(?x:[ ][\t])(?-x: \t)')

        self.given('''
            /spacetab/spacetab2/
                spacetab = (verbose) 1 of: +space +tab
                spacetab2 = (-verbose) 1 of: +space +tab
        ''',
        expect_regex=r'(?x:[ \t])(?-x:[ \t])')

        self.given('''
            /linechar/lf/
                lf = (-word) 1 of: +linechar
        ''',
        expect_regex=r'[\r\n\x0B\x0C](?-w:\n)')

        self.given('''
            (unicode)
            linechar
        ''',
        expect_regex=r'(?V1mwu)[\r\n\x0B\x0C\x85\u2028\u2029]')

        self.given('''
            (word unicode)
            linechar
        ''',
        expect_regex=r'(?V1mwu)[\r\n\x0B\x0C\x85\u2028\u2029]')

        self.given('''
            (unicode word)
            linechar
        ''',
        expect_regex=r'(?V1muw)[\r\n\x0B\x0C\x85\u2028\u2029]')

        self.given('''
            (unicode)
            (word) linechar
        ''',
        expect_regex=r'(?V1mwu)(?w:[\r\n\x0B\x0C\x85\u2028\u2029])')

        self.given('''
            (unicode -word)
            /linechar/line2/
                line2 = (word) linechar
        ''',
        expect_regex=r'(?V1mu-w)\n(?w:[\r\n\x0B\x0C\x85\u2028\u2029])')

        self.given('''
            (-word unicode)
            (word) /linechar/line2/
                line2 = (-word) linechar
        ''',
        expect_regex=r'(?V1mu-w)(?w:[\r\n\x0B\x0C\x85\u2028\u2029](?-w:\n))')

        self.given('''
            (unicode)
            (-word) /linechar/line2/
                line2 = (word) linechar
        ''',
        expect_regex=r'(?V1mwu)(?-w:\n(?w:[\r\n\x0B\x0C\x85\u2028\u2029]))')


class TestMatches(unittest.TestCase):
    def given(self, oprex_source, fn=regex.match, expect_full_match=[], no_match=[], partial_match={}):
        regex_source = oprex(oprex_source)
        for text in expect_full_match:
            match = fn(regex_source, text)
            partial = match and match.group(0) != text
            if not match or partial:
                raise AssertionError(u'%s\nis expected to fully match: %s\n%s\nThe regex is: %s' % (
                    oprex_source or u'(empty string)', 
                    text or u'(empty string)', 
                    u'It does match, but only partially. The match is: ' + (match.group(0) or u'(empty string)') if partial else u"But it doesn't match at all.",
                    regex_source or u'(empty string)',
                ))

        for text in no_match:
            match = fn(regex_source, text)
            if match:
                raise AssertionError(u'%s\nis expected NOT to match: %s\n%s\nThe regex is: %s' % (
                    oprex_source or u'(empty string)', 
                    text or u'(empty string)', 
                    u'But it does match. The match is: ' + (match.group(0) or u'(empty string)'),
                    regex_source or u'(empty string)',
                ))

        for text, partmatch in partial_match.iteritems():
            match = fn(regex_source, text)
            partial = match and match.group(0) != text and match.group(0) == partmatch
            if not match or not partial:
                if match and match.group(0) == text:
                    raise AssertionError(u"%s\nis expected to partially match: %s\nBut instead it's a full-match.\nThe regex is: %s" % (
                        oprex_source or u'(empty string)', 
                        text or u'(empty string)', 
                        regex_source or u'(empty string)',
                    ))
                else:
                    raise AssertionError(u'%s\nis expected to partially match: %s\n%s\nThe regex is: %s' % (
                        oprex_source or u'(empty string)', 
                        text or u'(empty string)', 
                        u"But it doesn't match at all." if not match else u'The expected partial match is: %s\nBut the resulting match is: %s' % (
                            partmatch or u'(empty string)', 
                            match.group(0) or u'(empty string)'
                        ),
                        regex_source or u'(empty string)',
                    ))


    def test_unicode(self):
        self.given(u'''
            'Déjà vu'
        ''',
        expect_full_match=[u'Déjà vu'])

    def test_simple_optional(self):
        self.given('''
            /a?/ether/
                ether = /e/ther/
                    e = 'e'
                    ther = 'ther'
                a = 'a'
        ''',
        expect_full_match=['ether', 'aether'])

        self.given('''
            /air/man?/ship?/
                air = 'air'
                man = 'man'
                ship = 'ship'
        ''',
        expect_full_match=['air', 'airman', 'airship', 'airmanship'],
        no_match=['manship'],
        partial_match={'airma' : 'air'})

        self.given('''
            /ultra?/nagog/
                ultra = "ultra"
                nagog = 'nagog'
        ''',
        expect_full_match=['ultranagog', 'nagog'],
        no_match=['ultra'])

        self.given('''
            /cat?/fish?/
                cat  = 'cat'
                fish = 'fish'
        ''',
        expect_full_match=['catfish', 'cat', 'fish', ''],
        partial_match={
            'catfishing' : 'catfish', 
            'cafis' : '',
        })

        self.given('''
            /very?/very?/nice/
                very = 'very '
                nice = "nice"
        ''',
        expect_full_match=['nice', 'very nice', 'very very nice'])


    def test_escaping(self):
        self.given('''
            orly
                orly = "O RLY?"
        ''',
        expect_full_match=['O RLY?'],
        no_match=['O RLY', 'O RL'])

        self.given('''
            stars
                stars = '***'
        ''',
        expect_full_match=['***'],
        partial_match={'****' : '***'},
        no_match=['', '*'])

        self.given('''
            add
                add: +plus
                    plus: +
        ''',
        expect_full_match=['+'],
        no_match=[''])


    def test_character_class(self):
        self.given('''
            papersize
                papersize = /series/size/
                    series: A B C
                    size: 0 1 2 3 4 5 6 7 8
        ''',
        expect_full_match=['A3', 'A4'],
        no_match=['Legal', 'Folio'])

        self.given('''
            x
                x: U+41 U+042 U+00043 U+44 U+0045
        ''',
        expect_full_match=['A', 'B', 'C', 'D', 'E'],
        no_match=['a', 'b', 'c', 'd', 'e'])

        self.given('''
            x
                x: :SKULL_AND_CROSSBONES :BIOHAZARD_SIGN :CANCER
        ''',
        expect_full_match=[u'☠', u'☣', u'♋'])

        self.given('''
            x
                x: /Letter /Number
        ''',
        expect_full_match=['A', '1'],
        no_match=['?', '$'])

        self.given('''
            x
                x: /Symbol
        ''',
        expect_full_match=['$'],
        no_match=['A', '1'])

        # uppercase or greek
        self.given('''
            x
                x: /Lu /Greek
        ''',
        expect_full_match=['A', u'γ', u'Γ'],
        no_match=['a'])

        # not uppercase or not greek == not(uppercase and greek)
        self.given('''
            x
                x: /Uppercase_Letter /IsGreek
        ''',
        expect_full_match=['A', u'γ', u'Γ'],
        no_match=['a'])

        self.given('''
            /open/bs/caret/close/
                open: [
                bs: \\
                caret: ^
                close: ]
        ''',
        expect_full_match=['[\\^]'])

    def test_character_range(self):
        self.given('''
            AZ
                AZ: U+41..Z
        ''',
        expect_full_match=['A', 'B', 'C', 'X', 'Y', 'Z'],
        no_match=['a', 'x', 'z', '1', '0'])

        self.given('''
            arrows
                arrows: :LEFTWARDS_ARROW..:LEFT_RIGHT_OPEN-HEADED_ARROW
        ''',
        expect_full_match=[u'←', u'→', u'⇶', u'⇿'],
        no_match=['>'])

        self.given('''
            need_escape
                need_escape: [ ^ a - z ]
        ''',
        expect_full_match=['[', '^', 'a', '-', 'z', ']'],
        no_match=['b', 'A'])


    def test_charclass_include(self):
        self.given(u'''
            /op/op/op/op/
                op: +add +sub +mul +div
                    add: +
                    sub: -
                    mul: * ×
                    div: / ÷ :
        ''',
        expect_full_match=['++++', '+-*/', u'×÷*/'],
        no_match=[u'×××x', '+++'])

        self.given(u'''
            binary
                binary: +bindigit
                    bindigit: 0..1
        ''',
        expect_full_match=['0', '1'],
        no_match=['2', 'I', ''],
        partial_match={
            '0-1'  : '0',
            '0..1' : '0',
        })

        self.given(u'''
            /hex/hex/hex/
                hex: +hexdigit
                    hexdigit: 0..9 a..f A..F
        ''',
        expect_full_match=['AcE', '12e', 'fff'],
        no_match=['WOW', 'hi!', '...'])

        self.given(u'''
            aUmlaut
                aUmlaut: +a_with_diaeresis
                    a_with_diaeresis: ä
        ''',
        expect_full_match=[u'ä'])

        self.given(u'''
            aUmlaut
                aUmlaut: +small_a_umlaut
                    small_a_umlaut: +a_with_diaeresis
                        a_with_diaeresis: ä
        ''',
        expect_full_match=[u'ä'])

        self.given(u'''
            aUmlaut
                aUmlaut: +a_with_diaeresis
                    a_with_diaeresis: U+E4
        ''',
        expect_full_match=[u'ä'])

        self.given(u'''
            aUmlaut
                aUmlaut: +a_with_diaeresis
                    a_with_diaeresis: :LATIN_SMALL_LETTER_A_WITH_DIAERESIS
        ''',
        expect_full_match=[u'ä'])

        self.given(u'''
            alphabetic
                alphabetic: +is_alphabetic
                    is_alphabetic: /Alphabetic
        ''',
        expect_full_match=[u'ä', 'a'])

        self.given(u'''
            lowaz
                lowaz: +lowerAZ
                    lowerAZ: a..z
        ''',
        expect_full_match=['a', 'b', 'c', 'z'],
        no_match=['A', 'Z', u'ä'])

        self.given(u'''
            /hex/
                hex: +hexx +hexy +hexz
                    hexx = hexdigit
                        hexdigit: 0..9
                    hexy = hexz = hexalpha
                        hexalpha: a..f A..F
        ''',
        expect_full_match=['a', 'b', 'f', 'A', 'B', 'F', '0', '1', '9'],
        no_match=['z', 'Z', u'ä', '$'])

        self.given(u'''
            /plus/minus/pmz/
                plus: +
                minus: -
                pmz: +plus +minus z
        ''',
        expect_full_match=['+-+', '+--', '+-z'],
        no_match=['+-a'])


    def test_nested_charclass(self):
        self.given(u'''
            vowhex
                vowhex: +vowel +hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_full_match=['a', 'b', 'f', 'A', 'B', 'F', '0', '1', '9', 'i', 'u', 'E', 'O'],
        no_match=['$', 'z', 'k'])


    def test_charclass_operation(self):
        self.given(u'''
            xb123
                xb123: X x +hex  not  c..f C..D :LATIN_CAPITAL_LETTER_F +vowel  and  1 2 3 /Alphabetic
                    hex: 0..9 a..f A..F
                    vowel: a i u e o A I U E O
        ''',
        expect_full_match=['x', 'X', 'b', 'B', '1', '2', '3'],
        no_match=['a', 'A', 'c', 'C', 'd', 'D', 'e', 'E', 'f', 'F', 'y', 'Y', 'z', 'Z', '0', '4', '9', '-'])

        self.given(u'''
            allButU
                allButU: not: U
        ''',
        expect_full_match=['^', 'u'],
        no_match=['U', ''])

        self.given(u'''
            nonalpha
                nonalpha: not: /Alphabetic
        ''',
        expect_full_match=['-', '^', '1'],
        no_match=['A', 'a', u'Ä', u'ä'])

        self.given(u'''
            otherz
                otherz: +nonz
                    nonz: not: z
        ''',
        expect_full_match=['-', '^', '1', 'A', 'a', u'Ä', u'ä', 'Z'],
        no_match=['z'])

        self.given(u'''
            a_or_consonant
                a_or_consonant: A a +consonant 
                    consonant: a..z A..Z not a i u e o A I U E O 
        ''',
        expect_full_match=['A', 'a', 'Z', 'z'],
        no_match=[u'Ä', u'ä', '-', '^', '1'])

        self.given(u'''
            maestro
                maestro: m +ae s t r o 
                    ae: +vowel and +hex not +upper
                        hex: +digit a..f A..F 
                        vowel: a i u e o A I U E O
        ''',
        expect_full_match=['m', 'a', 'e', 's', 't', 'r', 'o'],
        no_match=[u'Ä', u'ä', '-', '^', '1', 'N', 'E', 'W', 'b'])


    def test_charclass_escape(self):
        self.given('''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_full_match=[u'\u0061', u'\U00000061', '\x61', '\61', 'a'],
        no_match=['\u0061', r'\u0061', r'\x61', r'\61'])

        self.given(r'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_full_match=[u'\u0061', u'\U00000061', '\x61', '\61', 'a'],
        no_match=['\u0061', r'\u0061', r'\x61', r'\61'])

        self.given(u'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_full_match=[u'\u0061', u'\U00000061', '\x61', '\61', 'a'],
        no_match=['\u0061', r'\u0061', r'\x61', r'\61'])

        self.given(ur'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_full_match=[u'\u0061', u'\U00000061', '\x61', '\61', 'a'],
        no_match=['\u0061', r'\u0061', r'\x61', r'\61'])

        self.given(r'''
            allowed_escape
                allowed_escape: \n \r \t \a \b \v \f
        ''',
        expect_full_match=['\n', '\r', '\t', '\a', '\b', '\v', '\f'],
        no_match=[r'\n', r'\r', r'\t', r'\a', r'\b', r'\v', r'\f'])

        self.given(r'''
            unicode_charname
                unicode_charname: \N{AMPERSAND} :AMPERSAND
        ''',
        expect_full_match=['&', u'\N{AMPERSAND}'],
        no_match=['\N{AMPERSAND}', r'\N{AMPERSAND}'])


    def test_builtin(self):
        self.given('''
            lowhex
                lowhex: +alpha +alnum +lower not G..Z g..z +upper +digit
        ''',
        expect_full_match=['a', 'b', 'c', 'd', 'e', 'f'],
        no_match=['A', 'B', 'F', 'x', 'X', 'z', 'Z', '0', '1', '9'])


    def test_quantifier(self):
        self.given('''
            1 of alpha
        ''',
        expect_full_match=['a', 'B'],
        no_match=['', '1', '$'],
        partial_match={'Cd' : 'C'})

        self.given('''
            2 of alpha
        ''',
        expect_full_match=['ab', 'Cd'],
        no_match=['', 'A1', '$1'],
        partial_match={'ABC' : 'AB'})

        self.given('''
            3.. of alpha
        ''',
        expect_full_match=['abc', 'DeFGhij'],
        no_match=['', 'Aa4'])

        self.given('''
            4..5 of alpha
        ''',
        expect_full_match=['abcd', 'abcDE'],
        no_match=['', 'ab123'],
        partial_match={'ABCDEF' : 'ABCDE'})

        self.given('''
            /prefix/alnum/
                prefix = 1..2 <<- of alpha
        ''',
        expect_full_match=['A1', 'Ab', 'Ab3', 'abc'],
        no_match=['', '99', '9z'],
        partial_match={'YAMM' : 'YAM', 'B52' : 'B5'})

        self.given('''
            /prefix/alnum/
                prefix = 3.. <<- of alpha
        ''',
        expect_full_match=['AAA1', 'YAMM', 'Fubar', 'YAMM2', 'Fubar4'],
        no_match=['', 'A1', 'Ab', 'abc', 'Ab3', 'ABC', '99', '9z', 'B52'],
        partial_match={'Test123' : 'Test1'})

        self.given('''
            /open/content/close/
                open: (
                close: )
                content = 1.. <<- of: +alnum +open +close
        ''',
        expect_full_match=['(sic)'],
        no_match=['f(x)'],
        partial_match={'(pow)wow(kaching)zzz' : '(pow)wow(kaching)'})

        self.given('''
            /open/content/close/
                open: (
                close: )
                content = 1 <<+.. of: +alnum +open +close
        ''',
        expect_full_match=['(sic)'],
        no_match=['f(x)'],
        partial_match={'(pow)wow(kaching)zzz' : '(pow)'})

        self.given('''
            /open/content/close/
                open: (
                close: )
                content = 1.. of: +alnum +open +close
        ''',
        no_match=['(pow)wow(kaching)zzz'])

        self.given('''
            css_color
                css_color = 6 of hex
                    hex: 0..9 a..f
        ''',
        expect_full_match=['ff0000', 'cccccc', 'a762b3'],
        no_match=['', 'black', 'white'])

        self.given('''
            DWORD_speak
                DWORD_speak = 1.. of 4 of hex
                    hex: 0..9 A..F
        ''',
        expect_full_match=['CAFEBABE', 'DEADBEEF', '0FF1CE95'],
        no_match=['', 'YIKE'])


    def test_reference(self):
        self.given(u'''
            /bang/=bang/
                <bang>: b a n g !
        ''',
        expect_full_match=['bb', 'aa', 'nn', 'gg', '!!'],
        no_match=['', 'a', 'ba'])
        
        self.given(u'''
            /=bang/bang/
                <bang>: b a n g !
        ''',
        no_match=['', 'a', 'ba', 'bb', 'aa', 'nn', 'gg', '!!'])
        
        self.given(u'''
            /bang/=bang?/
                <bang>: b a n g !
        ''',
        expect_full_match=['a', 'bb', 'aa', 'nn', 'gg', '!!'],
        no_match=['', 'clang!'],
        partial_match={
            'ba'    : 'b',
            'bang!' : 'b',
        })
        
        self.given(u'''
            /=bang?/bang/
                <bang>: b a n g !
        ''',
        expect_full_match=['b', 'a', 'n', 'g', '!'],
        no_match=['', 'clang!'],
        partial_match={'ba' : 'b', 'bb' : 'b', 'aa' : 'a', 'nn' : 'n', 'gg' : 'g', '!!' : '!', 'bang!' : 'b'})

        self.given(u'''
            /bang/&bang/
                <bang>: b a n g !
        ''',
        expect_full_match=['bb', 'aa', 'nn', 'gg', '!!', 'ba', 'ng', 'b!', '!g'],
        no_match=['', 'b', 'a'])


    def test_wordchar_boundary(self):
        self.given('''
            /wordchar/./_/
        ''',
        expect_full_match=[],
        no_match=['a', 'b', 'Z', '_'])

        self.given('''
            realworld_wordchar
                realworld_wordchar: +wordchar - not +digit _
        ''',
        expect_full_match=['a', 'Z', '-'],
        no_match=['0', '9', '_'])

        self.given('''
            cat
                cat = 'cat'
        ''',
        fn=regex.search,
        expect_full_match=['cat'],
        no_match=['garfield'],
        partial_match={'tomcat' : 'cat', 'catasthrope' : 'cat', 'complicated' : 'cat', 'cat videos' : 'cat', 'grumpy cat' : 'cat'})

        self.given('''
            cat
                cat = 'cat'_
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=['cat', 'cat videos','grumpy cat', 'tomcat', 'garfield'],
        partial_match={'catasthrope' : 'cat', 'complicated' : 'cat'})

        self.given('''
            cat
                cat = 'cat'.
        ''',
        fn=regex.search,
        expect_full_match=['cat'],
        no_match=['catasthrope', 'complicated', 'garfield'],
        partial_match={'tomcat' : 'cat', 'cat videos' : 'cat', 'grumpy cat' : 'cat'})

        self.given('''
            cat
                cat = _'cat'
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=['cat', 'catasthrope', 'cat videos', 'grumpy cat', 'garfield'],
        partial_match={'tomcat' : 'cat', 'complicated' : 'cat'})

        self.given('''
            cat
                cat = .'cat'
        ''',
        fn=regex.search,
        expect_full_match=['cat'],
        no_match=['tomcat', 'complicated', 'garfield'],
        partial_match={'catasthrope' : 'cat', 'cat videos' : 'cat', 'grumpy cat' : 'cat'})

        self.given('''
            cat
                cat = _'cat'_
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=['cat', 'catasthrope', 'cat videos', 'tomcat', 'grumpy cat', 'garfield'],
        partial_match={'complicated' : 'cat'})

        self.given('''
            cat
                cat = .'cat'.
        ''',
        fn=regex.search,
        expect_full_match=['cat'],
        no_match=['tomcat', 'catasthrope', 'complicated', 'garfield'],
        partial_match={'cat videos' : 'cat', 'grumpy cat' : 'cat'})

        self.given('''
            /./cat/./
                cat = 'cat'
        ''',
        fn=regex.search,
        expect_full_match=['cat'],
        no_match=['tomcat', 'catasthrope', 'complicated', 'garfield'],
        partial_match={'cat videos' : 'cat', 'grumpy cat' : 'cat'})

        self.given('''
            /./cat/./
                cat = .'cat'.
        ''',
        fn=regex.search,
        expect_full_match=['cat'],
        no_match=['tomcat', 'catasthrope', 'complicated', 'garfield'],
        partial_match={'cat videos' : 'cat', 'grumpy cat' : 'cat'})

        self.given('''
            /anti/_/
                anti = 'anti'
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=['anti', 'anti-virus', 'rianti cartwright'],
        partial_match={'antivirus' : 'anti', 'meantime' : 'anti'})

        self.given('''
            somethingtastic
                somethingtastic = _'tastic'
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=['tastic', 'tasticism'],
        partial_match={'fantastic' : 'tastic', 'fantastico' : 'tastic'})

        self.given('''
            expletification
                expletification = _'bloody'_
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=['bloody', 'bloody hell'],
        partial_match={'absobloodylutely' : 'bloody'})


    def test_flags(self):
        self.given('''
            lower
        ''',
        expect_full_match=['a'],
        no_match=['A', u'ä', u'Ä'])

        self.given('''
            (unicode)
            lower
        ''',
        expect_full_match=['a', u'ä'],
        no_match=['A', u'Ä'])

        self.given('''
            (ignorecase)
            1 of: a i u e o
        ''',
        expect_full_match=['a', 'A'],
        no_match=[u'Ä', u'ä'])

        self.given('''
            (ignorecase) 1 of: a i u e o
        ''',
        expect_full_match=['a', 'A'],
        no_match=[u'Ä', u'ä'])

        self.given('''
            (unicode)
            (ignorecase) lower
        ''',
        expect_full_match=['a', 'A', u'Ä', u'ä'])

        self.given('''
            (unicode ignorecase)
            lower
        ''',
        expect_full_match=['a', 'A', u'Ä', u'ä'])

        self.given('''
            (unicode ignorecase)
            lower
        ''',
        expect_full_match=['a', 'A', u'Ä', u'ä'])

        self.given('''
            (ignorecase) 'AAa'
        ''',
        expect_full_match=['AAa', 'aAa', 'aaa', 'AAA'])

        self.given('''
            (ignorecase) /VOWEL/BIGVOWEL/
                VOWEL: A I U E O
                BIGVOWEL = (-ignorecase) VOWEL
        ''',
        expect_full_match=['AA', 'aA'],
        no_match=['Aa', 'aa'])


    def test_string_escape(self):
        self.given(r'''
            '\n'
        ''',
        expect_full_match=['\n'],
        no_match=[r'\n', '\\n'])

        self.given(r'''
            '\t'
        ''',
        expect_full_match=['\t', '	'],
        no_match=[r'\t', '\\t'])

        self.given('''
            '\t'
        ''',
        expect_full_match=['\t', '	'],
        no_match=[r'\t', '\\t'])

        self.given(r'''
            '\x61'
        ''',
        expect_full_match=[u'\U00000061', u'\u0061', u'a', 'a', '\x61', '\141'],
        no_match=[r'\x61', '\\x61'])

        self.given('''
            '\x61'
        ''',
        expect_full_match=[u'\U00000061', u'\u0061', u'a', 'a', '\x61', '\141'],
        no_match=[r'\x61', '\\x61'])

        self.given(u'''
            '\U00000061'
        ''',
        expect_full_match=[u'\U00000061', u'\u0061', u'a', 'a', '\x61', '\141'],
        no_match=[r'\U00000061', '\\U00000061'])

        self.given(r'''
            '\u0061'
        ''',
        expect_full_match=[u'\U00000061', u'\u0061', u'a', 'a', '\x61', '\141'],
        no_match=[r'\u0061', '\\u0061'])

        self.given(r'''
            '\141'
        ''',
        expect_full_match=[u'\U00000061', u'\u0061', u'a', 'a', '\x61', '\141'],
        no_match=[r'\141', '\\141'])

        self.given(u'''
            '\N{AMPERSAND}'
        ''',
        expect_full_match=[u'\N{AMPERSAND}', u'&', '&'],
        no_match=[r'\N{AMPERSAND}', '\N{AMPERSAND}', '\\N{AMPERSAND}'])

        self.given(r'''
            '\N{AMPERSAND}'
        ''',
        expect_full_match=[u'\N{AMPERSAND}', u'&', '&'],
        no_match=[r'\N{AMPERSAND}', '\N{AMPERSAND}', '\\N{AMPERSAND}'])

        self.given(r'''
            '\N{BIOHAZARD SIGN}'
        ''',
        expect_full_match=[u'\N{BIOHAZARD SIGN}', u'☣'],
        no_match=[r'\N{BIOHAZARD SIGN}', '\N{BIOHAZARD SIGN}', '\\N{BIOHAZARD SIGN}', '☣'])

        self.given(r'''
            2 of 'M\N{AMPERSAND}M\N{APOSTROPHE}s'
        ''',
        expect_full_match=["M&M'sM&M's"],
        no_match=[r'M\N{AMPERSAND}M\N{APOSTROPHE}s'])

        self.given(ur'''
            2 of 'M\N{AMPERSAND}M\N{APOSTROPHE}s'
        ''',
        expect_full_match=["M&M'sM&M's"],
        no_match=[r'M\N{AMPERSAND}M\N{APOSTROPHE}s'])

        self.given(r'''
            '\a\b\f\v\t'
        ''',
        expect_full_match=['\a\b\f\v\t'],
        no_match=[r'\a\b\f\v\t'])

        self.given(r'''
            '.\w\b\s\X\n'
        ''',
        expect_full_match=['.\w\b\s\X\n'],
        no_match=[r'.\w\b\s\X\n'])


    def test_flag_dependents(self):
        self.given(r'''
            linechar
        ''',
        expect_full_match=['\n', '\r', '\v', '\f', '\x0b', '\x0C'],
        no_match=['\x85', '\u2028', r'\u2028', u'\u2028', u'\u2029'],
        partial_match={'\r\n' : '\r'})

        self.given(r'''
            (unicode)
            linechar
        ''',
        expect_full_match=['\n', '\r', '\v', '\f', '\x0b', '\x0C', '\x85', u'\u2028', u'\u2029'],
        no_match=['\u2028', r'\u2028'],
        partial_match={'\r\n' : '\r'})

        self.given(r'''
            (-word)
            linechar
        ''',
        expect_full_match=['\n'],
        no_match=['\r', '\v', '\f', '\x0b', '\x0C', '\x85', u'\u2028', u'\u2029', '\u2028', r'\u2028'],
        partial_match={'\n\r' : '\n'})

        self.given(r'''
            (unicode -word)
            linechar
        ''',
        expect_full_match=['\n'],
        no_match=['\r', '\v', '\f', '\x0b', '\x0C', '\x85', u'\u2028', u'\u2029', '\u2028', r'\u2028'],
        partial_match={'\n\r' : '\n'})

        self.given(r'''
            (-word unicode)
            linechar
        ''',
        expect_full_match=['\n'],
        no_match=['\r', '\v', '\f', '\x0b', '\x0C', '\x85', u'\u2028', u'\u2029', '\u2028', r'\u2028'],
        partial_match={'\n\r' : '\n'})

        self.given(r'''
            (unicode)
            (-word) linechar
        ''',
        expect_full_match=['\n'],
        no_match=['\r', '\v', '\f', '\x0b', '\x0C', '\x85', u'\u2028', u'\u2029', '\u2028', r'\u2028'],
        partial_match={'\n\r' : '\n'})


if __name__ == '__main__':
    unittest.main()
