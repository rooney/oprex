# -*- coding: utf-8 -*-

import unittest, regex
from oprex import oprex, OprexSyntaxError

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
            raise AssertionError(msg % (
                oprex_source or '(empty string)', 
                got_error or '\n(no error)', 
                expect_error or '\n(no error)',
            ))


    def test_white_guards(self):
        self.given('one-liner input',
        expect_error='''Line 1: First line must be blank, not: one-liner input''')

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
        expect_error='''Line 4: Unexpected VARNAME\nroot2\n^''')

        self.given('''
*           /warming/and/warming/
        ''',
        expect_error='Line 2: Unexpected GLOBALMARK\n*           /warming/and/warming/\n^')

        self.given('''
            /greeting/world/
                greeting = 'hello'
                    world = 'world'
        ''',
        expect_error='''Line 4: Unexpected BEGINSCOPE (indentation error?)''')


    def test_indentation_error(self):
        self.given('''
            /greeting/world/
                greeting = 'hello'
                 world = 'world'
        ''',
        expect_error='''Line 4: Unexpected BEGINSCOPE (indentation error?)''')

        self.given('''
            root
                branch
               misaligned
        ''',
        expect_error='''Line 4: Indentation error''')

        self.given('''
                root
                    branch
            hyperroot
        ''',
        expect_error='''Line 4: Indentation error''')


    def test_correct_error_line_numbering(self):
        self.given('''
            /greeting/world/
                greeting = 'hello'

                    world = 'world'
        ''',
        expect_error='''Line 5: Unexpected BEGINSCOPE (indentation error?)''')

        self.given('''

            /greeting/world/


                greeting = 'hello'

                 world = 'world'
        ''',
        expect_error='''Line 8: Unexpected BEGINSCOPE (indentation error?)''')

        self.given('''
            /greeting/world/
                greeting = 'hello'


               world = 'world'
        ''',
        expect_error='Line 6: Indentation error')

        self.given('''
            warming


            *   warming = 'global'
        ''',
        expect_error='''Line 5: The "make global" asterisk must be the line's first character''')


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
*                   article = 'the'
*                   adjective = /speed/color/
                        speed = 'quick'
                        color = 'brown'
*                   noun = 'fox'
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
        expect_error='''Line 3: Missing closing quote: 'McDonald's''')

        self.given('''
            quotes_mismatch
                quotes_mismatch = "'
        ''',
        expect_error="""Line 3: Missing closing quote: "'""")


    def test_invalid_global_mark(self):
        self.given('''
            *
        ''',
        expect_error='''Line 2: The "make global" asterisk must be the line's first character''')

        self.given('''
*
        ''',
        expect_error='Line 2: Indentation error')

        self.given('''
*\t
        ''',
        expect_error='Line 2: Unexpected GLOBALMARK\n*\t\n^')

        self.given('''
*warming
        ''',
        expect_error='Line 2: Indentation error')

        self.given('''
*           warming
        ''',
        expect_error='Line 2: Unexpected GLOBALMARK\n*           warming\n^')

        self.given('''
            warming
                *warming = 'global'
        ''',
        expect_error='''Line 3: The "make global" asterisk must be the line's first character''')

        self.given('''
            warming
            *   warming = 'global'
        ''',
        expect_error='''Line 3: The "make global" asterisk must be the line's first character''')

        self.given('''
            warming
*           *   warming = 'global'
        ''',
        expect_error='Line 3: Syntax error: *           *   ')

        self.given('''
            warming
*               warming* = 'global'
        ''',
        expect_error="Line 3: Unsupported syntax: * = 'global'")

        self.given('''
            warming
                warming* = 'global'
        ''',
        expect_error="Line 3: Unsupported syntax: * = 'global'")


    def test_character_class(self):
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
        expect_error='Line 3: Invalid character in character class definition: ae (each character must be len==1)')

        self.given('''
            miscolon
                miscolon: /colon/should/be/equal/sign/
        ''',
        expect_error='Line 3: Invalid character in character class definition: /colon/should/be/equal/sign/ (each character must be len==1)')

        self.given('''
            miscolon
                miscolon: 'colon should be equal sign'
        ''',
        expect_error="Line 3: Invalid character in character class definition: 'colon (each character must be len==1)")

        self.given('''
            /A/a/
                A: a: A a
        ''',
        expect_error='Line 3: Invalid character in character class definition: a: (each character must be len==1)')

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


    def test_global_aliasing(self):
        self.given('''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
                    satu = '1'
*                   uno = ichi = satu
                oneone = /uno/ichi/
                one = ichi
                    ichi: 1
        ''',
        expect_error="Line 8: Names must be unique within a scope, 'ichi' is already defined (previous definition at line 5)")

        self.given('''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
                    satu = '1'
*                   uno = ichi = satu
                oneone = /uno/ichi/
                one = uno
                    uno: 1
        ''',
        expect_error="Line 8: Names must be unique within a scope, 'uno' is already defined (previous definition at line 5)")

        self.given('''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
                    satu = '1'
*                   uno = ichi = satu
                oneone = /uno/ichi/
                one = satu
        ''',
        expect_error="Line 7: 'satu' is not defined")

        self.given('''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
*                   satu = '1'
                    uno = ichi = satu
                one = satu
                oneone = /uno/ichi/
        ''',
        expect_error="Line 7: 'uno' is not defined")


class TestOutput(unittest.TestCase):
    def given(self, oprex_source, expect_regex):
        regex_source = oprex(oprex_source)
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
*               warming = 'global'
        ''',
        expect_regex='localglobal')

        # indentation using tab
        self.given('''
/weather/warming/
\tweather = 'local'
*\twarming = 'global'
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
*                   article = 'the'
*                   adjective = /speed/color/
                        speed = 'quick'
                        color = 'brown'
*                   noun = 'fox'
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
*                   empat = sekawan: 4
                banana4 = /gedang/sekawan/
                    gedang = 'banana'
                papaya4 = /gedang/opat/
                    gedang = 'papaya'
                    opat = empat
        ''',
        expect_regex='[1][4][4]banana[4]papaya[4]')

        self.given('''
            /oneoneone/oneone/one/
                oneoneone = /satu/uno/ichi/
                    satu = '1'
*                   uno = ichi = satu
                oneone = /uno/ichi/
                one = satu
                    satu: 1
        ''',
        expect_regex='11111[1]')


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
        expect_regex='[X][X][X][X][X]')


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


class TestMatches(unittest.TestCase):
    def given(self, oprex_source, expect_full_match, no_match=[], partial_match={}):
        regex_source = oprex(oprex_source)
        for text in expect_full_match:
            match = regex.match(regex_source, text)
            partial = match and match.group(0) != text
            if not match or partial:
                raise AssertionError('%s\nis expected to fully match: %s\n%s\nThe regex is: %s' % (
                    oprex_source or '(empty string)', 
                    text or '(empty string)', 
                    'It does match, but only partially. The match is: ' + (match.group(0) or '(empty string)') if partial else "But it doesn't match at all.",
                    regex_source or '(empty string)',
                ))

        for text in no_match:
            match = regex.match(regex_source, text)
            if match:
                raise AssertionError('%s\nis expected NOT to match: %s\n%s\nThe regex is: %s' % (
                    oprex_source or '(empty string)', 
                    text or '(empty string)', 
                    'But it does match. The match is: ' + (match.group(0) or '(empty string)'),
                    regex_source or '(empty string)',
                ))


        for text, partmatch in partial_match.iteritems():
            match = regex.match(regex_source, text)
            partial = match and match.group(0) != text and match.group(0) == partmatch
            if not match or not partial:
                raise AssertionError('%s\nis expected to partially match: %s\n%s\nThe regex is: %s' % (
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


if __name__ == '__main__':
    unittest.main()
