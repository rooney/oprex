# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import unittest, regex, os
from __init__ import oprex, OprexSyntaxError

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
        expect_error=b'Line 1: First line must be blank, not: one-liner input')

        self.given(b'''something in the first line
        ''',
        expect_error=b'Line 1: First line must be blank, not: something in the first line')

        self.given(b'''
        something in the last line''',
        expect_error=b'Line 2: Last line must be blank, not:         something in the last line')


    def test_unknown_symbol(self):
        self.given(b'''
            `@$%^&;{}[]\\
        ''',
        expect_error=b'Line 2: Syntax error at or near: `@$%^&;{}[]\\')


    def test_unexpected_token(self):
        self.given(b'''
            /to/be/?
        ''',
        expect_error=b'''Line 2: Unexpected QUESTMARK
            /to/be/?
                   ^''')

        self.given(b'''
            root
                branch
        ''',
        expect_error=b'''Line 3: Unexpected NEWLINE
                branch
                      ^''')

        self.given(b'''
            root
                root = '/'
            root2
        ''',
        expect_error=b'''Line 4: Unexpected VARNAME
            root2
            ^''')

        self.given(b'''
            root
                root = '/'\nroot2
        ''',
        expect_error=b'Line 4: Unexpected VARNAME\nroot2\n^')

        self.given(b'''
*)          /warming/and/warming/
        ''',
        expect_error=b'Line 2: Unexpected GLOBALMARK\n*)          /warming/and/warming/\n^')

        self.given(b'''
            /greeting/world/
                greeting = 'hello'
                    world = 'world'
        ''',
        expect_error="Line 4: 'world' is defined but not used (by its parent expression)")


    def test_indentation_error(self):
        self.given(b'''
            /greeting/world/
                greeting = 'hello'
                 world = 'world'
        ''',
        expect_error="Line 4: 'world' is defined but not used (by its parent expression)")

        self.given(b'''
            root
                branch
               misaligned
        ''',
        expect_error=b'Line 4: Indentation error')

        self.given(b'''
                root
                    branch
            hyperroot
        ''',
        expect_error=b'Line 4: Indentation error')


    def test_correct_error_line_numbering(self):
        self.given(b'''
            /greeting/world/
                greeting = 'hello'

                    world = 'world'
        ''',
        expect_error="Line 5: 'world' is defined but not used (by its parent expression)")

        self.given(b'''

            /greeting/world/


                greeting = 'hello'

                 world = 'world'
        ''',
        expect_error="Line 8: 'world' is defined but not used (by its parent expression)")

        self.given(b'''
            /greeting/world/
                greeting = 'hello'


               world = 'world'
        ''',
        expect_error=b'Line 6: Indentation error')

        self.given(b'''
            warming


            *)  warming = 'global'
        ''',
        expect_error="Line 5: The GLOBALMARK *) must be put at the line's beginning")


    def test_mixed_indentation(self):
        self.given(b'''
            \tthis_line_mixes_tab_and_spaces_for_indentation
        ''',
        expect_error=b'Line 2: Cannot mix space and tab for indentation')

        self.given(b'''
            /tabs/vs/spaces/
\t\ttabs = 'this line is tabs-indented'
                spaces = 'this line is spaces-indented'
        ''',
        expect_error=b'Line 3: Inconsistent indentation character')


    def test_undefined_variable(self):
        self.given(b'''
            bigfoot
        ''',
        expect_error="Line 2: 'bigfoot' is not defined")

        self.given(b'''
            /horses/and/unicorns/
                horses = 'Thoroughbreds'
                and = ' and '
        ''',
        expect_error="Line 2: 'unicorns' is not defined")

        self.given(b'''
            /unicorns/and/horses/
                horses = 'Thoroughbreds'
                and = ' and '
        ''',
        expect_error="Line 2: 'unicorns' is not defined")


    def test_illegal_variable_name(self):
        self.given(b'''
            101dalmatians
                101dalmatians = 101 of 'dalmatians'
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            101dalmatians
               ^''')
        
        self.given(b'''
            /101dalmatians/
                101dalmatians = 101 of 'dalmatians'
        ''',
        expect_error=b'''Line 2: Unexpected NUMBER
            /101dalmatians/
             ^''')
        
        self.given(b'''
            _
        ''',
        expect_error=b'''Line 2: Unexpected NEWLINE
            _
             ^''')

        self.given(b'''
            /_/
        ''',
        expect_error=b'''Line 2: Unexpected UNDERSCORE
            /_/
             ^''')

        self.given(b'''
            underscore
                _ = '_'
        ''',
        expect_error=b'''Line 3: Unexpected UNDERSCORE
                _ = '_'
                ^''')

        self.given(b'''
            <<|
              |_
        ''',
        expect_error=b'''Line 3: Unexpected NEWLINE
              |_
                ^''')

        self.given(b'''
            @|
             |/_/
        ''',
        expect_error=b'''Line 3: Unexpected UNDERSCORE
             |/_/
               ^''')

        self.given(b'''
            <@>
               _
        ''',
        expect_error=b'''Line 3: Unexpected UNDERSCORE
               _
               ^''')

        self.given(b'''
            <@>
               |_|
        ''',
        expect_error=b'''Line 3: Unexpected UNDERSCORE
               |_|
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
        expect_error=b'')

        self.given(u'''
            chicken
                chicken = /egg/hatches/
                    egg = /chicken/lays/
                        chicken = /velociraptor/evolves/
        ''',
        expect_error="Line 5: Names must be unique within a scope, 'chicken' is already declared (previous declaration at line 3)")

        self.given(b'''
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
        self.given(b'''
            /alice/bob/
                alice = 'alice'
                bob = 'bob'
                trudy = 'trudy'
        ''',
        expect_error="Line 5: 'trudy' is defined but not used (by its parent expression)")

        self.given(b'''
            /alice/bob/
                alice = 'alice'
                bob = robert
                    robert = 'bob'
                    doe = 'doe'
        ''',
        expect_error="Line 6: 'doe' is defined but not used (by its parent expression)")

        self.given(b'''
            non-vowel
                vowel: a i u e o
        ''',
        expect_error=b'') # vowel should be counted as used


    def test_invalid_atomizer(self):
        self.given(b'''
            @alpha -- atomizer only applicable to chained lookup
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            @alpha -- atomizer only applicable to chained lookup
             ^''')


    def test_unclosed_literal(self):
        self.given(b'''
            mcd
                mcd = 'McDonald's
        ''',
        expect_error=b'''Line 3: Unexpected VARNAME
                mcd = 'McDonald's
                                ^''')
        
        self.given(b'''
            "she said \\"Hi\\"
        ''',
        expect_error=b'Line 2: Syntax error at or near: "she said \\"Hi\\"')
        
        self.given(b'''
            quotes_mismatch
                quotes_mismatch = "'
        ''',
        expect_error="""Line 3: Syntax error at or near: "'""")


    def test_invalid_string_escape(self):
        self.given(b'''
            '\N{KABAYAN}'
        ''',
        expect_error="Line 2: undefined character name 'KABAYAN'")

        self.given(u'''
            '\N{APOSTROPHE}'
        ''',
        expect_error="Line 2: Syntax error at or near: '")


    def test_invalid_global_mark(self):
        self.given(b'''
            *)
        ''',
        expect_error="Line 2: The GLOBALMARK *) must be put at the line's beginning")

        self.given(b'''
*)
        ''',
        expect_error=b'Line 2: Syntax error: *)')

        self.given(b'''
*)\t
        ''',
        expect_error=b'Line 2: Unexpected GLOBALMARK\n*) \n^')

        self.given(b'''
*)warming
        ''',
        expect_error=b'Line 2: Syntax error: *)')

        self.given(b'''
*)          warming
        ''',
        expect_error=b'Line 2: Unexpected GLOBALMARK\n*)          warming\n^')

        self.given(b'''
            warming
                *)warming = 'global'
        ''',
        expect_error="Line 3: The GLOBALMARK *) must be put at the line's beginning")

        self.given(b'''
            warming
            *)  warming = 'global'
        ''',
        expect_error="Line 3: The GLOBALMARK *) must be put at the line's beginning")

        self.given(b'''
            warming
                warming*) = 'global'
        ''',
        expect_error="Line 3: Syntax error at or near: *) = 'global'")

        self.given(b'''
            warming
                warming = global *)
        ''',
        expect_error="Line 3: Syntax error:                 warming = global *)")

        self.given(b'''
            warming
                warming = *) 'global'
        ''',
        expect_error="Line 3: Syntax error:                 warming = *) 'global'")

        self.given(b'''
            warming
                warming *) = 'global'
        ''',
        expect_error="Line 3: Syntax error:                 warming *) = 'global'")

        self.given(b'''
            warming
*)          *)  warming = 'global'
        ''',
        expect_error=b'Line 3: Syntax error: *)          *)  ')

        self.given(b'''
            warming
*)              warming*) = 'global'
        ''',
        expect_error="Line 3: Syntax error at or near: *) = 'global'")

        self.given(b'''
            warming
*)              warming = global *)
        ''',
        expect_error="Line 3: Syntax error: *)              warming = global *)")

        self.given(b'''
            warming
                warming = 'global'
*)              
        ''',
        expect_error="Line 4: Unexpected NEWLINE\n*)              \n                ^")

        self.given(b'''
            warming
                warming = 'global'
*)
        ''',
        expect_error="Line 4: Syntax error: *)")

        self.given(b'''
            warming
                warming = 'global'
*)              junk
        ''',
        expect_error="Line 4: Unexpected NEWLINE\n*)              junk\n                    ^")

        self.given(b'''
            warming
                warming = 'global'
*)            *)junk
        ''',
        expect_error="Line 4: Syntax error: *)            *)")

        self.given(b'''
            warming
                warming = 'global'
*)              *)
        ''',
        expect_error="Line 4: Syntax error: *)              *)")

        self.given(b'''
            warming
                warming = 'global'
*)            *)
        ''',
        expect_error="Line 4: Syntax error: *)            *)")


    def test_global_aliasing(self):
        self.given(b'''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
                    satu = '1'
*)                  uno = ichi = satu
                oneone = /uno/ichi/
                one = ichi
                    ichi: 1
        ''',
        expect_error="Line 8: Names must be unique within a scope, 'ichi' is already defined (previous definition at line 5)")

        self.given(b'''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
                    satu = '1'
*)                  uno = ichi = satu
                oneone = /uno/ichi/
                one = uno
                    uno: 1
        ''',
        expect_error="Line 8: Names must be unique within a scope, 'uno' is already defined (previous definition at line 5)")

        self.given(b'''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
                    satu = '1'
*)                  uno = ichi = satu
                oneone = /uno/ichi/
                one = satu
        ''',
        expect_error="Line 7: 'satu' is not defined")

        self.given(b'''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
*)                  satu = '1'
                    uno = ichi = satu
                one = satu
                oneone = /uno/ichi/
        ''',
        expect_error="Line 7: 'uno' is not defined")


    def test_invalid_charclass(self):
        self.given(b'''
            empty_charclass
                empty_charclass:
        ''',
        expect_error=b'''Line 3: Unexpected NEWLINE
                empty_charclass:
                                ^''')

        self.given(b'''
            noSpaceAfterColon
                noSpaceAfterColon:n o
        ''',
        expect_error=b'''Line 3: Unexpected CHAR
                noSpaceAfterColon:n o
                                  ^''')

        self.given(b'''
            diphtong
                diphtong: ae au
        ''',
        expect_error="Line 3: Cannot include 'ae': not defined")

        self.given(b'''
            miscolon
                miscolon: /colon/should/be/equal/sign/
        ''',
        expect_error=b'Line 3: /colon compiles to \p{colon} which is rejected by the regex engine with error message: unknown property at position 10')

        self.given(b'''
            miscolon
                miscolon: /alphabetic/colon/should/be/equal/sign/
        ''',
        expect_error=b'Line 3: /colon compiles to \p{colon} which is rejected by the regex engine with error message: unknown property at position 10')

        self.given(b'''
            miscolon
                miscolon: 'colon should be equal sign'
        ''',
        expect_error=b'''Line 3: Unexpected CHAR
                miscolon: 'colon should be equal sign'
                           ^''')

        self.given(b'''
            /A/a/
                A: a: A a
        ''',
        expect_error=b'''Line 3: Unexpected CHAR
                A: a: A a
                    ^''')

        self.given(b'''
            /A/a/
                A: a = A a
        ''',
        expect_error="Line 2: 'a' is not defined")

        self.given(b'''
            /A/a/
                A: a = A
        ''',
        expect_error="Line 2: 'a' is not defined")

        self.given(b'''
            /shouldBeColon/
                shouldBeColon = A a
        ''',
        expect_error=b'''Line 3: Unexpected VARNAME
                shouldBeColon = A a
                                  ^''')

        self.given(b'''
            mixedAssignment
                mixedAssignment : = x
        ''',
        expect_error=b'''Line 3: Unexpected COLON
                mixedAssignment : = x
                                ^''')

        self.given(b'''
            mixedAssignment
                mixedAssignment := x
        ''',
        expect_error=b'''Line 3: Unexpected COLON
                mixedAssignment := x
                                ^''')

        self.given(b'''
            mixedAssignment
                mixedAssignment:= x
        ''',
        expect_error=b'''Line 3: Unexpected CHAR
                mixedAssignment:= x
                                ^''')

        self.given(b'''
            mixedAssignment
                mixedAssignment=: x
        ''',
        expect_error=b'''Line 3: Unexpected COLON
                mixedAssignment=: x
                                ^''')

        self.given(b'''
            mixedAssignment
                mixedAssignment =: x
        ''',
        expect_error=b'''Line 3: Unexpected COLON
                mixedAssignment =: x
                                 ^''')

        self.given(b'''
            x
                x: /IsAwesome
        ''',
        expect_error=b'Line 3: /IsAwesome compiles to \p{IsAwesome} which is rejected by the regex engine with error message: unknown property at position 14')

        self.given(b'''
            x
                x: :KABAYAN_SABA_KOTA
        ''',
        expect_error=b'Line 3: :KABAYAN_SABA_KOTA compiles to \N{KABAYAN SABA KOTA} which is rejected by the regex engine with error message: undefined character name at position 22')

        self.given(br'''
            x
                x: \N{KABAYAN}
        ''',
        expect_error=b'Line 3: \N{KABAYAN} compiles to \N{KABAYAN} which is rejected by the regex engine with error message: undefined character name at position 12')

        self.given(br'''
            x
                x: \o
        ''',
        expect_error=b'Line 3: Bad escape sequence: \o')

        self.given(br'''
            x
                x: \w
        ''',
        expect_error=b'Line 3: Bad escape sequence: \w')

        self.given(br'''
            x
                x: \'
        ''',
        expect_error="Line 3: Bad escape sequence: \\'")

        self.given(br'''
            x
                x: \"
        ''',
        expect_error=b'Line 3: Bad escape sequence: \\"')

        self.given(br'''
            x
                x: \ron
        ''',
        expect_error=br'Line 3: Bad escape sequence: \ron')

        self.given(br'''
            x
                x: \u123
        ''',
        expect_error=b'Line 3: Bad escape sequence: \u123')

        self.given(br'''
            x
                x: \U1234
        ''',
        expect_error=b'Line 3: Bad escape sequence: \U1234')

        self.given(br'''
            x
                x: \u12345
        ''',
        expect_error=b'Line 3: Bad escape sequence: \u12345')


    def test_invalid_char(self):
        self.given(b'''
            x
                x: u1234
        ''',
        expect_error="Line 3: Cannot include 'u1234': not defined")

        self.given(b'''
            x
                x: \uab
        ''',
        expect_error=b'Line 3: Bad escape sequence: \uab')

        self.given(b'''
            x
                x: \u123z
        ''',
        expect_error=b'Line 3: Bad escape sequence: \u123z')

        self.given(b'''
            x
                x: \U1234567z
        ''',
        expect_error=b'Line 3: Bad escape sequence: \U1234567z')

        self.given(b'''
            x
                x: \U123456789
        ''',
        expect_error=b'Line 3: Bad escape sequence: \U123456789')

        self.given(b'''
            x
                x: \U
        ''',
        expect_error=b'Line 3: Bad escape sequence: \U')

        self.given(b'''
            x
                x: :YET_ANOTHER_CHARACTER_THAT_SHOULD_NOT_BE_IN_UNICODE
        ''',
        expect_error=b'Line 3: :YET_ANOTHER_CHARACTER_THAT_SHOULD_NOT_BE_IN_UNICODE compiles to \N{YET ANOTHER CHARACTER THAT SHOULD NOT BE IN UNICODE} which is rejected by the regex engine with error message: undefined character name at position 56')

        # unicode character name should be in uppercase
        self.given(b'''
            x
                x: check-mark
        ''',
        expect_error=b'''Line 3: Unexpected CHAR
                x: check-mark
                        ^''')

        self.given(b'''
            x
                x: @omic
        ''',
        expect_error=b'''Line 3: Unexpected CHAR
                x: @omic
                    ^''')

        self.given(b'''
            x
                x: awe$ome
        ''',
        expect_error=b'''Line 3: Unexpected CHAR
                x: awe$ome
                      ^''')


    def test_invalid_range(self):
        self.given(b'''
            x
                x: ..
        ''',
        expect_error=b'''Line 3: Unexpected DOT
                x: ..
                    ^''')

        self.given(b'''
            x
                x: ...,
        ''',
        expect_error=b'''Line 3: Unexpected DOT
                x: ...,
                    ^''')

        self.given(b'''
            x
                x: ,...
        ''',
        expect_error=b'''Line 3: Unexpected DOT
                x: ,...
                      ^''')

        self.given(b'''
            x
                x: ;..,
        ''',
        expect_error=b'Line 3: ;.., compiles to [;-,] which is rejected by the regex engine with error message: bad character range at position 4')

        self.given(b'''
            x
                x: x....
        ''',
        expect_error=b'''Line 3: Unexpected DOT
                x: x....
                      ^''')

        self.given(b'''
            x
                x: infinity..
        ''',
        expect_error=b'''Line 3: Unexpected NEWLINE
                x: infinity..
                             ^''')

        self.given(b'''
            x
                x: ..bigbang
        ''',
        expect_error=b'''Line 3: Unexpected DOT
                x: ..bigbang
                    ^''')

        self.given(b'''
            x
                x: bigcrunch..bigbang
        ''',
        expect_error=b'Line 3: Invalid character range: bigcrunch..bigbang')

        self.given(b'''
            x
                x: A...Z
        ''',
        expect_error=b'''Line 3: Unexpected DOT
                x: A...Z
                      ^''')

        self.given(b'''
            x
                x: 1..2..3
        ''',
        expect_error=b'''Line 3: Unexpected DOT
                x: 1..2..3
                       ^''')

        self.given(b'''
            x
                x: /IsAlphabetic..Z
        ''',
        expect_error=b'Line 3: Invalid character range: /IsAlphabetic..Z')

        self.given(b'''
            x
                x: +alpha..Z
        ''',
        expect_error=b'Line 3: Invalid character range: +alpha..Z')

        self.given(b'''
            aB
                aB: a..B
        ''',
        expect_error=b'Line 3: a..B compiles to [a-B] which is rejected by the regex engine with error message: bad character range at position 4')

        self.given(br'''
            BA
                BA: \u0042..A
        ''',
        expect_error=b'Line 3: \u0042..A compiles to [\u0042-A] which is rejected by the regex engine with error message: bad character range at position 9')

        self.given(br'''
            BA
                BA: \U00000042..\u0041
        ''',
        expect_error=b'Line 3: \U00000042..\u0041 compiles to [\U00000042-\u0041] which is rejected by the regex engine with error message: bad character range at position 18')

        self.given(br'''
            BA
                BA: \x42..\U00000041
        ''',
        expect_error=br'Line 3: \x42..\U00000041 compiles to [\x42-\U00000041] which is rejected by the regex engine with error message: bad character range at position 16')

        self.given(br'''
            BA
                BA: \102..\x41
        ''',
        expect_error=br'Line 3: \102..\x41 compiles to [\102-\x41] which is rejected by the regex engine with error message: bad character range at position 10')

        self.given(br'''
            BA
                BA: \N{LATIN CAPITAL LETTER B}..\101
        ''',
        expect_error=br'Line 3: \N{LATIN CAPITAL LETTER B}..\101 compiles to [\N{LATIN CAPITAL LETTER B}-\101] which is rejected by the regex engine with error message: bad character range at position 32')

        self.given(b'''
            BA
                BA: :LATIN_CAPITAL_LETTER_B..\N{LATIN CAPITAL LETTER A}
        ''',
        expect_error=b'Line 3: :LATIN_CAPITAL_LETTER_B..\N{LATIN CAPITAL LETTER A} compiles to [\N{LATIN CAPITAL LETTER B}-\N{LATIN CAPITAL LETTER A}] which is rejected by the regex engine with error message: bad character range at position 54')

        self.given(b'''
            BA
                BA: \N{LATIN CAPITAL LETTER B}..:LATIN_CAPITAL_LETTER_A
        ''',
        expect_error=b'Line 3: \N{LATIN CAPITAL LETTER B}..:LATIN_CAPITAL_LETTER_A compiles to [\N{LATIN CAPITAL LETTER B}-\N{LATIN CAPITAL LETTER A}] which is rejected by the regex engine with error message: bad character range at position 54')

        self.given(br'''
            aZ
                aZ: \N{LATIN SMALL LETTER A}..:LATIN_CAPITAL_LETTER_Z
        ''',
        expect_error=b'Line 3: \N{LATIN SMALL LETTER A}..:LATIN_CAPITAL_LETTER_Z compiles to [\N{LATIN SMALL LETTER A}-\N{LATIN CAPITAL LETTER Z}] which is rejected by the regex engine with error message: bad character range at position 52')


    def test_invalid_charclass_include(self):
        self.given(b'''
            x
                x: +1
        ''',
        expect_error="Line 3: Cannot include '1': not defined")

        self.given(b'''
            x
                x: +7even
        ''',
        expect_error="Line 3: Cannot include '7even': not defined")

        self.given(b'''
            x
                x: +7even
                    7even: 7
        ''',
        expect_error=b'''Line 4: Unexpected NUMBER
                    7even: 7
                    ^''')

        self.given(b'''
            x
                x: +bang!
        ''',
        expect_error=b'''Line 3: Unexpected CHAR
                x: +bang!
                        ^''')

        self.given(b'''
            x
                x: ++
        ''',
        expect_error=b'''Line 3: Unexpected CHAR
                x: ++
                    ^''')

        self.given(b'''
            x
                x: +!awe+some
        ''',
        expect_error=b'''Line 3: Unexpected CHAR
                x: +!awe+some
                    ^''')

        self.given(b'''
            x
                x: y
                    y: m i s n g +
        ''',
        expect_error="Line 4: 'y' is defined but not used (by its parent expression)")

        self.given(b'''
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
        expect_error=b'''Line 3: Unexpected CHAR
                vowhex: +!vowel +hex
                         ^''')

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
            1 of: not: not x
        ''',
        expect_error="Line 2: Bad set operation 'not: not'")

        self.given(u'''
            1 of: not: and x
        ''',
        expect_error="Line 2: Bad set operation 'not: and'")


    def test_invalid_quantifier(self):
        self.given(b'''
            3 of
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            3 of
              ^''')

        self.given(b'''
            3 of          
                of = 'trailing spaces above after the "of"'
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            3 of          
              ^''')

        self.given(b'''
            3 of -- 3 of what?
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            3 of -- 3 of what?
              ^''')

        self.given(b'''
            3 of-- 3 of what?
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            3 of-- 3 of what?
              ^''')

        self.given(b'''
            3 of of--
        ''',
        expect_error=b'''Line 2: Unexpected MINUS
            3 of of--
                   ^''')

        self.given(b'''
            3 alpha
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            3 alpha
              ^''')

        self.given(b'''
            3 ofalpha
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            3 ofalpha
              ^''')

        self.given(b'''
            3of alpha
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            3of alpha
             ^''')

        self.given(b'''
            3 o falpha
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            3 o falpha
              ^''')

        self.given(b'''
            3 office alpha
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            3 office alpha
              ^''')

        self.given(b'''
            3. of alpha
        ''',
        expect_error=b'''Line 2: Unexpected WHITESPACE
            3. of alpha
              ^''')

        self.given(b'''
            3... of alpha
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            3... of alpha
               ^''')

        self.given(b'''
            3+ of alpha
        ''',
        expect_error=b'''Line 2: Unexpected PLUS
            3+ of alpha
             ^''')

        self.given(b'''
            3+3 of alpha
        ''',
        expect_error=b'''Line 2: Unexpected PLUS
            3+3 of alpha
             ^''')

        self.given(b'''
            @3..2 of alpha
        ''',
        expect_error=b'Line 2: Repeat max must be > min')

        self.given(b'''
            @2..2 of alpha
        ''',
        expect_error=b'Line 2: Repeat max must be > min')

        self.given(b'''
            @1..1 of alpha
        ''',
        expect_error=b'Line 2: Repeat max must be > min')

        self.given(b'''
            @0..0 of alpha
        ''',
        expect_error=b'Line 2: Repeat max must be > min')

        self.given(b'''
            1 ..3 of alpha
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            1 ..3 of alpha
              ^''')

        self.given(b'''
            1.. 3 of alpha
        ''',
        expect_error=b'''Line 2: Unexpected NUMBER
            1.. 3 of alpha
                ^''')

        self.given(b'''
            1 .. of alpha
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            1 .. of alpha
              ^''')

        self.given(b'''
            1 <<- of alpha
        ''',
        expect_error=b'''Line 2: Unexpected MINUS
            1 <<- of alpha
                ^''')

        self.given(b'''
            1 <<+ of alpha
        ''',
        expect_error=b'''Line 2: Unexpected WHITESPACE
            1 <<+ of alpha
                 ^''')

        self.given(b'''
            1 <<+..0 of alpha
        ''',
        expect_error=b'Line 2: Repeat max must be > min')

        self.given(b'''
            0 <<+..0 of alpha
        ''',
        expect_error=b'Line 2: Repeat max must be > min')

        self.given(b'''
            1 <<+..1 of alpha
        ''',
        expect_error=b'Line 2: Repeat max must be > min')

        self.given(b'''
            2 <<+..2 of alpha
        ''',
        expect_error=b'Line 2: Repeat max must be > min')

        self.given(b'''
            2..1 <<- of alpha
        ''',
        expect_error=b'Line 2: Repeat max must be > min')

        self.given(b'''
            ? <<- of alpha
        ''',
        expect_error=b'''Line 2: Unexpected LT
            ? <<- of alpha
              ^''')

        self.given(b'''
            1.. of alpha
        ''',
        expect_error=b'''Line 2: Unexpected OF
            1.. of alpha
                ^''')

        self.given(b'''
            1..2 of alpha
        ''',
        expect_error=b'''Line 2: Unexpected OF
            1..2 of alpha
                 ^''')

        self.given(b'''
            .. of alpha
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            .. of alpha
             ^''')

        self.given(b'''
            ..1 of alpha
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            ..1 of alpha
             ^''')

        self.given(b'''
            ..2 <<- of alpha
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            ..2 <<- of alpha
             ^''')

        self.given(b'''
            @.. of alpha
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            @.. of alpha
              ^''')

        self.given(b'''
            @..1 of alpha
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            @..1 of alpha
              ^''')

        self.given(b'''
            @..2 <<- of alpha
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            @..2 <<- of alpha
              ^''')

        self.given(b'''
            @? of alpha
        ''',
        expect_error=b'''Line 2: Unexpected QUESTMARK
            @? of alpha
             ^''')


    def test_commenting_error(self):
        self.given(b'''
            - this comment is missing another - prefix
        ''',
        expect_error=b'''Line 2: Unexpected MINUS
            - this comment is missing another - prefix
            ^''')

        self.given(b'''
            1 of vowel - this comment is missing another - prefix
                vowel: a i u e o 
        ''',
        expect_error=b'''Line 2: Unexpected WHITESPACE
            1 of vowel - this comment is missing another - prefix
                      ^''')

        self.given(b'''
            1 of vowel- this comment is missing another - prefix
                vowel: a i u e o 
        ''',
        expect_error=b'''Line 2: Unexpected MINUS
            1 of vowel- this comment is missing another - prefix
                      ^''')

        self.given(b'''
            1 of vowel
                vowel: a i u e o - this comment is missing another - prefix
        ''',
        expect_error="Line 3: Cannot include 'this': not defined")

        self.given(b'''
            1 of vowel
                vowel: a i u e o- this comment is missing another - prefix
        ''',
        expect_error=b'''Line 3: Unexpected CHAR
                vowel: a i u e o- this comment is missing another - prefix
                                ^''')

        self.given(b'''
            /comment/-- whitespace required before the "--"
                comment = 'first'
        ''',
        expect_error=b'''Line 2: Unexpected MINUS
            /comment/-- whitespace required before the "--"
                     ^''')

        self.given(b'''
            /comment/--
                comment = 'first'
        ''',
        expect_error=b'''Line 2: Unexpected MINUS
            /comment/--
                     ^''')


    def test_invalid_reference(self):
        self.given(b'''
            =missing
        ''',
        expect_error="Line 2: Bad Backreference: 'missing' is not defined/not a capturing group")

        self.given(b'''
            =missing?
        ''',
        expect_error="Line 2: Bad Backreference: 'missing' is not defined/not a capturing group")

        self.given(b'''
            =alpha
        ''',
        expect_error="Line 2: Bad Backreference: 'alpha' is not defined/not a capturing group")

        self.given(b'''
            /bang/=bang/
                bang: b a n g !
        ''',
        expect_error="Line 2: Bad Backreference: 'bang' is not defined/not a capturing group")


    def test_invalid_boundaries(self):
        self.given(b'''
            /cat./
                cat = 'cat'
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            /cat./
                ^''')

        self.given(b'''
            /.cat/
                cat = 'cat'
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            /.cat/
             ^''')

        self.given(b'''
            /cat_/
                cat = 'cat'
        ''',
        expect_error="Line 2: 'cat_' is not defined")

        self.given(b'''
            /cat/
                cat = 'cat' .
        ''',
        expect_error=b'''Line 3: Unexpected WHITESPACE
                cat = 'cat' .
                           ^''')

        self.given(b'''
            /cat/
                cat = 'cat'__
        ''',
        expect_error=b'''Line 3: Unexpected DOUBLEUNDERSCORE
                cat = 'cat'__
                           ^''')

        self.given(b'''
            /_/
                _ = 'underscore'
        ''',
        expect_error=b'''Line 2: Unexpected UNDERSCORE
            /_/
             ^''')

        self.given(b'''
            /_./
        ''',
        expect_error=b'''Line 2: Unexpected UNDERSCORE
            /_./
             ^''')


    def test_invalid_flags(self):
        self.given(b'''
            (pirate) 'carribean'
        ''',
        expect_error="Line 2: Unknown flag 'pirate'. Supported flags are: ascii bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse unicode verbose version0 version1 word")
 
        self.given(b'''
            (-pirate) 'carribean'
        ''',
        expect_error="Line 2: Unknown flag '-pirate'. Supported flags are: ascii bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse unicode verbose version0 version1 word")
 
        self.given(b'''
            (--ignorecase) 'carribean'
        ''',
        expect_error="Line 2: Unknown flag '--ignorecase'. Supported flags are: ascii bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse unicode verbose version0 version1 word")
 
        self.given(b'''
            (unicode-ignorecase)
            alpha
        ''',
        expect_error="Line 2: Unknown flag 'unicode-ignorecase'. Supported flags are: ascii bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse unicode verbose version0 version1 word")

        self.given(b'''
            (unicode) alpha
        ''',
        expect_error="Line 2: 'unicode' is a global flag and must be set using global flag syntax, not scoped.")

        self.given(b'''
            (ignorecase)alpha
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            (ignorecase)alpha
                        ^''')

        self.given(b'''
            (ignorecase)
             alpha
        ''',
        expect_error=b'Line 3: Unexpected INDENT')

        self.given(b'''
            (ignorecase -ignorecase) alpha
        ''',
        expect_error=b'Line 2: (ignorecase -ignorecase) compiles to (?i-i) which is rejected by the regex engine with error message: bad inline flags: flag turned on and off at position 10')
 
        self.given(b'''
            (-ignorecase ignorecase) alpha
        ''',
        expect_error=b'Line 2: (-ignorecase ignorecase) compiles to (?i-i) which is rejected by the regex engine with error message: bad inline flags: flag turned on and off at position 10')
 
        self.given(b'''
            (-ignorecase ignorecase unicode)
            alpha
        ''',
        expect_error=b'Line 2: (-ignorecase ignorecase unicode) compiles to (?iu-i) which is rejected by the regex engine with error message: bad inline flags: flag turned on and off at position 11')
 
        self.given(b'''
            (-ignorecase unicode ignorecase)
            alpha
        ''',
        expect_error=b'Line 2: (-ignorecase unicode ignorecase) compiles to (?ui-i) which is rejected by the regex engine with error message: bad inline flags: flag turned on and off at position 11')
 
        self.given(b'''
            (-unicode)
            alpha
        ''',
        expect_error=b'Line 2: (-unicode) compiles to (?-u) which is rejected by the regex engine with error message: bad inline flags: cannot turn off global flag at position 9')
 
        self.given(b'''
            (ignorecase)
            (-ignorecase)
        ''',
        expect_error=b'''Line 3: Unexpected NEWLINE
            (-ignorecase)
                         ^''')
 
        self.given(b'''
            (unicode ignorecase)
            (-ignorecase)
        ''',
        expect_error=b'''Line 3: Unexpected NEWLINE
            (-ignorecase)
                         ^''')

        self.given(b'''
            (ascii unicode)
        ''',
        expect_error=b'Line 2: (ascii unicode) compiles to (?au) which is rejected by the regex engine with error message: ASCII, LOCALE and UNICODE flags are mutually incompatible')

        self.given(b'''
            (unicode ascii)
        ''',
        expect_error=b'Line 2: (unicode ascii) compiles to (?ua) which is rejected by the regex engine with error message: ASCII, LOCALE and UNICODE flags are mutually incompatible')

        self.given(b'''
            (ascii locale)
        ''',
        expect_error=b'Line 2: (ascii locale) compiles to (?aL) which is rejected by the regex engine with error message: ASCII, LOCALE and UNICODE flags are mutually incompatible')

        self.given(b'''
            (unicode locale)
        ''',
        expect_error=b'Line 2: (unicode locale) compiles to (?uL) which is rejected by the regex engine with error message: ASCII, LOCALE and UNICODE flags are mutually incompatible')

        self.given(b'''
            (version0 version1)
        ''',
        expect_error=b'Line 2: (version0 version1) compiles to (?V0V1) which is rejected by the regex engine with error message: 8448')

        self.given(b'''
            (version1 version0)
        ''',
        expect_error=b'Line 2: (version1 version0) compiles to (?V1V0) which is rejected by the regex engine with error message: 8448')


    def test_invalid_orblock(self):
        self.given(b'''
            empty_orblock_not_allowed
                empty_orblock_not_allowed = @|
        ''',
        expect_error=b'Line 4: Unexpected END_OF_ORBLOCK')

        self.given(b'''
            /empty_orblock/not_allowed/
                empty_orblock = @|

                not_allowed = 'NOTALLOWED'
        ''',
        expect_error=b'Line 5: Unexpected END_OF_ORBLOCK')

        self.given(b'''
            <<|
        ''',
        expect_error=b'Line 3: Unexpected END_OF_ORBLOCK')

        self.given(b'''
            /x/y/
                x = @|
                     |'AM'
                     |'PM'
                y = 'forgot empty line to terminate the orblock'
        ''',
        expect_error=b'''Line 6: Unexpected VARNAME (forgot to close ORBLOCK?)
                y = 'forgot empty line to terminate the orblock'
                ^''')

        self.given(b'''
            @|
             |am
             |pm
                am = 'AM'
                pm = 'PM
        ''',
        expect_error=b'''Line 5: Unexpected VARNAME (forgot to close ORBLOCK?)
                am = 'AM'
                ^''')

        self.given(b'''
            /trailing/bar/
                trailing = <<|
                             |'choice 1'
                             |'choice 2'
                             |
                bar: |
        ''',
        expect_error=b'''Line 7: Unexpected VARNAME (forgot to close ORBLOCK?)
                bar: |
                ^''')

        self.given(b'''
            <<|
              |'alignment check'
             |'this one is bad'
        ''',
        expect_error=b'Line 4: Misaligned OR')

        self.given(b'''
            @|
              |'also misalignment'
        ''',
        expect_error=b'Line 3: Misaligned OR')

        self.given(b'''
            orblock_type
                orblock_type = | -- atomic? backtrack? must specify
                               |'to be'
                               |'not to be'
        ''',
        expect_error=b'''Line 3: Unexpected BAR
                orblock_type = | -- atomic? backtrack? must specify
                               ^''')

        self.given(b'''
            syntax_err
                syntax_err = <<|'to be'       -- choices should start in second line
                               |'not to be'
        ''',
        expect_error=b'''Line 3: Unexpected STRING
                syntax_err = <<|'to be'       -- choices should start in second line
                                ^''')

        self.given(b'''
            <<|
              |missing/a/slash/
        ''',
        expect_error=b'''Line 3: Unexpected SLASH
              |missing/a/slash/
                      ^''')

        self.given(b'''
            nested_orblock
                nested_orblock = @|
                                  |'nested orblock not allowed'
                                  |@|
                                    |'make it a var'
                                  |'then lookup'
        ''',
        expect_error=b'Line 5: ORBLOCK cannot contain ORBLOCK')

        self.given(b'''
            nested_orblock
                nested_orblock = <<|
                                   |@|
        ''',
        expect_error=b'Line 4: ORBLOCK cannot contain ORBLOCK')

        self.given(b'''
            nested_orblock
                nested_orblock = @|
                                  |<<|
        ''',
        expect_error=b'Line 4: ORBLOCK cannot contain ORBLOCK')

        self.given(b'''
            nested_orblock
                nested_orblock = <<|
                                   |<<|
        ''',
        expect_error=b'Line 4: ORBLOCK cannot contain ORBLOCK')

        self.given(b'''
            orblock_containing_lookblock
                orblock_containing_lookblock = <<|
                                                 |<@>
                                                   |!/allowed/>
        ''',
        expect_error=b'Line 4: ORBLOCK cannot contain LOOKAROUND')


    def test_invalid_conditionals(self):
        self.given(b'''
            <<|
              |[capt]?'whitespace needed around the ?'
        ''',
        expect_error=b'''Line 3: Unexpected QUESTMARK
              |[capt]?'whitespace needed around the ?'
                     ^''')

        self.given(b'''
            <<|
              |[capt]? 'whitespace needed around the ?'
        ''',
        expect_error=b'''Line 3: Unexpected QUESTMARK
              |[capt]? 'whitespace needed around the ?'
                     ^''')

        self.given(b'''
            <<|
              |[capt] ?'whitespace needed around the ?'
        ''',
        expect_error=b'''Line 3: Unexpected STRING
              |[capt] ?'whitespace needed around the ?'
                       ^''')

        self.given(b'''
            <<|
              |[capt] ? 'the capture must be defined'
              |
        ''',
        expect_error="Line 3: Bad CaptureCondition: 'capt' is not defined/not a capturing group")

        self.given(b'''
            <<|
              |[alpha] ? 'the capture must be a capture'
              |
        ''',
        expect_error="Line 3: Bad CaptureCondition: 'alpha' is not defined/not a capturing group")

        self.given(b'''
            <<|
              |[capt] ? 'last branch must not be conditional'
        ''',
        expect_error=b'Line 3: The last branch of OR-block must not be conditional')

        self.given(b'''
            /currency/amount/
                currency = <<|
                             |dollar
                             |euro
                
                    [dollar]: $
                    [euro]: :EURO_SIGN
                    
                amount = <<|
                           |[dollar] ? /digits/dot/digits/
                           |[euro] ? /digits/comma/digits/
              
                    digits = @1.. of digit
                    dot: .
                    comma: ,
        ''',
        expect_error=b'Line 12: The last branch of OR-block must not be conditional')


    def test_invalid_lookaround(self):
        self.given(b'''
            empty_lookaround_not_allowed
                empty_lookaround_not_allowed = <@>
        ''',
        expect_error=b'Line 4: Unexpected END_OF_LOOKAROUND')

        self.given(b'''
            /empty_lookaround/not_allowed/
                empty_lookaround = <@>

                not_allowed = 'NOTALLOWED'
        ''',
        expect_error=b'Line 5: Unexpected END_OF_LOOKAROUND')

        self.given(b'''
            <@>
            |> -- empty lookahead
        ''',
        expect_error=b'''Line 3: Unexpected GT
            |> -- empty lookahead
             ^''')

        self.given(b'''
            <@>
            <| -- empty lookbehind
        ''',
        expect_error=b'''Line 3: Unexpected BAR
            <| -- empty lookbehind
             ^''')

        self.given(b'''
            <@>
            || -- empty base
        ''',
        expect_error=b'''Line 3: Unexpected BAR
            || -- empty base
             ^''')

        self.given(b'''
            <@>
        ''',
        expect_error=b'Line 3: Unexpected END_OF_LOOKAROUND')

        self.given(b'''
            /x/y/
                x = <@>
                    <behind|
                           |ahead>
                y = 'forgot empty line to terminate the lookaround'
        ''',
        expect_error=b'''Line 6: Unexpected VARNAME (forgot to close LOOKAROUND?)
                y = 'forgot empty line to terminate the lookaround'
                ^''')

        self.given(b'''
            <@>
            <past|
                 |future>
                past = 'behind'
                future = 'ahead'
        ''',
        expect_error=b'''Line 5: Unexpected VARNAME (forgot to close LOOKAROUND?)
                past = 'behind'
                ^''')

        self.given(b'''
            alignment_check
                alignment_check = <@>
                                  <mis|
                                       |align>
        ''',
        expect_error=b'Line 5: Misaligned |')

        self.given(b'''
            <@>
            <mis|
                 |align>
        ''',
        expect_error=b'Line 4: Misaligned |')

        self.given(b'''
            <@>
            <mis|
               |align>
        ''',
        expect_error=b'Line 4: Misaligned |')

        self.given(b'''
            <@>
            <this_is_good|
                         |alignment|
             <this_is_bad|
        ''',
        expect_error=b'Line 5: Misaligned |')

        self.given(b'''
            <@>
             |this_is_good>
             |alignment|
             |this_is_bad>
        ''',
        expect_error=b'Line 5: Misaligned |')

        self.given(b'''
            <@>
             |wrong|
             |chaining|
        ''',
        expect_error=b'Line 4: Misaligned |')

        self.given(b'''
            check_indent
                check_indent = <@>
                                |/this/line/OK/|
          </this/line/needs/deeper/indentation/|
        ''',
        expect_error=b'Line 5: needs deeper indentation')

        self.given(b'''
            check_indent
                check_indent = <@>
                                       |this_line_OK|
               </this/line/needs/deeper/indentation/|
        ''',
        expect_error=b'Line 5: needs deeper indentation')

        self.given(b'''
            check_indent
                check_indent = <@>
               <this_line_needs_deeper_indentation|
                                                  |/this/one/OK/|
        ''',
        expect_error=b'Line 4: needs deeper indentation')

        self.given(b'''
                <@>
               |/more/indent/please/|
        ''',
        expect_error=b'Line 3: needs deeper indentation')

        self.given(b'''
                <@>
               |more_indent_please>
        ''',
        expect_error=b'Line 3: needs deeper indentation')

        self.given(b'''
                <@>
               <!enough_indent|
        ''',
        expect_error=b'Line 3: needs deeper indentation')

        self.given(b'''
            syntax_err
                syntax_err = <@>|ahead>
        ''',
        expect_error=b'''Line 3: Unexpected BAR
                syntax_err = <@>|ahead>
                                ^''')

        self.given(b'''
            syntax_err
                syntax_err = <@>
                             <missing/a/slash/|
        ''',
        expect_error=b'''Line 4: Unexpected SLASH
                             <missing/a/slash/|
                                     ^''')

        self.given(b'''
            syntax_err
                syntax_err = <@>
                             </missing/a/slash|
        ''',
        expect_error=b'''Line 4: Unexpected BAR
                             </missing/a/slash|
                                              ^''')

        self.given(b'''
            syntax_err
                syntax_err = <@>
                             <!missing/a/slash/|
        ''',
        expect_error=b'''Line 4: Unexpected SLASH
                             <!missing/a/slash/|
                                      ^''')

        self.given(b'''
            syntax_err
                syntax_err = <@>
                             |!missing/a/slash>
        ''',
        expect_error=b'''Line 4: Unexpected SLASH
                             |!missing/a/slash>
                                      ^''')

        self.given(b'''
            syntax_err
                syntax_err = <@>
                             |missing/slashes|
        ''',
        expect_error=b'''Line 4: Unexpected SLASH
                             |missing/slashes|
                                     ^''')

        self.given(b'''
            syntax_err
                syntax_err = <@>
                             </ahead/behind/>
        ''',
        expect_error=b'''Line 4: Unexpected GT
                             </ahead/behind/>
                                            ^''')

        self.given(b'''
            syntax_err
                syntax_err = <@>
                             <behind<
        ''',
        expect_error=b'''Line 4: Unexpected LT
                             <behind<
                                    ^''')

        self.given(b'''
            syntax_err
                syntax_err = <@>
                             </missing/bar/
        ''',
        expect_error=b'''Line 4: Unexpected NEWLINE
                             </missing/bar/
                                           ^''')

        self.given(b'''
            syntax_err
                syntax_err = <@>
                             /missing/bar/>
        ''',
        expect_error=b'''Line 4: Unexpected SLASH
                             /missing/bar/>
                             ^''')

        self.given(b'''
            syntax_err
                syntax_err = <@>
                             !/missing/bar/>
        ''',
        expect_error=b'''Line 4: Unexpected EXCLAMARK
                             !/missing/bar/>
                             ^''')

        self.given(b'''
            syntax_err
                syntax_err = <@>
                             missing_bar>
        ''',
        expect_error=b'''Line 4: Unexpected VARNAME (forgot to close LOOKAROUND?)
                             missing_bar>
                             ^''')

        self.given(b'''
            syntax_err
                syntax_err = <@>
                             |missing_bar_or_gt
        ''',
        expect_error=b'''Line 4: Unexpected NEWLINE
                             |missing_bar_or_gt
                                               ^''')

        self.given(b'''
            nested_orblock
                nested_orblock = <@>
                                  |nested_lookaround>
                                  |<@>
                                    |!allowed>
        ''',
        expect_error=b'Line 5: LOOKAROUND cannot contain LOOKAROUND')

        self.given(b'''
            lookblock_containing_orblock
                lookblock_containing_orblock = <@>
                                                @|
                                                 |"can't"
        ''',
        expect_error=b'Line 4: LOOKAROUND cannot contain ORBLOCK')


    def test_invalid_non_op(self):
        self.given(b'''
            non-BOS
        ''',
        expect_error="Line 2: 'non-BOS': 'BOS' is not a character-class")

        self.given(b'''
            non-any
        ''',
        expect_error="Line 2: 'non-any': 'any' is not a character-class")

        self.given(b'''
            non-vowel
                vowel = (ignorecase) 1 of: a i u e o
        ''',
        expect_error="Line 2: 'non-vowel': 'vowel' is not a character-class")

        self.given(b'''
            non-pin
                pin = @4..6 of digit
        ''',
        expect_error="Line 2: 'non-pin': 'pin' is not a character-class")

        self.given(b'''
            non-digits
                digits = @1.. of digit
        ''',
        expect_error="Line 2: 'non-digits': 'digits' is not a character-class")

        self.given(b'''
            non-digits
                digits = 1.. <<- of digit
        ''',
        expect_error="Line 2: 'non-digits': 'digits' is not a character-class")

        self.given(b'''
            non-digits
                digits = 1 <<+.. of digit
        ''',
        expect_error="Line 2: 'non-digits': 'digits' is not a character-class")

        self.given(b'''
            non-non-alpha
        ''',
        expect_error=b'''Line 2: Unexpected NON
            non-non-alpha
                ^''')


    def test_invalid_anchor_sugar(self):
        self.given(b'''
            ./
        ''',
        expect_error=b'''Line 2: Unexpected NEWLINE
            ./
              ^''')

        self.given(b'''
            /.
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            /.
             ^''')

        self.given(b'''
            .//.
        ''',
        expect_error=b'''Line 2: Unexpected SLASH
            .//.
              ^''')

        self.given(b'''
            ./alpha./
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            ./alpha./
                   ^''')

        self.given(b'''
            /.alpha/.
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            /.alpha/.
             ^''')

        self.given(b'''
            //
        ''',
        expect_error=b'''Line 2: Unexpected NEWLINE
            //
              ^''')

        self.given(b'''
            ////
        ''',
        expect_error=b'''Line 2: Unexpected SLASH
            ////
              ^''')

        self.given(b'''
            /alpha//digit/
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            /alpha//digit/
                    ^''')

        self.given(b'''
            /alpha/.digit/
        ''',
        expect_error=b'''Line 2: Unexpected VARNAME
            /alpha/.digit/
                    ^''')
                    
                    
    def test_invalid_numrange_shortcut(self):
        self.given(b'''
            123..456 -- the numbers should be as string
        ''',
        expect_error=b'''Line 2: Unexpected NEWLINE
            123..456 -- the numbers should be as string
                    ^''')

        self.given(b'''
            '456'..'123'
        ''',
        expect_error="Line 2: Bad number-range format: '456'..'123' (start > end)")

        self.given(b'''
            '000'..'fff' -- only supports decimal for now
        ''',
        expect_error="Line 2: Bad number-range format: 'fff'")

        self.given(b'''
            'I'..'MCMXCVIII' -- only supports decimal for now
        ''',
        expect_error="Line 2: Bad number-range format: 'I'")

        self.given(b'''
            'one'..'ten'
        ''',
        expect_error="Line 2: Bad number-range format: 'one'")

        self.given(b'''
            '2.718'..'3.14'
        ''',
        expect_error=r"Line 2: Bad number-range format: '2\.718'")

        self.given(b'''
            '2.718'..'3.14'..'0.001'
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            '2.718'..'3.14'..'0.001'
                           ^''')

        self.given(b'''
            '3,14'..'2,718'
        ''',
        expect_error=r"Line 2: Bad number-range format: '3,14'")

        self.given(b'''
            '-1'..'-10' -- negative numbers not supported for now
        ''',
        expect_error="Line 2: Bad number-range format: '-1'")

        self.given(b'''
            '1'..'99'..'2'
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            '1'..'99'..'2'
                     ^''')

        self.given(b'''
            '1'...'10'
        ''',
        expect_error=b'''Line 2: Unexpected DOT
            '1'...'10'
                 ^''')

        self.given(b'''
            ''..''
        ''',
        expect_error="Line 2: Bad number-range format: ''")

        self.given(b'''
            '0'..''
        ''',
        expect_error="Line 2: Bad number-range format: ''")

        self.given(b'''
            ''..'1'
        ''',
        expect_error="Line 2: Bad number-range format: ''")

        self.given(b'''
            '1'..'1oo'
        ''',
        expect_error="Line 2: Bad number-range format: '1oo'")

        self.given(b'''
            'o01'..'999'
        ''',
        expect_error="Line 2: Bad number-range format: 'o01' (ambiguous leading-zero spec)")

        self.given(b'''
            '0o1'..'999'
        ''',
        expect_error="Line 2: Bad number-range format: '0o1'")

        self.given(b'''
            'o'..'999' -- should be '0'..'999'
        ''',
        expect_error="Line 2: Bad number-range format: 'o'")

        self.given(b'''
            'ooo'..'999' -- should be 'oo0'..'999'
        ''',
        expect_error="Line 2: Bad number-range format: 'ooo'")

        self.given(b'''
            '01'..'999' -- should be '001'..'999'
        ''',
        expect_error="Line 2: Bad number-range format: '01'..'999' (lengths must be the same if using leading-zero/o format)")

        self.given(b'''
            'o1'..'999' -- should be 'oo1'..'999'
        ''',
        expect_error="Line 2: Bad number-range format: 'o1'..'999' (lengths must be the same if using leading-zero/o format)")

        self.given(b'''
            'oo1'..'099'
        ''',
        expect_error="Line 2: Bad number-range format: 'oo1'..'099' (one cannot be o-led while the other is zero-led)")

        self.given(b'''
            '09'..'o1'
        ''',
        expect_error="Line 2: Bad number-range format: '09'..'o1' (one cannot be o-led while the other is zero-led)")


    def test_invalid_infinite_numrange(self):
        self.given(b'''
            '00'..
        ''',
        expect_error="Line 2: Infinite range cannot have (non-optional) leading zero: '00'..")
        
        self.given(b'''
            '01'..
        ''',
        expect_error="Line 2: Infinite range cannot have (non-optional) leading zero: '01'..")
        
        self.given(b'''
            '0123'..
        ''',
        expect_error="Line 2: Infinite range cannot have (non-optional) leading zero: '0123'..")
        
        self.given(b'''
            'oo0'..
        ''',
        expect_error="Line 2: Infinite range: excessive leading-o: 'oo0'..")
        
        self.given(b'''
            'oo1'..
        ''',
        expect_error="Line 2: Infinite range: excessive leading-o: 'oo1'..")
        
        self.given(b'''
            'oo123'..
        ''',
        expect_error="Line 2: Infinite range: excessive leading-o: 'oo123'..")


    def test_invalid_wordchar_redef(self):
        self.given(b'''
            .'cat'.
                wordchar: A..z
        ''',
        expect_error=b'Line 3: Redefining wordchar: must be global')
        
        self.given(b'''
            .'cat'.
*)              wordchar = 'A-z'
        ''',
        expect_error=b'Line 3: Redefining wordchar: wordchar must be a charclass')
        
        self.given(b'''
            /cat/
                cat = 'cat'
*)              wordchar: A..z
        ''',
        expect_error=b'Line 4: Redefining wordchar: must be the first/before any other definition')
        
        self.given(b'''
            /cat/
                cat = 'cat'
*)                  wordchar: A..z
        ''',
        expect_error=b'Line 4: Redefining wordchar: must be the first/before any other definition')
        
        
class TestOutput(unittest.TestCase):
    def given(self, oprex_source, expect_regex):
        default_flags = '(?V1w)'
        regex_source = oprex(oprex_source)
        regex_source = regex_source.replace(default_flags, b'', 1)
        if regex_source != expect_regex:
            msg = 'For input: %s\n---------------------------- Got Output: -----------------------------\n%s\n\n------------------------- Expected Output: ---------------------------\n%s'
            raise AssertionError(msg % (
                oprex_source or '(empty string)', 
                regex_source or '(empty string)', 
                expect_regex or '(empty string)',
            ))


    def test_empties(self):
        self.given('',
        expect_regex=b'')

        self.given(b'''
        ''',
        expect_regex=b'')

        self.given(b'''

        ''',
        expect_regex=b'')
        self.given(b'''


        ''',
        expect_regex=b'')


    def test_indentation(self):
        # indentation using space
        self.given(b'''
            /weather/warming/
                weather = 'local'
*)              warming = 'global'
        ''',
        expect_regex=b'localglobal')

        # indentation using tab
        self.given(b'''
/weather/warming/
\tweather = 'local'
*)\twarming = 'global'
        ''',
        expect_regex=b'localglobal')


    def test_escaping_output(self):
        self.given(b'''
            stars
                stars = '***'
        ''',
        expect_regex=br'\*\*\*')

        self.given(b'''
            add
                add: +plus
                    plus: +
        ''',
        expect_regex=br'\+')


    def test_assignment_whitespace(self):
        self.given(b'''
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
        expect_regex=b'abcdefghijzzz')

        self.given(b'''
            add
                add: +plus
                    plus: +
        ''',
        expect_regex=br'\+')


    def test_character_class(self):
        self.given(b'''
            papersize
                papersize = /series/size/
                    series: A B C
                    size: 0 1 2 3 4 5 6 7 8
        ''',
        expect_regex=b'[ABC][012345678]')

        self.given(b'''
            /A/a/
                A = a: A a
        ''',
        expect_regex=b'[Aa][Aa]')

        self.given(b'''
            /A/a/
                A = a: A a
        ''',
        expect_regex=b'[Aa][Aa]')

        self.given(b'''
            x
                x: [ ^ \\ ]
        ''',
        expect_regex=b'[\\[\\^\\\\\\]]')


    def test_char(self):
        self.given(b'''
            x
                x: /Alphabetic /Script=Latin /InBasicLatin /IsCyrillic /Script=Cyrillic
        ''',
        expect_regex=b'[\p{Alphabetic}\p{Script=Latin}\p{InBasicLatin}\p{IsCyrillic}\p{Script=Cyrillic}]')

        self.given(b'''
            x
                x: \u00ab \u00AB \U000000ab \u00Ab
        ''',
        expect_regex=b'[\u00ab\u00AB\U000000ab\u00Ab]')

        self.given(b'''
            x
                x: \u12ab \u12AB \u12Ab
        ''',
        expect_regex=b'[\u12ab\u12AB\u12Ab]')

        try:
            self.given(b'''
                x
                    x: \U0001234a \U0001234A \U0001234a
            ''',
            expect_regex=b'[\U0001234a\U0001234A\U0001234a]')
        except ValueError as e:
            if 'narrow Python build' in e.message:
                pass
            else:
                raise

        self.given(b'''
            x
                x: :SKULL_AND_CROSSBONES :BIOHAZARD_SIGN :CANCER
        ''',
        expect_regex=b'[\N{SKULL AND CROSSBONES}\N{BIOHAZARD SIGN}\N{CANCER}]')


    def test_character_range_output(self):
        self.given(br'''
            AB
                AB: A..\u0042
        ''',
        expect_regex=br'[A-\u0042]')

        self.given(br'''
            AB
                AB: \u0041..\U00000042
        ''',
        expect_regex=br'[\u0041-\U00000042]')

        self.given(br'''
            AB
                AB: \U00000041..\x42
        ''',
        expect_regex=br'[\U00000041-\x42]')

        self.given(br'''
            AB
                AB: \x41..\102
        ''',
        expect_regex=br'[\x41-\102]')

        self.given(br'''
            AB
                AB: \101..\N{LATIN CAPITAL LETTER B}
        ''',
        expect_regex=br'[\101-\N{LATIN CAPITAL LETTER B}]')

        self.given(b'''
            AB
                AB: \N{LATIN CAPITAL LETTER A}..:LEFT_RIGHT_OPEN-HEADED_ARROW
        ''',
        expect_regex=br'[\N{LATIN CAPITAL LETTER A}-\N{LEFT RIGHT OPEN-HEADED ARROW}]')

        self.given(b'''
            AB
                AB: :LATIN_CAPITAL_LETTER_A..\N{LEFT RIGHT OPEN-HEADED ARROW}
        ''',
        expect_regex=br'[\N{LATIN CAPITAL LETTER A}-\N{LEFT RIGHT OPEN-HEADED ARROW}]')

        self.given(br'''
            colon_to_semi
                colon_to_semi: :..;
        ''',
        expect_regex=b'[:-;]')

        self.given(b'''
            need_escape
                need_escape: [ ^ a - z ]
        ''',
        expect_regex=br'[\[\^a\-z\]]')


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

        self.given(b'''
            aUmlaut
                aUmlaut: +a_with_diaeresis
                    a_with_diaeresis: \u00E4
        ''',
        expect_regex=br'\u00E4')

        self.given(u'''
            aUmlaut
                aUmlaut: +a_with_diaeresis
                    a_with_diaeresis: :LATIN_SMALL_LETTER_A_WITH_DIAERESIS
        ''',
        expect_regex=br'\N{LATIN SMALL LETTER A WITH DIAERESIS}')

        self.given(u'''
            alphabetic
                alphabetic: +is_alphabetic
                    is_alphabetic: /Alphabetic
        ''',
        expect_regex=br'\p{Alphabetic}')

        self.given(u'''
            lowaz
                lowaz: +lowerAZ
                    lowerAZ: a..z
        ''',
        expect_regex=b'[a-z]')

        self.given(u'''
            /hex/
                hex: +hexx +hexy +hexz
                    hexx = hexdigit
                        hexdigit: 0..9
                    hexy = hexz = hexalpha
                        hexalpha: a..f A..F
        ''',
        expect_regex=b'[0-9a-fA-Fa-fA-F]')

        self.given(u'''
            /xx/dup/
                xx: x X
                dup: +xx
        ''',
        expect_regex=b'[xX][xX]')

        self.given(u'''
            /cc/
                cc: +yy a
                    yy: y not Y
        ''',
        expect_regex=b'[[y--Y]a]')

        self.given(u'''
            /cc/
                cc: a +yy
                    yy: y not Y
        ''',
        expect_regex=b'[a[y--Y]]')

        self.given(u'''
            /cc/
                cc: +xx +yy
                    xx: x not X
                    yy: y not Y
        ''',
        expect_regex=b'[[x--X][y--Y]]')

        self.given(u'''
            /cc/
                cc: +xx a +yy
                    xx: x not X
                    yy: y not Y
        ''',
        expect_regex=b'[[x--X]a[y--Y]]')

        self.given(u'''
            /notX/
                notX:  not: X
        ''',
        expect_regex=b'[^X]')

        self.given(u'''
            not: X
        ''',
        expect_regex=b'[^X]')

        self.given(u'''
            not: X Y Z
        ''',
        expect_regex=b'[^XYZ]')

        self.given(u'''
            /not_X/
                not_X: notX
                    notX:  not: X
        ''',
        expect_regex=b'[^X]')

        self.given(u'''
            /notNotX/
                notNotX: not: +notX
                    notX:  not: X
        ''',
        expect_regex=b'X')

        self.given(u'''
            not: not: X
        ''',
        expect_regex=b'X')

        self.given(u'''
            1 of: not: not: X
        ''',
        expect_regex=b'X')

        self.given(u'''
            not: not: not: X
        ''',
        expect_regex=b'[^X]')

        self.given(u'''
            not: not: not: not: X
        ''',
        expect_regex=b'X')

        self.given(u'''
            not: not: -
        ''',
        expect_regex=b'-')

        self.given(u'''
            not: -
        ''',
        expect_regex=br'[^\-]')

        self.given(u'''
            /plus/minus/pmz/
                plus: +
                minus: -
                pmz: +plus +minus z
        ''',
        expect_regex=b'\+-[+\-z]')

        self.given(u'''
            vowhex
                vowhex: +vowel +hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_regex=b'[aiueoAIUEO0-9a-fA-F]')

        self.given(b'''
            x
                x: +__special__
                    __special__: x
        ''',
        expect_regex=b'x')

        self.given(b'''
            x
                x: __special__
                   __special__: x
        ''',
        expect_regex=b'x')

        self.given(b'''
            /dot/period/
                period: .
                dot: . period
        ''',
        expect_regex=b'[..]\.')


    def test_charclass_operation_output(self):
        self.given(u'''
            xb123
                xb123: X x +hex not c..f C..D :LATIN_CAPITAL_LETTER_F +vowel and 1 2 3 /Alphabetic
                    hex: 0..9 a..f A..F
                    vowel: a i u e o A I U E O
        ''',
        expect_regex=b'[Xx0-9a-fA-F--c-fC-D\N{LATIN CAPITAL LETTER F}aiueoAIUEO&&123\p{Alphabetic}]')

        self.given(u'''
            allButU
                allButU: not: U
        ''',
        expect_regex=b'[^U]')

        self.given(u'''
            nonalpha
                nonalpha: not: /Alphabetic
        ''',
        expect_regex=b'\P{Alphabetic}')

        self.given(u'''
            not: digit
        ''',
        expect_regex=b'\D')

        self.given(u'''
            not: /Alphabetic
        ''',
        expect_regex=b'\P{Alphabetic}')

        self.given(u'''
            otherz
                otherz: +nonz
                    nonz: not: z
        ''',
        expect_regex=b'[^z]')

        self.given(u'''
            a_or_consonant
                a_or_consonant: A a +consonant 
                    consonant: a..z A..Z not a i u e o A I U E O 
        ''',
        expect_regex=b'[Aa[a-zA-Z--aiueoAIUEO]]')

        self.given(u'''
            maestro
                maestro: m +ae s t r o 
                    ae: +vowel and +hex not +upper
                        hex: +digit a..f A..F 
                        vowel: a i u e o A I U E O
        ''',
        expect_regex=br'[m[aiueoAIUEO&&\da-fA-F--A-Z]stro]')


    def test_charclass_escape_output(self):
        self.given(b'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_regex=b'[\u0061\U00000061\x61\61]')

        self.given(br'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_regex=br'[\u0061\U00000061\x61\61]')

        self.given(u'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_regex=u'[\u0061\U00000061\x61\61]')

        self.given(ur'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_regex=ur'[\u0061\U00000061\x61\61]')

        self.given(br'''
            allowed_escape
                allowed_escape: \n \r \t \a \b \v \f
        ''',
        expect_regex=br'[\n\r\t\a\b\v\f]')

        self.given(b'''
            backspace
                backspace: \\
        ''',
        expect_regex=br'\\')

        self.given(br'''
            unicode_charname
                unicode_charname: \N{AMPERSAND} :AMPERSAND \N{BIOHAZARD SIGN} :BIOHAZARD_SIGN
        ''',
        expect_regex=b'[\N{AMPERSAND}\N{AMPERSAND}\N{BIOHAZARD SIGN}\N{BIOHAZARD SIGN}]')


    def test_string_literal(self):
        self.given(b'''
            'lorem ipsum'
        ''',
        expect_regex=b'lorem ipsum')

        self.given(b'''
            "lorem ipsum"
        ''',
        expect_regex=b'lorem ipsum')

        self.given(b'''
            "Ron's"
        ''',
        expect_regex="Ron's")

        self.given(br'''
            'Ron\'s'
        ''',
        expect_regex="Ron's")

        self.given(b'''
            'Ron\\'s'
        ''',
        expect_regex="Ron's")

        self.given(b'''
            'said "Hi"'
        ''',
        expect_regex=b'said "Hi"')

        self.given(br'''
            "said \"Hi\""
        ''',
        expect_regex=b'said "Hi"')

        self.given(br'''
            "name:\toprex\nawesome:\tyes"
        ''',
        expect_regex=b'name:\\toprex\\nawesome:\\tyes')


    def test_string_interpolation(self):
        self.given(b'''
            /p/pXs/s/
                p = '%'
                s = 's'
                pXs = /p/X/s/
                    [X] = 'X'
        ''',
        expect_regex=b'%%(?P<X>X)ss')

        self.given(b'''
            /p/pXs/s/
                p = '%'
                s = 's'
                [pXs] = /p/X/s/
                    [X] = 'X'
        ''',
        expect_regex=b'%(?P<pXs>%(?P<X>X)s)s')

        self.given(b'''
            greeting
                greeting = 'Hello %(name)s'
        ''',
        expect_regex=b'Hello %\(name\)s')


        self.given(b'''
            message
                message = /greeting/name/
                    greeting = 'Hello%'
                    name = /salutation/first/last/
                        [salutation] = 'Sir/Madam'
                        first = 's%(first)s'
                        last  = '%(last)s'
        ''',
        expect_regex=b'Hello%(?P<salutation>Sir/Madam)s%\(first\)s%\(last\)s')


    def test_scoping(self):
        self.given(b'''
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
        expect_regex=b'thequickbrownfoxjumpsoverthelazydog')

        self.given(b'''
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
        expect_regex=b'thequickbrownfoxjumpsoverthequickbrownfox')

        self.given(b'''
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
        expect_regex=b'144banana4papaya4')

        self.given(b'''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
                    satu = '1'
*)                  uno = ichi = satu
                oneone = /uno/ichi/
                one = satu
                    satu: 1
        ''',
        expect_regex=b'111111')


    def test_aliases(self):
        self.given(b'''
            /griffin/griffon/gryphon/alce/keythong/opinicus/
                griffin = griffon = 'protoceratops'
                gryphon = griffon
                alce = keythong = opinicus = griffin
        ''',
        expect_regex=b'protoceratopsprotoceratopsprotoceratopsprotoceratopsprotoceratopsprotoceratops')

        self.given(b'''
            /X/deadeye/ten/unknown_thing/wrong_answer/
                deadeye = X: X
                ten = X
                unknown_thing = wrong_answer = X
        ''',
        expect_regex=b'XXXXX')


    def test_empty_lines_ok(self):
        self.given(b'''

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
        expect_regex=b'thequickbrownfoxjumpsoverthelazydog')


    def test_captures_output(self):
        self.given(b'''
            /extra/extra?/
                [extra] = 'icing'
        ''',
        expect_regex=b'(?P<extra>icing)(?P<extra>icing)?')

        self.given(b'''
            /defcon/level/
                defcon = 'DEFCON'
                [level]: 1 2 3 4 5
        ''',
        expect_regex=br'DEFCON(?P<level>[12345])')

        self.given(b'''
            captured?
                [captured] = /L/R/
                    [L] = 'Left'
                    [R] = 'Right'
        ''',
        expect_regex=br'(?P<captured>(?P<L>Left)(?P<R>Right))?')

        self.given(b'''
            uncaptured?
                uncaptured = /L?/R/
                    [L] = 'Left'
                    [R] = 'Right'
        ''',
        expect_regex=br'(?:(?P<L>Left)?(?P<R>Right))?')


    def test_atomic_grouping_output(self):
        self.given(b'''
            @/alpha/ -- possible though pointless
        ''',
        expect_regex=br'(?>[a-zA-Z])')

        self.given(b'''
            @/alpha/digit/ -- possible though pointless
        ''',
        expect_regex=br'(?>[a-zA-Z]\d)')

        self.given(b'''
            @/digits?/even/
                digits = 1.. <<- of digit
                even: 0 2 4 6 8
        ''',
        expect_regex=br'(?>\d*[02468])')

        self.given(b'''
            ./digits?/even/.
                digits = 1.. <<- of digit
                even: 0 2 4 6 8
        ''',
        expect_regex=br'\A\d*[02468]\Z')

        self.given(b'''
            //digits?/even//
                digits = 1.. <<- of digit
                even: 0 2 4 6 8
        ''',
        expect_regex=br'(?m:^)\d*[02468](?m:$)')


    def test_builtin_output(self):
        self.given(b'''
            /alpha/upper/lower/digit/alnum/
        ''',
        expect_regex=br'[a-zA-Z][A-Z][a-z]\d[a-zA-Z0-9]')

        self.given(b'''
            (unicode)
            /alpha/upper/lower/digit/alnum/
        ''',
        expect_regex=br'(?V1wu)\p{Alphabetic}\p{Uppercase}\p{Lowercase}\d\p{Alphanumeric}')

        self.given(b'''
            /BOS/EOS/BOL/EOL/BOW/EOW/WOB/
        ''',
        expect_regex=br'\A\Z(?m:^)(?m:$)\m\M\b')

        self.given(b'''
            (multiline)
            /BOS/EOS/BOL/EOL/BOW/EOW/WOB/
        ''',
        expect_regex=br'(?V1wm)\A\Z^$\m\M\b')

        self.given(b'''
            (-multiline)
            /BOS/EOS/BOL/EOL/BOW/EOW/WOB/
        ''',
        expect_regex=br'(?V1w-m)\A\Z(?m:^)(?m:$)\m\M\b')

        self.given(b'''
            /any/uany/
        ''',
        expect_regex=br'(?s:.)\X')

        self.given(b'''
            (dotall)
            /any/uany/
        ''',
        expect_regex=br'(?V1ws).\X')

        self.given(b'''
            (-dotall)
            /any/uany/
        ''',
        expect_regex=br'(?V1w-s)(?s:.)\X')

        self.given(b'''
            /backslash/wordchar/whitechar/linechar/padchar/space/tab/
        ''',
        expect_regex=br'\\\w\s[\r\n\x0B\x0C][ \t] \t')

        self.given(b'''
            (word verbose)
            /backslash/wordchar/whitechar/linechar/padchar/space/tab/
        ''',
        expect_regex=br'(?V1wx)\\\w\s[\r\n\x0B\x0C][ \t][ ]\t')

        self.given(b'''
            (-word -verbose)
            /backslash/wordchar/whitechar/linechar/padchar/space/tab/
        ''',
        expect_regex=br'(?V1-wx)\\\w\s\n[ \t] \t')

        self.given(b'''
            /non-alpha/non-upper/non-lower/non-digit/non-alnum/
        ''',
        expect_regex=br'[^a-zA-Z][^A-Z][^a-z]\D[^a-zA-Z0-9]')

        self.given(b'''
            (unicode)
            /non-alpha/non-upper/non-lower/non-digit/non-alnum/
        ''',
        expect_regex=br'(?V1wu)\P{Alphabetic}\P{Uppercase}\P{Lowercase}\D\P{Alphanumeric}')

        self.given(b'''
            /non-WOB/
        ''',
        expect_regex=br'\B')

        self.given(b'''
            /non-backslash/non-wordchar/non-whitechar/non-linechar/non-padchar/non-space/non-tab/
        ''',
        expect_regex=br'[^\\]\W\S.[^ \t][^ ][^\t]')

        self.given(b'''
            (word verbose)
            /non-backslash/non-wordchar/non-whitechar/non-linechar/non-padchar/non-space/non-tab/
        ''',
        expect_regex=br'(?V1wx)[^\\]\W\S.[^ \t][^ ][^\t]')

        self.given(b'''
            (-word -verbose)
            /non-backslash/non-wordchar/non-whitechar/non-linechar/non-padchar/non-space/non-tab/
        ''',
        expect_regex=br'(?V1-wx)[^\\]\W\S.[^ \t][^ ][^\t]')


    def test_quantifier_output(self):
        self.given(b'''
            0 of alpha
        ''',
        expect_regex=b'')

        self.given(b'''
            1 of alpha
        ''',
        expect_regex=b'[a-zA-Z]')

        self.given(b'''
            2 of alpha
        ''',
        expect_regex=b'[a-zA-Z]{2}')

        self.given(b'''
            0 of: alpha
        ''',
        expect_regex=b'')

        self.given(b'''
            1 of: alpha
        ''',
        expect_regex=b'[a-zA-Z]')

        self.given(b'''
            2 of: alpha
        ''',
        expect_regex=b'[a-zA-Z]{2}')

        self.given(b'''
            @0 of alpha
        ''',
        expect_regex=b'')

        self.given(b'''
            @1 of alpha
        ''',
        expect_regex=b'[a-zA-Z]')

        self.given(b'''
            @2 of alpha
        ''',
        expect_regex=b'[a-zA-Z]{2}')

        self.given(b'''
            @0 of: alpha
        ''',
        expect_regex=b'')

        self.given(b'''
            @1 of: alpha
        ''',
        expect_regex=b'[a-zA-Z]')

        self.given(b'''
            @2 of: alpha
        ''',
        expect_regex=b'[a-zA-Z]{2}')

        self.given(b'''
            @0.. of alpha
        ''',
        expect_regex=b'[a-zA-Z]*+')

        self.given(b'''
            @1.. of alpha
        ''',
        expect_regex=b'[a-zA-Z]++')

        self.given(b'''
            @2.. of alpha
        ''',
        expect_regex=b'[a-zA-Z]{2,}+')

        self.given(b'''
            @0..2 of alpha
        ''',
        expect_regex=b'[a-zA-Z]{,2}+')

        self.given(b'''
            @0..1 of alpha
        ''',
        expect_regex=b'[a-zA-Z]?+')

        self.given(b'''
            @3..4 of alpha
        ''',
        expect_regex=b'[a-zA-Z]{3,4}+')

        self.given(b'''
            0.. <<- of alpha
        ''',
        expect_regex=b'[a-zA-Z]*')

        self.given(b'''
            1.. <<- of alpha
        ''',
        expect_regex=b'[a-zA-Z]+')

        self.given(b'''
            2.. <<- of alpha
        ''',
        expect_regex=b'[a-zA-Z]{2,}')

        self.given(b'''
            0..2 <<- of alpha
        ''',
        expect_regex=b'[a-zA-Z]{,2}')

        self.given(b'''
            0..1 <<- of alpha
        ''',
        expect_regex=b'[a-zA-Z]?')

        self.given(b'''
            0 <<+..1 of alpha
        ''',
        expect_regex=b'[a-zA-Z]??')

        self.given(b'''
            3..4 <<- of alpha
        ''',
        expect_regex=b'[a-zA-Z]{3,4}')

        self.given(b'''
            0 <<+.. of alpha
        ''',
        expect_regex=b'[a-zA-Z]*?')

        self.given(b'''
            1 <<+.. of alpha
        ''',
        expect_regex=b'[a-zA-Z]+?')

        self.given(b'''
            2 <<+.. of alpha
        ''',
        expect_regex=b'[a-zA-Z]{2,}?')

        self.given(b'''
            0 <<+..1 of alpha
        ''',
        expect_regex=b'[a-zA-Z]??')

        self.given(b'''
            0 <<+..2 of alpha
        ''',
        expect_regex=b'[a-zA-Z]{,2}?')

        self.given(b'''
            1 <<+..2 of alpha
        ''',
        expect_regex=b'[a-zA-Z]{1,2}?')

        self.given(b'''
            alphas?
                alphas = @1.. of alpha
        ''',
        expect_regex=b'[a-zA-Z]*+')

        self.given(b'''
            alphas?
                alphas = @0.. of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]*+)?')

        self.given(b'''
            opt_alpha?
                opt_alpha = @0..1 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]?+)?')

        self.given(b'''
            opt_alpha?
                opt_alpha = 0..1 <<- of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]?)?')

        self.given(b'''
            opt_alpha?
                opt_alpha = 0 <<+..1 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]??)?')

        self.given(b'''
            @0..1 of @0..1 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]?+)?+')

        self.given(b'''
            @0..1 of 0..1 <<- of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]?)?+')

        self.given(b'''
            0 <<+..1 of @0..1 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]?+)??')

        self.given(b'''
            0..1 <<- of 0 <<+..1 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]??)?')

        self.given(b'''
            2 of @0..1 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]?+){2}')

        self.given(b'''
            @0..1 of 2 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{2})?+')

        self.given(b'''
            @0..1 of @1..3 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{1,3}+)?+')

        self.given(b'''
            @1..3 of @0..1 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]?+){1,3}+')

        self.given(b'''
            1..3 <<- of @5..7 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{5,7}+){1,3}')

        self.given(b'''
            @1..3 of 5..7 <<- of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{5,7}){1,3}+')

        self.given(b'''
            1..3 <<- of 5..7 <<- of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{5,7}){1,3}')

        self.given(b'''
            1 <<+..3 of 5..7 <<- of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{5,7}){1,3}?')

        self.given(b'''
            1..3 <<- of 5 <<+..7 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{5,7}?){1,3}')

        self.given(b'''
            1 <<+..3 of 5 <<+..7 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{5,7}?){1,3}?')

        self.given(b'''
            2 of @3..4 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{3,4}+){2}')

        self.given(b'''
            2 of 3..4 <<- of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{3,4}){2}')

        self.given(b'''
            2 of 3 <<+..4 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{3,4}?){2}')

        self.given(b'''
            @2..3 of 4 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{4}){2,3}+')

        self.given(b'''
            2..3 <<- of 4 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{4}){2,3}')

        self.given(b'''
            2 <<+..3 of 4 of alpha
        ''',
        expect_regex=b'(?:[a-zA-Z]{4}){2,3}?')

        self.given(b'''
            css_color
                css_color = 6 of hex
                    hex: 0..9 a..f
        ''',
        expect_regex=b'[0-9a-f]{6}')

        self.given(b'''
            css_color
                css_color = 3 of 2 of hex
                    hex: 0..9 a..f
        ''',
        expect_regex=b'[0-9a-f]{6}')

        self.given(b'''
            css_color
                css_color = 3 of hexbyte
                    hexbyte = 2 of: 0..9 a..f
        ''',
        expect_regex=b'[0-9a-f]{6}')

        self.given(b'''
            DWORD_speak
                DWORD_speak = @1.. of 4 of hex
                    hex: 0..9 A..F
        ''',
        expect_regex=b'(?:[0-9A-F]{4})++')
        
        self.given(b'''
            ? of alpha
        ''',
        expect_regex=b'[a-zA-Z]?')
        
        self.given(b'''
            ? of alphas
                alphas = @1.. of alpha
        ''',
        expect_regex=b'[a-zA-Z]*+')
        
        self.given(b'''
            ? of alphas
                alphas = 1.. <<- of alpha
        ''',
        expect_regex=b'[a-zA-Z]*')
        
        self.given(b'''
            ? of alphas
                alphas = 1 <<+.. of alpha
        ''',
        expect_regex=b'[a-zA-Z]*?')


    def test_commenting(self):
        self.given(b'''
            -- comments should be ignored
        ''',
        expect_regex=b'')

        self.given(b'''
-- comments should be ignored
        ''',
        expect_regex=b'')

        self.given(b'''
            -- comments should be ignored
            --comments should be ignored
        ''',
        expect_regex=b'')

        self.given(b'''
-- comments should be ignored
--comments should be ignored
        ''',
        expect_regex=b'')

        self.given(b'''
            --comments should be ignored
--comments should be ignored
            -- comments should be ignored
        ''',
        expect_regex=b'')

        self.given(b'''
            --comments should be ignored
-- comments should be ignored
            -- comments should be ignored
--comments should be ignored
        ''',
        expect_regex=b'')

        self.given(b'''-- first line containing comments, and only comments, is OK
        -- so is last line''',
        expect_regex=b'')

        self.given(b'''--
--      ''',
        expect_regex=b'')

        self.given(b''' --
        --''',
        expect_regex=b'')

        self.given(b'''
            --
        ''',
        expect_regex=b'')

        self.given(b'''
--
        ''',
        expect_regex=b'')

        self.given(b'''
            ---
        ''',
        expect_regex=b'')

        self.given(b'''
            --
            --
        ''',
        expect_regex=b'')

        self.given(b'''
--
--
        ''',
        expect_regex=b'')

        self.given(b'''
            --
--
            --
        ''',
        expect_regex=b'')

        self.given(b'''
            --
--
            --
--
        ''',
        expect_regex=b'')

        self.given(b'''
            /comment/ -- should be ignored
                comment = 'first'
        ''',
        expect_regex=b'first')

        self.given(b'''
            /comment/ --should be ignored
                comment = 'first'
        ''',
        expect_regex=b'first')

        self.given(b'''
            /comment/ --
                comment = 'first'
        ''',
        expect_regex=b'first')

        self.given(b'''
-- begin
            /social_symbol/literally/literal/ --comments should be ignored
                social_symbol: @ #        -- the social media symbols
                literally = 'literally' -- string literal
                literal = literally --alias
--end
        ''',
        expect_regex=b'[@#]literallyliterally')


    def test_reference_output(self):
        self.given(u'''
            /bang/=bang/
                [bang]: b a n g !
        ''',
        expect_regex=b'(?P<bang>[bang!])(?P=bang)')
        
        self.given(u'''
            /=bang/bang/
                [bang]: b a n g !
        ''',
        expect_regex=b'(?P=bang)(?P<bang>[bang!])')
        
        self.given(u'''
            /bang/=bang?/
                [bang]: b a n g !
        ''',
        expect_regex=b'(?P<bang>[bang!])(?P=bang)?')
        
        self.given(u'''
            /=bang?/bang/
                [bang]: b a n g !
        ''',
        expect_regex=b'(?P=bang)?(?P<bang>[bang!])')


    def test_wordchar_boundary_output(self):
        self.given(b'''
            /wordchar/WOB/non-WOB/BOW/EOW/
        ''',
        expect_regex=br'\w\b\B\m\M')

        self.given(b'''
            realworld_wordchar
                realworld_wordchar: +wordchar - not +digit _
        ''',
        expect_regex=br'[\w\---\d_]')

        self.given(b'''
            cat
                cat = .'cat'.
        ''',
        expect_regex=br'\bcat\b')

        self.given(b'''
            /WOB/cat/WOB/
                cat = 'cat'
        ''',
        expect_regex=br'\bcat\b')

        self.given(b'''
            /BOW/cat/EOW/
                cat = 'cat'
        ''',
        expect_regex=br'\mcat\M')

        self.given(b'''
            /WOB/cat/WOB/
                cat = .'cat'.
        ''',
        expect_regex=br'\b\bcat\b\b')

        self.given(b'''
            /anti/non-WOB/
                anti = 'anti'
        ''',
        expect_regex=br'anti\B')

        self.given(b'''
            somethingtastic
                somethingtastic = _'tastic'
        ''',
        expect_regex=br'\Btastic')

        self.given(b'''
            expletification
                expletification = _'bloody'_
        ''',
        expect_regex=br'\Bbloody\B')

        self.given(b'''
            non-WOB
        ''',
        expect_regex=br'\B')

        self.given(b'''
            WOB
        ''',
        expect_regex=br'\b')

        self.given(b'''
            2 of WOB
        ''',
        expect_regex=br'\b{2}')

        self.given(b'''
            bdry
                bdry = @/WOB/
        ''',
        expect_regex=br'(?>\b)')

        self.given(b'''
            bdry
                [bdry] = WOB
        ''',
        expect_regex=br'(?P<bdry>\b)')

        self.given(b'''
            bdries
                bdries = 1 of 2 of 3 of WOB
        ''',
        expect_regex=br'\b{6}')

        self.given(b'''
            bdries?
                bdries = @1.. of WOB
        ''',
        expect_regex=br'\b*+')


    def test_string_escape_output(self):
        self.given(br'''
            @3.. of '\n'
        ''',
        expect_regex=br'\n{3,}+')

        self.given(br'''
            @3.. of '\t'
        ''',
        expect_regex=br'\t{3,}+')

        self.given(b'''
            @3.. of '\t'
        ''',
        expect_regex=b'\t{3,}+')

        self.given(br'''
            @3.. of '\x61'
        ''',
        expect_regex=br'\x61{3,}+')

        self.given(b'''
            @3.. of '\x61'
        ''',
        expect_regex=b'a{3,}+')

        self.given(u'''
            @3.. of '\U00000061'
        ''',
        expect_regex=b'a{3,}+')

        self.given(br'''
            @3.. of '\u0061'
        ''',
        expect_regex=br'\u0061{3,}+')

        self.given(br'''
            @3.. of '\61'
        ''',
        expect_regex=br'\61{3,}+')

        self.given(u'''
            @3.. of '\N{AMPERSAND}'
        ''',
        expect_regex=b'&{3,}+')

        self.given(br'''
            @3.. of '\N{AMPERSAND}'
        ''',
        expect_regex=br'\N{AMPERSAND}{3,}+')

        self.given(br'''
            @3.. of '\N{LEFTWARDS ARROW}'
        ''',
        expect_regex=br'\N{LEFTWARDS ARROW}{3,}+')

        self.given(u'''
            @3.. of 'M\N{AMPERSAND}M\\\N{APOSTROPHE}s'
        ''',
        expect_regex="(?:M&M's){3,}+")

        self.given(ur'''
            @3.. of 'M\N{AMPERSAND}M\N{APOSTROPHE}s'
        ''',
        expect_regex=br'(?:M\N{AMPERSAND}M\N{APOSTROPHE}s){3,}+')

        self.given(ur'''
            @3.. of '\r\n'
        ''',
        expect_regex=br'(?:\r\n){3,}+')

        self.given(br'''
            '\a\b\f\v\t'
        ''',
        expect_regex=br'\x07\x08\x0C\x0B\t')

        self.given(br'''
            '.\w\b\s\X\n'
        ''',
        expect_regex=br'\.\\w\x08\\s\\X\n')


    def test_flagging_output(self):
        self.given(b'''
            (unicode)
        ''',
        expect_regex=b'(?V1wu)')

        self.given(b'''
            (ascii version0)
        ''',
        expect_regex=b'(?waV0)')

        self.given(b'''
            (bestmatch dotall enhancematch fullcase ignorecase locale multiline reverse verbose version1 word)
        ''',
        expect_regex=b'(?bsefiLmrxV1w)')

        self.given(b'''
            (multiline)
        ''',
        expect_regex=b'(?V1wm)')

        self.given(b'''
            (-multiline)
        ''',
        expect_regex=b'(?V1w-m)')

        self.given(b'''
            (-word)
        ''',
        expect_regex=b'(?V1-w)')

        self.given(b'''
            (ignorecase)
        ''',
        expect_regex=b'(?V1wi)')

        self.given(b'''
            (-ignorecase)
        ''',
        expect_regex=b'(?V1w-i)')

        self.given(b'''
            (unicode ignorecase)
        ''',
        expect_regex=b'(?V1wui)')

        self.given(b'''
            (unicode)
            (ignorecase) alpha
        ''',
        expect_regex=b'(?V1wu)(?i:\p{Alphabetic})')

        self.given(b'''
            (unicode ignorecase)
            (-ignorecase) lower
        ''',
        expect_regex=b'(?V1wui)(?-i:\p{Lowercase})')

        self.given(b'''
            (ignorecase) .'giga'_
        ''',
        expect_regex=br'(?i:\bgiga\B)')

        self.given(b'''
            (ignorecase) /super/uppers/
                super = 'super'
                uppers = (-ignorecase) @1.. of upper
        ''',
        expect_regex=b'(?i:super(?-i:[A-Z]++))')

        self.given(b'''
            hex?
                hex = (ignorecase) 1 of: +digit a..f
        ''',
        expect_regex=br'(?i:[\da-f])?')

        self.given(b'''
            (ignorecase) 2 of 'yadda'
        ''',
        expect_regex=br'(?i:(?:yadda){2})')

        self.given(b'''
            2 of (ignorecase) 'yadda'
        ''',
        expect_regex=br'(?i:yadda){2}')

        self.given(b'''
            2 of (ignorecase) 3 of 4 of (ignorecase) 'yadda'
        ''',
        expect_regex=br'(?i:(?i:yadda){12}){2}')


    def test_variable_named_of(self):
        self.given(b'''
            2 of of -- a variable named "of"
                of = 'of'
        ''',
        expect_regex=br'(?:of){2}')

        self.given(b'''
            1 of 2 of of               
                of = 'of'
        ''',
        expect_regex=br'(?:of){2}')

        self.given(b'''
            1 of 2 of 3 of of
                of: o f
        ''',
        expect_regex=br'[of]{6}')

        self.given(b'''
            2  of  /digit/of/digit/
                of: o f
        ''',
        expect_regex=br'(?:\d[of]\d){2}')

        self.given(b'''
            1 of 2 of '3 of alpha'
        ''',
        expect_regex=br'(?:3 of alpha){2}')


    def test_flag_dependent_charclass_output(self):
        self.given(b'''
            /BOL/EOL/line2/BOS/EOS/
                line2 = (multiline) /BOL/EOL/BOS/EOS/
        ''',
        expect_regex=b'(?m:^)(?m:$)(?m:^$\A\Z)\A\Z')

        self.given(b'''
            (multiline)
            /BOL/EOL/line2/BOS/EOS/
                line2 = (multiline) /BOL/EOL/BOS/EOS/
        ''',
        expect_regex=b'(?V1wm)^$(?m:^$\A\Z)\A\Z')

        self.given(b'''
            (-multiline)
            /BOL/EOL/line2/BOS/EOS/
                line2 = (multiline) /BOL/EOL/BOS/EOS/
        ''',
        expect_regex=b'(?V1w-m)(?m:^)(?m:$)(?m:^$\A\Z)\A\Z')

        self.given(b'''
            /BOL/EOL/line2/BOS/EOS/
                line2 = (-multiline) /BOL/EOL/BOS/EOS/
        ''',
        expect_regex=b'(?m:^)(?m:$)(?-m:(?m:^)(?m:$)\A\Z)\A\Z')

        self.given(b'''
            (multiline)
            /BOL/EOL/line2/BOS/EOS/
                line2 = (-multiline) /BOL/EOL/BOS/EOS/
        ''',
        expect_regex=b'(?V1wm)^$(?-m:(?m:^)(?m:$)\A\Z)\A\Z')

        self.given(b'''
            (-multiline)
            /BOL/EOL/line2/BOS/EOS/
                line2 = (-multiline) /BOL/EOL/BOS/EOS/
        ''',
        expect_regex=b'(?V1w-m)(?m:^)(?m:$)(?-m:(?m:^)(?m:$)\A\Z)\A\Z')

        self.given(b'''
            /BOL/EOL/BOS/EOS/line2/
                line2 = (dotall) /BOL/EOL/BOS/EOS/ -- should be unaffected
        ''',
        expect_regex=b'(?m:^)(?m:$)\A\Z(?s:(?m:^)(?m:$)\A\Z)')

        self.given(b'''
            /any/any2/any3/
                any2 = (dotall) any
                any3 = (-dotall) any
        ''',
        expect_regex=b'(?s:.)(?s:.)(?-s:(?s:.))')

        self.given(b'''
            /space/tab/spacetab2/spacetab3/
                spacetab2 = (verbose) /space/tab/
                spacetab3 = (-verbose) /space/tab/
        ''',
        expect_regex=br' \t(?x:[ ]\t)(?-x: \t)')

        self.given(b'''
            /spacetab/spacetab2/
                spacetab = (verbose) 1 of: +space +tab
                spacetab2 = (-verbose) 1 of: +space +tab
        ''',
        expect_regex=br'(?x:[ \t])(?-x:[ \t])')

        self.given(b'''
            /linechar/lf/
                lf = (-word) 1 of: +linechar
        ''',
        expect_regex=br'[\r\n\x0B\x0C](?-w:\n)')

        self.given(b'''
            (unicode)
            linechar
        ''',
        expect_regex=br'(?V1wu)[\r\n\x0B\x0C\x85\u2028\u2029]')

        self.given(b'''
            (word unicode)
            linechar
        ''',
        expect_regex=br'(?V1wu)[\r\n\x0B\x0C\x85\u2028\u2029]')

        self.given(b'''
            (unicode word)
            linechar
        ''',
        expect_regex=br'(?V1uw)[\r\n\x0B\x0C\x85\u2028\u2029]')

        self.given(b'''
            (unicode)
            (word) linechar
        ''',
        expect_regex=br'(?V1wu)(?w:[\r\n\x0B\x0C\x85\u2028\u2029])')

        self.given(b'''
            (unicode -word)
            /linechar/line2/
                line2 = (word) linechar
        ''',
        expect_regex=br'(?V1u-w)\n(?w:[\r\n\x0B\x0C\x85\u2028\u2029])')

        self.given(b'''
            (-word unicode)
            (word) /linechar/line2/
                line2 = (-word) linechar
        ''',
        expect_regex=br'(?V1u-w)(?w:[\r\n\x0B\x0C\x85\u2028\u2029](?-w:\n))')

        self.given(b'''
            (unicode)
            (-word) /linechar/line2/
                line2 = (word) linechar
        ''',
        expect_regex=br'(?V1wu)(?-w:\n(?w:[\r\n\x0B\x0C\x85\u2028\u2029]))')


    def test_orblock_output(self):
        self.given(b'''
            @|
             |'cat'
             |'dog'
        ''',
        expect_regex=b'(?>cat|dog)')

        self.given(b'''
            <<|
              |'tea'
              |'coffee'
        ''',
        expect_regex=b'tea|coffee')

        self.given(b'''
            backtrackable_choice
                backtrackable_choice = <<|
                                         |'catastrophy'
                                         |'catass trophy'
                                         |'cat'
        ''',
        expect_regex=b'catastrophy|catass trophy|cat')

        self.given(b'''
            no_backtrack
                no_backtrack = @|
                                |'red pill'
                                |'blue pill'
        ''',
        expect_regex=b'(?>red pill|blue pill)')

        self.given(b'''
            /digit/space/ampm/
                ampm = (ignorecase) <<|
                                      |'AM'
                                      |'PM'
        ''',
        expect_regex=b'\d (?i:AM|PM)')

        self.given(b'''
            2 of <<|
                   |'fast'
                   |'good'
                   |'cheap'
        ''',
        expect_regex=b'(?:fast|good|cheap){2}')

        self.given(b'''
            <<|
              |2 of 'ma'
              |2 of 'pa'
              |2 of 'bolo'
        ''',
        expect_regex=b'(?:ma){2}|(?:pa){2}|(?:bolo){2}')

        self.given(b'''
            /blood_type/rhesus/
                blood_type =<<|
                              |'AB'
                              |1 of: A B O

                rhesus = <<|
                           |'+'
                           |'-'
                           | -- allow empty/unknown rhesus
        ''',
        expect_regex=b'(?:AB|[ABO])(?:\+|-|)')

        self.given(b'''
            subexpr_types
                subexpr_types = <<|
                                  |'string literal'
                                  |(ignorecase) 1 of: a i u e o
                                  |2..3 <<- of X
                                  |/alpha/digit/
                                  |alpha

                    X = 'X'
        ''',
        expect_regex=b'string literal|(?i:[aiueo])|X{2,3}|[a-zA-Z]\d|[a-zA-Z]')

        self.given(b'''
            <<| -- comment here is ok
              |'android'
              |'ios'
        ''',
        expect_regex=b'android|ios')

        self.given(b'''
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
        expect_regex=b'(?>lawful |chaotic |neutral )(?>good|evil|neutral)')

        self.given(b'''
            any_color_as_long_as_it_is_
                any_color_as_long_as_it_is_ = <<|
                                                |'black'
                                                -- single-entry "choice" is OK
        ''',
        expect_regex=b'black')

        self.given(b'''-- nested ORBLOCKs
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
        expect_regex=b'espresso|cappuccino|kopi tubruk|earl grey|ocha|teh tarik|cendol')

        self.given(b'''
            /currency/amount/
                currency = <<|
                             |dollar
                             |euro
                
                    [dollar]: $
                    [euro]: :EURO_SIGN
                    
                amount = <<|
                           |[dollar] ? /digits/dot/digits/
                           |[euro] ? /digits/comma/digits/
                           |
              
                    digits = @1.. of digit
                    dot: .
                    comma: ,
        ''',
        expect_regex=b'(?:(?P<dollar>\$)|(?P<euro>\N{EURO SIGN}))(?(dollar)\d++\.\d++|(?(euro)\d++,\d++))')

        self.given(b'''
            /currency/amount/
                currency = <<|
                             |dollar
                             |euro
                
                    [dollar]: $
                    [euro]: :EURO_SIGN
                    
                amount = <<|
                           |[dollar] ? /digits/dot/digits/
                           |[euro] ? /digits/comma/digits/
                           |FAIL!
              
                    digits = @1.. of digit
                    dot: .
                    comma: ,
        ''',
        expect_regex=b'(?:(?P<dollar>\$)|(?P<euro>\N{EURO SIGN}))(?(dollar)\d++\.\d++|(?(euro)\d++,\d++|(?!)))')

        self.given(b'''
            /alpha/or/
                or = @|
                      |alpha
                      |digit
        ''',
        expect_regex=b'[a-zA-Z](?>[a-zA-Z]|\d)')

        self.given(b'''
            /or/alpha/
                or = @|
                      |alpha
                      |digit
        ''',
        expect_regex=b'(?>[a-zA-Z]|\d)[a-zA-Z]')

        self.given(b'''
            /alpha/or/
                or = <<|
                       |alpha
                       |digit
        ''',
        expect_regex=b'[a-zA-Z](?:[a-zA-Z]|\d)')

        self.given(b'''
            /or/alpha/
                or = <<|
                       |alpha
                       |digit
        ''',
        expect_regex=b'(?:[a-zA-Z]|\d)[a-zA-Z]')

        self.given(b'''
            /az?/or/
                [az]: a..z
                or = <<|
                       |[az] ? alpha
                       |digit
        ''',
        expect_regex=b'(?P<az>[a-z])?(?(az)[a-zA-Z]|\d)')

        self.given(b'''
            /or/az/
                [az]: a..z
                or = <<|
                       |[az] ? alpha
                       |digit
        ''',
        expect_regex=b'(?(az)[a-zA-Z]|\d)(?P<az>[a-z])')

        self.given(b'''
            /az?/or/
                [az]: a..z
                or = <<|
                       |[az] ? alpha
                       |
        ''',
        expect_regex=b'(?P<az>[a-z])?(?(az)[a-zA-Z])')

        self.given(b'''
            /az?/or/
                [az]: a..z
                or = <<|
                       |[az] ?
                       |digit                      
        ''',
        expect_regex=b'(?P<az>[a-z])?(?(az)|\d)')

        self.given(b'''
            /az?/or/
                [az]: a..z
                or = <<|
                       |[az] ?
                       |
        ''',
        expect_regex=b'(?P<az>[a-z])?(?(az))')


    def test_lookaround_output(self):
        self.given(b'''
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
        expect_regex=b'(?<=yamaha)(?<!yanglain)semakin(?=didepan)(?!ketinggalan)')

        self.given(b'''
            actually_no_lookaround
                actually_no_lookaround = <@>
                                        |alpha| -- possible, though pointless
        ''',
        expect_regex=b'[a-zA-Z]')

        self.given(b'''
            <@>
                |anyam>
                |anyaman|
                 <nyaman|

                anyam = 'anyam'
                anyaman = 'anyaman'
                nyaman = 'nyaman'
        ''',
        expect_regex=b'(?=anyam)anyaman(?<=nyaman)')

        self.given(b'''
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
        expect_regex=br'(?=(?=[^A-Z]*+[A-Z])(?=[^a-z]*+[a-z]))(?=\D*+\d)(?=\p{Alphanumeric}*+\P{Alphanumeric})\A(?s:.){8,255}+\Z')

        self.given(b'''
            word_ends_with_s
                word_ends_with_s = <@>
                    |wordchars|
                            <s|

                    wordchars = @1.. of wordchar
                    s = 's'
        ''',
        expect_regex=b'\w++(?<=s)')

        self.given(b'''
            un_x_able
                un_x_able = <@>
                    |un>
                    |unxable|
                       <able|

                    un = 'un'
                    unxable = @1.. of wordchar
                    able = 'able'
        ''',
        expect_regex=b'(?=un)\w++(?<=able)')

        self.given(b'''
            escape
                escape = <@>
                    <backslash|
                              |any|
        ''',
        expect_regex=br'(?<=\\)(?s:.)')

        self.given(b'''
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
        expect_regex=b'(?<=\$)(?P<digits>\d++)|(?P<digits>\d++)(?= buck)')

        self.given(b'''
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
        expect_regex=br'\bBEGIN\b(?:[^E]++|\bE(?!ND\b))++\bEND\b')


    def test_non_op_output(self):
        self.given(b'''
            /non-alpha/non-digit/non-whitechar/non-wordchar/non-WOB/
        ''',
        expect_regex=br'[^a-zA-Z]\D\S\W\B')

        self.given(b'''
            non_digits
                non_digits = @1.. of non-digit
        ''',
        expect_regex=br'\D++')

        self.given(b'''
            non-alphabetic
                alphabetic: /Alphabetic
        ''',
        expect_regex=b'\P{Alphabetic}')

        self.given(b'''
            non-minus
                minus: -
        ''',
        expect_regex=br'[^\-]')

        self.given(b'''
            non-caret
                caret: ^
        ''',
        expect_regex=br'[^\^]')

        self.given(b'''
            /non-non_alpha/non-non_digit/
                non_alpha = non-alpha
                non_digit = non-digit
        ''',
        expect_regex=br'[a-zA-Z]\d')

        self.given(b'''
            non-consonant
                consonant: alpha not vowel
                    vowel: a i u e o A I U E O
        ''',
        expect_regex=br'[^a-zA-Z--aiueoAIUEO]')

        self.given(b'''
            /lower/non-lower/non_lower/non-non_lower/nonnon_lower/non-nonnon_lower/
                non_lower: not: lower
                nonnon_lower: not: non_lower
        ''',
        expect_regex=br'[a-z][^a-z][^a-z][a-z][a-z][^a-z]')

        self.given(b'''
            /digit/non-digit/non_digit/non-non_digit/nonnon_digit/non-nonnon_digit/
                non_digit: not: digit
                nonnon_digit: not: non_digit
        ''',
        expect_regex=br'\d\D\D\d\d\D')

        self.given(b'''
            /ex/non-ex/non_ex/non-non_ex/nonnon_ex/non-nonnon_ex/
                ex: X
                non_ex: not: ex
                nonnon_ex: not: non_ex
        ''',
        expect_regex=br'X[^X][^X]XX[^X]')

        self.given(b'''
            /minus/non-minus/non_minus/non-non_minus/nonnon_minus/non-nonnon_minus/
                minus: -
                non_minus: not: minus
                nonnon_minus: not: non_minus
        ''',
        expect_regex=br'-[^\-][^\-]--[^\-]')

        self.given(b'''
            /plus/non-plus/non_plus/non-non_plus/nonnon_plus/non-nonnon_plus/
                plus: +
                non_plus: not: plus
                nonnon_plus: not: non_plus
        ''',
        expect_regex=br'\+[^+][^+]\+\+[^+]')

        self.given(b'''
            /caret/non-caret/non_caret/non-non_caret/nonnon_caret/non-nonnon_caret/
                caret: ^
                non_caret: not: caret
                nonnon_caret: not: non_caret
        ''',
        expect_regex=br'\^[^\^][^\^]\^\^[^\^]')


    def test_recursion_output(self):
        self.given(b'''
            singularity
                singularity = singularity
        ''',
        expect_regex=b'(?P<singularity>(?&singularity))')

        self.given(b'''
            ./palindrome/.
                palindrome = <<|
                               |/letter/palindrome/=letter/
                               |/letter/=letter/
                               |letter

                    [letter]: alpha
        ''',
        expect_regex=b'\A(?P<palindrome>(?P<letter>[a-zA-Z])(?&palindrome)(?P=letter)|(?P<letter>[a-zA-Z])(?P=letter)|(?P<letter>[a-zA-Z]))\Z')

        self.given(b'''
            csv
                csv = /value?/more_values?/
                    value = @1.. of non-separator
*)                      separator: ,
                    more_values = /separator/value?/more_values?/
        ''',
        expect_regex=b'[^,]*+(?P<more_values>,[^,]*+(?&more_values)?)?')

        self.given(b'''
            text_in_parens
                text_in_parens = /open/text/close/
                    open: (
                    close: )
                    text = @1.. of <<|
                                     |non-open
                                     |non-close
                                     |text_in_parens
        ''',
        expect_regex=b'(?P<text_in_parens>\((?:[^(]|[^)]|(?&text_in_parens))++\))')


    def test_anchor_sugar_output(self):
        self.given(b'''
            //wordchar/
        ''',
        expect_regex=br'(?m:^)\w')

        self.given(b'''
            /wordchar//
        ''',
        expect_regex=br'\w(?m:$)')

        self.given(b'''
            //wordchar//
        ''',
        expect_regex=br'(?m:^)\w(?m:$)')

        self.given(b'''
            ./wordchar/
        ''',
        expect_regex=br'\A\w')

        self.given(b'''
            /wordchar/.
        ''',
        expect_regex=br'\w\Z')

        self.given(b'''
            ./wordchar/.
        ''',
        expect_regex=br'\A\w\Z')

        self.given(b'''
            ./wordchar//
        ''',
        expect_regex=br'\A\w(?m:$)')

        self.given(b'''
            //wordchar/.
        ''',
        expect_regex=br'(?m:^)\w\Z')

        self.given(b'''
            @//wordchar/
        ''',
        expect_regex=br'(?>(?m:^)\w)')

        self.given(b'''
            @./wordchar/
        ''',
        expect_regex=br'(?>\A\w)')

        self.given(b'''
            @//wordchar//
        ''',
        expect_regex=br'(?>(?m:^)\w(?m:$))')

        self.given(b'''
            @./wordchar//
        ''',
        expect_regex=br'(?>\A\w(?m:$))')

        self.given(b'''
            @//wordchar/.
        ''',
        expect_regex=br'(?>(?m:^)\w\Z)')

        self.given(b'''
            @./wordchar/.
        ''',
        expect_regex=br'(?>\A\w\Z)')

        self.given(b'''
            ./wordchar/digit//
        ''',
        expect_regex=br'\A\w\d(?m:$)')

        self.given(b'''
            @//wordchar/digit/.
        ''',
        expect_regex=br'(?>(?m:^)\w\d\Z)')

        self.given(b'''
            //wordchar/digit//
        ''',
        expect_regex=br'(?m:^)\w\d(?m:$)')

        self.given(b'''
            @./wordchar/digit/.
        ''',
        expect_regex=br'(?>\A\w\d\Z)')

        self.given(b'''
            <<|
              |./wordchar//
              |//wordchar/.
        ''',
        expect_regex=br'\A\w(?m:$)|(?m:^)\w\Z')

        self.given(b'''
            (multiline)
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
        expect_regex=br'(?V1wm)(?=\A\w$)(?=\A\w\Z)(?=^\w$)(?=\A\w$)\A\w\Z^\w$^\w\Z\A\w$(?<=\A\w\Z)(?<=^\w\Z)(?<=(?>^\w$))(?<=(?>\A\w$))')


    def test_fail_output(self):
        self.given(b'''
            FAIL!
        ''',
        expect_regex=b'(?!)')

        self.given(b'''
            /FAIL!/
        ''',
        expect_regex=b'(?!)')

        self.given(b'''
            /alpha/FAIL!/
        ''',
        expect_regex=b'[a-zA-Z](?!)')

        self.given(b'''
            2 of FAIL!
        ''',
        expect_regex=b'(?!){2}')

        self.given(b'''
            <<|
              |FAIL!
        ''',
        expect_regex=b'(?!)')

        self.given(b'''
            <<|
              |FAIL!
              |alpha
        ''',
        expect_regex=b'(?!)|[a-zA-Z]')

        self.given(b'''
            <<|
              |alpha
              |FAIL!
        ''',
        expect_regex=b'[a-zA-Z]|(?!)')

        self.given(b'''
            /opener?/contents?/closer/
                opener = <<|
                           |paren
                           |curly
                           |square
                           |chevron
                
                    [paren]: (
                    [curly]: {
                    [square]: [
                    [chevron]: <
                    
                contents = 1.. <<- of any
                
                closer = <<|
                           |[paren] ? 1 of: )
                           |[curly] ? 1 of: }
                           |[square] ? 1 of: ]
                           |[chevron] ? 1 of: >
                           |FAIL!
        ''',
        expect_regex=b'(?:(?P<paren>\()|(?P<curly>\{)|(?P<square>\[)|(?P<chevron><))?(?s:.)*(?(paren)\)|(?(curly)\}|(?(square)\]|(?(chevron)>|(?!)))))')

        self.given(b'''
            <@>
             |FAIL!>
        ''',
        expect_regex=b'(?=(?!))')

        self.given(b'''
            <@>
             |!FAIL!>
        ''',
        expect_regex=b'(?!(?!))')


    def test_numrange_shortcut_output(self):
        self.given(u'''
            '0'..'1'
        ''',
        expect_regex=br'[01](?!\d)')

        self.given(u'''
            '0'..'2'
        ''',
        expect_regex=br'[0-2](?!\d)')

        self.given(u'''
            '0'..'9'
        ''',
        expect_regex=br'\d(?!\d)')

        self.given(u'''
            '1'..'2'
        ''',
        expect_regex=br'[12](?!\d)')

        self.given(u'''
            '1'..'9'
        ''',
        expect_regex=br'[1-9](?!\d)')

        self.given(u'''
            '2'..'9'
        ''',
        expect_regex=br'[2-9](?!\d)')

        self.given(u'''
            '8'..'9'
        ''',
        expect_regex=br'[89](?!\d)')

        self.given(u'''
            '0'..'10'
        ''',
        expect_regex=br'(?>10|\d)(?!\d)')

        self.given(u'''
            '1'..'10'
        ''',
        expect_regex=br'(?>10|[1-9])(?!\d)')

        self.given(u'''
            '2'..'10'
        ''',
        expect_regex=br'(?>10|[2-9])(?!\d)')

        self.given(u'''
            '8'..'10'
        ''',
        expect_regex=br'(?>10|[89])(?!\d)')

        self.given(u'''
            '9'..'10'
        ''',
        expect_regex=br'(?>10|9)(?!\d)')

        self.given(u'''
            '0'..'11'
        ''',
        expect_regex=br'(?>1[01]|\d)(?!\d)')

        self.given(u'''
            '1'..'11'
        ''',
        expect_regex=br'(?>1[01]|[1-9])(?!\d)')

        self.given(u'''
            '9'..'11'
        ''',
        expect_regex=br'(?>1[01]|9)(?!\d)')

        self.given(u'''
            '10'..'11'
        ''',
        expect_regex=br'1[01](?!\d)')

        self.given(u'''
            '0'..'12'
        ''',
        expect_regex=br'(?>1[0-2]|\d)(?!\d)')

        self.given(u'''
            '1'..'12'
        ''',
        expect_regex=br'(?>1[0-2]|[1-9])(?!\d)')

        self.given(u'''
            '2'..'12'
        ''',
        expect_regex=br'(?>1[0-2]|[2-9])(?!\d)')

        self.given(u'''
            '0'..'19'
        ''',
        expect_regex=br'(?>1\d|\d)(?!\d)')

        self.given(u'''
            '1'..'19'
        ''',
        expect_regex=br'(?>1\d|[1-9])(?!\d)')

        self.given(u'''
            '9'..'19'
        ''',
        expect_regex=br'(?>1\d|9)(?!\d)')

        self.given(u'''
            '10'..'19'
        ''',
        expect_regex=br'1\d(?!\d)')

        self.given(u'''
            '0'..'20'
        ''',
        expect_regex=br'(?>20|1\d|\d)(?!\d)')

        self.given(u'''
            '2'..'20'
        ''',
        expect_regex=br'(?>20|1\d|[2-9])(?!\d)')

        self.given(u'''
            '10'..'20'
        ''',
        expect_regex=br'(?>20|1\d)(?!\d)')

        self.given(u'''
            '19'..'20'
        ''',
        expect_regex=br'(?>20|19)(?!\d)')

        self.given(u'''
            '0'..'29'
        ''',
        expect_regex=br'(?>[12]\d|\d)(?!\d)')

        self.given(u'''
            '2'..'29'
        ''',
        expect_regex=br'(?>[12]\d|[2-9])(?!\d)')

        self.given(u'''
            '9'..'29'
        ''',
        expect_regex=br'(?>[12]\d|9)(?!\d)')

        self.given(u'''
            '2'..'42'
        ''',
        expect_regex=br'(?>4[0-2]|[1-3]\d|[2-9])(?!\d)')

        self.given(u'''
            '12'..'42'
        ''',
        expect_regex=br'(?>4[0-2]|[23]\d|1[2-9])(?!\d)')

        self.given(u'''
            '24'..'42'
        ''',
        expect_regex=br'(?>4[0-2]|3\d|2[4-9])(?!\d)')

        self.given(u'''
            '38'..'42'
        ''',
        expect_regex=br'(?>4[0-2]|3[89])(?!\d)')

        self.given(u'''
            '0'..'90'
        ''',
        expect_regex=br'(?>90|[1-8]\d|\d)(?!\d)')

        self.given(u'''
            '9'..'90'
        ''',
        expect_regex=br'(?>90|[1-8]\d|9)(?!\d)')

        self.given(u'''
            '10'..'90'
        ''',
        expect_regex=br'(?>90|[1-8]\d)(?!\d)')

        self.given(u'''
            '0'..'98'
        ''',
        expect_regex=br'(?>9[0-8]|[1-8]\d|\d)(?!\d)')

        self.given(u'''
            '1'..'98'
        ''',
        expect_regex=br'(?>9[0-8]|[1-8]\d|[1-9])(?!\d)')

        self.given(u'''
            '0'..'99'
        ''',
        expect_regex=br'(?>[1-9]\d?+|0)(?!\d)')

        self.given(u'''
            '1'..'99'
        ''',
        expect_regex=br'[1-9]\d?+(?!\d)')

        self.given(u'''
            '2'..'99'
        ''',
        expect_regex=br'(?>[1-9]\d|[2-9])(?!\d)')

        self.given(u'''
            '9'..'99'
        ''',
        expect_regex=br'(?>[1-9]\d|9)(?!\d)')

        self.given(u'''
            '10'..'99'
        ''',
        expect_regex=br'[1-9]\d(?!\d)')

        self.given(u'''
            '11'..'99'
        ''',
        expect_regex=br'(?>[2-9]\d|1[1-9])(?!\d)')

        self.given(u'''
            '19'..'99'
        ''',
        expect_regex=br'(?>[2-9]\d|19)(?!\d)')

        self.given(u'''
            '20'..'99'
        ''',
        expect_regex=br'[2-9]\d(?!\d)')

        self.given(u'''
            '29'..'99'
        ''',
        expect_regex=br'(?>[3-9]\d|29)(?!\d)')

        self.given(u'''
            '46'..'99'
        ''',
        expect_regex=br'(?>[5-9]\d|4[6-9])(?!\d)')

        self.given(u'''
            '80'..'99'
        ''',
        expect_regex=br'[89]\d(?!\d)')

        self.given(u'''
            '89'..'99'
        ''',
        expect_regex=br'(?>9\d|89)(?!\d)')

        self.given(u'''
            '90'..'99'
        ''',
        expect_regex=br'9\d(?!\d)')

        self.given(u'''
            '0'..'100'
        ''',
        expect_regex=br'(?>100|[1-9]\d?+|0)(?!\d)')

        self.given(u'''
            '10'..'100'
        ''',
        expect_regex=br'(?>100|[1-9]\d)(?!\d)')

        self.given(u'''
            '90'..'100'
        ''',
        expect_regex=br'(?>100|9\d)(?!\d)')

        self.given(u'''
            '99'..'100'
        ''',
        expect_regex=br'(?>100|99)(?!\d)')

        self.given(u'''
            '1'..'101'
        ''',
        expect_regex=br'(?>10[01]|[1-9]\d?+)(?!\d)')

        self.given(u'''
            '99'..'101'
        ''',
        expect_regex=br'(?>10[01]|99)(?!\d)')

        self.given(u'''
            '100'..'101'
        ''',
        expect_regex=br'10[01](?!\d)')

        self.given(u'''
            '1'..'109'
        ''',
        expect_regex=br'(?>10\d|[1-9]\d?+)(?!\d)')

        self.given(u'''
            '9'..'109'
        ''',
        expect_regex=br'(?>10\d|[1-9]\d|9)(?!\d)')

        self.given(u'''
            '10'..'109'
        ''',
        expect_regex=br'(?>10\d|[1-9]\d)(?!\d)')

        self.given(u'''
            '99'..'109'
        ''',
        expect_regex=br'(?>10\d|99)(?!\d)')

        self.given(u'''
            '100'..'109'
        ''',
        expect_regex=br'10\d(?!\d)')

        self.given(u'''
            '1'..'110'
        ''',
        expect_regex=br'(?>1(?>10|0\d)|[1-9]\d?+)(?!\d)')

        self.given(u'''
            '10'..'110'
        ''',
        expect_regex=br'(?>1(?>10|0\d)|[1-9]\d)(?!\d)')

        self.given(u'''
            '11'..'110'
        ''',
        expect_regex=br'(?>1(?>10|0\d)|[2-9]\d|1[1-9])(?!\d)')

        self.given(u'''
            '100'..'110'
        ''',
        expect_regex=br'1(?>10|0\d)(?!\d)')

        self.given(u'''
            '1'..'111'
        ''',
        expect_regex=br'(?>1(?>1[01]|0\d)|[1-9]\d?+)(?!\d)')

        self.given(u'''
            '11'..'111'
        ''',
        expect_regex=br'(?>1(?>1[01]|0\d)|[2-9]\d|1[1-9])(?!\d)')
        
        self.given(u'''
            '1'..'119'
        ''',
        expect_regex=br'(?>1[01]\d|[1-9]\d?+)(?!\d)')

        self.given(u'''
            '11'..'119'
        ''',
        expect_regex=br'(?>1[01]\d|[2-9]\d|1[1-9])(?!\d)')

        self.given(u'''
            '19'..'119'
        ''',
        expect_regex=br'(?>1[01]\d|[2-9]\d|19)(?!\d)')

        self.given(u'''
            '1'..'123'
        ''',
        expect_regex=br'(?>1(?>2[0-3]|[01]\d)|[1-9]\d?+)(?!\d)')

        self.given(u'''
            '12'..'123'
        ''',
        expect_regex=br'(?>1(?>2[0-3]|[01]\d)|[2-9]\d|1[2-9])(?!\d)')

        self.given(u'''
            '23'..'123'
        ''',
        expect_regex=br'(?>1(?>2[0-3]|[01]\d)|[3-9]\d|2[3-9])(?!\d)')

        self.given(u'''
            '1'..'199'
        ''',
        expect_regex=br'(?>1\d{2}|[1-9]\d?+)(?!\d)')

        self.given(u'''
            '10'..'199'
        ''',
        expect_regex=br'(?>1\d{2}|[1-9]\d)(?!\d)')

        self.given(u'''
            '19'..'199'
        ''',
        expect_regex=br'(?>1\d{2}|[2-9]\d|19)(?!\d)')

        self.given(u'''
            '99'..'199'
        ''',
        expect_regex=br'(?>1\d{2}|99)(?!\d)')

        self.given(u'''
            '100'..'199'
        ''',
        expect_regex=br'1\d{2}(?!\d)')

        self.given(u'''
            '109'..'199'
        ''',
        expect_regex=br'1(?>[1-9]\d|09)(?!\d)')

        self.given(u'''
            '110'..'199'
        ''',
        expect_regex=br'1[1-9]\d(?!\d)')

        self.given(u'''
            '190'..'199'
        ''',
        expect_regex=br'19\d(?!\d)')

        self.given(u'''
            '1'..'200'
        ''',
        expect_regex=br'(?>200|1\d{2}|[1-9]\d?+)(?!\d)')

        self.given(u'''
            '20'..'200'
        ''',
        expect_regex=br'(?>200|1\d{2}|[2-9]\d)(?!\d)')

        self.given(u'''
            '100'..'200'
        ''',
        expect_regex=br'(?>200|1\d{2})(?!\d)')

        self.given(u'''
            '199'..'200'
        ''',
        expect_regex=br'(?>200|199)(?!\d)')

        self.given(u'''
            '1'..'201'
        ''',
        expect_regex=br'(?>20[01]|1\d{2}|[1-9]\d?+)(?!\d)')

        self.given(u'''
            '199'..'201'
        ''',
        expect_regex=br'(?>20[01]|199)(?!\d)')

        self.given(u'''
            '200'..'201'
        ''',
        expect_regex=br'20[01](?!\d)')

        self.given(u'''
            '1'..'299'
        ''',
        expect_regex=br'(?>[12]\d{2}|[1-9]\d?+)(?!\d)')

        self.given(u'''
            '100'..'299'
        ''',
        expect_regex=br'[12]\d{2}(?!\d)')

        self.given(u'''
            '199'..'299'
        ''',
        expect_regex=br'(?>2\d{2}|199)(?!\d)')

        self.given(u'''
            '200'..'299'
        ''',
        expect_regex=br'2\d{2}(?!\d)')

        self.given(u'''
            '290'..'299'
        ''',
        expect_regex=br'29\d(?!\d)')

        self.given(u'''
            '1'..'300'
        ''',
        expect_regex=br'(?>300|[12]\d{2}|[1-9]\d?+)(?!\d)')

        self.given(u'''
            '1'..'399'
        ''',
        expect_regex=br'(?>[1-3]\d{2}|[1-9]\d?+)(?!\d)')

        self.given(u'''
            '123'..'456'
        ''',
        expect_regex=br'(?>4(?>5[0-6]|[0-4]\d)|[23]\d{2}|1(?>[3-9]\d|2[3-9]))(?!\d)')

        self.given(u'''
            '1'..'901'
        ''',
        expect_regex=br'(?>90[01]|[1-8]\d{2}|[1-9]\d?+)(?!\d)')

        self.given(u'''
            '0'..'999'
        ''',
        expect_regex=br'(?>[1-9]\d{,2}+|0)(?!\d)')

        self.given(u'''
            '1'..'999'
        ''',
        expect_regex=br'[1-9]\d{,2}+(?!\d)')

        self.given(u'''
            '9'..'999'
        ''',
        expect_regex=br'(?>[1-9]\d{1,2}+|9)(?!\d)')

        self.given(u'''
            '10'..'999'
        ''',
        expect_regex=br'[1-9]\d{1,2}+(?!\d)')

        self.given(u'''
            '99'..'999'
        ''',
        expect_regex=br'(?>[1-9]\d{2}|99)(?!\d)')

        self.given(u'''
            '100'..'999'
        ''',
        expect_regex=br'[1-9]\d{2}(?!\d)')

        self.given(u'''
            '900'..'999'
        ''',
        expect_regex=br'9\d{2}(?!\d)')

        self.given(u'''
            '0'..'1000'
        ''',
        expect_regex=br'(?>1000|[1-9]\d{,2}+|0)(?!\d)')

        self.given(u'''
            '1'..'1000'
        ''',
        expect_regex=br'(?>1000|[1-9]\d{,2}+)(?!\d)')

        self.given(u'''
            '10'..'1000'
        ''',
        expect_regex=br'(?>1000|[1-9]\d{1,2}+)(?!\d)')

        self.given(u'''
            '100'..'1000'
        ''',
        expect_regex=br'(?>1000|[1-9]\d{2})(?!\d)')

        self.given(u'''
            '999'..'1000'
        ''',
        expect_regex=br'(?>1000|999)(?!\d)')

        self.given(u'''
            '1'..'1001'
        ''',
        expect_regex=br'(?>100[01]|[1-9]\d{,2}+)(?!\d)')

        self.given(u'''
            '11'..'1001'
        ''',
        expect_regex=br'(?>100[01]|[1-9]\d{2}|[2-9]\d|1[1-9])(?!\d)')

        self.given(u'''
            '101'..'1001'
        ''',
        expect_regex=br'(?>100[01]|[2-9]\d{2}|1(?>[1-9]\d|0[1-9]))(?!\d)')

        self.given(u'''
            '998'..'1001'
        ''',
        expect_regex=br'(?>100[01]|99[89])(?!\d)')

        self.given(u'''
            '1000'..'1001'
        ''',
        expect_regex=br'100[01](?!\d)')

        self.given(u'''
            '1000'..'1099'
        ''',
        expect_regex=br'10\d{2}(?!\d)')

        self.given(u'''
            '1'..'1999'
        ''',
        expect_regex=br'(?>1\d{3}|[1-9]\d{,2}+)(?!\d)')

        self.given(u'''
            '10'..'1999'
        ''',
        expect_regex=br'(?>1\d{3}|[1-9]\d{1,2}+)(?!\d)')

        self.given(u'''
            '100'..'1999'
        ''',
        expect_regex=br'(?>1\d{3}|[1-9]\d{2})(?!\d)')

        self.given(u'''
            '999'..'1999'
        ''',
        expect_regex=br'(?>1\d{3}|999)(?!\d)')

        self.given(u'''
            '1000'..'1999'
        ''',
        expect_regex=br'1\d{3}(?!\d)')

        self.given(u'''
            '1000'..'2000'
        ''',
        expect_regex=br'(?>2000|1\d{3})(?!\d)')

        self.given(u'''
            '1999'..'2000'
        ''',
        expect_regex=br'(?>2000|1999)(?!\d)')

        self.given(u'''
            '1998'..'2001'
        ''',
        expect_regex=br'(?>200[01]|199[89])(?!\d)')

        self.given(u'''
            '999'..'2999'
        ''',
        expect_regex=br'(?>[12]\d{3}|999)(?!\d)')

        self.given(u'''
            '1999'..'2999'
        ''',
        expect_regex=br'(?>2\d{3}|1999)(?!\d)')

        self.given(u'''
            '0'..'9999'
        ''',
        expect_regex=br'(?>[1-9]\d{,3}+|0)(?!\d)')

        self.given(u'''
            '1'..'9999'
        ''',
        expect_regex=br'[1-9]\d{,3}+(?!\d)')

        self.given(u'''
            '10'..'9999'
        ''',
        expect_regex=br'[1-9]\d{1,3}+(?!\d)')

        self.given(u'''
            '99'..'9999'
        ''',
        expect_regex=br'(?>[1-9]\d{2,3}+|99)(?!\d)')

        self.given(u'''
            '100'..'9999'
        ''',
        expect_regex=br'[1-9]\d{2,3}+(?!\d)')

        self.given(u'''
            '999'..'9999'
        ''',
        expect_regex=br'(?>[1-9]\d{3}|999)(?!\d)')

        self.given(u'''
            '1000'..'9999'
        ''',
        expect_regex=br'[1-9]\d{3}(?!\d)')

        self.given(u'''
            '1999'..'9999'
        ''',
        expect_regex=br'(?>[2-9]\d{3}|1999)(?!\d)')

        self.given(u'''
            '2999'..'9999'
        ''',
        expect_regex=br'(?>[3-9]\d{3}|2999)(?!\d)')

        self.given(u'''
            '7999'..'9999'
        ''',
        expect_regex=br'(?>[89]\d{3}|7999)(?!\d)')

        self.given(u'''
            '8999'..'9999'
        ''',
        expect_regex=br'(?>9\d{3}|8999)(?!\d)')

        self.given(u'''
            '9000'..'9999'
        ''',
        expect_regex=br'9\d{3}(?!\d)')

        self.given(u'''
            '0'..'10000'
        ''',
        expect_regex=br'(?>10000|[1-9]\d{,3}+|0)(?!\d)')

        self.given(u'''
            '1'..'10000'
        ''',
        expect_regex=br'(?>10000|[1-9]\d{,3}+)(?!\d)')

        self.given(u'''
            '10'..'10000'
        ''',
        expect_regex=br'(?>10000|[1-9]\d{1,3}+)(?!\d)')

        self.given(u'''
            '100'..'10000'
        ''',
        expect_regex=br'(?>10000|[1-9]\d{2,3}+)(?!\d)')

        self.given(u'''
            '1000'..'10000'
        ''',
        expect_regex=br'(?>10000|[1-9]\d{3})(?!\d)')

        self.given(u'''
            '9000'..'10000'
        ''',
        expect_regex=br'(?>10000|9\d{3})(?!\d)')

        self.given(u'''
            '9999'..'10000'
        ''',
        expect_regex=br'(?>10000|9999)(?!\d)')

        self.given(u'''
            '9999'..'10001'
        ''',
        expect_regex=br'(?>1000[01]|9999)(?!\d)')

        self.given(u'''
            '10000'..'10001'
        ''',
        expect_regex=br'1000[01](?!\d)')


    def test_00numrange_shortcut_output(self):
        self.given(u'''
            '00'..'01'
        ''',
        expect_regex=br'0[01](?!\d)')
        
        self.given(u'''
            '000'..'001'
        ''',
        expect_regex=br'00[01](?!\d)')
        
        self.given(u'''
            '00'..'02'
        ''',
        expect_regex=br'0[0-2](?!\d)')

        self.given(u'''
            '00'..'09'
        ''',
        expect_regex=br'0\d(?!\d)')

        self.given(u'''
            '01'..'02'
        ''',
        expect_regex=br'0[12](?!\d)')

        self.given(u'''
            '01'..'09'
        ''',
        expect_regex=br'0[1-9](?!\d)')

        self.given(u'''
            '02'..'09'
        ''',
        expect_regex=br'0[2-9](?!\d)')

        self.given(u'''
            '08'..'09'
        ''',
        expect_regex=br'0[89](?!\d)')

        self.given(u'''
            '00'..'10'
        ''',
        expect_regex=br'(?>10|0\d)(?!\d)')

        self.given(u'''
            '01'..'10'
        ''',
        expect_regex=br'(?>10|0[1-9])(?!\d)')

        self.given(u'''
            '001'..'010'
        ''',
        expect_regex=br'0(?>10|0[1-9])(?!\d)')

        self.given(u'''
            '02'..'10'
        ''',
        expect_regex=br'(?>10|0[2-9])(?!\d)')

        self.given(u'''
            '08'..'10'
        ''',
        expect_regex=br'(?>10|0[89])(?!\d)')

        self.given(u'''
            '09'..'10'
        ''',
        expect_regex=br'(?>10|09)(?!\d)')

        self.given(u'''
            '00'..'11'
        ''',
        expect_regex=br'(?>1[01]|0\d)(?!\d)')

        self.given(u'''
            '01'..'11'
        ''',
        expect_regex=br'(?>1[01]|0[1-9])(?!\d)')

        self.given(u'''
            '09'..'11'
        ''',
        expect_regex=br'(?>1[01]|09)(?!\d)')

        self.given(u'''
            '010'..'011'
        ''',
        expect_regex=br'01[01](?!\d)')

        self.given(u'''
            '01'..'12'
        ''',
        expect_regex=br'(?>1[0-2]|0[1-9])(?!\d)')

        self.given(u'''
            '000'..'012'
        ''',
        expect_regex=br'0(?>1[0-2]|0\d)(?!\d)')
        
        self.given(u'''
            '02'..'12'
        ''',
        expect_regex=br'(?>1[0-2]|0[2-9])(?!\d)')

        self.given(u'''
            '00'..'19'
        ''',
        expect_regex=br'[01]\d(?!\d)')

        self.given(u'''
            '01'..'19'
        ''',
        expect_regex=br'(?>1\d|0[1-9])(?!\d)')

        self.given(u'''
            '09'..'19'
        ''',
        expect_regex=br'(?>1\d|09)(?!\d)')

        self.given(u'''
            '010'..'019'
        ''',
        expect_regex=br'01\d(?!\d)')

        self.given(u'''
            '00'..'20'
        ''',
        expect_regex=br'(?>20|[01]\d)(?!\d)')

        self.given(u'''
            '02'..'20'
        ''',
        expect_regex=br'(?>20|1\d|0[2-9])(?!\d)')

        self.given(u'''
            '010'..'020'
        ''',
        expect_regex=br'0(?>20|1\d)(?!\d)')

        self.given(u'''
            '019'..'020'
        ''',
        expect_regex=br'0(?>20|19)(?!\d)')


    def test_oonumrange_shortcut_output(self):
        self.given(u'''
            'o0'..'o1'
        ''',
        expect_regex=br'0?[01](?!\d)')
        
        self.given(u'''
            'oo0'..'oo1'
        ''',
        expect_regex=br'0{,2}[01](?!\d)')
        
        self.given(u'''
            'o0'..'o2'
        ''',
        expect_regex=br'0?[0-2](?!\d)')

        self.given(u'''
            'o0'..'o9'
        ''',
        expect_regex=br'0?\d(?!\d)')

        self.given(u'''
            'o1'..'o2'
        ''',
        expect_regex=br'0?+[12](?!\d)')

        self.given(u'''
            'o1'..'o9'
        ''',
        expect_regex=br'0?+[1-9](?!\d)')

        self.given(u'''
            'o2'..'o9'
        ''',
        expect_regex=br'0?+[2-9](?!\d)')

        self.given(u'''
            'o8'..'o9'
        ''',
        expect_regex=br'0?+[89](?!\d)')

        self.given(u'''
            'o0'..'10'
        ''',
        expect_regex=br'(?>10|0?\d)(?!\d)')

        self.given(u'''
            'o1'..'10'
        ''',
        expect_regex=br'(?>10|0?+[1-9])(?!\d)')

        self.given(u'''
            'oo1'..'o10'
        ''',
        expect_regex=br'(?>0?+10|0{,2}+[1-9])(?!\d)')

        self.given(u'''
            'o2'..'10'
        ''',
        expect_regex=br'(?>10|0?+[2-9])(?!\d)')

        self.given(u'''
            'o8'..'10'
        ''',
        expect_regex=br'(?>10|0?+[89])(?!\d)')

        self.given(u'''
            'o9'..'10'
        ''',
        expect_regex=br'(?>10|0?+9)(?!\d)')

        self.given(u'''
            'o0'..'11'
        ''',
        expect_regex=br'(?>1[01]|0?\d)(?!\d)')

        self.given(u'''
            'o1'..'11'
        ''',
        expect_regex=br'(?>1[01]|0?+[1-9])(?!\d)')

        self.given(u'''
            'o9'..'11'
        ''',
        expect_regex=br'(?>1[01]|0?+9)(?!\d)')

        self.given(u'''
            'o10'..'o11'
        ''',
        expect_regex=br'0?+1[01](?!\d)')

        self.given(u'''
            'o1'..'12'
        ''',
        expect_regex=br'(?>1[0-2]|0?+[1-9])(?!\d)')

        self.given(u'''
            'oo0'..'o12'
        ''',
        expect_regex=br'(?>0?1[0-2]|0{,2}\d)(?!\d)')
        
        self.given(u'''
            'o2'..'12'
        ''',
        expect_regex=br'(?>1[0-2]|0?+[2-9])(?!\d)')

        self.given(u'''
            'o0'..'19'
        ''',
        expect_regex=br'(?>1\d|0?\d)(?!\d)')

        self.given(u'''
            'o1'..'19'
        ''',
        expect_regex=br'(?>1\d|0?+[1-9])(?!\d)')

        self.given(u'''
            'o9'..'19'
        ''',
        expect_regex=br'(?>1\d|0?+9)(?!\d)')

        self.given(u'''
            'o10'..'o19'
        ''',
        expect_regex=br'0?+1\d(?!\d)')

        self.given(u'''
            'o0'..'20'
        ''',
        expect_regex=br'(?>20|1\d|0?\d)(?!\d)')

        self.given(u'''
            'o2'..'20'
        ''',
        expect_regex=br'(?>20|1\d|0?+[2-9])(?!\d)')

        self.given(u'''
            'o10'..'o20'
        ''',
        expect_regex=br'0?+(?>20|1\d)(?!\d)')

        self.given(u'''
            'o19'..'o20'
        ''',
        expect_regex=br'0?+(?>20|19)(?!\d)')


    def test_norange_shortcut_output(self):
        self.given(u'''
            '0'..'0'
        ''',
        expect_regex=br'0(?!\d)')

        self.given(u'''
            '00'..'00'
        ''',
        expect_regex=br'00(?!\d)')

        self.given(u'''
            '000'..'000'
        ''',
        expect_regex=br'000(?!\d)')

        self.given(u'''
            '1'..'1'
        ''',
        expect_regex=br'1(?!\d)')

        self.given(u'''
            '2'..'2'
        ''',
        expect_regex=br'2(?!\d)')

        self.given(u'''
            '9'..'9'
        ''',
        expect_regex=br'9(?!\d)')

        self.given(u'''
            '10'..'10'
        ''',
        expect_regex=br'10(?!\d)')

        self.given(u'''
            '99'..'99'
        ''',
        expect_regex=br'99(?!\d)')

        self.given(u'''
            '100'..'100'
        ''',
        expect_regex=br'100(?!\d)')

        self.given(u'''
            '123'..'123'
        ''',
        expect_regex=br'123(?!\d)')

        self.given(u'''
            '12345'..'12345'
        ''',
        expect_regex=br'12345(?!\d)')

        self.given(u'''
            '9999999'..'9999999'
        ''',
        expect_regex=br'9999999(?!\d)')

        self.given(u'''
            'o0'..'o0'
        ''',
        expect_regex=br'0?0(?!\d)')

        self.given(u'''
            'oo0'..'oo0'
        ''',
        expect_regex=br'0{,2}0(?!\d)')

        self.given(u'''
            'ooo0'..'ooo0'
        ''',
        expect_regex=br'0{,3}0(?!\d)')

        self.given(u'''
            'o1'..'o1'
        ''',
        expect_regex=br'0?+1(?!\d)')

        self.given(u'''
            'oo9'..'oo9'
        ''',
        expect_regex=br'0{,2}+9(?!\d)')

        self.given(u'''
            'o10'..'o10'
        ''',
        expect_regex=br'0?+10(?!\d)')

        self.given(u'''
            'oo100'..'oo100'
        ''',
        expect_regex=br'0{,2}+100(?!\d)')

        self.given(u'''
            'o9999'..'o9999'
        ''',
        expect_regex=br'0?+9999(?!\d)')

        self.given(u'''
            'ooo9999'..'ooo9999'
        ''',
        expect_regex=br'0{,3}+9999(?!\d)')


    def test_infinite_numrange_output(self):
        self.given(u'''
            '0'..
        ''',
        expect_regex=br'(?!0\d)\d++')

        self.given(u'''
            '1'..
        ''',
        expect_regex=br'[1-9]\d*+')

        self.given(u'''
            '2'..
        ''',
        expect_regex=br'(?>[1-9]\d++|[2-9])')

        self.given(u'''
            '10'..
        ''',
        expect_regex=br'[1-9]\d++')

        self.given(u'''
            '20'..
        ''',
        expect_regex=br'(?>[1-9]\d{2,}+|[2-9]\d)')

        self.given(u'''
            '46'..
        ''',
        expect_regex=br'(?>[1-9]\d{2,}+|[5-9]\d|4[6-9])')

        self.given(u'''
            '100'..
        ''',
        expect_regex=br'[1-9]\d{2,}+')

        self.given(u'''
            '200'..
        ''',
        expect_regex=br'(?>[1-9]\d{3,}+|[2-9]\d{2})')

        self.given(u'''
            '234'..
        ''',
        expect_regex=br'(?>[1-9]\d{3,}+|[3-9]\d{2}|2(?>[4-9]\d|3[4-9]))')

        self.given(u'''
            ? of '1'..
        ''',
        expect_regex=br'(?:[1-9]\d*+)?')

        self.given(u'''
            ? of '2'..
        ''',
        expect_regex=br'(?>[1-9]\d++|[2-9])?')


    def test_infinite_onumrange_output(self):
        self.given(u'''
            'o0'..
        ''',
        expect_regex=br'\d++')

        self.given(u'''
            'o1'..
        ''',
        expect_regex=br'0*+[1-9]\d*+')

        self.given(u'''
            'o2'..
        ''',
        expect_regex=br'0*+(?>[1-9]\d++|[2-9])')

        self.given(u'''
            'o10'..
        ''',
        expect_regex=br'0*+[1-9]\d++')

        self.given(u'''
            'o20'..
        ''',
        expect_regex=br'0*+(?>[1-9]\d{2,}+|[2-9]\d)')

        self.given(u'''
            'o46'..
        ''',
        expect_regex=br'0*+(?>[1-9]\d{2,}+|[5-9]\d|4[6-9])')

        self.given(u'''
            'o100'..
        ''',
        expect_regex=br'0*+[1-9]\d{2,}+')

        self.given(u'''
            'o200'..
        ''',
        expect_regex=br'0*+(?>[1-9]\d{3,}+|[2-9]\d{2})')

        self.given(u'''
            'o234'..
        ''',
        expect_regex=br'0*+(?>[1-9]\d{3,}+|[3-9]\d{2}|2(?>[4-9]\d|3[4-9]))')

        self.given(u'''
            amount?
                amount = 'o0'..
        ''',
        expect_regex=br'\d*+')

        self.given(u'''
            ? of 'o0'..
        ''',
        expect_regex=br'\d*+')

        self.given(u'''
            ? of 'o1'..
        ''',
        expect_regex=br'(?:0*+[1-9]\d*+)?')


    def test_numrange_optimization_output(self):
        self.given(u'''
            /xnum/x/numx/num/
                x: x
                num = '1'..'10'
                numx = /num/x/
                xnum = /x/num/
        ''',
        expect_regex=br'x(?>10|[1-9])(?!\d)x(?>10|[1-9])x(?>10|[1-9])(?!\d)')

        
    def test_wordchar_redef_output(self):
        self.given(u'''
            /wordchar/pads/WOB/pads/str/pads/non-WOB/
*)              wordchar: digit
                str = .'  '_
                pads = '  '
        ''',
        expect_regex=br'\d  (?>(?<=\d)(?!\d)|(?<!\d)(?=\d))  (?>(?<=\d)(?!\d)|(?<!\d)(?=\d))  (?>(?<=\d)(?=\d)|(?<!\d)(?!\d))  (?>(?<=\d)(?=\d)|(?<!\d)(?!\d))')
                
        self.given(u'''
            WOB
*)              wordchar = lower
        ''',
        expect_regex=br'(?>(?<=[a-z])(?![a-z])|(?<![a-z])(?=[a-z]))')
                
        self.given(u'''
            .'cat'_
*)              wordchar: upper lower -
        ''',
        expect_regex=br'(?>(?<=[A-Za-z\-])(?![A-Za-z\-])|(?<![A-Za-z\-])(?=[A-Za-z\-]))cat(?>(?<=[A-Za-z\-])(?=[A-Za-z\-])|(?<![A-Za-z\-])(?![A-Za-z\-]))')
                
        
    def test_lazydotstar_output(self):
        self.given(u'''
            __
        ''',
        expect_regex=br'.+?')
        
        self.given(u'''
            __?
        ''',
        expect_regex=br'.*?')

        self.given(u'''
            /__?/
        ''',
        expect_regex=br'.*?')

        self.given(u'''
            /__/__?/
        ''',
        expect_regex=br'.+?.*?')

        self.given(u'''
            /__?/__/
        ''',
        expect_regex=br'.*?.+?')

        self.given(u'''
            /__/alpha/
        ''',
        expect_regex=br'[^a-zA-Z]++[a-zA-Z]')

        self.given(u'''
            /alpha/__/
        ''',
        expect_regex=br'[a-zA-Z].+?')

        self.given(u'''
            /lazydotstar/alpha/
                lazydotstar = __
        ''',
        expect_regex=br'.+?[a-zA-Z]')

        self.given(u'''
            (unicode)
            /__/alpha/
        ''',
        expect_regex=br'(?V1wu)\P{Alphabetic}++\p{Alphabetic}')

        self.given(u'''
            (unicode)
            /__/non-alpha/
        ''',
        expect_regex=br'(?V1wu)\p{Alphabetic}++\P{Alphabetic}')

        self.given(u'''
            /__/non-alpha/
        ''',
        expect_regex=br'[a-zA-Z]++[^a-zA-Z]')

        self.given(u'''
            /__/digit/
        ''',
        expect_regex=br'\D++\d')

        self.given(u'''
            /__/non-digit/
        ''',
        expect_regex=br'\d++\D')

        self.given(u'''
            (unicode)
            /__/non-digit/
        ''',
        expect_regex=br'(?V1wu)\d++\D')

        self.given(u'''
            /__/limiter/
                limiter = ''
        ''',
        expect_regex=br'.+?')

        self.given(u'''
            /__/limiter/
                limiter = .''
        ''',
        expect_regex=br'.+?\b')

        self.given(u'''
            /__/limiter/
                limiter = _''
        ''',
        expect_regex=br'.+?\B')

        self.given(u'''
            /__/limiter/
                limiter = 'END'
        ''',
        expect_regex=br'(?:[^E]++|E(?!ND))++END')

        self.given(u'''
            /__/limiter/
                limiter = .'END'
        ''',
        expect_regex=br'(?:[^E]++|(?<!\b)E|E(?!ND))++\bEND')

        self.given(u'''
            /__/limiter/
                limiter = _'END'
        ''',
        expect_regex=br'(?:[^E]++|(?<!\B)E|E(?!ND))++\BEND')

        self.given(u'''
            /__/limiter/
                limiter = '.'
        ''',
        expect_regex=br'[^.]++\.')

        self.given(u'''
            /__/limiter/
                limiter = .'.'
        ''',
        expect_regex=br'(?:[^.]++|(?<!\b)\.)++\b\.')

        self.given(u'''
            /__/limiter/
                limiter = _'.'
        ''',
        expect_regex=br'(?:[^.]++|(?<!\B)\.)++\B\.')
        
        
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
        self.given(b'''
            /a?/ether/
                ether = /e/ther/
                    e = 'e'
                    ther = 'ther'
                a = 'a'
        ''',
        expect_full_match=[b'ether', b'aether'])

        self.given(b'''
            /air/man?/ship?/
                air = 'air'
                man = 'man'
                ship = 'ship'
        ''',
        expect_full_match=[b'air', b'airman', b'airship', b'airmanship'],
        no_match=[b'manship'],
        partial_match={'airma' : 'air'})

        self.given(b'''
            /ultra?/nagog/
                ultra = "ultra"
                nagog = 'nagog'
        ''',
        expect_full_match=[b'ultranagog', b'nagog'],
        no_match=[b'ultra'])

        self.given(b'''
            /cat?/fish?/
                cat  = 'cat'
                fish = 'fish'
        ''',
        expect_full_match=[b'catfish', b'cat', b'fish', b''],
        partial_match={
            'catfishing' : 'catfish', 
            'cafis' : '',
        })

        self.given(b'''
            /very?/very?/nice/
                very = 'very '
                nice = "nice"
        ''',
        expect_full_match=[b'nice', b'very nice', b'very very nice'])


    def test_escaping(self):
        self.given(b'''
            orly
                orly = "O RLY?"
        ''',
        expect_full_match=[b'O RLY?'],
        no_match=[b'O RLY', b'O RL'])

        self.given(b'''
            stars
                stars = '***'
        ''',
        expect_full_match=[b'***'],
        partial_match={'****' : '***'},
        no_match=[b'', b'*'])

        self.given(b'''
            add
                add: +plus
                    plus: +
        ''',
        expect_full_match=[b'+'],
        no_match=[b''])


    def test_character_class(self):
        self.given(b'''
            papersize
                papersize = /series/size/
                    series: A B C
                    size: 0 1 2 3 4 5 6 7 8
        ''',
        expect_full_match=[b'A3', b'A4'],
        no_match=[b'Legal', b'Folio'])

        self.given(b'''
            x
                x: \u0041 \u0042 \u0043 \u0044 \u0045
        ''',
        expect_full_match=[b'A', b'B', b'C', b'D', b'E'],
        no_match=[b'a', b'b', b'c', b'd', b'e'])

        self.given(b'''
            x
                x: :SKULL_AND_CROSSBONES :BIOHAZARD_SIGN :CANCER
        ''',
        expect_full_match=[u'☠', u'☣', u'♋'])

        self.given(b'''
            x
                x: /Letter /Number
        ''',
        expect_full_match=[b'A', b'1'],
        no_match=[b'?', b'$'])

        self.given(b'''
            x
                x: /Symbol
        ''',
        expect_full_match=[b'$'],
        no_match=[b'A', b'1'])

        # uppercase or greek
        self.given(b'''
            x
                x: /Lu /Greek
        ''',
        expect_full_match=[b'A', u'γ', u'Γ'],
        no_match=[b'a'])

        # not uppercase or not greek == not(uppercase and greek)
        self.given(b'''
            x
                x: /Uppercase_Letter /IsGreek
        ''',
        expect_full_match=[b'A', u'γ', u'Γ'],
        no_match=[b'a'])

        self.given(b'''
            /open/bs/caret/close/
                open: [
                bs: \\
                caret: ^
                close: ]
        ''',
        expect_full_match=[b'[\\^]'])

    def test_character_range(self):
        self.given(br'''
            AZ
                AZ: \x41..Z
        ''',
        expect_full_match=[b'A', b'B', b'C', b'X', b'Y', b'Z'],
        no_match=[b'a', b'x', b'z', b'1', b'0'])

        self.given(br'''
            AB
                AB: A..\u0042
        ''',
        expect_full_match=[b'A', b'B'],
        no_match=[b'a', b'b'])

        self.given(br'''
            AB
                AB: \u0041..\U00000042
        ''',
        expect_full_match=[b'A', b'B'],
        no_match=[b'a', b'b'])

        self.given(br'''
            AB
                AB: \U00000041..\x42
        ''',
        expect_full_match=[b'A', b'B'],
        no_match=[b'a', b'b'])

        self.given(br'''
            AB
                AB: \x41..\102
        ''',
        expect_full_match=[b'A', b'B'],
        no_match=[b'a', b'b'])

        self.given(br'''
            AB
                AB: \101..\N{LATIN CAPITAL LETTER B}
        ''',
        expect_full_match=[b'A', b'B'],
        no_match=[b'a', b'b'])

        self.given(b'''
            arrows
                arrows: :LEFTWARDS_ARROW..:LEFT_RIGHT_OPEN-HEADED_ARROW
        ''',
        expect_full_match=[u'←', u'→', u'⇶', u'⇿'],
        no_match=[b'>'])

        self.given(b'''
            need_escape
                need_escape: [ ^ a - z ]
        ''',
        expect_full_match=[b'[', b'^', b'a', b'-', b'z', b']'],
        no_match=[b'b', b'A'])

        self.given(b'''
            1 of: a -..\\
        ''',
        expect_full_match=[b'a', b'-', b'\\', b'.'],
        no_match=[b','])

        self.given(b'''
            1 of: [..]
        ''',
        expect_full_match=[b'[', b']'],
        no_match=[b'-'])


    def test_charclass_include(self):
        self.given(u'''
            /op/op/op/op/
                op: +add +sub +mul +div
                    add: +
                    sub: -
                    mul: * ×
                    div: / ÷ :
        ''',
        expect_full_match=[b'++++', b'+-*/', u'×÷*/'],
        no_match=[u'×××x', b'+++'])

        self.given(u'''
            binary
                binary: +bindigit
                    bindigit: 0..1
        ''',
        expect_full_match=[b'0', b'1'],
        no_match=[b'2', b'I', b''],
        partial_match={
            '0-1'  : '0',
            '0..1' : '0',
        })

        self.given(u'''
            /hex/hex/hex/
                hex: +hexdigit
                    hexdigit: 0..9 a..f A..F
        ''',
        expect_full_match=[b'AcE', b'12e', b'fff'],
        no_match=[b'WOW', b'hi!', b'...'])

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

        self.given(b'''
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
        expect_full_match=[u'ä', b'a'])

        self.given(u'''
            lowaz
                lowaz: +lowerAZ
                    lowerAZ: a..z
        ''',
        expect_full_match=[b'a', b'b', b'c', b'z'],
        no_match=[b'A', b'Z', u'ä'])

        self.given(u'''
            /hex/
                hex: +hexx +hexy +hexz
                    hexx = hexdigit
                        hexdigit: 0..9
                    hexy = hexz = hexalpha
                        hexalpha: a..f A..F
        ''',
        expect_full_match=[b'a', b'b', b'f', b'A', b'B', b'F', b'0', b'1', b'9'],
        no_match=[b'z', b'Z', u'ä', b'$'])

        self.given(u'''
            /plus/minus/pmz/
                plus: +
                minus: -
                pmz: +plus +minus z
        ''',
        expect_full_match=[b'+-+', b'+--', b'+-z'],
        no_match=[b'+-a'])

        self.given(u'''
            vowhex
                vowhex: +vowel +hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_full_match=[b'a', b'b', b'f', b'A', b'B', b'F', b'0', b'1', b'9', b'i', b'u', b'E', b'O'],
        no_match=[b'$', b'z', b'k'])

        self.given(u'''
            1 of: . , ;
        ''',
        expect_full_match=[b'.', b',', b';'])


    def test_charclass_operation(self):
        self.given(u'''
            xb123
                xb123: X x +hex  not  c..f C..D :LATIN_CAPITAL_LETTER_F +vowel  and  1 2 3 /Alphabetic
                    hex: 0..9 a..f A..F
                    vowel: a i u e o A I U E O
        ''',
        expect_full_match=[b'x', b'X', b'b', b'B', b'1', b'2', b'3'],
        no_match=[b'a', b'A', b'c', b'C', b'd', b'D', b'e', b'E', b'f', b'F', b'y', b'Y', b'z', b'Z', b'0', b'4', b'9', b'-'])

        self.given(u'''
            allButU
                allButU: not: U
        ''',
        expect_full_match=[b'^', b'u'],
        no_match=[b'U', b''])

        self.given(u'''
            nonalpha
                nonalpha: not: /Alphabetic
        ''',
        expect_full_match=[b'-', b'^', b'1'],
        no_match=[b'A', b'a', u'Ä', u'ä'])

        self.given(u'''
            not: /Alphabetic
        ''',
        expect_full_match=[b'-', b'^', b'1'],
        no_match=[b'A', b'a', u'Ä', u'ä'])

        self.given(u'''
            otherz
                otherz: +nonz
                    nonz: not: z
        ''',
        expect_full_match=[b'-', b'^', b'1', b'A', b'a', u'Ä', u'ä', b'Z'],
        no_match=[b'z'])

        self.given(u'''
            a_or_consonant
                a_or_consonant: A a +consonant 
                    consonant: a..z A..Z not a i u e o A I U E O 
        ''',
        expect_full_match=[b'A', b'a', b'Z', b'z'],
        no_match=[u'Ä', u'ä', b'-', b'^', b'1'])

        self.given(u'''
            maestro
                maestro: m +ae s t r o 
                    ae: +vowel and +hex not +upper
                        hex: +digit a..f A..F 
                        vowel: a i u e o A I U E O
        ''',
        expect_full_match=[b'm', b'a', b'e', b's', b't', b'r', b'o'],
        no_match=[u'Ä', u'ä', b'-', b'^', b'1', b'N', b'E', b'W', b'b'])


    def test_charclass_escape(self):
        self.given(b'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_full_match=[u'\u0061', u'\U00000061', b'\x61', b'\61', b'a'],
        no_match=[b'\u0061', br'\u0061', br'\x61', br'\61'])

        self.given(br'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_full_match=[u'\u0061', u'\U00000061', b'\x61', b'\61', b'a'],
        no_match=[b'\u0061', br'\u0061', br'\x61', br'\61'])

        self.given(u'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_full_match=[u'\u0061', u'\U00000061', b'\x61', b'\61', b'a'],
        no_match=[b'\u0061', br'\u0061', br'\x61', br'\61'])

        self.given(ur'''
            1 of: \u0061 \U00000061 \x61 \61
        ''',
        expect_full_match=[u'\u0061', u'\U00000061', b'\x61', b'\61', b'a'],
        no_match=[b'\u0061', br'\u0061', br'\x61', br'\61'])

        self.given(br'''
            allowed_escape
                allowed_escape: \n \r \t \a \b \v \f
        ''',
        expect_full_match=[b'\n', b'\r', b'\t', b'\a', b'\b', b'\v', b'\f'],
        no_match=[br'\n', br'\r', br'\t', br'\a', br'\b', br'\v', br'\f'])

        self.given(br'''
            unicode_charname
                unicode_charname: \N{AMPERSAND} \N{BIOHAZARD SIGN}
        ''',
        expect_full_match=[b'&', u'\N{AMPERSAND}', u'\N{BIOHAZARD SIGN}', u'☣'],
        no_match=[b'\N{AMPERSAND}', br'\N{AMPERSAND}', br'\N{BIOHAZARD SIGN}', b'☣'])

        self.given(br'''
            unicode_charname
                unicode_charname: \N{AMPERSAND} :AMPERSAND \N{BIOHAZARD SIGN} :BIOHAZARD_SIGN
        ''',
        expect_full_match=[b'&', u'\N{AMPERSAND}', u'\N{BIOHAZARD SIGN}', u'☣'],
        no_match=[b'\N{AMPERSAND}', br'\N{AMPERSAND}', br'\N{BIOHAZARD SIGN}', b'☣'])


    def test_atomic_grouping(self):
        self.given(b'''
            @/digits/even/
                digits = 0.. <<- of digit
                even: 0 2 4 6 8
        ''',
        expect_full_match=[b'0', b'8', b'10', b'42', b'178'],
        no_match=[b'', b'1', b'9', b'1337'],
        partial_match={'24681' : '2468', b'134579' : '134'})

        self.given(b'''
            //digits/even//
                digits = 0.. <<- of digit
                even: 0 2 4 6 8
        ''',
        expect_full_match=[b'0', b'8', b'10', b'42', b'178'],
        no_match=[b'', b'1', b'9', b'1337', b'24681', b'134579'])


    def test_builtin(self):
        self.given(b'''
            lowhex
                lowhex: +alpha +alnum +lower not G..Z g..z +upper +digit padchar backslash tab whitechar
        ''',
        expect_full_match=[b'a', b'b', b'c', b'd', b'e', b'f'],
        no_match=[b'A', b'B', b'F', b'x', b'X', b'z', b'Z', b'0', b'1', b'9'])


    def test_fail(self):
        self.given(b'''
            FAIL!
        ''',
        expect_full_match=[],
        no_match=[b'nothing should match', b'', b'not even empty string'])

        self.given(b'''
            /FAIL!/
        ''',
        expect_full_match=[],
        no_match=[b'nothing should match', b'', b'not even empty string'])

        self.given(b'''
            /alpha/FAIL!/
        ''',
        expect_full_match=[],
        no_match=[b'', b'A', b'nothing should match'])

        self.given(b'''
            2 of FAIL!
        ''',
        expect_full_match=[],
        no_match=[b'nothing should match', b'', b'not even empty string'])

        self.given(b'''
            <<|
              |FAIL!
        ''',
        expect_full_match=[],
        no_match=[b'nothing should match', b'', b'not even empty string'])

        self.given(b'''
            <<|
              |FAIL!
              |alpha
        ''',
        expect_full_match=[b'A', b'a'],
        no_match=[b'1', b''])

        self.given(b'''
            <<|
              |alpha
              |FAIL!
        ''',
        expect_full_match=[b'A', b'a'],
        no_match=[b'1', b''])

        self.given(b'''
            /opener?/contents?/closer/
                opener = <<|
                           |paren
                           |curly
                           |square
                           |chevron
                
                    [paren]: (
                    [curly]: {
                    [square]: [
                    [chevron]: <
                    
                contents = 1.. <<- of any
                
                closer = <<|
                           |[paren] ? 1 of: )
                           |[curly] ? 1 of: }
                           |[square] ? 1 of: ]
                           |[chevron] ? 1 of: >
                           |FAIL!
        ''',
        expect_full_match=[b'()', b'{}', b'[]', b'<>', b'(riiiight)', b'{()}', b'[! @]', b'<<>>', b'<<<<<<<<<<<>'],
        no_match=[b'{]', b'<)', b'(', b'[unclosed'],
        partial_match={
            '(super) duper' : '(super)',
        })

        self.given(b'''
            <@>
             |FAIL!>
        ''',
        expect_full_match=[],
        no_match=[b'nothing should match', b'', b'not even empty string'])

        self.given(b'''
            <@>
             |!FAIL!>
        ''',
        expect_full_match=[b''],
        no_match=[],
        partial_match={
            'everything matches' : '',
            'though the match is empty string' : '',
        })


    def test_quantifier(self):
        self.given(b'''
            1 of alpha
        ''',
        expect_full_match=[b'a', b'B'],
        no_match=[b'', b'1', b'$'],
        partial_match={'Cd' : 'C'})

        self.given(b'''
            2 of alpha
        ''',
        expect_full_match=[b'ab', b'Cd'],
        no_match=[b'', b'A1', b'$1'],
        partial_match={'ABC' : 'AB'})

        self.given(b'''
            @3.. of alpha
        ''',
        expect_full_match=[b'abc', b'DeFGhij'],
        no_match=[b'', b'Aa4'])

        self.given(b'''
            @4..5 of alpha
        ''',
        expect_full_match=[b'abcd', b'abcDE'],
        no_match=[b'', b'ab123'],
        partial_match={'ABCDEF' : 'ABCDE'})

        self.given(b'''
            /prefix/alnum/
                prefix = 1..2 <<- of alpha
        ''',
        expect_full_match=[b'A1', b'Ab', b'Ab3', b'abc'],
        no_match=[b'', b'99', b'9z'],
        partial_match={'YAMM' : 'YAM', b'B52' : 'B5'})

        self.given(b'''
            /prefix/alnum/
                prefix = 3.. <<- of alpha
        ''',
        expect_full_match=[b'AAA1', b'YAMM', b'Fubar', b'YAMM2', b'Fubar4'],
        no_match=[b'', b'A1', b'Ab', b'abc', b'Ab3', b'ABC', b'99', b'9z', b'B52'],
        partial_match={'Test123' : 'Test1'})

        self.given(b'''
            /open/content/close/
                open: (
                close: )
                content = 1.. <<- of: +alnum +open +close
        ''',
        expect_full_match=[b'(sic)'],
        no_match=[b'f(x)'],
        partial_match={'(pow)wow(kaching)zzz' : '(pow)wow(kaching)'})

        self.given(b'''
            /open/content/close/
                open: (
                close: )
                content = 1 <<+.. of: +alnum +open +close
        ''',
        expect_full_match=[b'(sic)'],
        no_match=[b'f(x)'],
        partial_match={'(pow)wow(kaching)zzz' : '(pow)'})

        self.given(b'''
            /open/content/close/
                open: (
                close: )
                content = @1.. of: +alnum +open +close
        ''',
        no_match=[b'(pow)wow(kaching)zzz'])

        self.given(b'''
            css_color
                css_color = 6 of hex
                    hex: 0..9 a..f
        ''',
        expect_full_match=[b'ff0000', b'cccccc', b'a762b3'],
        no_match=[b'', b'black', b'white'])

        self.given(b'''
            DWORD_speak
                DWORD_speak = @1.. of 4 of hex
                    hex: 0..9 A..F
        ''',
        expect_full_match=[b'CAFEBABE', b'DEADBEEF', b'0FF1CE95'],
        no_match=[b'', b'YIKE'])
        
        self.given(b'''
            ? of alphas
                alphas = @1.. of alpha
        ''',
        expect_full_match=[b'', b'Cowabunga'],
        partial_match={
            '1one' : '',
            'hell0' : 'hell',
        })
        
        self.given(b'''
            ? of alphas
                alphas = 1.. <<- of alpha
        ''',
        expect_full_match=[b'', b'Cowabunga'],
        partial_match={
            '1one' : '',
            'hell0' : 'hell',
        })
        
        self.given(b'''
            ? of alphas
                alphas = 1 <<+.. of alpha
        ''',
        expect_full_match=[b''],
        partial_match={
            '1one' : '',
            'hell0' : '',
            'Cowabunga' : '',
        })
        
        self.given(b'''
            /opt_alphas/.
                opt_alphas = ? of alphas
                    alphas = 1 <<+.. of alpha
        ''',
        expect_full_match=[b'', b'Cowabunga'],
        no_match=[b'hell0', b'1one'])


    def test_reference(self):
        self.given(u'''
            /bang/=bang/
                [bang]: b a n g !
        ''',
        expect_full_match=[b'bb', b'aa', b'nn', b'gg', b'!!'],
        no_match=[b'', b'a', b'ba'])
        
        self.given(u'''
            /=bang/bang/
                [bang]: b a n g !
        ''',
        no_match=[b'', b'a', b'ba', b'bb', b'aa', b'nn', b'gg', b'!!'])
        
        self.given(u'''
            /bang/=bang?/
                [bang]: b a n g !
        ''',
        expect_full_match=[b'a', b'bb', b'aa', b'nn', b'gg', b'!!'],
        no_match=[b'', b'clang!'],
        partial_match={
            'ba'    : 'b',
            'bang!' : 'b',
        })
        
        self.given(u'''
            /=bang?/bang/
                [bang]: b a n g !
        ''',
        expect_full_match=[b'b', b'a', b'n', b'g', b'!'],
        no_match=[b'', b'clang!'],
        partial_match={'ba' : 'b', b'bb' : 'b', b'aa' : 'a', b'nn' : 'n', b'gg' : 'g', b'!!' : '!', b'bang!' : 'b'})


    def test_wordchar_boundary(self):
        self.given(b'''
            /wordchar/WOB/non-WOB/
        ''',
        expect_full_match=[],
        no_match=[b'a', b'b', b'Z', b'_'])

        self.given(b'''
            /EOW/wordchar/BOW/
        ''',
        expect_full_match=[],
        no_match=[b'a', b'b', b'Z', b'_'])

        self.given(b'''
            realworld_wordchar
                realworld_wordchar: +wordchar - not +digit _
        ''',
        expect_full_match=[b'a', b'Z', b'-'],
        no_match=[b'0', b'9', b'_'])

        self.given(b'''
            cat
                cat = 'cat'
        ''',
        fn=regex.search,
        expect_full_match=[b'cat'],
        no_match=[b'garfield'],
        partial_match={'tomcat' : 'cat', b'catasthrope' : 'cat', b'complicated' : 'cat', b'cat videos' : 'cat', b'grumpy cat' : 'cat'})

        self.given(b'''
            cat
                cat = 'cat'_
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=[b'cat', b'cat videos', b'grumpy cat', b'tomcat', b'garfield'],
        partial_match={'catasthrope' : 'cat', b'complicated' : 'cat'})

        self.given(b'''
            cat
                cat = 'cat'.
        ''',
        fn=regex.search,
        expect_full_match=[b'cat'],
        no_match=[b'catasthrope', b'complicated', b'garfield'],
        partial_match={'tomcat' : 'cat', b'cat videos' : 'cat', b'grumpy cat' : 'cat'})

        self.given(b'''
            cat
                cat = _'cat'
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=[b'cat', b'catasthrope', b'cat videos', b'grumpy cat', b'garfield'],
        partial_match={'tomcat' : 'cat', b'complicated' : 'cat'})

        self.given(b'''
            cat
                cat = .'cat'
        ''',
        fn=regex.search,
        expect_full_match=[b'cat'],
        no_match=[b'tomcat', b'complicated', b'garfield'],
        partial_match={'catasthrope' : 'cat', b'cat videos' : 'cat', b'grumpy cat' : 'cat'})

        self.given(b'''
            cat
                cat = _'cat'_
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=[b'cat', b'catasthrope', b'cat videos', b'tomcat', b'grumpy cat', b'garfield'],
        partial_match={'complicated' : 'cat'})

        self.given(b'''
            cat
                cat = .'cat'.
        ''',
        fn=regex.search,
        expect_full_match=[b'cat'],
        no_match=[b'tomcat', b'catasthrope', b'complicated', b'garfield'],
        partial_match={'cat videos' : 'cat', b'grumpy cat' : 'cat'})

        self.given(b'''
            /WOB/cat/WOB/
                cat = 'cat'
        ''',
        fn=regex.search,
        expect_full_match=[b'cat'],
        no_match=[b'tomcat', b'catasthrope', b'complicated', b'garfield'],
        partial_match={'cat videos' : 'cat', b'grumpy cat' : 'cat'})

        self.given(b'''
            /WOB/cat/WOB/
                cat = .'cat'.
        ''',
        fn=regex.search,
        expect_full_match=[b'cat'],
        no_match=[b'tomcat', b'catasthrope', b'complicated', b'garfield'],
        partial_match={'cat videos' : 'cat', b'grumpy cat' : 'cat'})

        self.given(b'''
            /BOW/cat/EOW/
                cat = 'cat'
        ''',
        fn=regex.search,
        expect_full_match=[b'cat'],
        no_match=[b'tomcat', b'catasthrope', b'complicated', b'garfield'],
        partial_match={'cat videos' : 'cat', b'grumpy cat' : 'cat'})

        self.given(b'''
            /BOW/cat/EOW/
                cat = .'cat'.
        ''',
        fn=regex.search,
        expect_full_match=[b'cat'],
        no_match=[b'tomcat', b'catasthrope', b'complicated', b'garfield'],
        partial_match={'cat videos' : 'cat', b'grumpy cat' : 'cat'})

        self.given(b'''
            /anti/non-WOB/
                anti = 'anti'
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=[b'anti', b'anti-virus', b'rianti cartwright'],
        partial_match={'antivirus' : 'anti', b'meantime' : 'anti'})

        self.given(b'''
            anti_
                anti_ = 'anti'_
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=[b'anti', b'anti-virus', b'rianti cartwright'],
        partial_match={'antivirus' : 'anti', b'meantime' : 'anti'})

        self.given(b'''
            somethingtastic
                somethingtastic = _'tastic'
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=[b'tastic', b'tasticism'],
        partial_match={'fantastic' : 'tastic', b'fantastico' : 'tastic'})

        self.given(b'''
            expletification
                expletification = _'bloody'_
        ''',
        fn=regex.search,
        expect_full_match=[],
        no_match=[b'bloody', b'bloody hell'],
        partial_match={'absobloodylutely' : 'bloody'})


    def test_flags(self):
        self.given(b'''
            lower
        ''',
        expect_full_match=[b'a'],
        no_match=[b'A', u'ä', u'Ä'])

        self.given(b'''
            (unicode)
            lower
        ''',
        expect_full_match=[b'a', u'ä'],
        no_match=[b'A', u'Ä'])

        self.given(b'''
            (ignorecase)
            1 of: a i u e o
        ''',
        expect_full_match=[b'a', b'A'],
        no_match=[u'Ä', u'ä'])

        self.given(b'''
            (ignorecase) 1 of: a i u e o
        ''',
        expect_full_match=[b'a', b'A'],
        no_match=[u'Ä', u'ä'])

        self.given(b'''
            (unicode)
            (ignorecase) lower
        ''',
        expect_full_match=[b'a', b'A', u'Ä', u'ä'])

        self.given(b'''
            (unicode ignorecase)
            lower
        ''',
        expect_full_match=[b'a', b'A', u'Ä', u'ä'])

        self.given(b'''
            (unicode ignorecase)
            lower
        ''',
        expect_full_match=[b'a', b'A', u'Ä', u'ä'])

        self.given(b'''
            (ignorecase) 'AAa'
        ''',
        expect_full_match=[b'AAa', b'aAa', b'aaa', b'AAA'])

        self.given(b'''
            (ignorecase) /VOWEL/BIGVOWEL/
                VOWEL: A I U E O
                BIGVOWEL = (-ignorecase) VOWEL
        ''',
        expect_full_match=[b'AA', b'aA'],
        no_match=[b'Aa', b'aa'])


    def test_string_escape(self):
        self.given(br'''
            '\n'
        ''',
        expect_full_match=[b'\n'],
        no_match=[br'\n', b'\\n'])

        self.given(br'''
            '\t'
        ''',
        expect_full_match=[b'\t', b'	'],
        no_match=[br'\t', b'\\t'])

        self.given(b'''
            '\t'
        ''',
        expect_full_match=[b'\t', b'	'],
        no_match=[br'\t', b'\\t'])

        self.given(br'''
            '\x61'
        ''',
        expect_full_match=[u'\U00000061', u'\u0061', u'a', b'a', b'\x61', b'\141'],
        no_match=[br'\x61', b'\\x61'])

        self.given(b'''
            '\x61'
        ''',
        expect_full_match=[u'\U00000061', u'\u0061', u'a', b'a', b'\x61', b'\141'],
        no_match=[br'\x61', b'\\x61'])

        self.given(u'''
            '\U00000061'
        ''',
        expect_full_match=[u'\U00000061', u'\u0061', u'a', b'a', b'\x61', b'\141'],
        no_match=[br'\U00000061', b'\\U00000061'])

        self.given(br'''
            '\u0061'
        ''',
        expect_full_match=[u'\U00000061', u'\u0061', u'a', b'a', b'\x61', b'\141'],
        no_match=[br'\u0061', b'\\u0061'])

        self.given(br'''
            '\141'
        ''',
        expect_full_match=[u'\U00000061', u'\u0061', u'a', b'a', b'\x61', b'\141'],
        no_match=[br'\141', b'\\141'])

        self.given(u'''
            '\N{AMPERSAND}'
        ''',
        expect_full_match=[u'\N{AMPERSAND}', u'&', b'&'],
        no_match=[br'\N{AMPERSAND}', b'\N{AMPERSAND}', b'\\N{AMPERSAND}'])

        self.given(br'''
            '\N{AMPERSAND}'
        ''',
        expect_full_match=[u'\N{AMPERSAND}', u'&', b'&'],
        no_match=[br'\N{AMPERSAND}', b'\N{AMPERSAND}', b'\\N{AMPERSAND}'])

        self.given(br'''
            '\N{BIOHAZARD SIGN}'
        ''',
        expect_full_match=[u'\N{BIOHAZARD SIGN}', u'☣'],
        no_match=[br'\N{BIOHAZARD SIGN}', b'\N{BIOHAZARD SIGN}', b'\\N{BIOHAZARD SIGN}', b'☣'])

        self.given(br'''
            2 of 'M\N{AMPERSAND}M\N{APOSTROPHE}s'
        ''',
        expect_full_match=["M&M'sM&M's"],
        no_match=[br'M\N{AMPERSAND}M\N{APOSTROPHE}s'])

        self.given(ur'''
            2 of 'M\N{AMPERSAND}M\N{APOSTROPHE}s'
        ''',
        expect_full_match=["M&M'sM&M's"],
        no_match=[br'M\N{AMPERSAND}M\N{APOSTROPHE}s'])

        self.given(ur'''
            3 of '\t\t'
        ''',
        expect_full_match=[b'\t\t\t\t\t\t'],
        no_match=[b'\t\t\t\t'])

        self.given(br'''
            '\a\b\f\v\t'
        ''',
        expect_full_match=[b'\a\b\f\v\t'],
        no_match=[br'\a\b\f\v\t'])

        self.given(br'''
            '.\w\b\s\X\n'
        ''',
        expect_full_match=[b'.\w\b\s\X\n'],
        no_match=[br'.\w\b\s\X\n'])


    def test_flag_dependents(self):
        self.given(br'''
            linechar
        ''',
        expect_full_match=[b'\n', b'\r', b'\v', b'\f', b'\x0b', b'\x0C'],
        no_match=[b'\x85', b'\u2028', br'\u2028', u'\u2028', u'\u2029'],
        partial_match={'\r\n' : '\r'})

        self.given(br'''
            (unicode)
            linechar
        ''',
        expect_full_match=[b'\n', b'\r', b'\v', b'\f', b'\x0b', b'\x0C', b'\x85', u'\u2028', u'\u2029'],
        no_match=[b'\u2028', br'\u2028'],
        partial_match={'\r\n' : '\r'})

        self.given(br'''
            (-word)
            linechar
        ''',
        expect_full_match=[b'\n'],
        no_match=[b'\r', b'\v', b'\f', b'\x0b', b'\x0C', b'\x85', u'\u2028', u'\u2029', b'\u2028', br'\u2028'],
        partial_match={'\n\r' : '\n'})

        self.given(br'''
            (unicode -word)
            linechar
        ''',
        expect_full_match=[b'\n'],
        no_match=[b'\r', b'\v', b'\f', b'\x0b', b'\x0C', b'\x85', u'\u2028', u'\u2029', b'\u2028', br'\u2028'],
        partial_match={'\n\r' : '\n'})

        self.given(br'''
            (-word unicode)
            linechar
        ''',
        expect_full_match=[b'\n'],
        no_match=[b'\r', b'\v', b'\f', b'\x0b', b'\x0C', b'\x85', u'\u2028', u'\u2029', b'\u2028', br'\u2028'],
        partial_match={'\n\r' : '\n'})

        self.given(br'''
            (unicode)
            (-word) linechar
        ''',
        expect_full_match=[b'\n'],
        no_match=[b'\r', b'\v', b'\f', b'\x0b', b'\x0C', b'\x85', u'\u2028', u'\u2029', b'\u2028', br'\u2028'],
        partial_match={'\n\r' : '\n'})


    def test_orblock(self):
        self.given(b'''
            @|
             |'cat'
             |'dog'
        ''',
        expect_full_match=[b'cat', b'dog'],
        no_match=[b'cadog'],
        partial_match={'catdog' : 'cat', b'catog' : 'cat'})

        self.given(b'''
            <<|
              |'tea'
              |'coffee'
        ''',
        expect_full_match=[b'tea', b'coffee'],
        no_match=[b'tecoffee'],
        partial_match={'teacoffee' : 'tea', b'teaoffee' : 'tea'})

        self.given(b'''
            backtrackable_choice
                backtrackable_choice = <<|
                                         |'catastrophy'
                                         |'catass trophy'
                                         |'cat'
        ''',
        expect_full_match=[b'catastrophy', b'catass trophy', b'cat'],
        partial_match={'catastrophy cat' : 'catastrophy', b'catass cat' : 'cat'})

        self.given(b'''
            no_backtrack
                no_backtrack = @|
                                |'red pill'
                                |'blue pill'
        ''',
        expect_full_match=[b'red pill', b'blue pill'],
        no_match=[b'red blue pill'],
        partial_match={'red pill pill' : 'red pill'})

        self.given(b'''
            /digit/space/ampm/
                ampm = (ignorecase) <<|
                                      |'AM'
                                      |'PM'
        ''',
        expect_full_match=[b'1 AM', b'2 pm', b'9 pM'],
        no_match=[b'10 am', b'1 APM', b'PM'],
        partial_match={'5 aMm ' : '5 aM'})

        self.given(b'''
            2 of <<|
                   |'fast'
                   |'good'
                   |'cheap'
        ''',
        expect_full_match=[b'fastgood', b'fastcheap', b'cheapgood', b'cheapfast', b'goodgood', b'cheapcheap'],
        no_match=[b'fast', b'good', b'cheap'],
        partial_match={'goodcheapfast' : 'goodcheap'})

        self.given(b'''
            <<|
              |2 of 'ma'
              |2 of 'pa'
              |2 of 'bolo'
        ''',
        expect_full_match=[b'mama', b'papa', b'bolobolo'],
        no_match=[b'ma', b'mapa', b'mabolo', b'boloma', b'pabolo'],
        partial_match={'papabolo' : 'papa', b'mamapapa' : 'mama'})

        self.given(b'''
            /blood_type/rhesus/
                blood_type =<<|
                              |'AB'
                              |1 of: A B O

                rhesus = <<|
                           |'+'
                           |'-'
                           | -- allow empty/unknown rhesus
        ''',
        expect_full_match=[b'A', b'A+', b'B', b'B-', b'AB', b'AB+', b'O', b'O-'],
        no_match=[b''],
        partial_match={'A+B' : 'A+', b'AAA' : 'A'})

        self.given(b'''
            subexpr_types
                subexpr_types = <<|
                                  |'string literal'
                                  |(ignorecase) 1 of: a i u e o
                                  |2..3 <<- of X
                                  |/alpha/digit/
                                  |alpha

                    X = 'X'
        ''',
        expect_full_match=[b'string literal', b'E', b'XX', b'R1', b'X'],
        no_match=[b'2', b'3'],
        partial_match={'aX' : 'a', b'string Z' : 's', b'YY' : 'Y'})

        self.given(b'''
            <<| -- comment here is ok
              |'android'
              |'ios'
        ''',
        expect_full_match=[b'android', b'ios'],
        no_match=[b'androiios'],
        partial_match={'androidos' : 'android'})

        self.given(b'''
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
        expect_full_match=[b'lawful good', b'chaotic good', b'chaotic evil', b'neutral evil', b'neutral neutral'],
        no_match=[b'neutral', b'neutral ', b'lawful ', b'good', b'evil', b'chaotic chaotic ', b'evilevil', b' '])

        self.given(b'''
            any_color_as_long_as_it_is_
                any_color_as_long_as_it_is_ = <<|
                                                |'black'
                                                -- single-entry "choice" is OK
        ''',
        expect_full_match=[b'black'],
        no_match=[b''],
        partial_match={'blackish' : 'black'})

        self.given(b'''-- nested ORBLOCKs
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
        expect_full_match=[b'cendol', b'kopi tubruk', b'teh tarik', b'ocha', b'cappuccino'],
        no_match=[b'kopi earl grey cendol'],
        partial_match={'espresso tubruk' : 'espresso'})

        self.given(b'''
            /alpha/or/
                or = @|
                      |alpha
                      |digit
        ''',
        expect_full_match=[b'Aa', b'a1'],
        no_match=[b'', b'a', b'1'])

        self.given(b'''
            /or/alpha/
                or = @|
                      |alpha
                      |digit
        ''',
        expect_full_match=[b'Aa', b'1A'],
        no_match=[b'', b'a', b'1'])

        self.given(b'''
            /alpha/or/
                or = <<|
                       |alpha
                       |digit
        ''',
        expect_full_match=[b'Aa', b'a1'],
        no_match=[b'', b'a', b'1'])

        self.given(b'''
            /or/alpha/
                or = <<|
                       |alpha
                       |digit
        ''',
        expect_full_match=[b'aA', b'1a'],
        no_match=[b'', b'a', b'1'])

        self.given(b'''
            /az?/or/
                [az]: a..z
                or = <<|
                       |[az] ? alpha
                       |digit
        ''',
        expect_full_match=[b'aa', b'aA', b'1'],
        no_match=[b'', b'a'])

        self.given(b'''
            /or/az/
                [az]: a..z
                or = <<|
                       |[az] ? alpha
                       |digit
        ''',
        expect_full_match=[b'1a'],
        no_match=[b'', b'a', b'1', b'aa', b'Aa', b'aA'])

        self.given(b'''
            /az?/or/
                [az]: a..z
                or = <<|
                       |[az] ? alpha
                       |
        ''',
        expect_full_match=[b'aA', b'aa', b''],
        no_match=[],
        partial_match={
            'Aa' : '',
            'A'  : '',
            'a'  : '',
            '1'  : '',
            '12' : '',
        })

        self.given(b'''
            /az?/or/
                [az]: a..z
                or = <<|
                       |[az] ?
                       |digit                      
        ''',
        expect_full_match=[b'a', b'1'],
        no_match=[b'A', b'', b'Aa'],
        partial_match={
            'aA' : 'a',
            'a1' : 'a',
            '12' : '1',
        })

        self.given(b'''
            /az?/or/
                [az]: a..z
                or = <<|
                       |[az] ?
                       |
        ''',
        expect_full_match=[b'a', b''],
        no_match=[],
        partial_match={
            'Aa' : '',
            'A'  : '',
            '1'  : '',
            '12' : '',
        })


    def test_lookaround(self):
        self.given(b'''
            actually_no_lookaround
                actually_no_lookaround = <@>
                    |alpha|
                          |digit|
                                |upper|
                                      |lower|
        ''',
        expect_full_match=[b'a1Aa'])

        self.given(b'''
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
        no_match=[b'yanglainsemakinketinggalan'],
        partial_match={'yamahasemakindidepan' : 'semakin'})

        self.given(b'''
            <@>
                |anyam>
                |anyaman|
                 <nyaman|

                anyam = 'anyam'
                anyaman = 'anyaman'
                nyaman = 'nyaman'
        ''',
        expect_full_match=[b'anyaman'],
        partial_match={'anyamanyamannyaman' : 'anyaman'})

        self.given(b'''
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
        expect_full_match=[b'AAaa11!!'],
        no_match=[b'$h0RT', b'noNumber!', b'noSymb0l', b'n0upcase!', b'N0LOWCASE!'])

        self.given(b'''
            word_ends_with_s
                word_ends_with_s = <@>
                    |wordchars|
                            <s|

                    wordchars = @1.. of wordchar
                    s = 's'
        ''',
        expect_full_match=[b'boss'],
        no_match=[b'sassy'])

        self.given(b'''
            un_x_able
                un_x_able = <@>
                    |un>
                    |unxable|
                       <able|

                    un = 'un'
                    unxable = @1.. of wordchar
                    able = 'able'
        ''',
        expect_full_match=[b'undoable', b'unable'])

        self.given(b'''
            escape
                escape = <@>
                    <backslash|
                              |any|
        ''',
        fn=regex.search,
        no_match=[b'\t', b'\\'],
        partial_match={r'\t' : 't', b'\z': 'z', b'\\\\':'\\', br'\r\n' : 'r', br'r\n' : 'n', b'\wow' : 'w', b'\\\'' : '\''})

        self.given(b'''
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
        no_match=[b'123', b'4 pm'],
        partial_match={
            '$1'        : '1',
            '$234'      : '234',
            '500 bucks' : '500',
            '1 buck'    : '1',
        })

        self.given(b'''
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
        no_match=[b'BEGINNER FIRE-BENDER', b'begin hey end', b'BEGINEND', b'BEGIN ...'],
        partial_match={
            'BEGIN huge wooden horse END brad pitt' : 'BEGIN huge wooden horse END',
            'BEGINNER BEGIN ENDANGERED END' : 'BEGIN ENDANGERED END',
        })


    def test_non_op(self):
        self.given(b'''
            /non-alpha/non-digit/non-whitechar/non-wordchar/
        ''',
        expect_full_match=[b'....'])

        self.given(b'''
            non_digits
                non_digits = @1.. of non-digit
        ''',
        expect_full_match=[b'ZERO-ZERO-SEVEN', b'ZEROZEROSEVEN'])

        self.given(b'''
            non-alphabetic
                alphabetic: /Alphabetic
        ''',
        expect_full_match=[b'1', b'!'],
        no_match=[b'a', u'ä'])

        self.given(b'''
            non-minus
                minus: -
        ''',
        expect_full_match=[b'a', b'1', b'!'],
        no_match=[b'-'])

        self.given(b'''
            non-caret
                caret: ^
        ''',
        expect_full_match=[b'a', b'1', b'!'],
        no_match=[b'^'])

        self.given(b'''
            /non-non_alpha/non-non_digit/
                non_alpha = non-alpha
                non_digit = non-digit
        ''',
        expect_full_match=[b'a1', b'A9'],
        no_match=[b'a', b'1', b'Aa', b'42', b'A+'])

        self.given(b'''
            non-consonant
                consonant: alpha not vowel
                    vowel: a i u e o A I U E O
        ''',
        expect_full_match=[b'a', b'1', b'!'],
        no_match=[b'b', b'Z'])


    def test_numrange_shortcut(self):
        self.given(u'''
            '0'..'1'
        ''',
        expect_full_match=[b'0', b'1'],
        no_match=[b'00', b'01', b'10', b'11'])

        self.given(u'''
            '0'..'2'
        ''',
        expect_full_match=[b'0', b'1', b'2'],
        no_match=[b'00', b'11', b'22', b'02'])

        self.given(u'''
            '0'..'9'
        ''',
        expect_full_match=[b'0', b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9'],
        no_match=[b'00', b'11', b'99', b'09', b'911', b'123abc'],
        partial_match={
            '0xdeadbeef' : '0',
            '9z' : '9',
            '3.14' : '3',
        })

        self.given(u'''
            '1'..'2'
        ''',
        expect_full_match=[b'1', b'2'],
        no_match=[b'0', b'11', b'22', b'12'])

        self.given(u'''
            '1'..'9'
        ''',
        expect_full_match=[b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9'],
        no_match=[b'0', b'11', b'99', b'19'])

        self.given(u'''
            '2'..'9'
        ''',
        expect_full_match=[b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9'],
        no_match=[b'1', b'22', b'99', b'29'])

        self.given(u'''
            '8'..'9'
        ''',
        expect_full_match=[b'8', b'9'],
        no_match=[b'88', b'99', b'89'])

        self.given(u'''
            '0'..'10'
        ''',
        expect_full_match=[b'0', b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9', b'10'],
        no_match=[b'11', b'010', b'100'])

        self.given(u'''
            '1'..'10'
        ''',
        expect_full_match=[b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9', b'10'],
        no_match=[b'0', b'11', b'010', b'100', b'110'])

        self.given(u'''
            '2'..'10'
        ''',
        expect_full_match=[b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9', b'10'],
        no_match=[b'0', b'22', b'010', b'100', b'210'])

        self.given(u'''
            '8'..'10'
        ''',
        expect_full_match=[b'8', b'9', b'10'],
        no_match=[b'88', b'010', b'100', b'810'])

        self.given(u'''
            '9'..'10'
        ''',
        expect_full_match=[b'9', b'10'],
        no_match=[b'99', b'010', b'100', b'910'])

        self.given(u'''
            '0'..'11'
        ''',
        expect_full_match=[b'0', b'1', b'5', b'10', b'11'],
        no_match=[b'01', b'12', b'011', b'111'])

        self.given(u'''
            '1'..'11'
        ''',
        expect_full_match=[b'1', b'6', b'10', b'11'],
        no_match=[b'0', b'01', b'011', b'111'])

        self.given(u'''
            '9'..'11'
        ''',
        expect_full_match=[b'9', b'10', b'11'],
        no_match=[b'90', b'09', b'911'])

        self.given(u'''
            '10'..'11'
        ''',
        expect_full_match=[b'10', b'11'],
        no_match=[b'100', b'101', b'111', b'1011'])

        self.given(u'''
            '0'..'12'
        ''',
        expect_full_match=[b'0', b'1', b'2', b'5', b'10', b'11', b'12'],
        no_match=[b'00', b'012'])

        self.given(u'''
            '1'..'12'
        ''',
        expect_full_match=[b'1', b'2', b'8', b'9', b'10', b'11', b'12'],
        no_match=[b'01', b'012', b'112', b'121'])

        self.given(u'''
            '2'..'12'
        ''',
        expect_full_match=[b'2', b'8', b'9', b'10', b'11', b'12'],
        no_match=[b'20', b'100', b'110', b'120'])

        self.given(u'''
            '0'..'19'
        ''',
        expect_full_match=[b'0', b'1', b'9', b'10', b'18', b'19'],
        no_match=[b'00', b'019', b'190', b'20'])

        self.given(u'''
            '1'..'19'
        ''',
        expect_full_match=[b'1', b'9', b'10', b'18', b'19'],
        no_match=[b'0', b'00', b'019', b'190', b'20'])

        self.given(u'''
            '9'..'19'
        ''',
        expect_full_match=[b'9', b'10', b'15', b'19'],
        no_match=[b'919'])

        self.given(u'''
            '10'..'19'
        ''',
        expect_full_match=[b'10', b'19'],
        no_match=[b'0', b'1', b'9', b'100', b'1019', b'20', b'190'])

        self.given(u'''
            '0'..'20'
        ''',
        expect_full_match=[b'0', b'1', b'2', b'10', b'19', b'20'],
        no_match=[b'00', b'020', b'200'])

        self.given(u'''
            '2'..'20'
        ''',
        expect_full_match=[b'2', b'10', b'19', b'20'],
        no_match=[b'00', b'020', b'200', b'220'])

        self.given(u'''
            '10'..'20'
        ''',
        expect_full_match=[b'10', b'11', b'15', b'19', b'20'],
        no_match=[b'0', b'1', b'010', b'020', b'100', b'200', b'1020'])

        self.given(u'''
            '19'..'20'
        ''',
        expect_full_match=[b'19', b'20'],
        no_match=[b'1', b'019', b'2000', b'1920'])

        self.given(u'''
            '0'..'29'
        ''',
        expect_full_match=[b'0', b'1', b'2', b'9', b'29'],
        no_match=[b'00', b'029', b'299'])

        self.given(u'''
            '2'..'29'
        ''',
        expect_full_match=[b'2', b'9', b'15', b'21', b'22', b'29'],
        no_match=[b'0', b'1', b'229', b'292'])

        self.given(u'''
            '9'..'29'
        ''',
        expect_full_match=[b'9', b'29', b'19', b'15'],
        no_match=[b'92', b'929', b'299'])

        self.given(u'''
            '2'..'42'
        ''',
        expect_full_match=[b'2', b'4', b'12', b'22', b'39', b'41', b'42'],
        no_match=[b'02', b'242', b'422'])

        self.given(u'''
            '12'..'42'
        ''',
        expect_full_match=[b'12', b'22', b'32', b'42', b'19', b'41', b'35'],
        no_match=[b'1', b'2', b'1242', b'4212'])

        self.given(u'''
            '24'..'42'
        ''',
        expect_full_match=[b'24', b'39', b'40', b'42'],
        no_match=[b'2', b'4', b'2442', b'4224'])

        self.given(u'''
            '38'..'42'
        ''',
        expect_full_match=[b'38', b'39', b'40', b'41', b'42'],
        no_match=[b'3', b'4', b'3842'])

        self.given(u'''
            '0'..'90'
        ''',
        expect_full_match=[b'0', b'1', b'2', b'5', b'7', b'8', b'9', b'10', b'11', b'30', b'42', b'69', b'83', b'88', b'89', b'90'],
        no_match=[b'09', b'090', b'900'])

        self.given(u'''
            '9'..'90'
        ''',
        expect_full_match=[b'9', b'10', b'19', b'42', b'89', b'90'],
        no_match=[b'09', b'99', b'900'])

        self.given(u'''
            '10'..'90'
        ''',
        expect_full_match=[b'10', b'19', b'20', b'42', b'89', b'90'],
        no_match=[b'0', b'1', b'100', b'900', b'010'])

        self.given(u'''
            '0'..'98'
        ''',
        expect_full_match=[b'0', b'1', b'8', b'9', b'18', b'20', b'42', b'89', b'90', b'97', b'98'],
        no_match=[b'00', b'09', b'098', b'980'])

        self.given(u'''
            '1'..'98'
        ''',
        expect_full_match=[b'1', b'8', b'9', b'18', b'20', b'42', b'89', b'90', b'97', b'98'],
        no_match=[b'0', b'01', b'09', b'098', b'198', b'980'])

        self.given(u'''
            '0'..'99'
        ''',
        expect_full_match=[b'0', b'1', b'8', b'9', b'18', b'20', b'42', b'89', b'90', b'97', b'98', b'99'],
        no_match=[b'00', b'09', b'099', b'990'],
        partial_match={
            '0xcafebabe' : '0',
            '9z' : '9',
            '12ab' : '12',
            '3.1415' : '3',
        })

        self.given(u'''
            '1'..'99'
        ''',
        expect_full_match=[b'1', b'8', b'9', b'18', b'20', b'42', b'89', b'90', b'97', b'98', b'99'],
        no_match=[b'0', b'01', b'09', b'099', b'199', b'991'])

        self.given(u'''
            '2'..'99'
        ''',
        expect_full_match=[b'2', b'8', b'9', b'18', b'20', b'42', b'89', b'90', b'97', b'98', b'99'],
        no_match=[b'0', b'1', b'02', b'099', b'990'])

        self.given(u'''
            '9'..'99'
        ''',
        expect_full_match=[b'9', b'18', b'20', b'42', b'89', b'90', b'97', b'98', b'99'],
        no_match=[b'0', b'1', b'09', b'099', b'990'])

        self.given(u'''
            '10'..'99'
        ''',
        expect_full_match=[b'10', b'18', b'19', b'20', b'42', b'89', b'90', b'97', b'98', b'99'],
        no_match=[b'1', b'010', b'100', b'099', b'990', b'1099'])

        self.given(u'''
            '11'..'99'
        ''',
        expect_full_match=[b'11', b'18', b'20', b'42', b'89', b'90', b'97', b'98', b'99'],
        no_match=[b'0', b'1', b'9', b'10', b'011', b'110', b'099', b'990', b'1199'])

        self.given(u'''
            '19'..'99'
        ''',
        expect_full_match=[b'19', b'20', b'42', b'89', b'90', b'97', b'98', b'99'],
        no_match=[b'0', b'1', b'9', b'10', b'019', b'190', b'099', b'990', b'1999'])

        self.given(u'''
            '20'..'99'
        ''',
        expect_full_match=[b'20', b'42', b'89', b'90', b'97', b'98', b'99'],
        no_match=[b'2', b'9', b'020', b'200', b'099', b'990', b'2099'])

        self.given(u'''
            '29'..'99'
        ''',
        expect_full_match=[b'29', b'42', b'89', b'90', b'97', b'98', b'99'],
        no_match=[b'2', b'9', b'029', b'290', b'099', b'990', b'2999'])

        self.given(u'''
            '46'..'99'
        ''',
        expect_full_match=[b'46', b'85', b'90', b'97', b'98', b'99'],
        no_match=[b'4', b'9', b'046', b'460', b'099', b'990', b'4699'])

        self.given(u'''
            '80'..'99'
        ''',
        expect_full_match=[b'80', b'85', b'90', b'97', b'98', b'99'],
        no_match=[b'8', b'9', b'080', b'800', b'099', b'990', b'8099'])

        self.given(u'''
            '89'..'99'
        ''',
        expect_full_match=[b'89', b'90', b'97', b'98', b'99'],
        no_match=[b'8', b'9', b'089', b'890', b'099', b'990', b'8099'])

        self.given(u'''
            '90'..'99'
        ''',
        expect_full_match=[b'90', b'91', b'92', b'95', b'97', b'98', b'99'],
        no_match=[b'9', b'090', b'900', b'099', b'990', b'9099'])

        self.given(u'''
            '0'..'100'
        ''',
        expect_full_match=[b'0', b'1', b'2', b'9', b'10', b'46', b'99', b'100'],
        no_match=[b'00', b'010', b'0100', b'1000'])

        self.given(u'''
            '10'..'100'
        ''',
        expect_full_match=[b'10', b'46', b'99', b'100'],
        no_match=[b'1', b'010', b'0100', b'1000'])

        self.given(u'''
            '90'..'100'
        ''',
        expect_full_match=[b'90', b'91', b'92', b'95', b'97', b'98', b'99', b'100'],
        no_match=[b'9', b'090', b'900', b'0100', b'1000'])

        self.given(u'''
            '99'..'100'
        ''',
        expect_full_match=[b'99', b'100'],
        no_match=[b'9', b'1', b'10', b'099', b'0100', b'990', b'1000'])


    def test_00numrange_shortcut(self):
        self.given(u'''
            '00'..'01'
        ''',
        expect_full_match=[b'00', b'01'],
        no_match=[b'0', b'1', b'000', b'001', b'010'])
        
        self.given(u'''
            '000'..'001'
        ''',
        expect_full_match=[b'000', b'001'],
        no_match=[b'0', b'1', b'00', b'01', b'0000', b'0001', b'0010'])
        
        self.given(u'''
            '00'..'02'
        ''',
        expect_full_match=[b'00', b'01', b'02'],
        no_match=[b'0', b'1', b'2', b'000', b'001', b'002', b'020'])

        self.given(u'''
            '00'..'09'
        ''',
        expect_full_match=[b'00', b'01', b'02', b'03', b'04', b'05', b'06', b'07', b'08', b'09'],
        no_match=[b'0', b'1', b'2', b'9', b'000', b'009', b'090', b'010', b'9z', b'3.14'],
        partial_match={
            '09z' : '09',
            '03.14' : '03',
        })

        self.given(u'''
            '01'..'02'
        ''',
        expect_full_match=[b'01', b'02'],
        no_match=[b'0', b'1', b'2', b'001', b'002', b'010', b'020'])

        self.given(u'''
            '01'..'09'
        ''',
        expect_full_match=[b'01', b'02', b'03', b'04', b'05', b'06', b'07', b'08', b'09'],
        no_match=[b'1', b'2', b'3', b'9', b'001', b'009', b'010', b'090'])

        self.given(u'''
            '02'..'09'
        ''',
        expect_full_match=[b'02', b'03', b'04', b'05', b'06', b'07', b'08', b'09'],
        no_match=[b'2', b'9', b'002', b'009', b'020', b'090'])

        self.given(u'''
            '08'..'09'
        ''',
        expect_full_match=[b'08', b'09'],
        no_match=[b'8', b'9', b'008', b'009', b'080', b'090'])

        self.given(u'''
            '00'..'10'
        ''',
        expect_full_match=[b'00', b'01', b'02', b'03', b'04', b'05', b'06', b'07', b'08', b'09', b'10'],
        no_match=[b'0', b'1', b'2', b'9', b'000', b'010', b'100'])

        self.given(u'''
            '01'..'10'
        ''',
        expect_full_match=[b'01', b'02', b'03', b'04', b'05', b'06', b'07', b'08', b'09', b'10'],
        no_match=[b'1', b'2', b'9', b'001', b'010', b'100'])

        self.given(u'''
            '001'..'010'
        ''',
        expect_full_match=[b'001', b'002', b'003', b'004', b'005', b'006', b'007', b'008', b'009', b'010'],
        no_match=[b'1', b'2', b'9', b'10', b'01', b'02', b'0001', b'0010', b'0100'])

        self.given(u'''
            '02'..'10'
        ''',
        expect_full_match=[b'02', b'03', b'04', b'05', b'06', b'07', b'08', b'09', b'10'],
        no_match=[b'2', b'9', b'002', b'020', b'010', b'100'])

        self.given(u'''
            '08'..'10'
        ''',
        expect_full_match=[b'08', b'09', b'10'],
        no_match=[b'8', b'008', b'080', b'010', b'100'])

        self.given(u'''
            '09'..'10'
        ''',
        expect_full_match=[b'09', b'10'],
        no_match=[b'9', b'009', b'090', b'010', b'100'])

        self.given(u'''
            '00'..'11'
        ''',
        expect_full_match=[b'00', b'01', b'05', b'09', b'10', b'11'],
        no_match=[b'0', b'1', b'000', b'001', b'011', b'110'])

        self.given(u'''
            '01'..'11'
        ''',
        expect_full_match=[b'01', b'05', b'09', b'10', b'11'],
        no_match=[b'0', b'1', b'00', b'001', b'010', b'011', b'110'])

        self.given(u'''
            '09'..'11'
        ''',
        expect_full_match=[b'09', b'10', b'11'],
        no_match=[b'0', b'9', b'009', b'090', b'011', b'110'])

        self.given(u'''
            '010'..'011'
        ''',
        expect_full_match=[b'010', b'011'],
        no_match=[b'0', b'01', b'10', b'11', b'0010', b'090', b'0011', b'0100', b'0110'])

        self.given(u'''
            '01'..'12'
        ''',
        expect_full_match=[b'01', b'02', b'05', b'09', b'10', b'11', b'12'],
            no_match=[b'1', b'001', b'012', b'010', b'012'])
        
        self.given(u'''
            '02'..'12'
        ''',
        expect_full_match=[b'02', b'08', b'09', b'10', b'11', b'12'],
        no_match=[b'2', b'8', b'9', b'002', b'009', b'020', b'012', b'120'])

        self.given(u'''
            '000'..'012'
        ''',
        expect_full_match=[b'000', b'001', b'002', b'008', b'009', b'010', b'011', b'012'],
        no_match=[b'0', b'1', b'2', b'10', b'12', b'0000', b'0012', b'0120'])
        
        self.given(u'''
            '00'..'19'
        ''',
        expect_full_match=[b'00', b'01', b'02', b'09', b'10', b'18', b'19'],
        no_match=[b'0', b'1', b'000', b'019', b'190'])

        self.given(u'''
            '01'..'19'
        ''',
        expect_full_match=[b'01', b'02', b'09', b'10', b'18', b'19'],
        no_match=[b'0', b'1', b'000', b'019', b'190'])

        self.given(u'''
            '09'..'19'
        ''',
        expect_full_match=[b'09', b'10', b'18', b'19'],
        no_match=[b'0', b'1', b'9', b'009', b'019', b'090', b'190'])

        self.given(u'''
            '010'..'019'
        ''',
        expect_full_match=[b'010', b'011', b'015', b'018', b'019'],
        no_match=[b'0', b'1', b'10', b'11', b'19' '0010', b'0190', b'0100', b'0190'])

        self.given(u'''
            '00'..'20'
        ''',
        expect_full_match=[b'00', b'01', b'02', b'10', b'19', b'20'],
        no_match=[b'0', b'2', b'000', b'020', b'200'])

        self.given(u'''
            '02'..'20'
        ''',
        expect_full_match=[b'02', b'10', b'19', b'20'],
        no_match=[b'0', b'2', b'002', b'020', b'200'])

        self.given(u'''
            '010'..'020'
        ''',
        expect_full_match=[b'010', b'011', b'012', b'015', b'018', b'019', b'020'],
        no_match=[b'0', b'01', b'02', b'10', b'20', b'0100', b'0200', b'0010', b'0020'])

        self.given(u'''
            '019'..'020'
        ''',
        expect_full_match=[b'019', b'020'],
        no_match=[b'0', b'01', b'02', b'19', b'20', b'0190', b'0200', b'0019', b'0020'])


    def test_oonumrange_shortcut(self):
        self.given(u'''
            'o0'..'o1'
        ''',
        expect_full_match=[b'0', b'1', b'00', b'01'],
        no_match=[b'000', b'001', b'010'])
        
        self.given(u'''
            'oo0'..'oo1'
        ''',
        expect_full_match=[b'0', b'1', b'00', b'01', b'000', b'001'],
        no_match=[b'0000', b'0001', b'0010'])
        
        self.given(u'''
            'o0'..'o2'
        ''',
        expect_full_match=[b'0', b'1', b'2', b'00', b'01', b'02'],
        no_match=[b'000', b'001', b'002', b'020'])

        self.given(u'''
            'o0'..'o9'
        ''',
        expect_full_match=[b'0', b'1', b'2', b'9', b'00', b'01', b'02', b'03', b'04', b'05', b'06', b'07', b'08', b'09'],
        no_match=[b'000', b'009', b'090', b'010'],
        partial_match={
            '9z' : '9',
            '09z' : '09',
            '3.14' : '3',
            '03.14' : '03',
        })

        self.given(u'''
            'o1'..'o2'
        ''',
        expect_full_match=[b'1', b'2', b'01', b'02'],
        no_match=[b'0', b'001', b'002', b'010', b'020'])

        self.given(u'''
            'o1'..'o9'
        ''',
        expect_full_match=[b'1', b'2', b'3', b'9', b'01', b'02', b'03', b'04', b'05', b'06', b'07', b'08', b'09'],
        no_match=[b'001', b'009', b'010', b'090'])

        self.given(u'''
            'o2'..'o9'
        ''',
        expect_full_match=[b'2', b'9', b'02', b'03', b'04', b'05', b'06', b'07', b'08', b'09'],
        no_match=[b'002', b'009', b'020', b'090'])

        self.given(u'''
            'o8'..'o9'
        ''',
        expect_full_match=[b'8', b'9', b'08', b'09'],
        no_match=[b'008', b'009', b'080', b'090'])

        self.given(u'''
            'o0'..'10'
        ''',
        expect_full_match=[b'0', b'1', b'2', b'9', b'00', b'01', b'02', b'03', b'04', b'05', b'06', b'07', b'08', b'09', b'10'],
        no_match=[b'000', b'010', b'100'])

        self.given(u'''
            'o1'..'10'
        ''',
        expect_full_match=[b'1', b'2', b'9', b'01', b'02', b'03', b'04', b'05', b'06', b'07', b'08', b'09', b'10'],
        no_match=[b'001', b'010', b'100'])

        self.given(u'''
            'oo1'..'o10'
        ''',
        expect_full_match=[b'1', b'2', b'9', b'10', b'01', b'02', b'001', b'002', b'003', b'004', b'005', b'006', b'007', b'008', b'009', b'010'],
        no_match=[b'0001', b'0010', b'0100'])

        self.given(u'''
            'o2'..'10'
        ''',
        expect_full_match=[b'2', b'9', b'02', b'03', b'04', b'05', b'06', b'07', b'08', b'09', b'10'],
        no_match=[b'002', b'020', b'010', b'100'])

        self.given(u'''
            'o8'..'10'
        ''',
        expect_full_match=[b'8', b'08', b'09', b'10'],
        no_match=[b'008', b'080', b'010', b'100'])

        self.given(u'''
            'o9'..'10'
        ''',
        expect_full_match=[b'9', b'09', b'10'],
        no_match=[b'009', b'090', b'010', b'100'])

        self.given(u'''
            'o0'..'11'
        ''',
        expect_full_match=[b'0', b'1', b'00', b'01', b'05', b'09', b'10', b'11'],
        no_match=[b'000', b'001', b'011', b'110'])

        self.given(u'''
            'o1'..'11'
        ''',
        expect_full_match=[b'1', b'01', b'05', b'09', b'10', b'11'],
        no_match=[b'0', b'00', b'001', b'010', b'011', b'110'])

        self.given(u'''
            'o9'..'11'
        ''',
        expect_full_match=[b'9', b'09', b'10', b'11'],
        no_match=[b'0', b'009', b'090', b'011', b'110'])

        self.given(u'''
            'o10'..'o11'
        ''',
        expect_full_match=[b'10', b'11', b'010', b'011'],
        no_match=[b'0', b'01', b'0010', b'090', b'0011', b'0100', b'0110'])

        self.given(u'''
            'o1'..'12'
        ''',
        expect_full_match=[b'1', b'01', b'02', b'05', b'09', b'10', b'11', b'12'],
        no_match=[b'001', b'012', b'010', b'012'])
        
        self.given(u'''
            'o2'..'12'
        ''',
        expect_full_match=[b'2', b'8', b'9', b'02', b'08', b'09', b'10', b'11', b'12'],
        no_match=[b'002', b'009', b'020', b'012', b'120'])

        self.given(u'''
            'oo0'..'o12'
        ''',
        expect_full_match=[b'0', b'1', b'2', b'10', b'12', b'000', b'001', b'002', b'008', b'009', b'010', b'011', b'012'],
        no_match=[b'0000', b'0012', b'0120'])
        
        self.given(u'''
            'o0'..'19'
        ''',
        expect_full_match=[b'0', b'1', b'00', b'01', b'02', b'09', b'10', b'18', b'19'],
        no_match=[b'000', b'019', b'190'])

        self.given(u'''
            'o1'..'19'
        ''',
        expect_full_match=[b'1', b'01', b'02', b'09', b'10', b'18', b'19'],
        no_match=[b'0', b'000', b'019', b'190'])

        self.given(u'''
            'o9'..'19'
        ''',
        expect_full_match=[b'9', b'09', b'10', b'18', b'19'],
        no_match=[b'0', b'1', b'009', b'019', b'090', b'190'])

        self.given(u'''
            'o10'..'o19'
        ''',
        expect_full_match=[b'10', b'11', b'19', b'010', b'011', b'015', b'018', b'019'],
        no_match=[b'0', b'1', b'0010', b'0190', b'0100', b'0190'])

        self.given(u'''
            'o0'..'20'
        ''',
        expect_full_match=[b'0', b'2', b'00', b'01', b'02', b'10', b'19', b'20'],
        no_match=[b'000', b'020', b'200'])

        self.given(u'''
            'o2'..'20'
        ''',
        expect_full_match=[b'2', b'02', b'10', b'19', b'20'],
        no_match=[b'0', b'002', b'020', b'200'])

        self.given(u'''
            'o10'..'o20'
        ''',
        expect_full_match=[b'10', b'20', b'010', b'011', b'012', b'015', b'018', b'019', b'020'],
        no_match=[b'0', b'01', b'02', b'0100', b'0200', b'0010', b'0020'])

        self.given(u'''
            'o19'..'o20'
        ''',
        expect_full_match=[b'19', b'20', b'019', b'020'],
        no_match=[b'0', b'01', b'02', b'0190', b'0200', b'0019', b'0020'])


    def test_norange_shortcut(self):
        self.given(u'''
            '0'..'0'
        ''',
        expect_full_match=[b'0'],
        no_match=[b'00', b'01', b'1'])

        self.given(u'''
            '00'..'00'
        ''',
        expect_full_match=[b'00'],
        no_match=[b'0', b'01', b'000'])

        self.given(u'''
            '000'..'000'
        ''',
        expect_full_match=[b'000'],
        no_match=[b'0', b'00', b'0000', b'0001', b'001'])

        self.given(u'''
            '007'..'007'
        ''',
        expect_full_match=[b'007'],
        no_match=[b'0', b'00', b'07', b'7', b'0070', b'0007', b'006', b'008'])
        
        self.given(u'''
            '1'..'1'
        ''',
        expect_full_match=[b'1'],
        no_match=[b'00', b'01', b'0', b'2'])

        self.given(u'''
            '2'..'2'
        ''',
        expect_full_match=[b'2'],
        no_match=[b'0', b'1', b'3', b'02', b'20'])

        self.given(u'''
            '9'..'9'
        ''',
        expect_full_match=[b'9'],
        no_match=[b'0', b'8', b'10', b'09', b'90'])

        self.given(u'''
            '10'..'10'
        ''',
        expect_full_match=[b'10'],
        no_match=[b'0', b'1', b'9', b'11', b'010', b'100'])

        self.given(u'''
            '99'..'99'
        ''',
        expect_full_match=[b'99'],
        no_match=[b'0', b'9', b'98', b'100', b'099', b'990'])

        self.given(u'''
            '100'..'100'
        ''',
        expect_full_match=[b'100'],
        no_match=[b'0', b'1', b'99', b'101', b'0100', b'1000'])

        self.given(u'''
            '123'..'123'
        ''',
        expect_full_match=[b'123'],
        no_match=[b'1', b'12', b'122', b'124', b'023', b'1230'])

        self.given(u'''
            '12345'..'12345'
        ''',
        expect_full_match=[b'12345'],
        no_match=[b'0', b'1', b'12', b'123', b'1234', b'12344', b'12346', b'012345', b'123450'])

        self.given(u'''
            '9999999'..'9999999'
        ''',
        expect_full_match=[b'9999999'],
        no_match=[b'99999999', b'999999', b'99999', b'9999', b'999', b'99', b'9', b'9999998', b'10000000', b'09999999', b'99999990'])

        self.given(u'''
            'o0'..'o0'
        ''',
        expect_full_match=[b'0', b'00'],
        no_match=[b'000', b'1', b'01'])

        self.given(u'''
            'oo0'..'oo0'
        ''',
        expect_full_match=[b'0', b'00', b'000'],
        no_match=[b'0000', b'1', b'01', b'001'])

        self.given(u'''
            'ooo0'..'ooo0'
        ''',
        expect_full_match=[b'0', b'00', b'000', b'0000'],
        no_match=[b'00000', b'1', b'01', b'001', b'0001'])

        self.given(u'''
            'o1'..'o1'
        ''',
        expect_full_match=[b'1', b'01'],
        no_match=[b'001', b'0', b'00', b'02', b'010'])

        self.given(u'''
            'oo9'..'oo9'
        ''',
        expect_full_match=[b'9', b'09', b'009'],
        no_match=[b'0009', b'0', b'00', b'008', b'010', b'0090'])

        self.given(u'''
            'o10'..'o10'
        ''',
        expect_full_match=[b'10', b'010'],
        no_match=[b'0', b'01', b'009', b'011', b'0100', b'0010'])

        self.given(u'''
            'oo100'..'oo100'
        ''',
        expect_full_match=[b'100', b'0100', b'00100'],
        no_match=[b'0', b'1', b'10', b'00', b'01', b'010', b'000' '001', b'0010', b'99', b'101'])

        self.given(u'''
            'o9999'..'o9999'
        ''',
        expect_full_match=[b'9999', b'09999'],
        no_match=[b'0', b'9', b'09', b'099', b'0999', b'9998', b'10000', b'99990'])

        self.given(u'''
            'ooo9999'..'ooo9999'
        ''',
        expect_full_match=[b'9999', b'09999', b'009999', b'0009999'],
        no_match=[b'0', b'9', b'09', b'099', b'0999', b'009', b'0099', b'00999', b'0009', b'00099', b'000999', b'9998', b'10000'])
        
        
    def test_infinite_numrange(self):
        self.given(u'''
            '0'..
        ''',
        expect_full_match=[b'0', b'1', b'2', b'10', b'11', b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295'],
        no_match=[b'00', b'01', b'02', b'010', b'011', b'020', b'0100', b'0200', b'01000', b'09999', b'065535', b'04294967295'])

        self.given(u'''
            '1'..
        ''',
        expect_full_match=[b'1', b'2', b'10', b'11', b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295'],
        no_match=[b'0', b'00', b'01', b'02', b'010', b'011', b'020', b'0100', b'0200'])

        self.given(u'''
            '2'..
        ''',
        expect_full_match=[b'2', b'10', b'11', b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295'],
        no_match=[b'0', b'1', b'00', b'01', b'02', b'010', b'011', b'020', b'0100', b'0200'])

        self.given(u'''
            '10'..
        ''',
        expect_full_match=[b'10', b'11', b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295'],
        no_match=[b'0', b'1', b'2', b'00', b'01', b'02', b'010', b'011', b'020', b'0100', b'0200'])

        self.given(u'''
            '20'..
        ''',
        expect_full_match=[b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295'],
        no_match=[b'0', b'1', b'2', b'10', b'11', b'00', b'01', b'02', b'010', b'011', b'020', b'0100', b'0200'])

        self.given(u'''
            '46'..
        ''',
        expect_full_match=[b'100', b'200', b'1000', b'9999', b'65535', b'4294967295'],
        no_match=[b'0', b'1', b'2', b'10', b'11', b'20', b'00', b'01', b'02', b'010', b'011', b'020', b'0100', b'0200'])

        self.given(u'''
            '100'..
        ''',
        expect_full_match=[b'100', b'200', b'1000', b'9999', b'65535', b'4294967295'],
        no_match=[b'0', b'1', b'2', b'10', b'11', b'20', b'00', b'01', b'02', b'010', b'011', b'020', b'0100', b'0200'])

        self.given(u'''
            '200'..
        ''',
        expect_full_match=[b'200', b'1000', b'9999', b'65535', b'4294967295'],
        no_match=[b'0', b'1', b'2', b'10', b'11', b'20', b'100', b'00', b'01', b'02', b'010', b'011', b'020', b'0100', b'0200'])

        self.given(u'''
            '234'..
        ''',
        expect_full_match=[b'1000', b'9999', b'65535', b'4294967295'],
        no_match=[b'0', b'1', b'2', b'10', b'11', b'20', b'100', b'200', b'00', b'01', b'02', b'010', b'011', b'020', b'0100', b'0200'])

        self.given(u'''
            ? of '1'..
        ''',
        expect_full_match=[b'1', b'2', b'10', b'11', b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295'],
        partial_match={'0':'', b'00':'', b'01':'', b'02':'', b'010':'', b'011':'', b'020':'', b'0100':'', b'0200':''})

        self.given(u'''
            ? of '2'..
        ''',
        expect_full_match=[b'2', b'10', b'11', b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295'],
        partial_match={'0':'', b'1':'', b'00':'', b'01':'', b'02':'', b'010':'', b'011':'', b'020':'', b'0100':'', b'0200':''})


    def test_infinite_onumrange(self):
        self.given(u'''
            'o0'..
        ''',
        expect_full_match=[b'0', b'1', b'2', b'10', b'11', b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295',
                '00', b'01', b'02', b'010', b'011', b'020', b'0100', b'0200', b'01000', b'09999', b'065535', b'04294967295',
                '000', b'001', b'002', b'0010', b'0011', b'0020', b'00100', b'00200', b'001000', b'009999', b'0065535', b'004294967295',
                '0000', b'0001', b'0002', b'00010', b'00011', b'00020', b'000100', b'000200', b'0001000', b'0009999', b'00065535', b'0004294967295'],
        no_match=[b''])

        self.given(u'''
            'o1'..
        ''',
        expect_full_match=[b'1', b'2', b'10', b'11', b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295',
                        '01', b'02', b'010', b'011', b'020', b'0100', b'0200',
                        '001', b'002', b'0010', b'0011', b'0020', b'00100', b'00200'],
        no_match=[b'', b'0', b'00', b'000', b'0000', b'00000'])

        self.given(u'''
            'o2'..
        ''',
        expect_full_match=[b'2', b'10', b'11', b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295',
                        '02', b'010', b'011', b'020', b'0100', b'0200'],
        no_match=[b'', b'0', b'1', b'00', b'01', b'000', b'001'])

        self.given(u'''
            'o10'..
        ''',
        expect_full_match=[b'10', b'11', b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295',
                        '010', b'011', b'020', b'0100', b'0200'],
        no_match=[b'', b'0', b'1', b'2', b'00', b'01', b'02', b'000', b'001', b'002'])

        self.given(u'''
            'o20'..
        ''',
        expect_full_match=[b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295',
                        '020', b'0100', b'0200', b'0020', b'00100', b'00200'],
        no_match=[b'', b'0', b'1', b'2', b'10', b'11', b'00', b'01', b'02', b'010', b'011', b'000', b'001', b'002'])

        self.given(u'''
            'o46'..
        ''',
        expect_full_match=[b'100', b'200', b'1000', b'9999', b'65535', b'4294967295',
                        '0100', b'0200', b'00100', b'00200'],
        no_match=[b'', b'0', b'1', b'2', b'10', b'11', b'20', b'00', b'01', b'02', b'010', b'011', b'020', b'000', b'001', b'002'])

        self.given(u'''
            'o100'..
        ''',
        expect_full_match=[b'100', b'200', b'1000', b'9999', b'65535', b'4294967295',
                        '0100', b'0200', b'00100', b'00200'],
        no_match=[b'', b'0', b'1', b'2', b'10', b'11', b'20', b'00', b'01', b'02', b'010', b'011', b'020', b'000', b'001', b'002'])

        self.given(u'''
            'o200'..
        ''',
        expect_full_match=[b'200', b'1000', b'9999', b'65535', b'4294967295', b'0200', b'00200'],
        no_match=[b'', b'0', b'1', b'2', b'10', b'11', b'20', b'100', b'00', b'01', b'02', b'010', b'011', b'020', b'0100'])

        self.given(u'''
            'o234'..
        ''',
        expect_full_match=[b'1000', b'9999', b'65535', b'4294967295', b'01000', b'001000'],
        no_match=[b'', b'0', b'1', b'2', b'10', b'11', b'20', b'100', b'200', b'00', b'01', b'02', b'010', b'011', b'020', b'0100', b'0200'])

        self.given(u'''
            ? of 'o0'..
        ''',
        expect_full_match=[b'', b'0', b'1', b'2', b'10', b'11', b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295',
                '00', b'01', b'02', b'010', b'011', b'020', b'0100', b'0200', b'01000', b'09999', b'065535', b'04294967295',
                '000', b'001', b'002', b'0010', b'0011', b'0020', b'00100', b'00200', b'001000', b'009999', b'0065535', b'004294967295',
                '0000', b'0001', b'0002', b'00010', b'00011', b'00020', b'000100', b'000200', b'0001000', b'0009999', b'00065535', b'0004294967295'],
        no_match=[])

        self.given(u'''
            ? of 'o1'..
        ''',
        expect_full_match=[b'', b'1', b'2', b'10', b'11', b'20', b'100', b'200', b'1000', b'9999', b'65535', b'4294967295',
                '01', b'02', b'010', b'011', b'020', b'0100', b'0200', b'01000', b'09999', b'065535', b'04294967295',
                '01', b'002', b'0010', b'0011', b'0020', b'00100', b'00200', b'001000', b'009999', b'0065535', b'004294967295',
                '0001', b'0002', b'00010', b'00011', b'00020', b'000100', b'000200', b'0001000', b'0009999', b'00065535', b'0004294967295'],
        partial_match={'0':'', b'00':'', b'000':'', b'0000':''})


    def test_wordchar_redef(self):
        self.given(u'''
            .'cat'_
*)              wordchar: upper lower -
        ''',
        expect_full_match=[],
        no_match=[b'cat', b'cat9', b'bobcat', b'that-cat'],
        partial_match={
            'catasthropic' : 'cat',
            'cat-like' : 'cat',
            'cat-9' : 'cat',
        })


    def test_lazydotstar(self):
        self.given(u'''
            /quote/__?/quote/
                quote: "
        ''',
        expect_full_match=[b'"Hi!"', b'""'],
        no_match=[b'"unclosed'],
        partial_match={
            '"Hi!", he said, "How are you?"' : '"Hi!"',
        })
        
        self.given(u'''
            /quote/__/quote/
                quote: "
        ''',
        expect_full_match=[b'"Hi!"'],
        no_match=[b'"unclosed', b'""'],
        partial_match={
            '"Hi!", he said, "How are you?"' : '"Hi!"',
        })
        
        self.given(u'''
            /open/__/close/
                open: (
                close: )
        ''',
        expect_full_match=[b'(sic)', b'({})'],
        no_match=[b'(unclosed', b'()'],
        partial_match={
            '((x+y)*z)' : '((x+y)',
        })
        
        self.given(u'''
            /BEGIN/__?/END/
                BEGIN = 'BEGIN'
                END = 'END'
        ''',
        expect_full_match=[b'BEGINEND', b'BEGIN END', b'BEGINNING END', b'BEGIN SECRET MESSAGE END'],
        partial_match={
            'BEGINNINGENDING' : 'BEGINNINGEND',
            'BEGIN DONT SEND THE PACKAGE YET END' : 'BEGIN DONT SEND',
        })
        
        self.given(u'''
            /BEGIN/__?/END/
                BEGIN = 'BEGIN'
                END = .'END'
        ''',
        expect_full_match=[b'BEGIN END', b'BEGINNING END', b'BEGIN SECRET MESSAGE END', b'BEGIN DONT SEND THE PACKAGE YET END'],
        no_match=[b'BEGINEND'])
        
        self.given(u'''
            /__/END/
                END = '.'
        ''',
        expect_full_match=[b'this.'],
        no_match=[b'.', b'.com', b'...'],
        partial_match={
            'example.com' : 'example.',
            'Hmm...' : 'Hmm.',
        })
        
        self.given(u'''
            /__?/END/
                END = 'Z'
        ''',
        expect_full_match=[b'Z', b'WoZ', b'ATOZ', b'A TO Z'],
        partial_match={'ZOO' : 'Z', b'PIZZA' : 'PIZ'})
        
        self.given(u'''
            /__?/END/
                END = .'Z'
        ''',
        expect_full_match=[b'Z', b'A TO Z'],
        no_match=[b'WoZ', b'ATOZ', b'PIZZA'],
        partial_match={'ZOO' : 'Z'})
        
        self.given(u'''
            /__?/END/
                END = _'Z'
        ''',
        expect_full_match=[b'WoZ', b'ATOZ'],
        no_match=[b'Z', b'A TO Z', b'ZOO'],
        partial_match={'PIZZA' : 'PIZ'})
        

class TestSampleFiles(unittest.TestCase):
    def test_sample_files(self):
        try:
            samples_dir = os.path.join(os.path.dirname(__file__), b'samples')
            for f in os.listdir(samples_dir):
                filename = os.path.join(samples_dir, f)
                with open(filename) as f:
                    contents = f.read()
                    oprex(contents)
        except OprexSyntaxError as e:
            msg = '\nFile: %s\n' % filename
            msg += contents
            msg += e.message
            raise OprexSyntaxError(None, msg)


if __name__ == '__main__':
    unittest.main()
