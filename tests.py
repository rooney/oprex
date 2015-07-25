# -*- coding: utf-8 -*-

import unittest, regex
from oprex import oprex, OprexSyntaxError

class TestErrorHandling(unittest.TestCase):
    def given(self, oprex_source, expect_error):
        if expect_error:
            expect_error = '\n' + expect_error
        try:
            oprex(oprex_source)
        except Exception as err:
            got_error = err.message
        else:
            got_error = ''

        if got_error != expect_error:
            msg = 'For input: %s\n----------------------------- Got Error: -----------------------------%s\n\n-------------------------- Expected Error: ---------------------------%s'
            raise AssertionError(msg % (
                oprex_source or '(empty string)', 
                got_error or '\n(no error)', 
                expect_error or '\n(no error)',
            ))


    def test_white_guards(self):
        self.given('one-liner input',
        expect_error='Line 1: First line must be blank, not: one-liner input')

        self.given('''something in the first line
        ''',
        expect_error='Line 1: First line must be blank, not: something in the first line')

        self.given('''
        something in the last line''',
        expect_error='Line 2: Last line must be blank, not:         something in the last line')


    def test_unknown_symbol(self):
        self.given('''
            `@$%^&;{}[]\\
        ''',
        expect_error='Line 2: Syntax error at or near: `@$%^&;{}[]\\')


    def test_unexpected_token(self):
        self.given('''
            /to/be/?
        ''',
        expect_error='''Line 2: Unexpected QUESTMARK
            /to/be/?
                   ^''')

        self.given('''
            root
                branch
        ''',
        expect_error='''Line 3: Unexpected NEWLINE
                branch
                      ^''')

        self.given('''
            root
                root = '/'
            root2
        ''',
        expect_error='''Line 4: Unexpected VARNAME
            root2
            ^''')

        self.given('''
            root
                root = '/'\nroot2
        ''',
        expect_error='Line 4: Unexpected VARNAME\nroot2\n^')

        self.given('''
*)          /warming/and/warming/
        ''',
        expect_error='Line 2: Unexpected GLOBALMARK\n*)          /warming/and/warming/\n^')

        self.given('''
            /greeting/world/
                greeting = 'hello'
                    world = 'world'
        ''',
        expect_error="Line 4: 'world' is defined but not used (by its parent expression)")


    def test_indentation_error(self):
        self.given('''
            /greeting/world/
                greeting = 'hello'
                 world = 'world'
        ''',
        expect_error="Line 4: 'world' is defined but not used (by its parent expression)")

        self.given('''
            root
                branch
               misaligned
        ''',
        expect_error='Line 4: Indentation error')

        self.given('''
                root
                    branch
            hyperroot
        ''',
        expect_error='Line 4: Indentation error')


    def test_correct_error_line_numbering(self):
        self.given('''
            /greeting/world/
                greeting = 'hello'

                    world = 'world'
        ''',
        expect_error="Line 5: 'world' is defined but not used (by its parent expression)")

        self.given('''

            /greeting/world/


                greeting = 'hello'

                 world = 'world'
        ''',
        expect_error="Line 8: 'world' is defined but not used (by its parent expression)")

        self.given('''
            /greeting/world/
                greeting = 'hello'


               world = 'world'
        ''',
        expect_error='Line 6: Indentation error')

        self.given('''
            warming


            *)  warming = 'global'
        ''',
        expect_error="Line 5: The GLOBALMARK *) must be put at the line's beginning")


    def test_mixed_indentation(self):
        self.given('''
            \tthis_line_mixes_tab_and_spaces_for_indentation
        ''',
        expect_error='Line 2: Cannot mix space and tab for indentation')

        self.given('''
            /tabs/vs/spaces/
\t\ttabs = 'this line is tabs-indented'
                spaces = 'this line is spaces-indented'
        ''',
        expect_error='Line 3: Inconsistent indentation character')


    def test_undefined_variable(self):
        self.given('''
            bigfoot
        ''',
        expect_error="Line 2: 'bigfoot' is not defined")

        self.given('''
            /horses/and/unicorns/
                horses = 'Thoroughbreds'
                and = ' and '
        ''',
        expect_error="Line 2: 'unicorns' is not defined")

        self.given('''
            /unicorns/and/horses/
                horses = 'Thoroughbreds'
                and = ' and '
        ''',
        expect_error="Line 2: 'unicorns' is not defined")


    def test_illegal_variable_name(self):
        self.given('''
            101dalmatians
                101dalmatians = 101 of 'dalmatians'
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            101dalmatians
               ^''')
        
        self.given('''
            /101dalmatians/
                101dalmatians = 101 of 'dalmatians'
        ''',
        expect_error='''Line 2: Unexpected NUMBER
            /101dalmatians/
             ^''')
        
        self.given('''
            /_/
                _ = 'underscore'
        ''',
        expect_error='''Line 3: Unexpected UNDERSCORE
                _ = 'underscore'
                ^''')


    def test_duplicate_variable(self):
        self.given(u'''
            dejavu
                dejavu = 'Déjà vu'
                dejavu = 'Déjà vu'
        ''',
        expect_error="Line 4: Names must be unique within a scope, 'dejavu' is already defined (previous definition at line 3)")

        self.given(u'''
            dejavu
                dejavu = dejavu = 'Déjà vu'
        ''',
        expect_error="Line 3: Names must be unique within a scope, 'dejavu' is already declared (previous declaration at line 3)")

        self.given(u'''
            dejavu
                dejavu = 'Déjà vu'
                dejavu = dejavu
        ''',
        expect_error="Line 4: Names must be unique within a scope, 'dejavu' is already defined (previous definition at line 3)")

        self.given(u'''
            /de/jade/
                de = 'de'
                jade = /ja/de/
                    ja = 'JA'
                    de = 'DE'
        ''',
        expect_error="Line 6: Names must be unique within a scope, 'de' is already defined (previous definition at line 3)")

        self.given(u'''
            /deja/de/
                deja = /de/ja/
                    de = 'de'  -- different scope
                    ja = 'JA'
                de = 'DE'      -- different scope, so should be no error
        ''',
        expect_error='')

        self.given(u'''
            chicken
                chicken = /egg/hatches/
                    egg = /chicken/lays/
                        chicken = /velociraptor/evolves/
        ''',
        expect_error="Line 5: Names must be unique within a scope, 'chicken' is already declared (previous declaration at line 3)")

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
                    article = 'an'
        ''',
        expect_error="Line 13: Names must be unique within a scope, 'article' is already defined (previous definition at line 4)")


    def test_unused_variable(self):
        self.given('''
            /alice/bob/
                alice = 'alice'
                bob = 'bob'
                trudy = 'trudy'
        ''',
        expect_error="Line 5: 'trudy' is defined but not used (by its parent expression)")

        self.given('''
            /alice/bob/
                alice = 'alice'
                bob = robert
                    robert = 'bob'
                    doe = 'doe'
        ''',
        expect_error="Line 6: 'doe' is defined but not used (by its parent expression)")

        self.given('''
            non-vowel
                vowel: a i u e o
        ''',
        expect_error='') # vowel should be counted as used


    def test_invalid_atomizer(self):
        self.given('''
            @alpha -- atomizer only applicable to chained lookup
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            @alpha -- atomizer only applicable to chained lookup
             ^''')


    def test_unclosed_literal(self):
        self.given('''
            mcd
                mcd = 'McDonald's
        ''',
        expect_error='''Line 3: Unexpected VARNAME
                mcd = 'McDonald's
                                ^''')
        
        self.given('''
            "she said \\"Hi\\"
        ''',
        expect_error='Line 2: Syntax error at or near: "she said \\"Hi\\"')
        
        self.given('''
            quotes_mismatch
                quotes_mismatch = "'
        ''',
        expect_error="""Line 3: Syntax error at or near: "'""")


    def test_invalid_string_escape(self):
        self.given('''
            '\N{KABAYAN}'
        ''',
        expect_error="Line 2: undefined character name 'KABAYAN'")

        self.given(u'''
            '\N{APOSTROPHE}'
        ''',
        expect_error="Line 2: Syntax error at or near: '")


    def test_invalid_global_mark(self):
        self.given('''
            *)
        ''',
        expect_error="Line 2: The GLOBALMARK *) must be put at the line's beginning")

        self.given('''
*)
        ''',
        expect_error='Line 2: Syntax error: *)')

        self.given('''
*)\t
        ''',
        expect_error='Line 2: Unexpected GLOBALMARK\n*) \n^')

        self.given('''
*)warming
        ''',
        expect_error='Line 2: Syntax error: *)')

        self.given('''
*)          warming
        ''',
        expect_error='Line 2: Unexpected GLOBALMARK\n*)          warming\n^')

        self.given('''
            warming
                *)warming = 'global'
        ''',
        expect_error="Line 3: The GLOBALMARK *) must be put at the line's beginning")

        self.given('''
            warming
            *)  warming = 'global'
        ''',
        expect_error="Line 3: The GLOBALMARK *) must be put at the line's beginning")

        self.given('''
            warming
                warming*) = 'global'
        ''',
        expect_error="Line 3: Syntax error at or near: *) = 'global'")

        self.given('''
            warming
                warming = global *)
        ''',
        expect_error="Line 3: Syntax error:                 warming = global *)")

        self.given('''
            warming
                warming = *) 'global'
        ''',
        expect_error="Line 3: Syntax error:                 warming = *) 'global'")

        self.given('''
            warming
                warming *) = 'global'
        ''',
        expect_error="Line 3: Syntax error:                 warming *) = 'global'")

        self.given('''
            warming
*)          *)  warming = 'global'
        ''',
        expect_error='Line 3: Syntax error: *)          *)  ')

        self.given('''
            warming
*)              warming*) = 'global'
        ''',
        expect_error="Line 3: Syntax error at or near: *) = 'global'")

        self.given('''
            warming
*)              warming = global *)
        ''',
        expect_error="Line 3: Syntax error: *)              warming = global *)")

        self.given('''
            warming
                warming = 'global'
*)              
        ''',
        expect_error="Line 4: Unexpected NEWLINE\n*)              \n                ^")

        self.given('''
            warming
                warming = 'global'
*)
        ''',
        expect_error="Line 4: Syntax error: *)")

        self.given('''
            warming
                warming = 'global'
*)              junk
        ''',
        expect_error="Line 4: Unexpected NEWLINE\n*)              junk\n                    ^")

        self.given('''
            warming
                warming = 'global'
*)            *)junk
        ''',
        expect_error="Line 4: Syntax error: *)            *)")

        self.given('''
            warming
                warming = 'global'
*)              *)
        ''',
        expect_error="Line 4: Syntax error: *)              *)")

        self.given('''
            warming
                warming = 'global'
*)            *)
        ''',
        expect_error="Line 4: Syntax error: *)            *)")


    def test_global_aliasing(self):
        self.given('''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
                    satu = '1'
*)                  uno = ichi = satu
                oneone = /uno/ichi/
                one = ichi
                    ichi: 1
        ''',
        expect_error="Line 8: Names must be unique within a scope, 'ichi' is already defined (previous definition at line 5)")

        self.given('''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
                    satu = '1'
*)                  uno = ichi = satu
                oneone = /uno/ichi/
                one = uno
                    uno: 1
        ''',
        expect_error="Line 8: Names must be unique within a scope, 'uno' is already defined (previous definition at line 5)")

        self.given('''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
                    satu = '1'
*)                  uno = ichi = satu
                oneone = /uno/ichi/
                one = satu
        ''',
        expect_error="Line 7: 'satu' is not defined")

        self.given('''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
*)                  satu = '1'
                    uno = ichi = satu
                one = satu
                oneone = /uno/ichi/
        ''',
        expect_error="Line 7: 'uno' is not defined")


    def test_invalid_charclass(self):
        self.given('''
            empty_charclass
                empty_charclass:
        ''',
        expect_error='''Line 3: Unexpected NEWLINE
                empty_charclass:
                                ^''')

        self.given('''
            noSpaceAfterColon
                noSpaceAfterColon:n o
        ''',
        expect_error='''Line 3: Unexpected CHAR
                noSpaceAfterColon:n o
                                  ^''')

        self.given('''
            diphtong
                diphtong: ae au
        ''',
        expect_error="Line 3: Cannot include 'ae': not defined")

        self.given('''
            miscolon
                miscolon: /colon/should/be/equal/sign/
        ''',
        expect_error='Line 3: /colon compiles to \p{colon} which is rejected by the regex engine with error message: unknown property at position 10')

        self.given('''
            miscolon
                miscolon: /alphabetic/colon/should/be/equal/sign/
        ''',
        expect_error='Line 3: /colon compiles to \p{colon} which is rejected by the regex engine with error message: unknown property at position 10')

        self.given('''
            miscolon
                miscolon: 'colon should be equal sign'
        ''',
        expect_error='''Line 3: Unexpected CHAR
                miscolon: 'colon should be equal sign'
                           ^''')

        self.given('''
            /A/a/
                A: a: A a
        ''',
        expect_error='''Line 3: Unexpected CHAR
                A: a: A a
                    ^''')

        self.given('''
            /A/a/
                A: a = A a
        ''',
        expect_error="Line 2: 'a' is not defined")

        self.given('''
            /A/a/
                A: a = A
        ''',
        expect_error="Line 2: 'a' is not defined")

        self.given('''
            /shouldBeColon/
                shouldBeColon = A a
        ''',
        expect_error='''Line 3: Unexpected VARNAME
                shouldBeColon = A a
                                  ^''')

        self.given('''
            mixedAssignment
                mixedAssignment : = x
        ''',
        expect_error='''Line 3: Unexpected COLON
                mixedAssignment : = x
                                ^''')

        self.given('''
            mixedAssignment
                mixedAssignment := x
        ''',
        expect_error='''Line 3: Unexpected COLON
                mixedAssignment := x
                                ^''')

        self.given('''
            mixedAssignment
                mixedAssignment:= x
        ''',
        expect_error='''Line 3: Unexpected CHAR
                mixedAssignment:= x
                                ^''')

        self.given('''
            mixedAssignment
                mixedAssignment=: x
        ''',
        expect_error='''Line 3: Unexpected COLON
                mixedAssignment=: x
                                ^''')

        self.given('''
            mixedAssignment
                mixedAssignment =: x
        ''',
        expect_error='''Line 3: Unexpected COLON
                mixedAssignment =: x
                                 ^''')

        self.given('''
            x
                x: /IsAwesome
        ''',
        expect_error='Line 3: /IsAwesome compiles to \p{IsAwesome} which is rejected by the regex engine with error message: unknown property at position 14')

        self.given('''
            x
                x: :KABAYAN_SABA_KOTA
        ''',
        expect_error='Line 3: :KABAYAN_SABA_KOTA compiles to \N{KABAYAN SABA KOTA} which is rejected by the regex engine with error message: undefined character name at position 22')

        self.given(r'''
            x
                x: \N{KABAYAN}
        ''',
        expect_error='Line 3: \N{KABAYAN} compiles to \N{KABAYAN} which is rejected by the regex engine with error message: undefined character name at position 12')

        self.given(r'''
            x
                x: \o
        ''',
        expect_error='Line 3: Bad escape sequence: \o')

        self.given(r'''
            x
                x: \w
        ''',
        expect_error='Line 3: Bad escape sequence: \w')

        self.given(r'''
            x
                x: \'
        ''',
        expect_error="Line 3: Bad escape sequence: \\'")

        self.given(r'''
            x
                x: \"
        ''',
        expect_error='Line 3: Bad escape sequence: \\"')

        self.given(r'''
            x
                x: \ron
        ''',
        expect_error=r'Line 3: Bad escape sequence: \ron')

        self.given(r'''
            x
                x: \u123
        ''',
        expect_error='Line 3: Bad escape sequence: \u123')

        self.given(r'''
            x
                x: \U1234
        ''',
        expect_error='Line 3: Bad escape sequence: \U1234')

        self.given(r'''
            x
                x: \u12345
        ''',
        expect_error='Line 3: Bad escape sequence: \u12345')


    def test_invalid_char(self):
        self.given('''
            x
                x: u1234
        ''',
        expect_error="Line 3: Cannot include 'u1234': not defined")

        self.given('''
            x
                x: \uab
        ''',
        expect_error='Line 3: Bad escape sequence: \uab')

        self.given('''
            x
                x: \u123z
        ''',
        expect_error='Line 3: Bad escape sequence: \u123z')

        self.given('''
            x
                x: \U1234567z
        ''',
        expect_error='Line 3: Bad escape sequence: \U1234567z')

        self.given('''
            x
                x: \U123456789
        ''',
        expect_error='Line 3: Bad escape sequence: \U123456789')

        self.given('''
            x
                x: \U
        ''',
        expect_error='Line 3: Bad escape sequence: \U')

        self.given('''
            x
                x: :YET_ANOTHER_CHARACTER_THAT_SHOULD_NOT_BE_IN_UNICODE
        ''',
        expect_error='Line 3: :YET_ANOTHER_CHARACTER_THAT_SHOULD_NOT_BE_IN_UNICODE compiles to \N{YET ANOTHER CHARACTER THAT SHOULD NOT BE IN UNICODE} which is rejected by the regex engine with error message: undefined character name at position 56')

        # unicode character name should be in uppercase
        self.given('''
            x
                x: check-mark
        ''',
        expect_error='''Line 3: Unexpected CHAR
                x: check-mark
                        ^''')

        self.given('''
            x
                x: @omic
        ''',
        expect_error='''Line 3: Unexpected CHAR
                x: @omic
                    ^''')

        self.given('''
            x
                x: awe$ome
        ''',
        expect_error='''Line 3: Unexpected CHAR
                x: awe$ome
                      ^''')


    def test_invalid_range(self):
        self.given('''
            x
                x: ..
        ''',
        expect_error='''Line 3: Unexpected DOT
                x: ..
                    ^''')

        self.given('''
            x
                x: ...,
        ''',
        expect_error='''Line 3: Unexpected DOT
                x: ...,
                    ^''')

        self.given('''
            x
                x: ,...
        ''',
        expect_error='''Line 3: Unexpected DOT
                x: ,...
                      ^''')

        self.given('''
            x
                x: ;..,
        ''',
        expect_error='Line 3: ;.., compiles to [;-,] which is rejected by the regex engine with error message: bad character range at position 4')

        self.given('''
            x
                x: x....
        ''',
        expect_error='''Line 3: Unexpected DOT
                x: x....
                      ^''')

        self.given('''
            x
                x: infinity..
        ''',
        expect_error='''Line 3: Unexpected NEWLINE
                x: infinity..
                             ^''')

        self.given('''
            x
                x: ..bigbang
        ''',
        expect_error='''Line 3: Unexpected DOT
                x: ..bigbang
                    ^''')

        self.given('''
            x
                x: bigcrunch..bigbang
        ''',
        expect_error='Line 3: Invalid character range: bigcrunch..bigbang')

        self.given('''
            x
                x: A...Z
        ''',
        expect_error='''Line 3: Unexpected DOT
                x: A...Z
                      ^''')

        self.given('''
            x
                x: 1..2..3
        ''',
        expect_error='''Line 3: Unexpected DOT
                x: 1..2..3
                       ^''')

        self.given('''
            x
                x: /IsAlphabetic..Z
        ''',
        expect_error='Line 3: Invalid character range: /IsAlphabetic..Z')

        self.given('''
            x
                x: +alpha..Z
        ''',
        expect_error='Line 3: Invalid character range: +alpha..Z')

        self.given('''
            aB
                aB: a..B
        ''',
        expect_error='Line 3: a..B compiles to [a-B] which is rejected by the regex engine with error message: bad character range at position 4')

        self.given(r'''
            BA
                BA: \u0042..A
        ''',
        expect_error='Line 3: \u0042..A compiles to [\u0042-A] which is rejected by the regex engine with error message: bad character range at position 9')

        self.given(r'''
            BA
                BA: \U00000042..\u0041
        ''',
        expect_error='Line 3: \U00000042..\u0041 compiles to [\U00000042-\u0041] which is rejected by the regex engine with error message: bad character range at position 18')

        self.given(r'''
            BA
                BA: \x42..\U00000041
        ''',
        expect_error=r'Line 3: \x42..\U00000041 compiles to [\x42-\U00000041] which is rejected by the regex engine with error message: bad character range at position 16')

        self.given(r'''
            BA
                BA: \102..\x41
        ''',
        expect_error=r'Line 3: \102..\x41 compiles to [\102-\x41] which is rejected by the regex engine with error message: bad character range at position 10')

        self.given(r'''
            BA
                BA: \N{LATIN CAPITAL LETTER B}..\101
        ''',
        expect_error=r'Line 3: \N{LATIN CAPITAL LETTER B}..\101 compiles to [\N{LATIN CAPITAL LETTER B}-\101] which is rejected by the regex engine with error message: bad character range at position 32')

        self.given('''
            BA
                BA: :LATIN_CAPITAL_LETTER_B..\N{LATIN CAPITAL LETTER A}
        ''',
        expect_error='Line 3: :LATIN_CAPITAL_LETTER_B..\N{LATIN CAPITAL LETTER A} compiles to [\N{LATIN CAPITAL LETTER B}-\N{LATIN CAPITAL LETTER A}] which is rejected by the regex engine with error message: bad character range at position 54')

        self.given('''
            BA
                BA: \N{LATIN CAPITAL LETTER B}..:LATIN_CAPITAL_LETTER_A
        ''',
        expect_error='Line 3: \N{LATIN CAPITAL LETTER B}..:LATIN_CAPITAL_LETTER_A compiles to [\N{LATIN CAPITAL LETTER B}-\N{LATIN CAPITAL LETTER A}] which is rejected by the regex engine with error message: bad character range at position 54')

        self.given(r'''
            aZ
                aZ: \N{LATIN SMALL LETTER A}..:LATIN_CAPITAL_LETTER_Z
        ''',
        expect_error='Line 3: \N{LATIN SMALL LETTER A}..:LATIN_CAPITAL_LETTER_Z compiles to [\N{LATIN SMALL LETTER A}-\N{LATIN CAPITAL LETTER Z}] which is rejected by the regex engine with error message: bad character range at position 52')


    def test_invalid_charclass_include(self):
        self.given('''
            x
                x: +1
        ''',
        expect_error="Line 3: Cannot include '1': not defined")

        self.given('''
            x
                x: +7even
        ''',
        expect_error="Line 3: Cannot include '7even': not defined")

        self.given('''
            x
                x: +7even
                    7even: 7
        ''',
        expect_error='''Line 4: Unexpected NUMBER
                    7even: 7
                    ^''')

        self.given('''
            x
                x: +bang!
        ''',
        expect_error='''Line 3: Unexpected CHAR
                x: +bang!
                        ^''')

        self.given('''
            x
                x: ++
        ''',
        expect_error='''Line 3: Unexpected CHAR
                x: ++
                    ^''')

        self.given('''
            x
                x: +!awe+some
        ''',
        expect_error='''Line 3: Unexpected CHAR
                x: +!awe+some
                    ^''')

        self.given('''
            x
                x: y
                    y: m i s n g +
        ''',
        expect_error="Line 4: 'y' is defined but not used (by its parent expression)")

        self.given('''
            x
                x: +y
                    y = 'should be a charclass'
        ''',
        expect_error="Line 3: Cannot include 'y': not a character class")

        self.given(u'''
            vowhex
                vowhex: +!vowel +hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_error='''Line 3: Unexpected CHAR
                vowhex: +!vowel +hex
                         ^''')

        self.given(u'''
            notand
                notand: not and -- possible, but must use +not +and
                    not: n o t
                    and: a n d
        ''',
        expect_error="Line 3: Invalid use of binary 'not' operator")

        self.given(u'''
            /x/y/
                x = 'x'
                y: +x
        ''',
        expect_error="Line 4: Cannot include 'x': not a character class")

        self.given(u'''
            /plus/minus/pmz/
                plus: +
                minus = '-' -- gotcha: exactly-same output with "minus: -" but not includable 
                pmz: +plus +minus z
        ''',
        expect_error="Line 5: Cannot include 'minus': not a character class")

        self.given(u'''
            /plus/minus/pmz/
                plus: +
                minus = '-'
                pmz: +plus +dash z
                    dash: +minus
        ''',
        expect_error="Line 6: Cannot include 'minus': not a character class")


    def test_invalid_charclass_operation(self):
        self.given(u'''
            missing_arg
                missing_arg: /Alphabetic and
        ''',
        expect_error="Line 3: Invalid use of binary 'and' operator")

        self.given(u'''
            missing_arg
                missing_arg: and /Alphabetic
        ''',
        expect_error="Line 3: Invalid use of binary 'and' operator")

        self.given(u'''
            missing_arg
                missing_arg: /Alphabetic not
        ''',
        expect_error="Line 3: Invalid use of binary 'not' operator")

        self.given(u'''
            missing_arg
                missing_arg: not /Alphabetic
        ''',
        expect_error="Line 3: Invalid use of binary 'not' operator")

        self.given(u'''
            missing_args
                missing_args: and
        ''',
        expect_error="Line 3: Invalid use of binary 'and' operator")

        self.given(u'''
            missing_args
                missing_args: not
        ''',
        expect_error="Line 3: Invalid use of binary 'not' operator")

        self.given(u'''
            missing_args
                missing_args: not:
        ''',
        expect_error="Line 3: Invalid use of unary 'not:' operator")

        self.given(u'''
            1 of: x and not y
        ''',
        expect_error="Line 2: Bad set operation 'and not'")

        self.given(u'''
            1 of: x not and y
        ''',
        expect_error="Line 2: Bad set operation 'not and'")

        self.given(u'''
            1 of: x not not y
        ''',
        expect_error="Line 2: Bad set operation 'not not'")

        self.given(u'''
            1 of: x and and y
        ''',
        expect_error="Line 2: Bad set operation 'and and'")

        self.given(u'''
            1 of: not: not: x
        ''',
        expect_error="Line 2: Invalid use of unary 'not:' operator")

        self.given(u'''
            1 of: not: not x
        ''',
        expect_error="Line 2: Bad set operation 'not: not'")

        self.given(u'''
            1 of: not: and x
        ''',
        expect_error="Line 2: Bad set operation 'not: and'")


    def test_invalid_quantifier(self):
        self.given('''
            3 of
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            3 of
              ^''')

        self.given('''
            3 of          
                of = 'trailing spaces above after the "of"'
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            3 of          
              ^''')

        self.given('''
            3 of -- 3 of what?
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            3 of -- 3 of what?
              ^''')

        self.given('''
            3 of-- 3 of what?
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            3 of-- 3 of what?
              ^''')

        self.given('''
            3 of of--
        ''',
        expect_error='''Line 2: Unexpected MINUS
            3 of of--
                   ^''')

        self.given('''
            3 alpha
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            3 alpha
              ^''')

        self.given('''
            3 ofalpha
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            3 ofalpha
              ^''')

        self.given('''
            3of alpha
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            3of alpha
             ^''')

        self.given('''
            3 o falpha
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            3 o falpha
              ^''')

        self.given('''
            3 office alpha
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            3 office alpha
              ^''')

        self.given('''
            3. of alpha
        ''',
        expect_error='''Line 2: Unexpected WHITESPACE
            3. of alpha
              ^''')

        self.given('''
            3... of alpha
        ''',
        expect_error='''Line 2: Unexpected DOT
            3... of alpha
               ^''')

        self.given('''
            3+ of alpha
        ''',
        expect_error='''Line 2: Unexpected PLUS
            3+ of alpha
             ^''')

        self.given('''
            3+3 of alpha
        ''',
        expect_error='''Line 2: Unexpected PLUS
            3+3 of alpha
             ^''')

        self.given('''
            @3..2 of alpha
        ''',
        expect_error='Line 2: Repeat max must be > min')

        self.given('''
            @2..2 of alpha
        ''',
        expect_error='Line 2: Repeat max must be > min')

        self.given('''
            @1..1 of alpha
        ''',
        expect_error='Line 2: Repeat max must be > min')

        self.given('''
            @0..0 of alpha
        ''',
        expect_error='Line 2: Repeat max must be > min')

        self.given('''
            1 ..3 of alpha
        ''',
        expect_error='''Line 2: Unexpected DOT
            1 ..3 of alpha
              ^''')

        self.given('''
            1.. 3 of alpha
        ''',
        expect_error='''Line 2: Unexpected NUMBER
            1.. 3 of alpha
                ^''')

        self.given('''
            1 .. of alpha
        ''',
        expect_error='''Line 2: Unexpected DOT
            1 .. of alpha
              ^''')

        self.given('''
            1 <<- of alpha
        ''',
        expect_error='''Line 2: Unexpected MINUS
            1 <<- of alpha
                ^''')

        self.given('''
            1 <<+ of alpha
        ''',
        expect_error='''Line 2: Unexpected WHITESPACE
            1 <<+ of alpha
                 ^''')

        self.given('''
            1 <<+..0 of alpha
        ''',
        expect_error='Line 2: Repeat max must be > min')

        self.given('''
            0 <<+..0 of alpha
        ''',
        expect_error='Line 2: Repeat max must be > min')

        self.given('''
            1 <<+..1 of alpha
        ''',
        expect_error='Line 2: Repeat max must be > min')

        self.given('''
            2 <<+..2 of alpha
        ''',
        expect_error='Line 2: Repeat max must be > min')

        self.given('''
            2..1 <<- of alpha
        ''',
        expect_error='Line 2: Repeat max must be > min')

        self.given('''
            ? <<- of alpha
        ''',
        expect_error='''Line 2: Unexpected QUESTMARK
            ? <<- of alpha
            ^''')

        self.given('''
            1.. of alpha
        ''',
        expect_error='''Line 2: Unexpected OF
            1.. of alpha
                ^''')

        self.given('''
            1..2 of alpha
        ''',
        expect_error='''Line 2: Unexpected OF
            1..2 of alpha
                 ^''')

        self.given('''
            .. of alpha
        ''',
        expect_error='''Line 2: Unexpected DOT
            .. of alpha
             ^''')

        self.given('''
            ..1 of alpha
        ''',
        expect_error='''Line 2: Unexpected DOT
            ..1 of alpha
             ^''')

        self.given('''
            ..2 <<- of alpha
        ''',
        expect_error='''Line 2: Unexpected DOT
            ..2 <<- of alpha
             ^''')

        self.given('''
            @.. of alpha
        ''',
        expect_error='''Line 2: Unexpected DOT
            @.. of alpha
              ^''')

        self.given('''
            @..1 of alpha
        ''',
        expect_error='''Line 2: Unexpected DOT
            @..1 of alpha
              ^''')

        self.given('''
            @..2 <<- of alpha
        ''',
        expect_error='''Line 2: Unexpected DOT
            @..2 <<- of alpha
              ^''')

        self.given('''
            ? of alpha
        ''',
        expect_error='''Line 2: Unexpected QUESTMARK
            ? of alpha
            ^''')

        self.given('''
            @? of alpha
        ''',
        expect_error='''Line 2: Unexpected QUESTMARK
            @? of alpha
             ^''')


    def test_commenting_error(self):
        self.given('''
            - this comment is missing another - prefix
        ''',
        expect_error='''Line 2: Unexpected MINUS
            - this comment is missing another - prefix
            ^''')

        self.given('''
            1 of vowel - this comment is missing another - prefix
                vowel: a i u e o 
        ''',
        expect_error='''Line 2: Unexpected WHITESPACE
            1 of vowel - this comment is missing another - prefix
                      ^''')

        self.given('''
            1 of vowel- this comment is missing another - prefix
                vowel: a i u e o 
        ''',
        expect_error='''Line 2: Unexpected MINUS
            1 of vowel- this comment is missing another - prefix
                      ^''')

        self.given('''
            1 of vowel
                vowel: a i u e o - this comment is missing another - prefix
        ''',
        expect_error="Line 3: Cannot include 'this': not defined")

        self.given('''
            1 of vowel
                vowel: a i u e o- this comment is missing another - prefix
        ''',
        expect_error='''Line 3: Unexpected CHAR
                vowel: a i u e o- this comment is missing another - prefix
                                ^''')

        self.given('''
            /comment/-- whitespace required before the "--"
                comment = 'first'
        ''',
        expect_error='''Line 2: Unexpected MINUS
            /comment/-- whitespace required before the "--"
                     ^''')

        self.given('''
            /comment/--
                comment = 'first'
        ''',
        expect_error='''Line 2: Unexpected MINUS
            /comment/--
                     ^''')


    def test_invalid_reference(self):
        self.given('''
            =missing
        ''',
        expect_error="Line 2: Bad backreference: 'missing' is not defined/not a capturing group")

        self.given('''
            =missing?
        ''',
        expect_error="Line 2: Bad backreference: 'missing' is not defined/not a capturing group")

        self.given('''
            =alpha
        ''',
        expect_error="Line 2: Bad backreference: 'alpha' is not defined/not a capturing group")

        self.given('''
            /bang/=bang/
                bang: b a n g !
        ''',
        expect_error="Line 2: Bad backreference: 'bang' is not defined/not a capturing group")


    def test_invalid_boundaries(self):
        self.given('''
            /cat./
                cat = 'cat'
        ''',
        expect_error='''Line 2: Unexpected DOT
            /cat./
                ^''')

        self.given('''
            /.cat/
                cat = 'cat'
        ''',
        expect_error='''Line 2: Unexpected DOT
            /.cat/
             ^''')

        self.given('''
            /cat_/
                cat = 'cat'
        ''',
        expect_error="Line 2: 'cat_' is not defined")

        self.given('''
            /cat/
                cat = 'cat' .
        ''',
        expect_error='''Line 3: Unexpected WHITESPACE
                cat = 'cat' .
                           ^''')

        self.given('''
            /cat/
                cat = 'cat'__
        ''',
        expect_error='''Line 3: Unexpected VARNAME
                cat = 'cat'__
                           ^''')

        self.given('''
            /_/
                _ = 'underscore'
        ''',
        expect_error='''Line 3: Unexpected UNDERSCORE
                _ = 'underscore'
                ^''')

        self.given('''
            /_./
        ''',
        expect_error='''Line 2: Unexpected DOT
            /_./
              ^''')


    def test_invalid_flags(self):
        self.given('''
            (pirate) 'carribean'
        ''',
        expect_error="Line 2: Unknown flag 'pirate'. Supported flags are: ascii bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse unicode verbose version0 version1 word")
 
        self.given('''
            (-pirate) 'carribean'
        ''',
        expect_error="Line 2: Unknown flag '-pirate'. Supported flags are: ascii bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse unicode verbose version0 version1 word")
 
        self.given('''
            (--ignorecase) 'carribean'
        ''',
        expect_error="Line 2: Unknown flag '--ignorecase'. Supported flags are: ascii bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse unicode verbose version0 version1 word")
 
        self.given('''
            (unicode-ignorecase)
            alpha
        ''',
        expect_error="Line 2: Unknown flag 'unicode-ignorecase'. Supported flags are: ascii bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse unicode verbose version0 version1 word")

        self.given('''
            (unicode) alpha
        ''',
        expect_error="Line 2: 'unicode' is a global flag and must be set using global flag syntax, not scoped.")

        self.given('''
            (ignorecase)alpha
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            (ignorecase)alpha
                        ^''')

        self.given('''
            (ignorecase)
             alpha
        ''',
        expect_error='Line 3: Unexpected INDENT')

        self.given('''
            (ignorecase -ignorecase) alpha
        ''',
        expect_error='Line 2: (ignorecase -ignorecase) compiles to (?i-i) which is rejected by the regex engine with error message: bad inline flags: flag turned on and off at position 10')
 
        self.given('''
            (-ignorecase ignorecase) alpha
        ''',
        expect_error='Line 2: (-ignorecase ignorecase) compiles to (?i-i) which is rejected by the regex engine with error message: bad inline flags: flag turned on and off at position 10')
 
        self.given('''
            (-ignorecase ignorecase unicode)
            alpha
        ''',
        expect_error='Line 2: (-ignorecase ignorecase unicode) compiles to (?iu-i) which is rejected by the regex engine with error message: bad inline flags: flag turned on and off at position 11')
 
        self.given('''
            (-ignorecase unicode ignorecase)
            alpha
        ''',
        expect_error='Line 2: (-ignorecase unicode ignorecase) compiles to (?ui-i) which is rejected by the regex engine with error message: bad inline flags: flag turned on and off at position 11')
 
        self.given('''
            (-unicode)
            alpha
        ''',
        expect_error='Line 2: (-unicode) compiles to (?-u) which is rejected by the regex engine with error message: bad inline flags: cannot turn off global flag at position 9')
 
        self.given('''
            (ignorecase)
            (-ignorecase)
        ''',
        expect_error='''Line 3: Unexpected NEWLINE
            (-ignorecase)
                         ^''')
 
        self.given('''
            (unicode ignorecase)
            (-ignorecase)
        ''',
        expect_error='''Line 3: Unexpected NEWLINE
            (-ignorecase)
                         ^''')

        self.given('''
            (ascii unicode)
        ''',
        expect_error='Line 2: (ascii unicode) compiles to (?au) which is rejected by the regex engine with error message: ASCII, LOCALE and UNICODE flags are mutually incompatible')

        self.given('''
            (unicode ascii)
        ''',
        expect_error='Line 2: (unicode ascii) compiles to (?ua) which is rejected by the regex engine with error message: ASCII, LOCALE and UNICODE flags are mutually incompatible')

        self.given('''
            (ascii locale)
        ''',
        expect_error='Line 2: (ascii locale) compiles to (?aL) which is rejected by the regex engine with error message: ASCII, LOCALE and UNICODE flags are mutually incompatible')

        self.given('''
            (unicode locale)
        ''',
        expect_error='Line 2: (unicode locale) compiles to (?uL) which is rejected by the regex engine with error message: ASCII, LOCALE and UNICODE flags are mutually incompatible')

        self.given('''
            (version0 version1)
        ''',
        expect_error='Line 2: (version0 version1) compiles to (?V0V1) which is rejected by the regex engine with error message: 8448')

        self.given('''
            (version1 version0)
        ''',
        expect_error='Line 2: (version1 version0) compiles to (?V1V0) which is rejected by the regex engine with error message: 8448')


    def test_invalid_orblock(self):
        self.given('''
            empty_orblock_not_allowed
                empty_orblock_not_allowed = @|
        ''',
        expect_error='Line 4: Unexpected END_OF_ORBLOCK')

        self.given('''
            /empty_orblock/not_allowed/
                empty_orblock = @|

                not_allowed = 'NOTALLOWED'
        ''',
        expect_error='Line 5: Unexpected END_OF_ORBLOCK')

        self.given('''
            <<|
        ''',
        expect_error='Line 3: Unexpected END_OF_ORBLOCK')

        self.given('''
            /x/y/
                x = @|
                     |'AM'
                     |'PM'
                y = 'forgot empty line to terminate the orblock'
        ''',
        expect_error='''Line 6: Unexpected VARNAME (forgot to close ORBLOCK?)
                y = 'forgot empty line to terminate the orblock'
                ^''')

        self.given('''
            @|
             |am
             |pm
                am = 'AM'
                pm = 'PM
        ''',
        expect_error='''Line 5: Unexpected VARNAME (forgot to close ORBLOCK?)
                am = 'AM'
                ^''')

        self.given('''
            /trailing/bar/
                trailing = <<|
                             |'choice 1'
                             |'choice 2'
                             |
                bar: |
        ''',
        expect_error='''Line 7: Unexpected VARNAME (forgot to close ORBLOCK?)
                bar: |
                ^''')

        self.given('''
            <<|
              |'alignment check'
             |'this one is bad'
        ''',
        expect_error='Line 4: Misaligned OR')

        self.given('''
            @|
              |'also misalignment'
        ''',
        expect_error='Line 3: Misaligned OR')

        self.given('''
            orblock_type
                orblock_type = | -- atomic? backtrack? must specify
                               |'to be'
                               |'not to be'
        ''',
        expect_error='''Line 3: Unexpected OR
                orblock_type = | -- atomic? backtrack? must specify
                               ^''')

        self.given('''
            syntax_err
                syntax_err = <<|'to be'       -- choices should start in second line
                               |'not to be'
        ''',
        expect_error='''Line 3: Unexpected STRING
                syntax_err = <<|'to be'       -- choices should start in second line
                                ^''')

        self.given('''
            <<|
              |missing/a/slash/
        ''',
        expect_error='''Line 3: Unexpected SLASH
              |missing/a/slash/
                      ^''')

        self.given('''
            nested_orblock
                nested_orblock = @|
                                  |'nested orblock not allowed'
                                  |@|
                                    |'make it a var'
                                  |'then lookup'
        ''',
        expect_error='Line 5: ORBLOCK cannot contain ORBLOCK')

        self.given('''
            nested_orblock
                nested_orblock = <<|
                                   |@|
        ''',
        expect_error='Line 4: ORBLOCK cannot contain ORBLOCK')

        self.given('''
            nested_orblock
                nested_orblock = @|
                                  |<<|
        ''',
        expect_error='Line 4: ORBLOCK cannot contain ORBLOCK')

        self.given('''
            nested_orblock
                nested_orblock = <<|
                                   |<<|
        ''',
        expect_error='Line 4: ORBLOCK cannot contain ORBLOCK')

        self.given('''
            orblock_containing_lookblock
                orblock_containing_lookblock = <<|
                                                 |<@>
                                                   |!/allowed/>
        ''',
        expect_error='Line 4: ORBLOCK cannot contain LOOKAROUND')


    def test_invalid_lookaround(self):
        self.given('''
            empty_lookaround_not_allowed
                empty_lookaround_not_allowed = <@>
        ''',
        expect_error='Line 4: Unexpected END_OF_LOOKAROUND')

        self.given('''
            /empty_lookaround/not_allowed/
                empty_lookaround = <@>

                not_allowed = 'NOTALLOWED'
        ''',
        expect_error='Line 5: Unexpected END_OF_LOOKAROUND')

        self.given('''
            <@>
            |> -- empty lookahead
        ''',
        expect_error='''Line 3: Unexpected GT
            |> -- empty lookahead
             ^''')

        self.given('''
            <@>
            <| -- empty lookbehind
        ''',
        expect_error='''Line 3: Unexpected BAR
            <| -- empty lookbehind
             ^''')

        self.given('''
            <@>
            || -- empty base
        ''',
        expect_error='''Line 3: Unexpected BAR
            || -- empty base
             ^''')

        self.given('''
            <@>
        ''',
        expect_error='Line 3: Unexpected END_OF_LOOKAROUND')

        self.given('''
            /x/y/
                x = <@>
                    <behind|
                           |ahead>
                y = 'forgot empty line to terminate the lookaround'
        ''',
        expect_error='''Line 6: Unexpected VARNAME (forgot to close LOOKAROUND?)
                y = 'forgot empty line to terminate the lookaround'
                ^''')

        self.given('''
            <@>
            <past|
                 |future>
                past = 'behind'
                future = 'ahead'
        ''',
        expect_error='''Line 5: Unexpected VARNAME (forgot to close LOOKAROUND?)
                past = 'behind'
                ^''')

        self.given('''
            alignment_check
                alignment_check = <@>
                                  <mis|
                                       |align>
        ''',
        expect_error='Line 5: Misaligned |')

        self.given('''
            <@>
            <mis|
                 |align>
        ''',
        expect_error='Line 4: Misaligned |')

        self.given('''
            <@>
            <mis|
               |align>
        ''',
        expect_error='Line 4: Misaligned |')

        self.given('''
            <@>
            <this_is_good|
                         |alignment|
             <this_is_bad|
        ''',
        expect_error='Line 5: Misaligned |')

        self.given('''
            <@>
             |this_is_good>
             |alignment|
             |this_is_bad>
        ''',
        expect_error='Line 5: Misaligned |')

        self.given('''
            <@>
             |wrong|
             |chaining|
        ''',
        expect_error='Line 4: Misaligned |')

        self.given('''
            check_indent
                check_indent = <@>
                                |/this/line/OK/|
          </this/line/needs/deeper/indentation/|
        ''',
        expect_error='Line 5: needs deeper indentation')

        self.given('''
            check_indent
                check_indent = <@>
                                       |this_line_OK|
               </this/line/needs/deeper/indentation/|
        ''',
        expect_error='Line 5: needs deeper indentation')

        self.given('''
            check_indent
                check_indent = <@>
               <this_line_needs_deeper_indentation|
                                                  |/this/one/OK/|
        ''',
        expect_error='Line 4: needs deeper indentation')

        self.given('''
                <@>
               |/more/indent/please/|
        ''',
        expect_error='Line 3: needs deeper indentation')

        self.given('''
                <@>
               |more_indent_please>
        ''',
        expect_error='Line 3: needs deeper indentation')

        self.given('''
                <@>
               <!enough_indent|
        ''',
        expect_error='Line 3: needs deeper indentation')

        self.given('''
            syntax_err
                syntax_err = <@>|ahead>
        ''',
        expect_error='''Line 3: Unexpected BAR
                syntax_err = <@>|ahead>
                                ^''')

        self.given('''
            syntax_err
                syntax_err = <@>
                             <missing/a/slash/|
        ''',
        expect_error='''Line 4: Unexpected SLASH
                             <missing/a/slash/|
                                     ^''')

        self.given('''
            syntax_err
                syntax_err = <@>
                             </missing/a/slash|
        ''',
        expect_error='''Line 4: Unexpected BAR
                             </missing/a/slash|
                                              ^''')

        self.given('''
            syntax_err
                syntax_err = <@>
                             <!missing/a/slash/|
        ''',
        expect_error='''Line 4: Unexpected SLASH
                             <!missing/a/slash/|
                                      ^''')

        self.given('''
            syntax_err
                syntax_err = <@>
                             |!missing/a/slash>
        ''',
        expect_error='''Line 4: Unexpected SLASH
                             |!missing/a/slash>
                                      ^''')

        self.given('''
            syntax_err
                syntax_err = <@>
                             |missing/slashes|
        ''',
        expect_error='''Line 4: Unexpected SLASH
                             |missing/slashes|
                                     ^''')

        self.given('''
            syntax_err
                syntax_err = <@>
                             </ahead/behind/>
        ''',
        expect_error='''Line 4: Unexpected GT
                             </ahead/behind/>
                                            ^''')

        self.given('''
            syntax_err
                syntax_err = <@>
                             <behind<
        ''',
        expect_error='''Line 4: Unexpected LT
                             <behind<
                                    ^''')

        self.given('''
            syntax_err
                syntax_err = <@>
                             </missing/bar/
        ''',
        expect_error='''Line 4: Unexpected NEWLINE
                             </missing/bar/
                                           ^''')

        self.given('''
            syntax_err
                syntax_err = <@>
                             /missing/bar/>
        ''',
        expect_error='''Line 4: Unexpected SLASH
                             /missing/bar/>
                             ^''')

        self.given('''
            syntax_err
                syntax_err = <@>
                             !/missing/bar/>
        ''',
        expect_error='''Line 4: Unexpected EXCLAMARK
                             !/missing/bar/>
                             ^''')

        self.given('''
            syntax_err
                syntax_err = <@>
                             missing_bar>
        ''',
        expect_error='''Line 4: Unexpected VARNAME (forgot to close LOOKAROUND?)
                             missing_bar>
                             ^''')

        self.given('''
            syntax_err
                syntax_err = <@>
                             |missing_bar_or_gt
        ''',
        expect_error='''Line 4: Unexpected NEWLINE
                             |missing_bar_or_gt
                                               ^''')

        self.given('''
            nested_orblock
                nested_orblock = <@>
                                  |nested_lookaround>
                                  |<@>
                                    |!allowed>
        ''',
        expect_error='Line 5: LOOKAROUND cannot contain LOOKAROUND')

        self.given('''
            lookblock_containing_orblock
                lookblock_containing_orblock = <@>
                                                @|
                                                 |"can't"
        ''',
        expect_error='Line 4: LOOKAROUND cannot contain ORBLOCK')


    def test_invalid_non_op(self):
        self.given('''
            non-BOS
        ''',
        expect_error="Line 2: 'non-BOS': 'BOS' is not a character-class")

        self.given('''
            non-any
        ''',
        expect_error="Line 2: 'non-any': 'any' is not a character-class")

        self.given('''
            non-vowel
                vowel = (ignorecase) 1 of: a i u e o
        ''',
        expect_error="Line 2: 'non-vowel': 'vowel' is not a character-class")

        self.given('''
            non-pin
                pin = @4..6 of digit
        ''',
        expect_error="Line 2: 'non-pin': 'pin' is not a character-class")

        self.given('''
            non-digits
                digits = @1.. of digit
        ''',
        expect_error="Line 2: 'non-digits': 'digits' is not a character-class")

        self.given('''
            non-digits
                digits = 1.. <<- of digit
        ''',
        expect_error="Line 2: 'non-digits': 'digits' is not a character-class")

        self.given('''
            non-digits
                digits = 1 <<+.. of digit
        ''',
        expect_error="Line 2: 'non-digits': 'digits' is not a character-class")

        self.given('''
            non-non-alpha
        ''',
        expect_error='''Line 2: Unexpected NON
            non-non-alpha
                ^''')


    def test_invalid_anchor_sugar(self):
        self.given('''
            ./
        ''',
        expect_error='''Line 2: Unexpected NEWLINE
            ./
              ^''')

        self.given('''
            /.
        ''',
        expect_error='''Line 2: Unexpected DOT
            /.
             ^''')

        self.given('''
            .//.
        ''',
        expect_error='''Line 2: Unexpected SLASH
            .//.
              ^''')

        self.given('''
            ./alpha./
        ''',
        expect_error='''Line 2: Unexpected DOT
            ./alpha./
                   ^''')

        self.given('''
            /.alpha/.
        ''',
        expect_error='''Line 2: Unexpected DOT
            /.alpha/.
             ^''')

        self.given('''
            //
        ''',
        expect_error='''Line 2: Unexpected NEWLINE
            //
              ^''')

        self.given('''
            ////
        ''',
        expect_error='''Line 2: Unexpected SLASH
            ////
              ^''')

        self.given('''
            /alpha//digit/
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            /alpha//digit/
                    ^''')

        self.given('''
            /alpha/.digit/
        ''',
        expect_error='''Line 2: Unexpected VARNAME
            /alpha/.digit/
                    ^''')


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
                x: \u00ab \u00AB \U000000ab \u00Ab
        ''',
        expect_regex='[\u00ab\u00AB\U000000ab\u00Ab]')

        self.given('''
            x
                x: \u12ab \u12AB \u12Ab
        ''',
        expect_regex='[\u12ab\u12AB\u12Ab]')

        self.given('''
            x
                x: \U0001234a \U0001234A \U0001234a
        ''',
        expect_regex='[\U0001234a\U0001234A\U0001234a]')

        self.given('''
            x
                x: :SKULL_AND_CROSSBONES :BIOHAZARD_SIGN :CANCER
        ''',
        expect_regex='[\N{SKULL AND CROSSBONES}\N{BIOHAZARD SIGN}\N{CANCER}]')


    def test_character_range_output(self):
        self.given(r'''
            AB
                AB: A..\u0042
        ''',
        expect_regex=r'[A-\u0042]')

        self.given(r'''
            AB
                AB: \u0041..\U00000042
        ''',
        expect_regex=r'[\u0041-\U00000042]')

        self.given(r'''
            AB
                AB: \U00000041..\x42
        ''',
        expect_regex=r'[\U00000041-\x42]')

        self.given(r'''
            AB
                AB: \x41..\102
        ''',
        expect_regex=r'[\x41-\102]')

        self.given(r'''
            AB
                AB: \101..\N{LATIN CAPITAL LETTER B}
        ''',
        expect_regex=r'[\101-\N{LATIN CAPITAL LETTER B}]')

        self.given('''
            AB
                AB: \N{LATIN CAPITAL LETTER A}..:LEFT_RIGHT_OPEN-HEADED_ARROW
        ''',
        expect_regex=r'[\N{LATIN CAPITAL LETTER A}-\N{LEFT RIGHT OPEN-HEADED ARROW}]')

        self.given('''
            AB
                AB: :LATIN_CAPITAL_LETTER_A..\N{LEFT RIGHT OPEN-HEADED ARROW}
        ''',
        expect_regex=r'[\N{LATIN CAPITAL LETTER A}-\N{LEFT RIGHT OPEN-HEADED ARROW}]')

        self.given(r'''
            colon_to_semi
                colon_to_semi: :..;
        ''',
        expect_regex='[:-;]')

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

        self.given('''
            aUmlaut
                aUmlaut: +a_with_diaeresis
                    a_with_diaeresis: \u00E4
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
            notand
                notand: +not +and
                    not: n o t
                    and: a n d
        ''',
        expect_regex='[notand]')

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

        self.given('''
            x
                x: +__special__
                    __special__: x
        ''',
        expect_regex='x')

        self.given('''
            x
                x: __special__
                   __special__: x
        ''',
        expect_regex='x')

        self.given('''
            /dot/period/
                period: .
                dot: . period
        ''',
        expect_regex='[..]\.')


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

        self.given('''
            backspace
                backspace: \\
        ''',
        expect_regex=r'\\')

        self.given(r'''
            unicode_charname
                unicode_charname: \N{AMPERSAND} :AMPERSAND \N{BIOHAZARD SIGN} :BIOHAZARD_SIGN
        ''',
        expect_regex='[\N{AMPERSAND}\N{AMPERSAND}\N{BIOHAZARD SIGN}\N{BIOHAZARD SIGN}]')


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
                    [X] = 'X'
        ''',
        expect_regex='%%(?P<X>X)ss')

        self.given('''
            /p/pXs/s/
                p = '%'
                s = 's'
                [pXs] = /p/X/s/
                    [X] = 'X'
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
                        [salutation] = 'Sir/Madam'
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
                [extra] = 'icing'
        ''',
        expect_regex='(?P<extra>icing)(?P<extra>icing)?')

        self.given('''
            /defcon/level/
                defcon = 'DEFCON'
                [level]: 1 2 3 4 5
        ''',
        expect_regex=r'DEFCON(?P<level>[12345])')

        self.given('''
            captured?
                [captured] = /L/R/
                    [L] = 'Left'
                    [R] = 'Right'
        ''',
        expect_regex=r'(?P<captured>(?P<L>Left)(?P<R>Right))?')

        self.given('''
            uncaptured?
                uncaptured = /L?/R/
                    [L] = 'Left'
                    [R] = 'Right'
        ''',
        expect_regex=r'(?:(?P<L>Left)?(?P<R>Right))?')


    def test_atomic_grouping_output(self):
        self.given('''
            @/alpha/ -- possible though pointless
        ''',
        expect_regex=r'(?>[a-zA-Z])')

        self.given('''
            @/alpha/digit/ -- possible though pointless
        ''',
        expect_regex=r'(?>[a-zA-Z]\d)')

        self.given('''
            @/digits?/even/
                digits = 1.. <<- of digit
                even: 0 2 4 6 8
        ''',
        expect_regex=r'(?>\d*[02468])')

        self.given('''
            ./digits?/even/.
                digits = 1.. <<- of digit
                even: 0 2 4 6 8
        ''',
        expect_regex=r'\A\d*[02468]\Z')

        self.given('''
            //digits?/even//
                digits = 1.. <<- of digit
                even: 0 2 4 6 8
        ''',
        expect_regex=r'^\d*[02468]$')


    def test_builtin_output(self):
        self.given('''
            /alpha/upper/lower/digit/alnum/
        ''',
        expect_regex=r'[a-zA-Z][A-Z][a-z]\d[a-zA-Z0-9]')

        self.given('''
            (unicode)
            /alpha/upper/lower/digit/alnum/
        ''',
        expect_regex=r'(?V1mwu)\p{Alphabetic}\p{Uppercase}\p{Lowercase}\d\p{Alphanumeric}')

        self.given('''
            /BOS/EOS/BOL/EOL/BOW/EOW/WOB/
        ''',
        expect_regex=r'\A\Z^$\m\M\b')

        self.given('''
            (multiline)
            /BOS/EOS/BOL/EOL/BOW/EOW/WOB/
        ''',
        expect_regex=r'(?V1wm)\A\Z^$\m\M\b')

        self.given('''
            (-multiline)
            /BOS/EOS/BOL/EOL/BOW/EOW/WOB/
        ''',
        expect_regex=r'(?V1w-m)\A\Z(?m:^)(?m:$)\m\M\b')

        self.given('''
            /any/uany/
        ''',
        expect_regex=r'(?s:.)\X')

        self.given('''
            (dotall)
            /any/uany/
        ''',
        expect_regex=r'(?V1mws).\X')

        self.given('''
            (-dotall)
            /any/uany/
        ''',
        expect_regex=r'(?V1mw-s)(?s:.)\X')

        self.given('''
            /backslash/wordchar/whitechar/linechar/padchar/space/tab/
        ''',
        expect_regex=r'\\\w\s[\r\n\x0B\x0C][ \t] \t')

        self.given('''
            (word verbose)
            /backslash/wordchar/whitechar/linechar/padchar/space/tab/
        ''',
        expect_regex=r'(?V1mwx)\\\w\s[\r\n\x0B\x0C][ \t][ ]\t')

        self.given('''
            (-word -verbose)
            /backslash/wordchar/whitechar/linechar/padchar/space/tab/
        ''',
        expect_regex=r'(?V1m-wx)\\\w\s\n[ \t] \t')

        self.given('''
            /non-alpha/non-upper/non-lower/non-digit/non-alnum/
        ''',
        expect_regex=r'[^a-zA-Z][^A-Z][^a-z]\D[^a-zA-Z0-9]')

        self.given('''
            (unicode)
            /non-alpha/non-upper/non-lower/non-digit/non-alnum/
        ''',
        expect_regex=r'(?V1mwu)\P{Alphabetic}\P{Uppercase}\P{Lowercase}\D\P{Alphanumeric}')

        self.given('''
            /non-WOB/
        ''',
        expect_regex=r'\B')

        self.given('''
            /non-backslash/non-wordchar/non-whitechar/non-linechar/non-padchar/non-space/non-tab/
        ''',
        expect_regex=r'[^\\]\W\S.[^ \t][^ ][^\t]')

        self.given('''
            (word verbose)
            /non-backslash/non-wordchar/non-whitechar/non-linechar/non-padchar/non-space/non-tab/
        ''',
        expect_regex=r'(?V1mwx)[^\\]\W\S.[^ \t][^ ][^\t]')

        self.given('''
            (-word -verbose)
            /non-backslash/non-wordchar/non-whitechar/non-linechar/non-padchar/non-space/non-tab/
        ''',
        expect_regex=r'(?V1m-wx)[^\\]\W\S.[^ \t][^ ][^\t]')


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
            @0.. of alpha
        ''',
        expect_regex='[a-zA-Z]*+')

        self.given('''
            @1.. of alpha
        ''',
        expect_regex='[a-zA-Z]++')

        self.given('''
            @2.. of alpha
        ''',
        expect_regex='[a-zA-Z]{2,}+')

        self.given('''
            @0..2 of alpha
        ''',
        expect_regex='[a-zA-Z]{,2}+')

        self.given('''
            @0..1 of alpha
        ''',
        expect_regex='[a-zA-Z]?+')

        self.given('''
            @3..4 of alpha
        ''',
        expect_regex='[a-zA-Z]{3,4}+')

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
            0..2 <<- of alpha
        ''',
        expect_regex='[a-zA-Z]{,2}')

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
            alphas?
                alphas = @1.. of alpha
        ''',
        expect_regex='[a-zA-Z]*+')

        self.given('''
            alphas?
                alphas = @0.. of alpha
        ''',
        expect_regex='(?:[a-zA-Z]*+)?')

        self.given('''
            opt_alpha?
                opt_alpha = @0..1 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?+)?')

        self.given('''
            opt_alpha?
                opt_alpha = 0..1 <<- of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?)?')

        self.given('''
            opt_alpha?
                opt_alpha = 0 <<+..1 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]??)?')

        self.given('''
            @0..1 of @0..1 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?+)?+')

        self.given('''
            @0..1 of 0..1 <<- of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?)?+')

        self.given('''
            0 <<+..1 of @0..1 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?+)??')

        self.given('''
            0..1 <<- of 0 <<+..1 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]??)?')

        self.given('''
            2 of @0..1 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?+){2}')

        self.given('''
            @0..1 of 2 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{2})?+')

        self.given('''
            @0..1 of @1..3 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{1,3}+)?+')

        self.given('''
            @1..3 of @0..1 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]?+){1,3}+')

        self.given('''
            1..3 <<- of @5..7 of alpha
        ''',
        expect_regex='(?:[a-zA-Z]{5,7}+){1,3}')

        self.given('''
            @1..3 of 5..7 <<- of alpha
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
            2 of @3..4 of alpha
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
            @2..3 of 4 of alpha
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
                DWORD_speak = @1.. of 4 of hex
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
                [bang]: b a n g !
        ''',
        expect_regex='(?P<bang>[bang!])(?P=bang)')
        
        self.given(u'''
            /=bang/bang/
                [bang]: b a n g !
        ''',
        expect_regex='(?P=bang)(?P<bang>[bang!])')
        
        self.given(u'''
            /bang/=bang?/
                [bang]: b a n g !
        ''',
        expect_regex='(?P<bang>[bang!])(?P=bang)?')
        
        self.given(u'''
            /=bang?/bang/
                [bang]: b a n g !
        ''',
        expect_regex='(?P=bang)?(?P<bang>[bang!])')


    def test_wordchar_boundary_output(self):
        self.given('''
            /wordchar/WOB/non-WOB/BOW/EOW/
        ''',
        expect_regex=r'\w\b\B\m\M')

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
            /WOB/cat/WOB/
                cat = 'cat'
        ''',
        expect_regex=r'\bcat\b')

        self.given('''
            /BOW/cat/EOW/
                cat = 'cat'
        ''',
        expect_regex=r'\mcat\M')

        self.given('''
            /WOB/cat/WOB/
                cat = .'cat'.
        ''',
        expect_regex=r'\b\bcat\b\b')

        self.given('''
            /anti/non-WOB/
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
            non-WOB
        ''',
        expect_regex=r'\B')

        self.given('''
            WOB
        ''',
        expect_regex=r'\b')

        self.given('''
            2 of WOB
        ''',
        expect_regex=r'\b{2}')

        self.given('''
            bdry
                bdry = @/WOB/
        ''',
        expect_regex=r'(?>\b)')

        self.given('''
            bdry
                [bdry] = WOB
        ''',
        expect_regex=r'(?P<bdry>\b)')

        self.given('''
            bdries
                bdries = 1 of 2 of 3 of WOB
        ''',
        expect_regex=r'\b{6}')

        self.given('''
            bdries?
                bdries = @1.. of WOB
        ''',
        expect_regex=r'\b*+')


    def test_string_escape_output(self):
        self.given(r'''
            @3.. of '\n'
        ''',
        expect_regex=r'\n{3,}+')

        self.given(r'''
            @3.. of '\t'
        ''',
        expect_regex=r'\t{3,}+')

        self.given('''
            @3.. of '\t'
        ''',
        expect_regex='\t{3,}+')

        self.given(r'''
            @3.. of '\x61'
        ''',
        expect_regex=r'\x61{3,}+')

        self.given('''
            @3.. of '\x61'
        ''',
        expect_regex='a{3,}+')

        self.given(u'''
            @3.. of '\U00000061'
        ''',
        expect_regex='a{3,}+')

        self.given(r'''
            @3.. of '\u0061'
        ''',
        expect_regex=r'\u0061{3,}+')

        self.given(r'''
            @3.. of '\61'
        ''',
        expect_regex=r'\61{3,}+')

        self.given(u'''
            @3.. of '\N{AMPERSAND}'
        ''',
        expect_regex='&{3,}+')

        self.given(r'''
            @3.. of '\N{AMPERSAND}'
        ''',
        expect_regex=r'\N{AMPERSAND}{3,}+')

        self.given(r'''
            @3.. of '\N{LEFTWARDS ARROW}'
        ''',
        expect_regex=r'\N{LEFTWARDS ARROW}{3,}+')

        self.given(u'''
            @3.. of 'M\N{AMPERSAND}M\\\N{APOSTROPHE}s'
        ''',
        expect_regex="(?:M&M's){3,}+")

        self.given(ur'''
            @3.. of 'M\N{AMPERSAND}M\N{APOSTROPHE}s'
        ''',
        expect_regex=r'(?:M\N{AMPERSAND}M\N{APOSTROPHE}s){3,}+')

        self.given(ur'''
            @3.. of '\r\n'
        ''',
        expect_regex=r'(?:\r\n){3,}+')

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
                uppers = (-ignorecase) @1.. of upper
        ''',
        expect_regex='(?i:super(?-i:[A-Z]++))')

        self.given('''
            hex?
                hex = (ignorecase) 1 of: +digit a..f
        ''',
        expect_regex=r'(?i:[\da-f])?')

        self.given('''
            (ignorecase) 2 of 'yadda'
        ''',
        expect_regex=r'(?i:(?:yadda){2})')

        self.given('''
            2 of (ignorecase) 'yadda'
        ''',
        expect_regex=r'(?i:yadda){2}')

        self.given('''
            2 of (ignorecase) 3 of 4 of (ignorecase) 'yadda'
        ''',
        expect_regex=r'(?i:(?i:yadda){12}){2}')


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
            /BOL/EOL/line2/BOS/EOS/
                line2 = (multiline) /BOL/EOL/BOS/EOS/
        ''',
        expect_regex='(?V1w-m)(?m:^)(?m:$)(?m:^$\A\Z)\A\Z')

        self.given('''
            /BOL/EOL/line2/BOS/EOS/
                line2 = (-multiline) /BOL/EOL/BOS/EOS/
        ''',
        expect_regex='^$(?-m:(?m:^)(?m:$)\A\Z)\A\Z')

        self.given('''
            /BOL/EOL/BOS/EOS/line2/
                line2 = (dotall) /BOL/EOL/BOS/EOS/ -- should be unaffected
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
        expect_regex=r' \t(?x:[ ]\t)(?-x: \t)')

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


    def test_orblock_output(self):
        self.given('''
            @|
             |'cat'
             |'dog'
        ''',
        expect_regex='(?>cat|dog)')

        self.given('''
            <<|
              |'tea'
              |'coffee'
        ''',
        expect_regex='tea|coffee')

        self.given('''
            backtrackable_choice
                backtrackable_choice = <<|
                                         |'catastrophy'
                                         |'catass trophy'
                                         |'cat'
        ''',
        expect_regex='catastrophy|catass trophy|cat')

        self.given('''
            no_backtrack
                no_backtrack = @|
                                |'red pill'
                                |'blue pill'
        ''',
        expect_regex='(?>red pill|blue pill)')

        self.given('''
            /digit/space/ampm/
                ampm = (ignorecase) <<|
                                      |'AM'
                                      |'PM'
        ''',
        expect_regex='\d (?i:AM|PM)')

        self.given('''
            2 of <<|
                   |'fast'
                   |'good'
                   |'cheap'
        ''',
        expect_regex='(?:fast|good|cheap){2}')

        self.given('''
            <<|
              |2 of 'ma'
              |2 of 'pa'
              |2 of 'bolo'
        ''',
        expect_regex='(?:ma){2}|(?:pa){2}|(?:bolo){2}')

        self.given('''
            /blood_type/rhesus/
                blood_type =<<|
                              |'AB'
                              |1 of: A B O

                rhesus = <<|
                           |'+'
                           |'-'
                           | -- allow empty/unknown rhesus
        ''',
        expect_regex='(?:AB|[ABO])(?:\+|-|)')

        self.given('''
            subexpr_types
                subexpr_types = <<|
                                  |'string literal'
                                  |(ignorecase) 1 of: a i u e o
                                  |2..3 <<- of X
                                  |/alpha/digit/
                                  |alpha

                    X = 'X'
        ''',
        expect_regex='string literal|(?i:[aiueo])|X{2,3}|[a-zA-Z]\d|[a-zA-Z]')

        self.given('''
            <<| -- comment here is ok
              |'android'
              |'ios'
        ''',
        expect_regex='android|ios')

        self.given('''
            /nature/side/
                nature = @|
                          |'lawful ' -- mind the trailing space
                          |'chaotic ' 
                          |'neutral '
                --allow comment on ORBLOCK "breaker" line
                side = @|
                        |'good'
                        |'evil'
                        |'neutral'
        ''',
        expect_regex='(?>lawful |chaotic |neutral )(?>good|evil|neutral)')

        self.given('''
            any_color_as_long_as_it_is_
                any_color_as_long_as_it_is_ = <<|
                                                |'black'
                                                -- single-entry "choice" is OK
        ''',
        expect_regex='black')

        self.given('''-- nested ORBLOCKs
            <<|
              |coffee
              |tea
              |'cendol'

                coffee = <<|
                           |'espresso'
                           |'cappuccino'
                           |'kopi tubruk'

                tea = <<|
                        |'earl grey'
                        |'ocha'
                        |'teh tarik'
        ''',
        expect_regex='espresso|cappuccino|kopi tubruk|earl grey|ocha|teh tarik|cendol')


    def test_lookaround_output(self):
        self.given('''
            <@>
                  <yamaha|
            <!/yang/lain/|
                         |semakin|
                                 |/di/depan/>
                                 |!ketinggalan>

                yamaha = 'yamaha'
                yang = 'yang'
                lain = 'lain'
                semakin = 'semakin'
                di = 'di'
                depan = 'depan'
                ketinggalan = 'ketinggalan'
        ''',
        expect_regex='(?<=yamaha)(?<!yanglain)semakin(?=didepan)(?!ketinggalan)')

        self.given('''
            actually_no_lookaround
                actually_no_lookaround = <@>
                                        |alpha| -- possible, though pointless
        ''',
        expect_regex='[a-zA-Z]')

        self.given('''
            <@>
                |anyam>
                |anyaman|
                 <nyaman|

                anyam = 'anyam'
                anyaman = 'anyaman'
                nyaman = 'nyaman'
        ''',
        expect_regex='(?=anyam)anyaman(?<=nyaman)')

        self.given('''
            <@>
            |mixed_case>
            |has_number>
            |has_symbol>
            |./len_8_to_255/.|

                len_8_to_255 = @8..255 of any
                mixed_case = <@>
                                |has_upper>
                                |has_lower>

                    has_upper = /non_uppers?/upper/
                        non_uppers = @1.. of: not: upper
                    has_lower = /non_lowers?/lower/
                        non_lowers = @1.. of: not: lower

                has_number = /non_digits?/digit/
                    non_digits = @1.. of: not: digit
                has_symbol = /non_symbols?/symbol/
                    symbol: not: /Alphanumeric
                    non_symbols = @1.. of: not: symbol
        ''',
        expect_regex='(?=(?=[^A-Z]*+[A-Z])(?=[^a-z]*+[a-z]))(?=[^\d]*+\d)(?=[^\P{Alphanumeric}]*+\P{Alphanumeric})\A(?s:.){8,255}+\Z')

        self.given('''
            word_ends_with_s
                word_ends_with_s = <@>
                    |wordchars|
                            <s|

                    wordchars = @1.. of wordchar
                    s = 's'
        ''',
        expect_regex='\w++(?<=s)')

        self.given('''
            un_x_able
                un_x_able = <@>
                    |un>
                    |unxable|
                       <able|

                    un = 'un'
                    unxable = @1.. of wordchar
                    able = 'able'
        ''',
        expect_regex='(?=un)\w++(?<=able)')

        self.given('''
            escape
                escape = <@>
                    <backslash|
                              |any|
        ''',
        expect_regex=r'(?<=\\)(?s:.)')

        self.given('''
            money_digits
                money_digits = <<|
                                 |dollar_digits
                                 |digits_buck

                    dollar_digits = <@>
                        <dollar|
                               |digits|

                        dollar = '$'
*)                      [digits] = @1.. of digit

                    digits_buck = <@>
                        |digits|
                               |buck>

                        buck = ' buck'
        ''',
        expect_regex='(?<=\$)(?P<digits>\d++)|(?P<digits>\d++)(?= buck)')

        self.given('''
            /begin/msg/end/
                begin = .'BEGIN'.
                end = .'END'.
                msg = @1.. of <<|
                                |@1.. of: not: E
                                |E_not_END

                    E_not_END = <@>
                        |E|
                          |!ND>

                        E = .'E'
                        ND = 'ND'.
        ''',
        expect_regex=r'\bBEGIN\b(?:[^E]++|\bE(?!ND\b))++\bEND\b')


    def test_non_op_output(self):
        self.given('''
            /non-alpha/non-digit/non-whitechar/non-wordchar/non-WOB/
        ''',
        expect_regex=r'[^a-zA-Z]\D\S\W\B')

        self.given('''
            non_digits
                non_digits = @1.. of non-digit
        ''',
        expect_regex=r'\D++')

        self.given('''
            non-alphabetic
                alphabetic: /Alphabetic
        ''',
        expect_regex='\P{Alphabetic}')

        self.given('''
            non-minus
                minus: -
        ''',
        expect_regex=r'[^\-]')

        self.given('''
            non-caret
                caret: ^
        ''',
        expect_regex=r'[^\^]')

        self.given('''
            /non-non_alpha/non-non_digit/
                non_alpha = non-alpha
                non_digit = non-digit
        ''',
        expect_regex=r'[a-zA-Z]\d')

        self.given('''
            non-consonant
                consonant: alpha not vowel
                    vowel: a i u e o A I U E O
        ''',
        expect_regex=r'[^a-zA-Z--aiueoAIUEO]')


    def test_recursion_output(self):
        self.given('''
            singularity
                singularity = singularity
        ''',
        expect_regex='(?P<singularity>(?&singularity))')

        self.given('''
            ./palindrome/.
                palindrome = <<|
                               |/letter/palindrome/=letter/
                               |/letter/=letter/
                               |alpha

                    [letter]: alpha
        ''',
        expect_regex='\A(?P<palindrome>(?P<letter>[a-zA-Z])(?&palindrome)(?P=letter)|(?P<letter>[a-zA-Z])(?P=letter)|[a-zA-Z])\Z')

        self.given('''
            csv
                csv = /value?/more_values?/
                    value = @1.. of non-separator
*)                      separator: ,
                    more_values = /separator/value?/more_values?/
        ''',
        expect_regex='[^,]*+(?P<more_values>,[^,]*+(?:(?&more_values)?)?)?')

        self.given('''
            text_in_parens
                text_in_parens = /open/text/close/
                    open: (
                    close: )
                    text = @1.. of <<|
                                     |non-open
                                     |non-close
                                     |text_in_parens
        ''',
        expect_regex='(?P<text_in_parens>\((?:[^\(]|[^\)]|(?&text_in_parens))++\))')


    def test_anchor_sugar_output(self):
        self.given('''
            //wordchar/
        ''',
        expect_regex=r'^\w')

        self.given('''
            /wordchar//
        ''',
        expect_regex=r'\w$')

        self.given('''
            //wordchar//
        ''',
        expect_regex=r'^\w$')

        self.given('''
            ./wordchar/
        ''',
        expect_regex=r'\A\w')

        self.given('''
            /wordchar/.
        ''',
        expect_regex=r'\w\Z')

        self.given('''
            ./wordchar/.
        ''',
        expect_regex=r'\A\w\Z')

        self.given('''
            ./wordchar//
        ''',
        expect_regex=r'\A\w$')

        self.given('''
            //wordchar/.
        ''',
        expect_regex=r'^\w\Z')

        self.given('''
            @//wordchar/
        ''',
        expect_regex=r'(?>^\w)')

        self.given('''
            @./wordchar/
        ''',
        expect_regex=r'(?>\A\w)')

        self.given('''
            @//wordchar//
        ''',
        expect_regex=r'(?>^\w$)')

        self.given('''
            @./wordchar//
        ''',
        expect_regex=r'(?>\A\w$)')

        self.given('''
            @//wordchar/.
        ''',
        expect_regex=r'(?>^\w\Z)')

        self.given('''
            @./wordchar/.
        ''',
        expect_regex=r'(?>\A\w\Z)')

        self.given('''
            ./wordchar/digit//
        ''',
        expect_regex=r'\A\w\d$')

        self.given('''
            @//wordchar/digit/.
        ''',
        expect_regex=r'(?>^\w\d\Z)')

        self.given('''
            //wordchar/digit//
        ''',
        expect_regex=r'^\w\d$')

        self.given('''
            @./wordchar/digit/.
        ''',
        expect_regex=r'(?>\A\w\d\Z)')

        self.given('''
            <<|
              |./wordchar//
              |//wordchar/.
        ''',
        expect_regex=r'\A\w$|^\w\Z')

        self.given('''
            <@>
             |./wordchar//>
             |./wordchar/.>
             |//wordchar//>
             |./wordchar//>
             |./wordchar/.|
                          |//wordchar//|
                                       |//wordchar/.|
                                                    |./wordchar//|
                                                    <./wordchar/.|
                                                    <//wordchar/.|
                                                   <@//wordchar//|
                                                   <@./wordchar//|
        ''',
        expect_regex=r'(?=\A\w$)(?=\A\w\Z)(?=^\w$)(?=\A\w$)\A\w\Z^\w$^\w\Z\A\w$(?<=\A\w\Z)(?<=^\w\Z)(?<=(?>^\w$))(?<=(?>\A\w$))')


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
                x: \u0041 \u0042 \u0043 \u0044 \u0045
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
        self.given(r'''
            AZ
                AZ: \x41..Z
        ''',
        expect_full_match=['A', 'B', 'C', 'X', 'Y', 'Z'],
        no_match=['a', 'x', 'z', '1', '0'])

        self.given(r'''
            AB
                AB: A..\u0042
        ''',
        expect_full_match=['A', 'B'],
        no_match=['a', 'b'])

        self.given(r'''
            AB
                AB: \u0041..\U00000042
        ''',
        expect_full_match=['A', 'B'],
        no_match=['a', 'b'])

        self.given(r'''
            AB
                AB: \U00000041..\x42
        ''',
        expect_full_match=['A', 'B'],
        no_match=['a', 'b'])

        self.given(r'''
            AB
                AB: \x41..\102
        ''',
        expect_full_match=['A', 'B'],
        no_match=['a', 'b'])

        self.given(r'''
            AB
                AB: \101..\N{LATIN CAPITAL LETTER B}
        ''',
        expect_full_match=['A', 'B'],
        no_match=['a', 'b'])

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

        self.given('''
            1 of: a -..\\
        ''',
        expect_full_match=['a', '-', '\\', '.'],
        no_match=[','])

        self.given('''
            1 of: [..]
        ''',
        expect_full_match=['[', ']'],
        no_match=['-'])


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

        self.given('''
            aUmlaut
                aUmlaut: +a_with_diaeresis
                    a_with_diaeresis: \u00E4
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

        self.given(u'''
            vowhex
                vowhex: +vowel +hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_full_match=['a', 'b', 'f', 'A', 'B', 'F', '0', '1', '9', 'i', 'u', 'E', 'O'],
        no_match=['$', 'z', 'k'])

        self.given(u'''
            1 of: . , ;
        ''',
        expect_full_match=['.', ',', ';'])


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
                unicode_charname: \N{AMPERSAND} \N{BIOHAZARD SIGN}
        ''',
        expect_full_match=['&', u'\N{AMPERSAND}', u'\N{BIOHAZARD SIGN}', u'☣'],
        no_match=['\N{AMPERSAND}', r'\N{AMPERSAND}', r'\N{BIOHAZARD SIGN}', '☣'])

        self.given(r'''
            unicode_charname
                unicode_charname: \N{AMPERSAND} :AMPERSAND \N{BIOHAZARD SIGN} :BIOHAZARD_SIGN
        ''',
        expect_full_match=['&', u'\N{AMPERSAND}', u'\N{BIOHAZARD SIGN}', u'☣'],
        no_match=['\N{AMPERSAND}', r'\N{AMPERSAND}', r'\N{BIOHAZARD SIGN}', '☣'])


    def test_atomic_grouping(self):
        self.given('''
            @/digits/even/
                digits = 0.. <<- of digit
                even: 0 2 4 6 8
        ''',
        expect_full_match=['0', '8', '10', '42', '178'],
        no_match=['', '1', '9', '1337'],
        partial_match={'24681' : '2468', '134579' : '134'})

        self.given('''
            //digits/even//
                digits = 0.. <<- of digit
                even: 0 2 4 6 8
        ''',
        expect_full_match=['0', '8', '10', '42', '178'],
        no_match=['', '1', '9', '1337', '24681', '134579'])


    def test_builtin(self):
        self.given('''
            lowhex
                lowhex: +alpha +alnum +lower not G..Z g..z +upper +digit padchar backslash tab whitechar
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
            @3.. of alpha
        ''',
        expect_full_match=['abc', 'DeFGhij'],
        no_match=['', 'Aa4'])

        self.given('''
            @4..5 of alpha
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
                content = @1.. of: +alnum +open +close
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
                DWORD_speak = @1.. of 4 of hex
                    hex: 0..9 A..F
        ''',
        expect_full_match=['CAFEBABE', 'DEADBEEF', '0FF1CE95'],
        no_match=['', 'YIKE'])


    def test_reference(self):
        self.given(u'''
            /bang/=bang/
                [bang]: b a n g !
        ''',
        expect_full_match=['bb', 'aa', 'nn', 'gg', '!!'],
        no_match=['', 'a', 'ba'])
        
        self.given(u'''
            /=bang/bang/
                [bang]: b a n g !
        ''',
        no_match=['', 'a', 'ba', 'bb', 'aa', 'nn', 'gg', '!!'])
        
        self.given(u'''
            /bang/=bang?/
                [bang]: b a n g !
        ''',
        expect_full_match=['a', 'bb', 'aa', 'nn', 'gg', '!!'],
        no_match=['', 'clang!'],
        partial_match={
            'ba'    : 'b',
            'bang!' : 'b',
        })
        
        self.given(u'''
            /=bang?/bang/
                [bang]: b a n g !
        ''',
        expect_full_match=['b', 'a', 'n', 'g', '!'],
        no_match=['', 'clang!'],
        partial_match={'ba' : 'b', 'bb' : 'b', 'aa' : 'a', 'nn' : 'n', 'gg' : 'g', '!!' : '!', 'bang!' : 'b'})


    def test_wordchar_boundary(self):
        self.given('''
            /wordchar/WOB/non-WOB/
        ''',
        expect_full_match=[],
        no_match=['a', 'b', 'Z', '_'])

        self.given('''
            /EOW/wordchar/BOW/
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
            /WOB/cat/WOB/
                cat = 'cat'
        ''',
        fn=regex.search,
        expect_full_match=['cat'],
        no_match=['tomcat', 'catasthrope', 'complicated', 'garfield'],
        partial_match={'cat videos' : 'cat', 'grumpy cat' : 'cat'})

        self.given('''
            /WOB/cat/WOB/
                cat = .'cat'.
        ''',
        fn=regex.search,
        expect_full_match=['cat'],
        no_match=['tomcat', 'catasthrope', 'complicated', 'garfield'],
        partial_match={'cat videos' : 'cat', 'grumpy cat' : 'cat'})

        self.given('''
            /BOW/cat/EOW/
                cat = 'cat'
        ''',
        fn=regex.search,
        expect_full_match=['cat'],
        no_match=['tomcat', 'catasthrope', 'complicated', 'garfield'],
        partial_match={'cat videos' : 'cat', 'grumpy cat' : 'cat'})

        self.given('''
            /BOW/cat/EOW/
                cat = .'cat'.
        ''',
        fn=regex.search,
        expect_full_match=['cat'],
        no_match=['tomcat', 'catasthrope', 'complicated', 'garfield'],
        partial_match={'cat videos' : 'cat', 'grumpy cat' : 'cat'})

        self.given('''
            /anti/non-WOB/
                anti = 'anti'
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=['anti', 'anti-virus', 'rianti cartwright'],
        partial_match={'antivirus' : 'anti', 'meantime' : 'anti'})

        self.given('''
            anti_
                anti_ = 'anti'_
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

        self.given(ur'''
            3 of '\t\t'
        ''',
        expect_full_match=['\t\t\t\t\t\t'],
        no_match=['\t\t\t\t'])

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


    def test_orblock(self):
        self.given('''
            @|
             |'cat'
             |'dog'
        ''',
        expect_full_match=['cat', 'dog'],
        no_match=['cadog'],
        partial_match={'catdog' : 'cat', 'catog' : 'cat'})

        self.given('''
            <<|
              |'tea'
              |'coffee'
        ''',
        expect_full_match=['tea', 'coffee'],
        no_match=['tecoffee'],
        partial_match={'teacoffee' : 'tea', 'teaoffee' : 'tea'})

        self.given('''
            backtrackable_choice
                backtrackable_choice = <<|
                                         |'catastrophy'
                                         |'catass trophy'
                                         |'cat'
        ''',
        expect_full_match=['catastrophy', 'catass trophy', 'cat'],
        partial_match={'catastrophy cat' : 'catastrophy', 'catass cat' : 'cat'})

        self.given('''
            no_backtrack
                no_backtrack = @|
                                |'red pill'
                                |'blue pill'
        ''',
        expect_full_match=['red pill', 'blue pill'],
        no_match=['red blue pill'],
        partial_match={'red pill pill' : 'red pill'})

        self.given('''
            /digit/space/ampm/
                ampm = (ignorecase) <<|
                                      |'AM'
                                      |'PM'
        ''',
        expect_full_match=['1 AM', '2 pm', '9 pM'],
        no_match=['10 am', '1 APM', 'PM'],
        partial_match={'5 aMm ' : '5 aM'})

        self.given('''
            2 of <<|
                   |'fast'
                   |'good'
                   |'cheap'
        ''',
        expect_full_match=['fastgood', 'fastcheap', 'cheapgood', 'cheapfast', 'goodgood', 'cheapcheap'],
        no_match=['fast', 'good', 'cheap'],
        partial_match={'goodcheapfast' : 'goodcheap'})

        self.given('''
            <<|
              |2 of 'ma'
              |2 of 'pa'
              |2 of 'bolo'
        ''',
        expect_full_match=['mama', 'papa', 'bolobolo'],
        no_match=['ma', 'mapa', 'mabolo', 'boloma', 'pabolo'],
        partial_match={'papabolo' : 'papa', 'mamapapa' : 'mama'})

        self.given('''
            /blood_type/rhesus/
                blood_type =<<|
                              |'AB'
                              |1 of: A B O

                rhesus = <<|
                           |'+'
                           |'-'
                           | -- allow empty/unknown rhesus
        ''',
        expect_full_match=['A', 'A+', 'B', 'B-', 'AB', 'AB+', 'O', 'O-'],
        no_match=[''],
        partial_match={'A+B' : 'A+', 'AAA' : 'A'})

        self.given('''
            subexpr_types
                subexpr_types = <<|
                                  |'string literal'
                                  |(ignorecase) 1 of: a i u e o
                                  |2..3 <<- of X
                                  |/alpha/digit/
                                  |alpha

                    X = 'X'
        ''',
        expect_full_match=['string literal', 'E', 'XX', 'R1', 'X'],
        no_match=['2', '3'],
        partial_match={'aX' : 'a', 'string Z' : 's', 'YY' : 'Y'})

        self.given('''
            <<| -- comment here is ok
              |'android'
              |'ios'
        ''',
        expect_full_match=['android', 'ios'],
        no_match=['androiios'],
        partial_match={'androidos' : 'android'})

        self.given('''
            /nature/side/
                nature = @|
                          |'lawful ' -- mind the trailing space
                          |'chaotic ' 
                          |'neutral '
                --allow comment on ORBLOCK "breaker" line
                side = @|
                        |'good'
                        |'evil'
                        |'neutral'
        ''',
        expect_full_match=['lawful good', 'chaotic good', 'chaotic evil', 'neutral evil', 'neutral neutral'],
        no_match=['neutral', 'neutral ', 'lawful ', 'good', 'evil', 'chaotic chaotic ', 'evilevil', ' '])

        self.given('''
            any_color_as_long_as_it_is_
                any_color_as_long_as_it_is_ = <<|
                                                |'black'
                                                -- single-entry "choice" is OK
        ''',
        expect_full_match=['black'],
        no_match=[''],
        partial_match={'blackish' : 'black'})

        self.given('''-- nested ORBLOCKs
            <<|
              |coffee
              |tea
              |'cendol'

                coffee = <<|
                           |'espresso'
                           |'cappuccino'
                           |'kopi tubruk'

                tea = <<|
                        |'earl grey'
                        |'ocha'
                        |'teh tarik'
        ''',
        expect_full_match=['cendol', 'kopi tubruk', 'teh tarik', 'ocha', 'cappuccino'],
        no_match=['kopi earl grey cendol'],
        partial_match={'espresso tubruk' : 'espresso'})


    def test_lookaround(self):
        self.given('''
            actually_no_lookaround
                actually_no_lookaround = <@>
                    |alpha|
                          |digit|
                                |upper|
                                      |lower|
        ''',
        expect_full_match=['a1Aa'])

        self.given('''
            <@>
                  <yamaha|
            <!/yang/lain/|
                         |semakin|
                                 |/di/depan/>
                                 |!ketinggalan>

                yamaha = 'yamaha'
                yang = 'yang'
                lain = 'lain'
                semakin = 'semakin'
                di = 'di'
                depan = 'depan'
                ketinggalan = 'ketinggalan'
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=['yanglainsemakinketinggalan'],
        partial_match={'yamahasemakindidepan' : 'semakin'})

        self.given('''
            <@>
                |anyam>
                |anyaman|
                 <nyaman|

                anyam = 'anyam'
                anyaman = 'anyaman'
                nyaman = 'nyaman'
        ''',
        expect_full_match=['anyaman'],
        partial_match={'anyamanyamannyaman' : 'anyaman'})

        self.given('''
            <@>
            |mixed_case>
            |has_number>
            |has_symbol>
            |./len_8_to_255/.|

                len_8_to_255 = @8..255 of any
                mixed_case = <@>
                                |has_upper>
                                |has_lower>

                    has_upper = /non_uppers?/upper/
                        non_uppers = @1.. of: not: upper
                    has_lower = /non_lowers?/lower/
                        non_lowers = @1.. of: not: lower

                has_number = /non_digits?/digit/
                    non_digits = @1.. of: not: digit
                has_symbol = /non_symbols?/symbol/
                    symbol: not: /Alphanumeric
                    non_symbols = @1.. of: not: symbol
        ''',
        expect_full_match=['AAaa11!!'],
        no_match=['$h0RT', 'noNumber!', 'noSymb0l', 'n0upcase!', 'N0LOWCASE!'])

        self.given('''
            word_ends_with_s
                word_ends_with_s = <@>
                    |wordchars|
                            <s|

                    wordchars = @1.. of wordchar
                    s = 's'
        ''',
        expect_full_match=['boss'],
        no_match=['sassy'])

        self.given('''
            un_x_able
                un_x_able = <@>
                    |un>
                    |unxable|
                       <able|

                    un = 'un'
                    unxable = @1.. of wordchar
                    able = 'able'
        ''',
        expect_full_match=['undoable', 'unable'])

        self.given('''
            escape
                escape = <@>
                    <backslash|
                              |any|
        ''',
        fn=regex.search,
        no_match=['\t', '\\'],
        partial_match={r'\t' : 't', '\z': 'z', '\\\\':'\\', r'\r\n' : 'r', r'r\n' : 'n', '\wow' : 'w', '\\\'' : '\''})

        self.given('''
            money_digits
                money_digits = <<|
                                 |dollar_digits
                                 |digits_buck

                    dollar_digits = <@>
                        <dollar|
                               |digits|

                        dollar = '$'
*)                      [digits] = @1.. of digit

                    digits_buck = <@>
                        |digits|
                               |buck>

                        buck = ' buck'
        ''',
        fn=regex.search,
        no_match=['123', '4 pm'],
        partial_match={
            '$1'        : '1',
            '$234'      : '234',
            '500 bucks' : '500',
            '1 buck'    : '1',
        })

        self.given('''
            /begin/msg/end/
                begin = .'BEGIN'.
                end = .'END'.
                msg = @1.. of <<|
                                |@1.. of: not: E
                                |E_not_END

                    E_not_END = <<|
                                  |check_ahead
                                  |check_behind

                        check_ahead = <@>
                            |E|
                              |!ND>

*)                          E = 'E'
                            ND = 'ND'.

                        check_behind = <@>
                            <!WOB|
                                 |E|
        ''',
        fn=regex.search,
        expect_full_match=[
            'BEGIN END', 
            'BEGIN hey END',
            'BEGIN BEGINNER FIRE-BENDER BEND ENDER END',
        ],
        no_match=['BEGINNER FIRE-BENDER', 'begin hey end', 'BEGINEND', 'BEGIN ...'],
        partial_match={
            'BEGIN huge wooden horse END brad pitt' : 'BEGIN huge wooden horse END',
            'BEGINNER BEGIN ENDANGERED END' : 'BEGIN ENDANGERED END',
        })


    def test_non_op(self):
        self.given('''
            /non-alpha/non-digit/non-whitechar/non-wordchar/
        ''',
        expect_full_match=['....'])

        self.given('''
            non_digits
                non_digits = @1.. of non-digit
        ''',
        expect_full_match=['ZERO-ZERO-SEVEN', 'ZEROZEROSEVEN'])

        self.given('''
            non-alphabetic
                alphabetic: /Alphabetic
        ''',
        expect_full_match=['1', '!'],
        no_match=['a', u'ä'])

        self.given('''
            non-minus
                minus: -
        ''',
        expect_full_match=['a', '1', '!'],
        no_match=['-'])

        self.given('''
            non-caret
                caret: ^
        ''',
        expect_full_match=['a', '1', '!'],
        no_match=['^'])

        self.given('''
            /non-non_alpha/non-non_digit/
                non_alpha = non-alpha
                non_digit = non-digit
        ''',
        expect_full_match=['a1', 'A9'],
        no_match=['a', '1', 'Aa', '42', 'A+'])

        self.given('''
            non-consonant
                consonant: alpha not vowel
                    vowel: a i u e o A I U E O
        ''',
        expect_full_match=['a', '1', '!'],
        no_match=['b', 'Z'])


    def test_recursion(self):
        self.given('''
            ./palindrome/.
                palindrome = <<|
                               |/letter/palindrome/=letter/
                               |/letter/=letter/
                               |alpha

                    [letter]: alpha
        ''',
        expect_full_match=['a', 'aa', 'aaa', 'aaaa', 'aaaaaa', 'kayak', 'amanaplanacanalpanama', 'amorroma', 'racecar', 'tacocat', 'wasitacaroracatisaw', 'noxinnixon', 'dammitimmad'],
        no_match=['', 'kayaking', 'racecars', 'akayak', 'aracecar', 'lala', 'lalala'])

        self.given('''
            csv
                csv = <@>
                    |/value?/more_values?/|
                               <!/BOS/EOS/|

                        value = @1.. of non-separator
*)                          separator: ,
                        more_values = /separator/value?/more_values?/
        ''',
        expect_full_match=[
            'single value', 
            'value,value', 'value, value, value', 
            'has,,,,empties', 'has,,empty', 'trailing,empty,', 'trailing,empties,,,,', ',,,,leading empties', ',leading empties', ',,,,'],
        no_match=[''])

        self.given('''
            text_in_parens
                text_in_parens = /open/text?/close/
                    open: (
                    close: )
                    text = @1.. of <<|
                                     |non-open
                                     |non-close
                                     |text_in_parens
        ''',
        expect_full_match=[
            '(EST)', 
            '((citation needed))', 
            '()', 
            '(())', 
            '((()))', 
            '(for example, if I (meaning myself) write like this)', 
            '(f (g (h)))', 
            '(((f) g) h)',
        ],
        no_match=['(', ')', ')(', '(()', '((())', '((()', 'f(x)'],
        partial_match={
            '(do-something a) ; or else' : '(do-something a)',
            '())'   : '()',
            '()))'  : '()',
            '(()))' : '(())',
        })


if __name__ == '__main__':
    unittest.main()
