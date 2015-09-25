# oprex
Regex alternative syntax. Make regex readable.

## Examples
##### 1. IPv4 Address
```oprex
/byte/dot/byte/dot/byte/dot/byte/
    byte = '0'..'255'
    dot = '.'
```
Compared to plain regex:

```regex
(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}
```
--
##### 2. BEGIN-something-END (e.g. extracting `<title>` from HTML)

```oprex
/begin/__/end/
    begin = '<title>'
    end = '</title>'
```
The above oprex compiles to the following regex:

```regex
<title>(?:[^<]++|<(?!/title>))++</title>
```

Which is [correct and high-performing](http://www.rexegg.com/regex-quantifiers.html#explicit_greed), **but unreadable** compared to `<title>.+?</title>` which looks nice but is [slow and sometimes problematic](http://www.rexegg.com/regex-quantifiers.html#lazytrap).

Using oprex, we get both correct+fast and readable.

--
##### 3. Date
```oprex
/yyyy/separator/mm/=separator/dd/
    yyyy = 4 of digit
    mm = '01'..'12'
    dd = '01'..'31'
    [separator] = 1 of: - /
```
It compiles to (prettified): 

```regex
\d{4}
(?P<separator>[\-/])
(?>1[0-2]|0[1-9])
(?P=separator)
(?>3[01]|[12]\d|0[1-9])(?!\d)
```
--
##### 4. Time
```oprex
<<|
  |/hh/colon/mm/colon/ss/space/ampm/ -- 12-hour format
  |/HH/colon/mm/colon/ss/            -- 24-hour format

    hh = '1'..'12'
    HH = 'o0'..'23'
    mm = ss = '00'..'59'
    colon: :
    ampm = (ignorecase) <<|
                          |'AM'
                          |'PM'
```
Compiles to: 

```regex
(?>1[0-2]|[1-9])
:[0-5]\d
:[0-5]\d (?i:AM|PM)
|
(?>2[0-3]|1\d|0?\d)
:[0-5]\d
:[0-5]\d(?!\d)
```
--
##### 5. Blood Type
```
/type/rhesus/
    [type] = <<|
               |'AB'
               |1 of: A B O

    [rhesus] = <<|
                 |'+'
                 |'-'
                 |
```
```
(?P<type>AB|[ABO])
(?P<rhesus>\+|-|)
```
--
##### 6. Quoted String (with escape support)
```
/opening_quote/contents/=opening_quote/
    [opening_quote] = 1 of quote
*)      quote: ' "
    contents = @1.. of <<|
                         |non-quote
                         |non_opening_quote
                         |escaped

        non_opening_quote = <@>
                      |quote|
            <!=opening_quote|

        escaped = <@>
            <backslash|
                      |quote|
```
```
(?P<opening_quote>['"])
(?:[^'"]|['"](?<!(?P=opening_quote))|(?<=\\)['"])++
(?P=opening_quote)
```
--
##### 7. Comma-Separated Values
```
//value/more_values?//
    value = @1.. of non-comma
*)      comma: ,
    more_values = /comma/value/more_values?/
```
```
(?m:^)
[^,]++
(?P<more_values>,[^,]++(?&more_values)?)?
(?m:$)
```
--
##### 8. Password Checks
```
(unicode)
<@>
|min_length_8>
|has_number>
|has_min_2_symbols>

    min_length_8 = @8.. of any
    has_number = /__?/digit/
    has_min_2_symbols = 2 of /__?/non-alnum/

```
```
(?V1wu)
(?=(?s:.){8,}+)
(?=\D*+\d)
(?=(?:\p{Alphanumeric}*+\P{Alphanumeric}){2})
```
--
##### 9. Balanced Parentheses
```oprex
/non_parens?/balanced_parens/non_parens?/.
    non_parens = @1.. of not: ( ) 
    balanced_parens = /open/contents?/close/
        open: (
        close: )
        contents = @1.. of <<|
                             |non_parens
                             |balanced_parens
```
```
[^()]*+
(?P<balanced_parens>\((?:[^()]++|(?&balanced_parens))*+\))
[^()]*+
\Z
```
## Installation
```
pip install oprex
```

## Usage
```
>>> from oprex import oprex
>>> oprex
<function oprex at ...>
```
The `oprex` function takes a parameter of type string (the oprex "source code") with the return value also of type string (the resulting regex).

```
>>> email_pattern = oprex('''
...     /somebody/at/somedomain/
...         somebody = @1.. of: alnum . _ - +
...         at = '@'
...         somedomain = /subdomain/TLD/
...             subdomain = /hostname/dot/subdomain?/
...                 hostname = <@>
...                     |!dash>
...                     |alnums_and_dashes|
...                                 <!dash|
...                 
...                         dash: -
...                         alnums_and_dashes = @1.. of: alnum dash
...                 dot = '.'
...             TLD = @2..63 of alpha
... ''')
```

```
>>> print email_pattern
(?V1w)[a-zA-Z0-9._\-+]++@(?P<subdomain>(?!-)[a-zA-Z0-9\-]++(?<!-)\.(?&subdomain)?)[a-zA-Z]{2,63}+
```
The output is designed to be used with Matthew Barnett's [`regex`](https://pypi.python.org/pypi/regex) module. If you want to use it with Python's built-in `re` module, you'll need to remove the `V1` flag (in addition to not using the features `re` [does not support](http://www.rexegg.com/regex-python.html#missing_in_re), of course).

Since the output is plain regular python string, such modification (or any other string manipulation you may want) should be pretty straightforward.

### As command line tool
```
$ python oprex.py <sourcefile>
```
You can use oprex from command line. It takes path-to-source-file as a parameter. The file should be in plaintext, containing oprex "source code". For consistency with embedded-in-python-triple-quote-string syntax, the first and last lines of the file should be blank. Example:

```oprex

./palindrome/.
    palindrome = <<|
                   |/letter/palindrome/=letter/
                   |/letter/=letter/
                   |letter

        [letter] = alpha
        
```
(notice that the first and last lines are blanks)

The output will be printed on `stdout`.

```
$ python oprex.py samples/palindrome.oprex
(?V1w)\A(?P<palindrome>(?P<letter>[a-zA-Z])(?&palindrome)(?P=letter)|(?P<letter>[a-zA-Z])(?P=letter)|(?P<letter>[a-zA-Z]))\Z
```

## Tutorial

Here's an oprex to match **CSS color** (hashtag-syntax only, e.g. `#ff0000`). It compiles to `#(?:[\dA-Fa-f]{6}|[\dA-Fa-f]{3})`.

```oprex
/hash/hexes/
    hash = '#'
    hexes = <<|
              |6 of hexdigit
              |3 of hexdigit

        hexdigit: digit A..F a..f    
```
The first line:

```
/hash/hexes/
```

Specifies that we want a regex that matches *`hash`-then-`hexes`*. We then define what those `hash` and `hexes` are using indented sub-block:

--
```
    hash = '#'
```
This defines `hash` as a [string literal](). It should match `#` literally.

--
```
    hexes = <<|
```
This defines `hexes` as an [alternation](). The `<<|` starts an alternation.

--
```
              |6 of hexdigit
```
This is the first alternative in our alternation: match `hexdigit` six times. 

The `of` keyword is oprex's operator for doing [quantification/repetition]().

All `|` in an alternation must vertically align.

--
```
              |3 of hexdigit
```
This is the second alternative in our alternation: match `hexdigit` three times. For matching e.g. `#f00`

--
Then we have a blank line.

```
 
```
In oprex, blank line means end-of-alternation/lookaround, so here we close our alternation block.

--
The definition of `hexes` above refers to something called `hexdigit` so now we need to define it. Again, to define something we use indented sub-block, this time with deeper indentation since the definition of `hexes` is already indented:

```
        hexdigit: digit A..F a..f
```
This defines `hexdigit` as a [character-class](). Character classes are defined using colon `:` then, after the colon, we list the character-class' members, separated by space:

* `digit` is a [built-in character-class]() (it compiles to regex's `\d`). Character classes can include other character classes.
* `A..F` and `a..f` are [character ranges]().

--
### Another example: stuff-inside-brackets
The following oprex matches stuff-inside-brackets, with the brackets can be one of `()``{}``<>` or `[]`.
 
- Sample matches: `<html>` `{x < 0}` `[1]` and `(see footnote [1])`
- Will not match e.g. `f(g(x))`
- Will only partially match `{{citation needed}}` as `{{citation needed}`
- To also match those, we can combine this example with the [balanced parentheses example](). But to keep it short and clear, we'll go with the above restrictions.

The output regex will be:

```regex
(?>(?P<paren>\()|(?P<curly>\{)|(?P<angle><)|(?P<square>\[))
(?:[^(){}<>\[\]]|(?s:.)(?<!(?>(?(paren)\)|(?(curly)\}|(?(angle)>|(?(square)\]|(?!))))))))*+
(?>(?(paren)\)|(?(curly)\}|(?(angle)>|(?(square)\]|(?!))))))
```

Here's the oprex:

```oprex
                                           -- Line 0, things after "--" are comments
/open/contents?/close/                     -- Line 1
    open = @|                                  --  2
            |paren                             --  3
            |curly                             --  4
            |angle                             --  5
            |square                            --  6
                                               --  7
        [paren]: (                             --  8
        [curly]: {                             --  9
        [angle]: <                             -- 10
        [square]: [                            -- 11
                                               -- 12
    close = @|                                 -- 13
             |[paren] ? ')'                    -- 14
             |[curly] ? '}'                    -- 15
             |[angle] ? '>'                    -- 16
             |[square] ? ']'                   -- 17
             |FAIL!                            -- 18
                                               -- 19
    contents = @1.. of <<|                     -- 20
                         |not: ( ) { } < > [ ] -- 21
                         |not_close            -- 22
                                               -- 23
        not_close = <@>                        -- 24
               |any|                           -- 25
            <!close|                           -- 26
                                               -- 27
```
As you can see, comments in oprex starts with `--` (a la SQL) not with `#` like in python. The reason for that is demonstrated by Line 21. Also, while first and last lines must be blank, comments-only lines are counted as blanks.

--
**Line 1**: `contents?` means that it is optional. It behaves just like `?` in regex.

**Line 2**: `@|` starts an alternation, just like `<<|` before (see the previous CSS-color example). The difference is `@` means **atomic** while `<<` means **allow backtracking**. So, alternations started using `@|` will be atomic while ones started using `<<|` may backtrack. (If you don't know about regex atomic vs. backtracking, here's an [excellent reference](http://www.regular-expressions.info/atomic.html)).

**Line 7**: Blank line (comments-only lines are treated as blank). It marks the end-of-alternation.

--
**Lines 8-11**: `[paren]` `[curly]` `[angle]` `[square]` define [named capture groups](). (Capturing group is one of regex-basics, we will not cover it here in an oprex tutorial). They need to be defined as capture groups because we will refer back to them later on lines 14-17.

--
```
    close = @|                                 -- 13
             |[paren] ? ')'                    -- 14
             |[curly] ? '}'                    -- 15
             |[angle] ? '>'                    -- 16
             |[square] ? ']'                   -- 17
             |FAIL!                            -- 18
```
**Line 13**: `@|` start-of-alternation, atomic.

**Line 14-17**: are [conditionals](), e.g. `[paren] ? ')'` means: match literal `)` only if capture-group `paren` is defined. In the definition of `open` (lines 2-7), only one of paren-curly-angle-square will be defined because they are in an alternation. So this means that `close` must match `)` if `open` is `(`, `}` if `open` is `{`, etc.

**Line 18**: `FAIL!` compiles to regex `(?!)`. [It always fails](http://www.rexegg.com/regex-tricks.html#fail). So if none of the conditions in met, it should just fail.

**Line 19**: Blank line, end-of-alternation.

--
**Line 20**: `@1.. of <<|`

- `of` is quantification operator.
- `@1..` is the [quantifier](). Again, `@` means atomic, i.e. make it a [possessive quantifier](http://www.regular-expressions.info/possessive.html). `1..` means one-or-more. `@1..` compiles to regex `++`.
- Things after `of` are what-should-be-repeated. So here we are quantifying an alternation.
- `<<|` starts an alternation (one that allows backtracking, as previously explained).

**Line 21**: `not: ( ) { } < > [ ]`

- `not:` is oprex operator for doing [negated character-class]().
- `( ) { } < > [ ]` are the character-class members, separated by space.
- Line 21 also demonstrates why comments are started with `--` -- a `#` there will be interpreted as a character class member.

**Line 23**: Blank line, end-of-alternation.

--
**Lines 24-26**:

```
        not_close = <@>                        -- 24
               |any|                           -- 25
            <!close|                           -- 26
```
- `<@>` starts a [lookaround block](). The `@` reminds you that [lookarounds are atomic](http://www.rexegg.com/regex-lookarounds.html#atomic).
- `any` is an oprex-built-in variable. It matches any character -- like regex's `.` with DOTALL turned on.
- `<!close|` is a [negative lookbehind](). `<` means lookbehind. `!` negates. `close` is already defined on Line 13.
- Like in alternation, all corresponding `|` in a lookaround must vertically align.

**Line 27**: Blank line, end-of-lookaround. Like alternation, lookaround block is closed with blank line.

## Examples explained
The *Tutorial* should explain most of the syntax used in *Examples*. The rest are covered here:

### 1. Match a range of number-strings
The *IPv4 Address*, *Date*, and *Time* examples use the [String-of-Digits Range Literal]() feature to match number-strings between two specified values (and reject non-numbers string/numbers but having value outside the range):

- `byte = '0'..'255'` (leading-zero not allowed, e.g. won't match `007`)
- `hh = '1'..'12'`
- `mm = '01'..'12'` (leading-zero mandatory for single-digits, e.g. will match `02` but not `2`)
- `dd = '01'..'31'`
- `mm = ss = '00'..'59'`
- `HH = 'o0'..'23'` (the `o` means optional leading-zero, e.g. will match both `2` and `02`)

--
### 2. Backreference
In the *Date* example:

```
    /yyyy/separator/mm/=separator/dd/
```
And the *Quoted String* example:

```
    /opening_quote/contents/=opening_quote/
```
The `=separator` and `=opening_quote` parts are [Backreference]().

--
### 3. Flags
`(ignorecase)` in *Time* and `(unicode)` in *Password Checks* are example of [Flags]() usage.

--
### 4. Match-anything-until
The `__` in *BEGIN-something-END* example:

```
    /begin/__/end/
```
And in *Password Checks*:

```
    has_number = /__?/digit/
    has_min_2_symbols = 2 of /__?/non-alnum/
```

Are sample uses of the [Match-Until Operator]().

--
### 5. Recursion
In *Comma-Separated Values*:

```
    more_values = /comma/value/more_values?/
```
The `more_values` refers to itself. This is an example of [Recursion](). Other examples can be seen in *E-mail Address*:

```
    subdomain = /hostname/dot/subdomain?/
```
*Balanced Parentheses*:
<pre>
    <b>balanced_parens</b> = /open/contents?/close/
        open: (
        close: )
        contents = @1.. of <<|
                             |non_parens
                             |<b>balanced_parens</b>
</pre>                        
And *Palindrome*:
<pre>
    <b>palindrome</b> = <<|
                   |/letter/<b>palindrome</b>/=letter/
                   |/letter/=letter/
                   |letter
</pre>

--
### 6. Global Variable
In *Quoted String*:

```
*)      quote: ' "
```
And *Comma-Separated Values*:

```
*)      comma: ,
```
The `*)` in the definitions of `quote` and `comma` marks the variables as [Global Variable]() which makes the variables accessible in latter, different scopes.

## Reference Manual
### 1. Built-in Variables
#### 1.1. Built-in Character Classes

Name        | Output             | Output when (unicode)          
----------- | ------------------ | ---------------------
`alpha`     | `[a-zA-Z]`         | `\p{Alphabetic}`
`upper`     | `[A-Z]`            | `\p{Uppercase}`
`lower`     | `[a-z]`            | `\p{Lowercase}`
`alnum`     | `[a-zA-Z0-9]`      | `\p{Alphanumeric}`
`linechar`  | `[\r\n\x0B\x0C]`   | `[\r\n\x0B\x0C\x85\u2028\u2029]`
            | `\n` when `(-word)`| `\n` when `(-word)`
`padchar`   | `[ \t]`            |
`space`     | `[ ]`              |
`tab`       | `\t`               |
`digit`     | `\d`               |
`whitechar` | `\s`               |
`wordchar`  | `\w`               |
`backslash` | `\\`               |

#### 1.2. Built-in Expressions

Name        | Meaning             | Output          
----------- | ------------------- | ------
`BOS`       | beginning of string | `\A`
`EOS`       | end of string       | `\Z`
`BOL`       | beginning of line   | `(?m:^)`
`EOL`       | end of line         | `(?m:$)`
`BOW`       | beginning of word   | `\m`
`EOW`       | end of word         | `\M`
`WOB`       | word boundary       | `\b`
`any`       | any character       | `(?s:.)` (`.` with DOTALL turned on)
`uany`      | unicode-any         | `\X` (single unicode grapheme)

- `WOB` is special: it is not a character-class, but you can apply the `non-` operator to it. `non-WOB` compiles to `\B`.
- Oprex-equivalent of regex's `.` with DOTALL turned OFF is `non-linechar` (see `linechar` in *Built-in Character Classes* table).

--
### 2. Main Syntax
The general syntax of oprex is in the form of:

```
>>> oprex('''
...     (flags)                -- comments
...     expression
...         def_x = expression
... ''')
```

#### 2.1. Flags
Syntax:

- `(flagname)` to turn it on.
- `(-flagname)` to turn it off.
- `(flag1 flag2 -flag3)` for multiple flags.
- `(flag) expression` to apply only to that `expression` (inline/scoped flag).
- `(flag)` at the very beginning (before the main expression, on its own line) to apply globally.

#### 2.1.1. Global Flags
- Can only be applied globally.
- Can only be turned on, never off.
- Supported global flags are `ascii`, `bestmatch`, `enhancedmatch`, `locale`, `reverse`, `unicode`, `version0`, and `version1`.

#### 2.1.2. Scoped Flags
- Can be applied both globally and inline/scoped.
- Can be turned on and off
- Supported scoped flags are `dotall`, `fullcase`, `ignorecase`, `multiline`, `verbose`, and `word`.

#### 2.1.3. Flags Example
```
    (unicode ignorecase) -- multiple global flags, scoped flag can be applied globally but not vice versa
    /password/
        password = (-ignorecase) 'correctHorseBatteryStaple' -- scoped flag, turn-off
```
Compiles to `(?V1wui)(?-i:correctHorseBatteryStaple)`

- `version1` and `word` are turned on by default (hence the `V1w` in the example's output).
- For what each flag does, refer to the [regex module documentation]().

#### 2.2. Comments
Comment starts with `--` to the end of the line. Block comment is not supported.

#### 2.3. Expression
Expression can be one of the following:

- [String literal]()
- [String-of-digits range literal]()
- A [variable]() name
- [Negation]()
- [Lookup chain]()
- [Alternation block]()
- [Lookaround block]()
- [Quantification/repetition]()

--
### 3. String Literal

Syntax:

- `'single quoted'` or `"double quoted"`
- Quotes can be escaped, e.g. `'Mother\'s Day'`
- The output will be properly regex-escaped, e.g. `"A+"` compiles to `A\\+`
- Backslash-escapes that are not regex-escape will NOT be escaped, e.g. `"\d\t"` compiles to `\\d\t` (the `\d` got escaped but the `\t` didn't)

#### 3.1. Boundaries
Word boundary (oprex's `WOB`, regex's `\b`) and non-boundary (oprex's `non-WOB`, regex's `\B`) can be easily appended and/or prepended to a string literal using the following syntax:
 
- `.` for word boundary, e.g. `'cat'.` compiles to `cat\b`, `.'cat'` compiles to `\bcat`.
- `_` for non-boundary, e.g. `'cat'_` compiles to `cat\B`, `_'cat'_` compiles to `\Bcat\B`.

--
### 4. String-of-Digits Range Literal
#### 4.1. Between (and including) two numbers
- Syntax: `"min".."max"` or `'min'..'max'`.
- `min` can have leading `0` (to require) or `o` (to allow) leading zero(es). Examples:
  - `'0'..'999'` will NOT match e.g. `007` and `012`.
  - `'000'..'999'` will match `007` and `012`, but NOT `7` and `12`.
  - `'oo0'..'999'` will match numbers both with and without leading zeroes.

#### 4.2. Greater than or equal to a number (maxless range)
- Syntax: `"min"..` or `'min'..`.
- Optional-leading-zero can be used with maxless range, e.g. `'o1'..`.
- Mandatory-leading-zero does NOT work with maxless range, e.g. `'01'..` will raise an error.

--
### 5. Variable
#### 5.1. Assignment/Definition

Syntax:

- `varname = expression` to define a subexpression
- `varname: c h a r s` to define a character-class
- `[varname]` to define a  named capture group, e.g. `[varname] = expression` or `[varname]: c h a r s`

#### 5.2. Scoping
The following example demonstrates variable scoping in oprex:

```
    /first/second/third/last/   -- can access direct children
        first = '1st'
        second = '2nd'
        third = /first/x/       -- can access older siblings
            x = /second/a/b/    -- can access parent's older-siblings
                a = /third?/x?/ -- can access parent, grandparent, great-grandparent, and so on (recursion)
                b = /B1/B2/b?/  -- can access self (recursion)
                    B1 = first  -- can access great-grandparent's (and so on's) older siblings
*)                  B2 = second
                        
                -- B1 is no longer defined beyond this point
            
            -- a and b are no longer defined beyond this point
                
        -- x is no longer defined beyond this point
        
        last = x                -- last's x is different from third's x
            x = B2              -- B2 is global, so it's accessible here (normally it isn't)
```

#### 5.3. Global Scope
A variable can be made global by prefixing its definition with `*)`. See `B2` in the example above.

#### 5.4. Scoping-Error Examples

- Can't access grandchildren (and great-grandchildren, and so on).

```
    /x/y/     -- can't access grandchildren
        x = y
            y = 'yadda'
```
--
- Can't access younger siblings.

```
    /x/y/
        x = y -- can't access younger siblings
        y = 'yadda'
```
--
- Can't access sibling's children.

```
    /x/yadda/
        x = y
            y = 'yadda'
        yadda = y -- can't access sibling's children
```
--
- All variable must be referenced by its immediate parent.

```
    /x/y/
        x = 'pow'
        y = 'wow'
        z = 'how' -- ERROR: defined but not used
```

```
    /x/y/
        pow = 'pow' -- ERROR: not referenced by parent
        x = pow
        y = pow
```

```
    /x/y/
        x = pow
            pow = 'pow'
*)          wow = 'wow' -- ERROR: not referenced by parent
        y = wow
```
--
- Global variables still need to be defined-before-used.

```
    /x/y/
        x = yadda -- can't access global variable before its definition
        y = yadda
*)          yadda = 'yadda'
```

#### 5.5. Recursion
A variable can refer to itself and/or its parent expressions (immediate parent, grandparent, great-grandparent, and so on). This will generate regex containing recursion. For examples, see *Comma-Separated Values* and *Balanced Parentheses* in the [Examples]() section and *Palindromes* in the [Usage]() section.


--
### 6. Character Class

In oprex, the colon symbol `:` is used to start a character class:

- When defining a variable, e.g. `upvowel: A I U E O`
- When quantifying, using `of:`
- When negating, using `not:`

After the colon, list out the character-class' members, separated by space.

Example:

```
<<|
  |1 of: a i u e o
  |not: b..d f..h j..n p..t v..z
  |upvowel
  
   upvowel: A I U E O
```

#### 6.1. Character Literal

In a character class, single-characters are interpreted literally, e.g.

```
    vowel: a i u e o A I U E O
    arith: + - * /
    colon: :
```
Can be unicode too:

```
    basic_math_constant: π e i
    danger: ⚠ ☣ ☢ ☠
```

#### 6.2. Escaped Characters

Works as expected:

```
    newline: \r \n
```
Octal, hex, and unicode escapes are also supported 

```
    xyz: \170 \171 \172
    xyz: \x78 \x79 \x7A
    xyz: \u0078 \u0079 \u007A
    xyz: \U00000078 \U00000079 \U0000007A
```

#### 6.2. Character Name 

You can also use the character's unicode-name. For example, instead of:

```
    dash: - – —
```
Which is not very clear, you can spell the names out for clarity:

```
    dash: \N{HYPHEN-MINUS} \N{EN DASH} \N{EM DASH}
```
And to make it even clearer, oprex has sugar for that:

```
    dash: :HYPHEN-MINUS :EN_DASH :EM_DASH
```

#### 6.3. Includes
Character-classes can include other character-classes:

```
	upnum: upper digit
	base64: alnum + / =
```

#### 6.4. Unicode Properties 
To build a character class based on [unicode character properties](http://www.regular-expressions.info/unicode.html#category), use the following syntax:

```
	money_char: /Number /Currency_Symbol . ,
	
	nonalpha: not: /IsAlphabetic
	nonalpha: not: /Alphabetic
	nonalpha: /Alphabetic=No
	nonalpha: /Alphabetic:No
	
	japanese_char: /Script=Hiragana /Script=Katakana
	japanese_char: /Script:Hiragana /Script:Katakana
	japanese_char: /InHiragana /InKatakana
	japanese_char: /IsHiragana /IsKatakana
	japanese_char: /Hiragana /Katakana
	
```

#### 6.5. Character Range

Syntax: `from..to` e.g.

```
    hex: 0..9 a..f A..F
    grade_char: A..F
    nonzero: 1..9
```
Names and escape codes can be used with range too:

```
    nonzero: \N{DIGIT ONE}..\N{DIGIT NINE}
    nonzero: :DIGIT_ONE..:DIGIT_NINE
    nonzero: \u0031..\u0039
```

#### 6.6. Character-Class Operation

Operator              | Operation    | Placement
--------------------- | ------------ | ---------
`and`                 | intersection | infix (`x and y`)
`not` (without colon) | subtraction  | infix (`x not y`)
`not:` (with colon)   | negation     | prefix (`not: x`)

##### 6.7.1. Intersection: `and`
Examples:

```
    arabic_number: /Number and /IsArabic
    greek_alphabet: /Alphabetic and /Script:Greek
    japanese_number: /Number and /Hiragana /Katakana
    japanese_number: /Hiragana /Katakana and /Number
```
##### 6.7.2. Subtraction: `not`
```
    nonzero: digit not 0
    upnum: alnum not lower
    nonlatin_alpha: /Alphabetic not /InBasicLatin
    gaijin_alpha: /Alphabetic not /Hiragana /Katakana
    consonant: alpha not a i u e o A I U E O
```

##### 6.7.3. Negation: `not:`
```
	non_quote: not: ' "
	inside_paren: not: ( )
	csv_data: not: ,
```

### 7. Character-Class Negation

Syntax:

- `non-` followed by a character-class variable name, e.g. `non-digit`.
- `not:` followed by character-class member(s), e.g. `not: a i u e o`.

The first form is for easy chaining, e.g. if you need "non-digit followed by non-alphabet" use `/non-digit/non-alpha/`.

Only character classes can be negated. But for the `non-` operator, the built-in variable `WOB` is an exception: `WOB` is not a character-class, but `non-WOB` compiles to `\B`.

--
### 8. Lookup Chain

Syntax: `/lookup1/lookup2/lookup3/etc/`

Each lookup can be one of the following:

- A [variable]() name
- [Negation]() using `non-`
- [Backreference]()
- [Match-until]() operator (the double underscore `__`)

#### 8.1. Syntactic Sugars for BOS, BOL, EOS, and EOL
To enhance readability, several sugars are available to use with lookup-chain syntax (you might want to first read about `BOS`, `BOL`, `EOS`, and `EOL` in the *Built-in Variables* section):


Syntactic Sugar      | Meaning | Example   | Equivalent To | Compiles To
--------------------- | ------ | ---------- | ------------- | ----------
`./` at the beginning | `BOS`  | `./digit/` | `/BOS/digit/` | `\A\d` 
`//` at the beginning | `BOL`  | `//digit/` | `/BOL/digit/` | `(?m:^)\d`
`/.` at the end       | `EOS`  | `/digit/.` | `/digit/EOS/` | `\d\Z`
`//` at the end       | `EOL`  | `/digit//` | `/digit/EOL/` | `\d(?m:$)`

#### 8.2. Backreference

Syntax: `=varname`, the varname must be a [named capture group](). Example:

```
    /number/=number/=number/
        [number] = digit
```
matches three of same numbers e.g. `777` or `000`. For more examples, see *Date* and *Quoted String* in the *Examples* section.


#### 8.3. The Match-Until Operator

The Match-Until operator `__` matches one or more characters until what follows it in the lookup chain. For example:

```
    /open/__/close/
        open: (
        close: )
```
The `__` will match one or more characters until closing-parenthesis is encountered. The example will fail on string `()` because `__` eats one-or-more. To make it zero-or-more, append the optionalize operator `?`:

```
    /open/__?/close/
        open: (
        close: )
```
#### 8.4. Match-Until Automatic Optimization
The above example is akin to the regex's "lazy dotstar" idiom `.*?`. The difference is, oprex's `__` will try to make some optimizations in some cases:

- If it is followed by character-class, example:

```
    /__?/stop/
        stop: . ;
```
Compiles to `[^.;]*+[.;]`. The `__?` uses what follows (the character-class `[.;]`) so it compiles to `[^.;]*+` which is the way to [optimize lazy-dotstar for such case]().

- If it is followed by string literal, example:

```
    /__?/stop/
        stop = 'END'
```
Compiles to `(?:[^E]++|E(?!ND))*+END`. Again, the `__?` uses what follows (the literal `END`) so it compiles to `(?:[^E]++|E(?!ND))*+` which is the way to [optimize lazy-dotstar for a case like this]().

In any case, **the oprex stays super-readable while giving optimized, high-performance regex** output.

#### 8.5. Non-Optimized Match-Until
If the `__` is not followed by character-class nor string literal, it will compile to the usual lazy-dotplus `.+?` (or lazy-dotstar `.*?` in the case of `__?`). Example:

```
/__/any//   -- match all characters except the last one 
```
Compiles to `.+?(?s:.)(?m:$)`

#### 8.6. Multiline Match-Until
If a Match-Until usage falls in unoptimized case, it will compile to the regular lazy-dotstar/dotplus. In such case, the dot in the lazy-dotstar/dotplus will adhere to the DOTALL flag setting (will not match newline characters without DOTALL). So if you want the dot to really match anything, including newline characters, you'll need to turn on the `dotall` flag:

```
(dotall) /__/any/.   -- match all characters (including newlines) except the last one 
```
Compiles to `(?s:.+?.\Z)`

--
### 9. Alternation Block

Alternation block starts with either `<<|` or `@|` and ends with empty line. `<<|` starts a backtrackable alternation block, while `@|` starts an atomic one.

#### 9.1. Backtrackable Alternation
```
    <<|
      |alt1
      |alt2
      |etc
      
```
Each alt in an alternation block can be:

- An [expression](), with restrictions:
  - It cannot be a lookaround block.
  - It cannot be another alternation block.
  - (These limitations force you to refactor sub-alternation/lookaround into a variable. This ensures readability.)
- A [conditional expression]().
- [FAIL!]()
- empty (will always succeed -- it will try to match empty string, which always succeeds).

#### 9.2. Atomic Alternation
The syntax is similar to the backtrackable one, with one minor difference: atomic alternation starts with `@|` rather than `<<|`. Here's an [excellent reference]() describing the difference between the two. Most of the time they are interexchangable, with the atomic version having better performance. But most is not all, and some cases that require backtracking will not work with the atomic version. For example, the *Palindrome* example shown in the *Usage* section will not work if its alternation block is changed to atomic.

#### 9.3. Conditional Expression
Syntax:

```
    <<|               -- can use @| too
      |[cond1] ? alt1
      |[cond2] ? alt2
      |alt_else
```
- `cond1` and `cond2` must be names of [capture groups]().
- Specs of alts can be seen in *Backtrackable Alternation* subsection, with one additional restriction: alts cannot be conditional expression.
- The last branch of an alternation must NOT be a conditional expression, because (see the following example):

```
     <<|
       |[x] ? alpha
       |[y] ? digit
```
If neither x nor y is defined, what should it match? Should it just succeed? Or should it fail? It's not clear. That's why the last branch cannot be a conditional. 

- If you want it to "just succeed", add an empty branch.
- If you want it to fail, add `FAIL!`.
- If you want it to match some (non-conditional) expression, put it as the last branch.

Example:

```
     <<|
       |[x] ? alpha
       |[y] ? digit
       |            -- or FAIL!, or (non-alternation non-lookaround) expression
```

For more example, see the *Stuff-Inside-Brackets* example in the *Tutorial* section.

#### 9.4. The `FAIL!` Command

`FAIL!` compiles to `(?!)` which [will always fail]().

--
### 10. Lookaround Block

A lookaround block starts with `<@>` and ends with empty line.

```
<@>
            |lookahead>              -- positive lookahead
            |!lookahead>             -- negative lookahead
 <lookbehind|                        -- positive lookbehind
<!lookbehind|                        -- negative lookbehind
            |match_things_normally|
                                  |lookahead>
                                  |!lookahead>
                       <lookbehind|
                      <!lookbehind|
                                  
```
Each of the `lookahead`, `lookbehind`, and `match_things_normally` in the above example can be one of:

- A [variable]() name
- [Negation]() using `non-`
- [Backreference]()
- [Lookup Chain]()

#### 10.1. Lookaround Examples

Description                        | Example
---------------------------------- | ---------------------
Lookahead a variable               | `|digit>`
Lookbehind a negation              | `<non-digit|`
Negative-lookahead a negation      | `|!non-digit>`
Negative-lookahead a backreference | `|!=captur>`
Negative-lookahead a lookup-chain  | `|!/captur/=captur/>`
Negative-lookbehind a lookup-chain | `<!/alpha/digit/|`

#### 10.2. The "Match Things Normally" Part

Lookaheads and lookbehinds match characters, but then gives up the match. They do not consume characters in the string. The "match things normally" part is that, match normally/don't just look around/don't give up the match/do consume the characters. Examples

```
<@>
<backslash|
          |quote|
```
```
<@>
|!dash>
|dashes_and_alnums|
            <!dash|
```

#### 10.3. A Note About `<@>`

Everywhere else in oprex, the **at**-sign `@` means _**at**omic_:

- In alternation: `@|` starts an *atomic alternation block*.
- In quantification: quantifiers that start with `@` (e.g. `@1..`) are *possessive quantifiers*, which work atomically.

So how about `<@>`? The `@` there reminds you that [lookarounds are atomic](). With `<` in a lookaround-block means lookbehind, and `>` means lookahead, `<@>` (which looks like an **eye**) is the perfect symbol to begin a **look**around-block. 

--
### 11. Quantification/Repetition
#### 11.1. The `of` keyword

`of` is oprex's keyword for doing quantification/repetition:

```
    quantifier of expression
```
```
    quantifier of: c h a r s
```
For *quantifier* description, see below. For the target, see [expression]() and [character-class]().

#### 11.2. Quantifier
##### 11.2.1. Repeat N Times: `N of`
Example (result in comments):

```
    zipcode = 5 of digit    -- \d{5}
    byte    = 8 of: 0 1     -- [01]{8}
```
--
##### 11.2.2. Repeat N-or-More: `N.. of`
```
    wont_listen = @3.. of "la"          -- (?:la){3,}+
    hex_number  = @1.. of: 0..9 A..F    -- [0-9A-F]++
```
--
##### 11.2.3. Repeat Min to Max Times: `M..N of`
```
    deck = @0..52 of: 2 3 4 5 6 7 8 9 X J Q K A
    batman_fight = @7..11 of <<|                
                               |'bam'
                               |'pow'
                               |'kapow'
```
--
#### 11.3. Greedy/Lazy/Possessive

In oprex, `@` means atomic, `<<` means allow backtrack. So, on quantifiers:

**`@`** = atomic = **possessive**

**`<<+`** = backtrack to add more = **lazy**

**`<<-`** = backtrack to lessen = **greedy**

The exact syntax is:

Type       | Syntax (max is optional)
---------- | ------------------------
possessive | `@min..max`
greedy     | `min..max <<-`
lazy       | `min <<+..max`

Example     | Meaning              | Compiles To
----------- | -------------------- | --------------------------------
`@1..`      | atomic one or more   | `++`
`1.. <<-`   | match one or more<br>allow backtrack to reduce the number of matches                  | `+`
`1 <<+..`   | match one<br>allow backtrack to match more, no max                                 | `+?`
`@0..10`    | atomic zero to ten   | `{,10}+`
`0..10 <<-` | match zero to ten<br>allow backtrack to lessen          | `{,10}`
`0 <<+..10` | match zero<br>may backtrack to match more, maximum ten  | `{,10}?`

#### 11.4. The `?` Operator
- Can be used as quantifier, i.e. `? of expression`, `? of: c h a r s`
- Can be applied directly to:
  - A variable lookup, e.g. `digit?`
  - Backreference, e.g. `=captur?`
  - Match-Until operator, i.e. `__?`
 
 Example: `? of /digit?/=captur?/__?/`

#### 11.5. `?` Applied to `1..`

If `?` is applied to an expression while the expression is already quantified by `1..`, it will change the quantifier into `0..` while keeping its greediness/laziness/possessivity.

Example:

```
    digits?
        digits = @1.. of digit
```
Compiles to `\d*+`.

If we change the quantifier from `@1..` to `1.. <<-`, the output becomes `\d*`, and if  we change it to `1 <<+..`, the output becomes `\d*?`.

This improves readability. Consider the following two examples:

```
    /quote/contents/quote/              -- contents is not optional
        quote: "
        contents = @0.. of not: quote   -- but it allows zero match
```
```
    /quote/contents?/quote/             -- contents is optional
        quote: "
        contents = @1.. of not: quote   -- minimum 1 match
```
Both compile to the same regex: `"[^"]*+"`. But the second example is better. It more clearly shows that there can be no content between the quotes.