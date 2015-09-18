# oprex
A more readable, maintainable regex syntax.

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
##### 9. Balanced Parentheses <a name="example-balanced-parens"></a>
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
- Will not match: `f(g(x))`
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

### 1. Range of digits
On the *IPv4 Address*, *Date*, and *Time* examples:

- `byte = '0'..'255'` (leading-zero not allowed, e.g. won't match `007`)
- `hh = '1'..'12'`
- `mm = '01'..'12'` (leading-zero mandatory for single-digits)
- `dd = '01'..'31'`
- `mm = ss = '00'..'59'`
- `HH = 'o0'..'23'` (the `o` means optional leading-zero)

### 2. Backreference

### 3. Flags

### 4. Match-anything-until

### 5. Recursion

### 6. Global Variable


## Reference Manual
### 1. Built-in Variables
#### 1.1. Built-in Character Classes

Name        | Output             | Output when (unicode)          
-------- | ------------ | ---------------------
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

Name        | Meaning               | Output          
-------- | -------------- | ---------------------
`BOS`       | `beginning of string` | `\A`
`EOS`       | `end of string`       | `\Z`
`BOL`       | `beginning of line`   | `(?m:^)`
`EOL`       | `end of line`         | `(?m:$)`
`BOW`       | `beginning of word`   | `\m`
`EOW`       | `end of word`         | `\M`
`WOB`       | `word boundary`       | `\b`
`any`       | `any character`       | `(?s:.)` (`.` with DOTALL turned on)
`uany`      | `unicode-any`         | `\X` (single unicode grapheme)

- `WOB` is special: it is not a character-class, but you can apply the `non-` operator to it. `non-WOB` compiles to `\B`.
- Oprex-equivalent of regex's `.` with DOTALL turned OFF is `non-linechar` (see `linechar` in *Built-in Character Classes* table).

--
### 2. Main Syntax
The general syntax of oprex is in the form of:

```
>>> oprex('''
...     (flags)
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
        password = (-ignorecase) 'correctHorseBatteryStaple' -- scoped flag, turning off
```
Compiles to `(?V1wui)(?-i:correctHorseBatteryStaple)`

- `version1` and `word` are turned on by default (hence the `V1w` in the example's output).
- For what each flag does, refer to the [regex module documentation]().

#### 2.2. Expression
Expression can be one of the following:

- String literal
- Range-of-digits literal
- Variable(s) lookup
- Alternation block
- Lookaround block
- Quantification/repetition
    
#### 2.3. Definition/Assignment
