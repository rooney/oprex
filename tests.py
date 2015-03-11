# -*- coding: utf-8 -*-

import unittest, regex
from oprex import oprex, OprexSyntaxError

def assertion_error(msg):
    raise AssertionError(msg.encode('utf-8'))


class TestErrorHandling(unittest.TestCase):
    def given(self, oprex_source, expect_error):
        expect_error = '\n' + expect_error
        try:
            oprex(oprex_source)
        except Exception as err:
            got_error = err.message
        else:
            got_error = ''

        if got_error != expect_error:
            msg = 'For input: %s\n----------------------------- Got Error: -----------------------------%s\n\n-------------------------- Expected Error: ---------------------------%s'
            assertion_error(msg % (
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
        expect_error='Line 2: Unsupported syntax: `@$%^&;{}[]\\')


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
        expect_error='Line 4: Unexpected INDENT')


    def test_indentation_error(self):
        self.given('''
            /greeting/world/
                greeting = 'hello'
                 world = 'world'
        ''',
        expect_error='Line 4: Unexpected INDENT')

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
        expect_error='Line 5: Unexpected INDENT')

        self.given('''

            /greeting/world/


                greeting = 'hello'

                 world = 'world'
        ''',
        expect_error='Line 8: Unexpected INDENT')

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

        self.given('''
            unicorn
                unicorn = unicorn
        ''',
        expect_error="Line 3: 'unicorn' is not defined")


    def test_illegal_variable_name(self):
        self.given('''
            101dalmatians
        ''',
        expect_error='Line 2: Illegal name (must start with a letter): 101dalmatians')

        self.given('''
            _this_
        ''',
        expect_error='Line 2: Illegal name (must start with a letter): _this_')

        self.given('''
            etc_
        ''',
        expect_error='Line 2: Illegal name (must not end with underscore): etc_')


    def test_duplicate_variable(self):
        self.given('''
            dejavu
                dejavu = 'Déjà vu'
                dejavu = 'Déjà vu'
        ''',
        expect_error="Line 4: Names must be unique within a scope, 'dejavu' is already defined (previous definition at line 3)")

        self.given('''
            dejavu
                dejavu = dejavu = 'Déjà vu'
        ''',
        expect_error="Line 3: Names must be unique within a scope, 'dejavu' is already defined (previous definition at line 3)")

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


    def test_unclosed_literal(self):
        self.given('''
            mcd
                mcd = 'McDonald's
        ''',
        expect_error="Line 3: Missing closing quote: 'McDonald's")

        self.given('''
            quotes_mismatch
                quotes_mismatch = "'
        ''',
        expect_error="""Line 3: Missing closing quote: "'""")


    def test_invalid_global_mark(self):
        self.given('''
            *)
        ''',
        expect_error="Line 2: The GLOBALMARK *) must be put at the line's beginning")

        self.given('''
*)
        ''',
        expect_error='Line 2: Indentation required after GLOBALMARK *)')

        self.given('''
*)\t
        ''',
        expect_error='Line 2: Unexpected GLOBALMARK\n*)\t\n^')

        self.given('''
*)warming
        ''',
        expect_error='Line 2: Indentation required after GLOBALMARK *)')

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
        expect_error="Line 3: Unsupported syntax: *) = 'global'")

        self.given('''
            warming
                warming = global *)
        ''',
        expect_error="Line 3: Syntax error:                 warming = global *)")

        self.given('''
            warming
                warming = *) 'global'
        ''',
        expect_error="Line 3: Unsupported syntax: *) 'global'")

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
        expect_error="Line 3: Unsupported syntax: *) = 'global'")

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
        expect_error="Line 4: Indentation required after GLOBALMARK *)")

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
        expect_error='Line 3: Empty character class is not allowed')

        self.given('''
            noSpaceAfterColon
                noSpaceAfterColon:n o
        ''',
        expect_error='Line 3: Character class definition requires space after the : (colon)')

        self.given('''
            diphtong
                diphtong: ae au
        ''',
        expect_error='Line 3: Not a valid character class keyword: ae')

        self.given('''
            miscolon
                miscolon: /colon/should/be/equal/sign/
        ''',
        expect_error='Line 3: /colon/should/be/equal/sign/ compiles to \p{colon/should/be/equal/sign/} which is rejected by the regex module with error message: bad fuzzy constraint')

        self.given('''
            miscolon
                miscolon: 'colon should be equal sign'
        ''',
        expect_error="Line 3: Not a valid character class keyword: 'colon")

        self.given('''
            /A/a/
                A: a: A a
        ''',
        expect_error='Line 3: Not a valid character class keyword: a:')

        self.given('''
            /A/a/
                A: a = A a
        ''',
        expect_error='Line 3: Duplicate character in character class definition: a')

        self.given('''
            /A/a/
                A: a = A
        ''',
        expect_error="Line 2: 'a' is not defined")

        self.given('''
            /shouldBeColon/
                shouldBeColon = A a
        ''',
        expect_error='Line 3: Unexpected WHITESPACE\n                shouldBeColon = A a\n                                 ^')

        self.given('''
            mixedAssignment
                mixedAssignment := x
        ''',
        expect_error='Line 3: Unexpected WHITESPACE\n                mixedAssignment := x\n                               ^')

        self.given('''
            mixedAssignment
                mixedAssignment:= x
        ''',
        expect_error='Line 3: Character class definition requires space after the : (colon)')

        self.given('''
            mixedAssignment
                mixedAssignment=: x
        ''',
        expect_error='Line 3: Unexpected COLON\n                mixedAssignment=: x\n                                ^')

        self.given('''
            mixedAssignment
                mixedAssignment =: x
        ''',
        expect_error='Line 3: Unexpected COLON\n                mixedAssignment =: x\n                                 ^')

        self.given('''
            x
                x: /IsAwesome
        ''',
        expect_error='Line 3: /IsAwesome compiles to \p{IsAwesome} which is rejected by the regex module with error message: unknown property')


    def test_invalid_char(self):
        self.given('''
            x
                x: u1234
        ''',
        expect_error='Line 3: Not a valid character class keyword: u1234')

        self.given('''
            x
                x: u+123z
        ''',
        expect_error='Line 3: Syntax error u+123z should be U+hexnumber')

        self.given('''
            x
                x: U+123456789
        ''',
        expect_error='Line 3: Syntax error U+123456789 out of range')

        self.given('''
            x
                x: U+
        ''',
        expect_error='Line 3: Syntax error U+ should be U+hexnumber')

        self.given('''
            x
                x: :YET_ANOTHER_CHARACTER_THAT_SHOULD_NOT_BE_IN_UNICODE
        ''',
        expect_error='Line 3: :YET_ANOTHER_CHARACTER_THAT_SHOULD_NOT_BE_IN_UNICODE compiles to \N{YET ANOTHER CHARACTER THAT SHOULD NOT BE IN UNICODE} which is rejected by the regex module with error message: undefined character name')

        # unicode character name should be in uppercase
        self.given('''
            x
                x: check-mark
        ''',
        expect_error='Line 3: Not a valid character class keyword: check-mark')

        self.given('''
            x
                x: @omic
        ''',
        expect_error='Line 3: Not a valid character class keyword: @omic')

        self.given('''
            x
                x: awe$ome
        ''',
        expect_error='Line 3: Not a valid character class keyword: awe$ome')


    def test_invalid_range(self):
        self.given('''
            x
                x: ..
        ''',
        expect_error='Line 3: Invalid character range: ..')

        self.given('''
            x
                x: infinity..
        ''',
        expect_error='Line 3: Invalid character range: infinity..')

        self.given('''
            x
                x: ..bigbang
        ''',
        expect_error='Line 3: Invalid character range: ..bigbang')

        self.given('''
            x
                x: bigcrunch..bigbang
        ''',
        expect_error='Line 3: Invalid character range: bigcrunch..bigbang')

        self.given('''
            x
                x: A...Z
        ''',
        expect_error='Line 3: Invalid character range: A...Z')

        self.given('''
            x
                x: 1..2..3
        ''',
        expect_error='Line 3: Invalid character range: 1..2..3')

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


    def test_invalid_charclass_include(self):
        self.given('''
            x
                x: +1
        ''',
        expect_error="Line 3: Cannot include '1': not defined")

        self.given('''
            x
                x: +7even
                    7even: 7
        ''',
        expect_error='Line 4: Illegal name (must start with a letter): 7even')

        self.given('''
            x
                x: +bang!
        ''',
        expect_error="Line 3: Cannot include 'bang!': not defined")

        self.given('''
            x
                x: ++
        ''',
        expect_error="Line 3: Cannot include '+': not defined")

        self.given('''
            x
                x: ++
                    +: p l u s
        ''',
        expect_error='Line 4: Unsupported syntax: +: p l u s')

        self.given('''
            x
                x: +!awe+some
        ''',
        expect_error="Line 3: Cannot include 'awe+some': not defined")

        self.given('''
            x
                x: +__special__
                    __special__: x
        ''',
        expect_error="Line 4: Illegal name (must start with a letter): __special__")

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


class TestOutput(unittest.TestCase):
    def given(self, oprex_source, expect_regex):
        alwayson_flags = '(?umV1)'
        regex_source = oprex(oprex_source)
        regex_source = regex_source.replace(alwayson_flags, '', 1)
        if regex_source != expect_regex:
            msg = 'For input: %s\n---------------------------- Got Output: -----------------------------\n%s\n\n------------------------- Expected Output: ---------------------------\n%s'
            assertion_error(msg % (
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


    def test_escaping(self):
        self.given('''
            stars
                stars = '***'
        ''',
        expect_regex=r'\*\*\*')


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
                x: /Alphabetic /Script=Latin /InBasicLatin /!IsCyrillic /Script!=Cyrillic /!Script=Cyrillic
        ''',
        expect_regex='[\p{Alphabetic}\p{Script=Latin}\p{InBasicLatin}\P{IsCyrillic}\P{Script=Cyrillic}\P{Script=Cyrillic}]')

        self.given('''
            x
                x: u+ab U+ab u+AB U+AB u+00ab u+00aB U+00ab U+00Ab
        ''',
        expect_regex='[\u00ab\u00ab\u00AB\u00AB\u00ab\u00aB\u00ab\u00Ab]')

        self.given('''
            x
                x: u+12ab u+12AB u+12aB U+12ab U+12AB U+12Ab
        ''',
        expect_regex='[\u12ab\u12AB\u12aB\u12ab\u12AB\u12Ab]')

        self.given('''
            x
                x: u+1234a u+1234A U+1234a U+1234A u+01234A U+01234a
        ''',
        expect_regex='[\U0001234a\U0001234A\U0001234a\U0001234A\U0001234A\U0001234a]')

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


    def test_negated_charclass_output(self):
        self.given(u'''
            notA
                notA: +!A
                    A: A
        ''',
        expect_regex='[^A]')

        self.given(u'''
            notAUmlaut
                notAUmlaut: +!small_a_umlaut
                    small_a_umlaut: +a_with_diaeresis
                        a_with_diaeresis: ä
        ''',
        expect_regex=u'[^ä]')

        self.given(u'''
            notAUmlaut
                notAUmlaut: +!AUmlaut
                    AUmlaut: U+FC
        ''',
        expect_regex=r'[^\u00FC]')

        self.given(u'''
            notAUmlaut
                notAUmlaut: +!a_with_diaeresis
                    a_with_diaeresis: :LATIN_SMALL_LETTER_A_WITH_DIAERESIS
        ''',
        expect_regex=r'[^\N{LATIN SMALL LETTER A WITH DIAERESIS}]')

        self.given(u'''
            alphabetic
                alphabetic: +!nonAlpha
                    nonAlpha: /!Alphabetic
        ''',
        expect_regex=r'[^\P{Alphabetic}]')

        self.given(u'''
            nonhex
                nonhex: +!hexdigit
                    hexdigit: 0..9 a..f A..F
        ''',
        expect_regex='[^0-9a-fA-F]')

        self.given(u'''
            hex
                hex: +!unhex
                    unhex: +!hexdigit
                        hexdigit: 0..9 a..f A..F
        ''',
        expect_regex='[0-9a-fA-F]')

        self.given(u'''
            nonaz
                nonaz: +!lowerAZ
                    lowerAZ: a..z
        ''',
        expect_regex='[^a-z]')


    def test_nested_charclass_output(self):
        self.given(u'''
            vowhex
                vowhex: +vowel +hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_regex='[aiueoAIUEO0-9a-fA-F]')

        self.given(u'''
            vowhex
                vowhex: +!vowel +hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_regex='[[^aiueoAIUEO]0-9a-fA-F]')

        self.given(u'''
            vowhex
                vowhex: +vowel +!hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_regex='[aiueoAIUEO[^0-9a-fA-F]]')

        self.given(u'''
            vowhex
                vowhex: +!vowel +!hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_regex='[[^aiueoAIUEO][^0-9a-fA-F]]')


    def test_capturing(self):
        self.given('''
            /defcon/(level)/
                defcon = 'DEFCON'
                level: 1 2 3 4 5
        ''',
        expect_regex=r'DEFCON(?<level>[12345])')


    def test_string_interpolation(self):
        # the implementation of chain-of-cells parsing uses string interpolation to translate variable names into values
        # these tests prove that it won't cause troubles with "%(something)s" strings since it'll be on the value part
        self.given('''
            /p/pXs/s/
                p = '%'
                s = 's'
                pXs = /p/(X)/s/
                    X = 'X'
        ''',
        expect_regex='%%(?<X>X)ss')

        self.given('''
            /p/(pXs)/s/
                p = '%'
                s = 's'
                pXs = /p/(X)/s/
                    X = 'X'
        ''',
        expect_regex='%(?<pXs>%(?<X>X)s)s')

        self.given('''
            greeting
                greeting = 'Hello %(name)s'
        ''',
        expect_regex='Hello %\(name\)s')


        self.given('''
            message
                message = /greeting/name/
                    greeting = 'Hello%'
                    name = /(salutation)/first/last/
                        salutation = 'Sir/Madam'
                        first = 's%(first)s'
                        last  = '%(last)s'
        ''',
        expect_regex='Hello%(?<salutation>Sir/Madam)s%\(first\)s%\(last\)s')


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


    def test_captures(self):
        self.given('''
            /extra/(extra)/(extra?)/(extra)?/
                extra = 'icing'
        ''',
        expect_regex='icing(?<extra>icing)(?<extra>(?:icing)?+)(?<extra>icing)?+')


class TestMatches(unittest.TestCase):
    def given(self, oprex_source, expect_full_match, no_match=[], partial_match={}):
        regex_source = oprex(oprex_source)
        for text in expect_full_match:
            match = regex.match(regex_source, text)
            partial = match and match.group(0) != text
            if not match or partial:
                assertion_error('%s\nis expected to fully match: %s\n%s\nThe regex is: %s' % (
                    oprex_source or '(empty string)', 
                    text or '(empty string)', 
                    'It does match, but only partially. The match is: ' + (match.group(0) or '(empty string)') if partial else "But it doesn't match at all.",
                    regex_source or '(empty string)',
                ))

        for text in no_match:
            match = regex.match(regex_source, text)
            if match:
                assertion_error('%s\nis expected NOT to match: %s\n%s\nThe regex is: %s' % (
                    oprex_source or '(empty string)', 
                    text or '(empty string)', 
                    'But it does match. The match is: ' + (match.group(0) or '(empty string)'),
                    regex_source or '(empty string)',
                ))


        for text, partmatch in partial_match.iteritems():
            match = regex.match(regex_source, text)
            partial = match and match.group(0) != text and match.group(0) == partmatch
            if not match or not partial:
                if match.group(0) == text:
                    assertion_error("%s\nis expected to partially match: %s\nBut instead it's a full-match.\nThe regex is: %s" % (
                        oprex_source or '(empty string)', 
                        text or '(empty string)', 
                        regex_source or '(empty string)',
                    ))
                else:
                    assertion_error('%s\nis expected to partially match: %s\n%s\nThe regex is: %s' % (
                        oprex_source or '(empty string)', 
                        text or '(empty string)', 
                        "But it doesn't match at all." if not match else 'The expected partial match is: %s\nBut the resulting match is: %s' % (
                            partmatch or '(empty string)', 
                            match.group(0) or '(empty string)'
                        ),
                        regex_source or '(empty string)',
                    ))


    def test_simple_optional(self):
        self.given('''
            /a?/ether/
                ether = /e/ther/
                    e = 'e'
                    ther = 'ther'
                a = 'a'
            ''',
            expect_full_match=['ether', 'aether'],
        )

        self.given('''
            /air/man?/ship?/
                air = 'air'
                man = 'man'
                ship = 'ship'
            ''',
            expect_full_match=['air', 'airman', 'airship', 'airmanship'],
            no_match=['manship'],
            partial_match={'airma' : 'air'},
        )

        self.given('''
            /ultra?/nagog/
                ultra = "ultra"
                nagog = 'nagog'
            ''',
            expect_full_match=['ultranagog', 'nagog'],
            no_match=['ultrnagog'],
        )

        self.given('''
            /cat?/fish?/
                cat  = 'cat'
                fish = 'fish'
            ''',
            expect_full_match=['catfish', 'cat', 'fish', ''],
            partial_match={
                'catfishing' : 'catfish', 
                'cafis' : '',
            }
        )

        self.given('''
            /very?/very?/nice/
                very = 'very '
                nice = "nice"
            ''',
            expect_full_match=['nice', 'very nice', 'very very nice'],
        )


    def test_escaping(self):
        self.given('''
            orly
                orly = "O RLY?"
            ''',
            expect_full_match=['O RLY?'],
            no_match=['O RLY', 'O RL'],
        )


    def test_character_class(self):
        self.given('''
            papersize
                papersize = /series/size/
                    series: A B C
                    size: 0 1 2 3 4 5 6 7 8
            ''',
            expect_full_match=['A3', 'A4'],
            no_match=['Legal', 'Folio'],
        )

        self.given('''
            x
                x: u+41 u+042 u+00043 U+44 U+0045
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
                x: /!Symbol
        ''',
        expect_full_match=['A', '1'],
        no_match=['$'])

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
                x: /!Uppercase_Letter /!IsGreek
        ''',
        expect_full_match=['a', 'A', u'γ'],
        no_match=[u'Γ'])

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
        no_match=['×××x', '+++'])

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
            /nonhex/nonhex/nonhex/
                nonhex: +!hexdigit
                    hexdigit: 0..9 a..f A..F
        ''',
        expect_full_match=['WOW', 'hi!', '...'],
        no_match=['ACE', '123'])

        self.given(u'''
            /hex/hex/hex/
                hex: +!unhex
                    unhex: +!hexdigit
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


    def test_negated_charclass(self):
        self.given(u'''
            notA
                notA: +!A
                    A: A
        ''',
        expect_full_match=['a', 'b', 'B', u'ä', u'Ä'],
        no_match=['A'])

        self.given(u'''
            notAUmlaut
                notAUmlaut: +!small_a_umlaut
                    small_a_umlaut: +a_with_diaeresis
                        a_with_diaeresis: ä
        ''',
        expect_full_match=['a', u'Ä'],
        no_match=[u'ä'])

        self.given(u'''
            notAUmlaut
                notAUmlaut: +!AUmlaut
                    AUmlaut: u+c4
        ''',
        expect_full_match=['a', u'ä'],
        no_match=[u'Ä'])

        self.given(u'''
            notAUmlaut
                notAUmlaut: +!a_with_diaeresis
                    a_with_diaeresis: :LATIN_SMALL_LETTER_A_WITH_DIAERESIS
        ''',
        expect_full_match=['a', u'Ä'],
        no_match=[u'ä]'])

        self.given(u'''
            alphabetic
                alphabetic: +!nonAlpha
                    nonAlpha: /!Alphabetic
        ''',
        expect_full_match=['a', u'ä', u'Ä'],
        no_match=['$'])

        self.given(u'''
            nonhex
                nonhex: +!hexdigit
                    hexdigit: 0..9 a..f A..F
        ''',
        expect_full_match=['W', '$', u'Ä'],
        no_match=['a', 'A', '0', '1', '9'])

        self.given(u'''
            hex
                hex: +!unhex
                    unhex: +!hexdigit
                        hexdigit: 0..9 a..f A..F
        ''',
        expect_full_match=['a', 'A', '0', '1', '9'],
        no_match=['W', '$', u'Ä'])

        self.given(u'''
            nonaz
                nonaz: +!lowerAZ
                    lowerAZ: a..z
        ''',
        expect_full_match=['A', 'Z', u'Ä', u'ä', '1', '$'],
        no_match=['a', 'b', 'z'])


    def test_nested_charclass(self):
        self.given(u'''
            vowhex
                vowhex: +vowel +hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_full_match=['a', 'b', 'f', 'A', 'B', 'F', '0', '1', '9', 'i', 'u', 'E', 'O'],
        no_match=['$', 'z', 'k'])

        self.given(u'''
            vowhex
                vowhex: +!vowel +hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_full_match=['a', 'b', 'f', 'A', 'B', 'F', '0', '1', '9', 'E', '$', 'z', 'k'],
        no_match=['i', 'u', 'O'])

        self.given(u'''
            vowhex
                vowhex: +vowel +!hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_full_match=['a', 'A', 'i', 'u', 'E', 'O', '$', 'z', 'k'],
        no_match=['b', 'f', 'B', 'F', '0', '1', '9'])

        self.given(u'''
            vowhex
                vowhex: +!vowel +!hex
                    vowel: a i u e o A I U E O
                    hex: 0..9 a..f A..F
        ''',
        expect_full_match=['b', 'f', 'B', 'F', '0', '1', '9', 'i', 'u', 'O', '$', 'z', 'k'],
        no_match=['a', 'A', 'E'])


if __name__ == '__main__':
    unittest.main()
