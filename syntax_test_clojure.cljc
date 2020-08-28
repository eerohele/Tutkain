; SYNTAX TEST "Packages/tutkain/Clojure (Tutkain).sublime-syntax"

; # Comments and whitespace

  ;blah
; ^ comment.line.clojure punctuation.definition.comment
;  ^^^^ comment.line.clojure

  ;;; blah
; ^^^ comment.line.clojure punctuation.definition.comment
;    ^^^^^ comment.line.clojure

  blah;blah;blah
; ^^^^- comment
;     ^ comment.line.clojure

  #!blah
; ^^ comment.line.clojure punctuation.definition.comment
;   ^^^^^ comment.line.clojure
  #! blah
; ^^ comment.line.clojure punctuation.definition.comment
;   ^^^^^^ comment.line.clojure
  #!#!#! blah
; ^^ comment.line.clojure punctuation.definition.comment
;   ^^^^^^^^^^ comment.line.clojure

  blah,blah, blah
;     ^ punctuation.comma.clojure
;     ^ comment.punctuation.comma.clojure
;      ^- comment
;          ^ punctuation.comma.clojure
;          ^ comment.punctuation.comma.clojure
;           ^- comment

; ## Include end-of-line

; ; blah
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ comment.line.clojure



; # Constants

  true false nil
; ^^^^ constant.language.clojure
;     ^ - constant
;      ^^^^^ constant.language.clojure
;           ^ - constant
;            ^^^ constant.language.clojure

; ## Breaks

  true,false,nil
; ^^^^ constant.language.clojure
;     ^ comment.punctuation.comma.clojure
;      ^^^^^ constant.language.clojure
  true;false;nil
; ^^^^ constant.language.clojure
;     ^ comment.line.clojure punctuation.definition.comment

; ## Unaffected

  'nil (true) (nil)
; ^ keyword.operator.macro.clojure
;  ^^^ constant.language.clojure
;      ^ punctuation.section.parens.begin.clojure
;       ^^^^ constant.language.clojure
;           ^ punctuation.section.parens.end.clojure

; ## No highlighting

  nill nil- -nil nil?
; ^^^^^^^^^^^^^^^^^^^ - constant



; # Numbers

  1234 1234N +1234 +1234N -1234 -1234N
; ^^^^ constant.numeric.integer.decimal.clojure
;     ^ - constant
;      ^^^^^ constant.numeric.integer.decimal.clojure
;          ^ storage.type.numeric.clojure
;           ^ - constant
;            ^ punctuation.definition.numeric.sign.clojure
;            ^^^^^ constant.numeric.integer.decimal.clojure
;                 ^ - constant
;                  ^ punctuation.definition.numeric.sign.clojure
;                  ^^^^^^ constant.numeric.integer.decimal.clojure
;                       ^ storage.type.numeric.clojure
;                        ^ - constant
;                         ^ punctuation.definition.numeric.sign.clojure
;                         ^^^^^ constant.numeric.integer.decimal.clojure
;                              ^ - constant
;                               ^ punctuation.definition.numeric.sign.clojure
;                               ^^^^^^ constant.numeric.integer.decimal.clojure
;                                    ^ storage.type.numeric.clojure
  0x1234af 0x1234afN 0X1234AF 0X1234AFN
; ^^ punctuation.definition.numeric.base.clojure
; ^^^^^^^^ constant.numeric.integer.hexadecimal.clojure
;         ^ - constant
;          ^^ punctuation.definition.numeric.base.clojure
;          ^^^^^^^^^ constant.numeric.integer.hexadecimal.clojure
;                  ^ storage.type.numeric.clojure
;                   ^ - constant
;                    ^^ punctuation.definition.numeric.base.clojure
;                    ^^^^^^^^ constant.numeric.integer.hexadecimal.clojure
;                            ^ - constant
;                             ^^ punctuation.definition.numeric.base.clojure
;                             ^^^^^^^^^ constant.numeric.integer.hexadecimal.clojure
;                                     ^ storage.type.numeric.clojure
  +0x1234af +0x1234afN +0X1234AF +0X1234AFN
; ^ punctuation.definition.numeric.sign.clojure
;  ^^ punctuation.definition.numeric.base.clojure
; ^^^^^^^^^ constant.numeric.integer.hexadecimal.clojure
;          ^ - constant
;           ^ punctuation.definition.numeric.sign.clojure
;            ^^ punctuation.definition.numeric.base.clojure
;           ^^^^^^^^^^ constant.numeric.integer.hexadecimal.clojure
;                    ^ storage.type.numeric.clojure
;                     ^ - constant
;                      ^ punctuation.definition.numeric.sign.clojure
;                       ^^ punctuation.definition.numeric.base.clojure
;                       ^^^^^^^^ constant.numeric.integer.hexadecimal.clojure
;                               ^ - constant
;                                ^ punctuation.definition.numeric.sign.clojure
;                                 ^^ punctuation.definition.numeric.base.clojure
;                                ^^^^^^^^^^ constant.numeric.integer.hexadecimal.clojure
;                                         ^ storage.type.numeric.clojure
  -0x1234af -0x1234afN -0X1234AF -0X1234AFN
; ^ punctuation.definition.numeric.sign.clojure
;  ^^ punctuation.definition.numeric.base.clojure
; ^^^^^^^^^ constant.numeric.integer.hexadecimal.clojure
;          ^ - constant
;           ^ punctuation.definition.numeric.sign.clojure
;            ^^ punctuation.definition.numeric.base.clojure
;           ^^^^^^^^^^ constant.numeric.integer.hexadecimal.clojure
;                    ^ storage.type.numeric.clojure
;                     ^ - constant
;                      ^ punctuation.definition.numeric.sign.clojure
;                       ^^ punctuation.definition.numeric.base.clojure
;                      ^^^^^^^^^ constant.numeric.integer.hexadecimal.clojure
;                               ^ - constant
;                                ^ punctuation.definition.numeric.sign.clojure
;                                 ^^ punctuation.definition.numeric.base.clojure
;                                ^^^^^^^^^^ constant.numeric.integer.hexadecimal.clojure
;                                         ^ storage.type.numeric.clojure
  2r1010 16r1234af 32r1234az 2R1010 16R1234AF 32R1234AZ
; ^^ punctuation.definition.numeric.base.clojure
; ^^^^^^ constant.numeric.integer.other.clojure
;       ^ - constant
;        ^^^ punctuation.definition.numeric.base.clojure
;        ^^^^^^^^^ constant.numeric.integer.other.clojure
;                 ^ - constant
;                  ^^^ punctuation.definition.numeric.base.clojure
;                  ^^^^^^^^^ constant.numeric.integer.other.clojure
;                           ^ - constant
;                            ^^ punctuation.definition.numeric.base.clojure
;                            ^^^^^^ constant.numeric.integer.other.clojure
;                                  ^ - constant
;                                   ^^^ punctuation.definition.numeric.base.clojure
;                                   ^^^^^^^^^ constant.numeric.integer.other.clojure
;                                            ^ - constant
;                                             ^^^ punctuation.definition.numeric.base.clojure
;                                             ^^^^^^^^^ constant.numeric.integer.other.clojure
  +2r1010 +16r1234af +32r1234az +2R1010 +16R1234AF +32R1234AZ
; ^ punctuation.definition.numeric.sign.clojure
;  ^^ punctuation.definition.numeric.base.clojure
; ^^^^^^^ constant.numeric.integer.other.clojure
;        ^ - constant
;         ^ punctuation.definition.numeric.sign.clojure
;          ^^^ punctuation.definition.numeric.base.clojure
;         ^^^^^^^^^^ constant.numeric.integer.other.clojure
;                   ^ - constant
;                    ^ punctuation.definition.numeric.sign.clojure
;                     ^^^ punctuation.definition.numeric.base.clojure
;                    ^^^^^^^^^^ constant.numeric.integer.other.clojure
;                              ^ - constant
;                               ^ punctuation.definition.numeric.sign.clojure
;                                ^^ punctuation.definition.numeric.base.clojure
;                               ^^^^^^^ constant.numeric.integer.other.clojure
;                                      ^ - constant
;                                       ^ punctuation.definition.numeric.sign.clojure
;                                        ^^^ punctuation.definition.numeric.base.clojure
;                                        ^^^^^^^^^ constant.numeric.integer.other.clojure
;                                                 ^ - constant
;                                                  ^ punctuation.definition.numeric.sign.clojure
;                                                   ^^^ punctuation.definition.numeric.base.clojure
;                                                  ^^^^^^^^^^ constant.numeric.integer.other.clojure
  -2r1010 -16r1234af -32r1234az -2R1010 -16R1234AF -32R1234AZ
; ^ punctuation.definition.numeric.sign.clojure
;  ^^ punctuation.definition.numeric.base.clojure
; ^^^^^^^ constant.numeric.integer.other.clojure
;        ^ - constant
;         ^ punctuation.definition.numeric.sign.clojure
;          ^^^ punctuation.definition.numeric.base.clojure
;          ^^^^^^^^^ constant.numeric.integer.other.clojure
;                   ^ - constant
;                    ^ punctuation.definition.numeric.sign.clojure
;                     ^^^ punctuation.definition.numeric.base.clojure
;                    ^^^^^^^^^^ constant.numeric.integer.other.clojure
;                              ^ - constant
;                               ^ punctuation.definition.numeric.sign.clojure
;                                ^^ punctuation.definition.numeric.base.clojure
;                               ^^^^^^^ constant.numeric.integer.other.clojure
;                                      ^ - constant
;                                       ^ punctuation.definition.numeric.sign.clojure
;                                        ^^^ punctuation.definition.numeric.base.clojure
;                                       ^^^^^^^^^^ constant.numeric.integer.other.clojure
;                                                 ^ - constant
;                                                  ^ punctuation.definition.numeric.sign.clojure
;                                                   ^^^ punctuation.definition.numeric.base.clojure
;                                                  ^^^^^^^^^^ constant.numeric.integer.other.clojure
  0/10 10/20 30/0
; ^^^^ constant.numeric.rational.decimal.clojure
;  ^ punctuation.separator.rational.clojure
;     ^ - constant
;      ^^^^^ constant.numeric.rational.decimal.clojure
;        ^ punctuation.separator.rational.clojure
;           ^ - constant
;            ^^^^ constant.numeric.rational.decimal.clojure
;              ^ punctuation.separator.rational.clojure
  +0/10 +10/20 +30/0
; ^^^^^ constant.numeric.rational.decimal.clojure
; ^ punctuation.definition.numeric.sign.clojure
;   ^ punctuation.separator.rational.clojure
;      ^ - constant
;       ^^^^^^ constant.numeric.rational.decimal.clojure
;       ^ punctuation.definition.numeric.sign.clojure
;          ^ punctuation.separator.rational.clojure
;             ^ - constant
;              ^^^^^ constant.numeric.rational.decimal.clojure
;              ^ punctuation.definition.numeric.sign.clojure
;                 ^ punctuation.separator.rational.clojure
  -0/10 -10/20 -30/0
; ^^^^^ constant.numeric.rational.decimal.clojure
; ^ punctuation.definition.numeric.sign.clojure
;   ^ punctuation.separator.rational.clojure
;      ^ - constant
;       ^^^^^^ constant.numeric.rational.decimal.clojure
;       ^ punctuation.definition.numeric.sign.clojure
;          ^ punctuation.separator.rational.clojure
;             ^ - constant
;              ^^^^^ constant.numeric.rational.decimal.clojure
;              ^ punctuation.definition.numeric.sign.clojure
;                 ^ punctuation.separator.rational.clojure
  1234M 1234.0M 1234.1234M
; ^^^^^ constant.numeric.float.decimal.clojure
;     ^ storage.type.numeric.clojure
;      ^ - constant
;       ^^^^^^^ constant.numeric.float.decimal.clojure
;           ^ punctuation.separator.decimal.clojure
;             ^ storage.type.numeric.clojure
;              ^ - constant
;               ^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                   ^ punctuation.separator.decimal.clojure
;                        ^ storage.type.numeric.clojure
  +1234M +1234.0M +1234.1234M
; ^^^^^^ constant.numeric.float.decimal.clojure
; ^ punctuation.definition.numeric.sign.clojure
;      ^ storage.type.numeric.clojure
;       ^ - constant
;        ^^^^^^^^ constant.numeric.float.decimal.clojure
;        ^ punctuation.definition.numeric.sign.clojure
;             ^ punctuation.separator.decimal.clojure
;               ^ storage.type.numeric.clojure
;                ^ - constant
;                 ^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                 ^ punctuation.definition.numeric.sign.clojure
;                      ^ punctuation.separator.decimal.clojure
;                           ^ storage.type.numeric.clojure
  -1234M -1234.0M -1234.1234M
; ^^^^^^ constant.numeric.float.decimal.clojure
; ^ punctuation.definition.numeric.sign.clojure
;      ^ storage.type.numeric.clojure
;       ^ - constant
;        ^^^^^^^^ constant.numeric.float.decimal.clojure
;        ^ punctuation.definition.numeric.sign.clojure
;             ^ punctuation.separator.decimal.clojure
;               ^ storage.type.numeric.clojure
;                ^ - constant
;                 ^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                 ^ punctuation.definition.numeric.sign.clojure
;                      ^ punctuation.separator.decimal.clojure
;                           ^ storage.type.numeric.clojure
  1234e10 1234E10M 1234.1234e10M 1234.1234E10M
; ^^^^^^^ constant.numeric.float.decimal.clojure
;        ^ - constant
;         ^^^^^^^ constant.numeric.float.decimal.clojure
;                ^ storage.type.numeric.clojure
;                 ^ - constant
;                  ^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                      ^ punctuation.separator.decimal.clojure
;                              ^ storage.type.numeric.clojure
;                               ^ - constant
;                                ^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                                    ^ punctuation.separator.decimal.clojure
;                                            ^ storage.type.numeric.clojure
  +1234e10 +1234E10M +1234.1234e10M +1234.1234E10M
; ^^^^^^^^ constant.numeric.float.decimal.clojure
; ^ punctuation.definition.numeric.sign.clojure
;         ^ - constant
;          ^^^^^^^^^ constant.numeric.float.decimal.clojure
;          ^ punctuation.definition.numeric.sign.clojure
;                  ^ storage.type.numeric.clojure
;                   ^ - constant
;                    ^^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                    ^ punctuation.definition.numeric.sign.clojure
;                         ^ punctuation.separator.decimal.clojure
;                                 ^ storage.type.numeric.clojure
;                                  ^ - constant
;                                   ^^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                                   ^ punctuation.definition.numeric.sign.clojure
;                                        ^ punctuation.separator.decimal.clojure
;                                                ^ storage.type.numeric.clojure
  -1234e10 -1234E10M -1234.1234e10M -1234.1234E10M
; ^^^^^^^^ constant.numeric.float.decimal.clojure
; ^ punctuation.definition.numeric.sign.clojure
;         ^ - constant
;          ^^^^^^^^^ constant.numeric.float.decimal.clojure
;          ^ punctuation.definition.numeric.sign.clojure
;                  ^ storage.type.numeric.clojure
;                   ^ - constant
;                    ^^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                    ^ punctuation.definition.numeric.sign.clojure
;                         ^ punctuation.separator.decimal.clojure
;                                 ^ storage.type.numeric.clojure
;                                  ^ - constant
;                                   ^^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                                   ^ punctuation.definition.numeric.sign.clojure
;                                        ^ punctuation.separator.decimal.clojure
;                                                ^ storage.type.numeric.clojure
  1234.1234e+10 1234.1234E+10 1234.1234e-10 1234.1234E-10
; ^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;     ^ punctuation.separator.decimal.clojure
;              ^ - constant
;               ^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                   ^ punctuation.separator.decimal.clojure
;                            ^ - constant
;                             ^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                                 ^ punctuation.separator.decimal.clojure
;                                          ^ - constant
;                                           ^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                                               ^ punctuation.separator.decimal.clojure
  +1234.1234e+10M +1234.1234E+10M +1234.1234e-10M +1234.1234E-10M
; ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
; ^ punctuation.definition.numeric.sign.clojure
;      ^ punctuation.separator.decimal.clojure
;               ^ storage.type.numeric.clojure
;                ^ - constant
;                 ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                 ^ punctuation.definition.numeric.sign.clojure
;                      ^ punctuation.separator.decimal.clojure
;                               ^ storage.type.numeric.clojure
;                                ^ - constant
;                                 ^ punctuation.definition.numeric.sign.clojure
;                                 ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                                      ^ punctuation.separator.decimal.clojure
;                                               ^ storage.type.numeric.clojure
;                                                ^ - constant
;                                                 ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                                                 ^ punctuation.definition.numeric.sign.clojure
;                                                      ^ punctuation.separator.decimal.clojure
;                                                               ^ storage.type.numeric.clojure
  -1234.1234e+10M -1234.1234E+10M -1234.1234e-10M -1234.1234E-10M
; ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
; ^ punctuation.definition.numeric.sign.clojure
;      ^ punctuation.separator.decimal.clojure
;               ^ storage.type.numeric.clojure
;                ^ - constant
;                 ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                 ^ punctuation.definition.numeric.sign.clojure
;                      ^ punctuation.separator.decimal.clojure
;                               ^ storage.type.numeric.clojure
;                                ^ - constant
;                                 ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                                 ^ punctuation.definition.numeric.sign.clojure
;                                      ^ punctuation.separator.decimal.clojure
;                                               ^ storage.type.numeric.clojure
;                                                ^ - constant
;                                                 ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.clojure
;                                                 ^ punctuation.definition.numeric.sign.clojure
;                                                      ^ punctuation.separator.decimal.clojure
;                                                               ^ storage.type.numeric.clojure

; ## Breaks

  10,20,30
; ^^ constant.numeric
;   ^ comment.punctuation.comma.clojure
;    ^^ constant.numeric
  10;20;30
; ^^ constant.numeric
;   ^ comment.line.clojure punctuation.definition.comment
  10'20'30
; ^^ constant.numeric
;   ^ keyword.operator.macro.clojure
  10`20`30
; ^^ constant.numeric
;   ^ keyword.operator.macro.clojure
  10#20#30
; ^^ constant.numeric
;   ^ - constant

; ## Unaffected

  '1234 '+1234 '-1234
; ^ keyword.operator.macro.clojure
;  ^^^^ constant.numeric

  (10 20 30) [10 20 30]
; ^ punctuation.section.parens.begin.clojure
;  ^^ constant.numeric
;            ^ punctuation.section.brackets.begin.clojure
;             ^^ constant.numeric

  ([100 200])
; ^ punctuation.section.parens.begin.clojure
;  ^ punctuation.section.brackets.begin.clojure
;   ^^^ constant.numeric
;       ^^^ constant.numeric
;          ^ punctuation.section.brackets.end.clojure
;           ^ punctuation.section.parens.end.clojure
  ([0x10 0x20])
; ^ punctuation.section.parens.begin.clojure
;  ^ punctuation.section.brackets.begin.clojure
;   ^^^^ constant.numeric
;        ^^^^ constant.numeric
;            ^ punctuation.section.brackets.end.clojure
;             ^ punctuation.section.parens.end.clojure
  ([2r100 16r200])
; ^ punctuation.section.parens.begin.clojure
;  ^ punctuation.section.brackets.begin.clojure
;   ^^^^^ constant.numeric
;         ^^^^^^ constant.numeric
;               ^ punctuation.section.brackets.end.clojure
;                ^ punctuation.section.parens.end.clojure
  ([10/20 30/40])
; ^ punctuation.section.parens.begin.clojure
;  ^ punctuation.section.brackets.begin.clojure
;   ^^^^^ constant.numeric
;         ^^^^^ constant.numeric
;              ^ punctuation.section.brackets.end.clojure
;               ^ punctuation.section.parens.end.clojure
  ([100.100 200.200])
; ^ punctuation.section.parens.begin.clojure
;  ^ punctuation.section.brackets.begin.clojure
;   ^^^^^^^ constant.numeric
;           ^^^^^^^ constant.numeric
;                  ^ punctuation.section.brackets.end.clojure
;                   ^ punctuation.section.parens.end.clojure
  ([1e+10 2e-20])
; ^ punctuation.section.parens.begin.clojure
;  ^ punctuation.section.brackets.begin.clojure
;   ^^^^^ constant.numeric
;         ^^^^^ constant.numeric
;              ^ punctuation.section.brackets.end.clojure
;               ^ punctuation.section.parens.end.clojure

; ## Invalid numbers

  01234 +01234 -01234 '01234
; ^^^^^ invalid.deprecated.clojure
;      ^- invalid
;       ^^^^^^ invalid.deprecated.clojure
;              ^^^^^^ invalid.deprecated.clojure
;                     ^ keyword.operator.macro.clojure
;                      ^^^^^ invalid.deprecated.clojure
  01234N +01234N -01234N '01234N
; ^^^^^^ invalid.deprecated.clojure
;       ^- invalid
;        ^^^^^^^ invalid.deprecated.clojure
;                ^^^^^^^ invalid.deprecated.clojure
;                        ^ keyword.operator.macro.clojure
  10-20 10+20 1234n 1234m 1234. 1234.M
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ - constant
  10.0/20 10/20.0 10/+20 10/-20
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ - constant
  10:20:30
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ - constant
  1r000
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ - constant

; ## Ignore

  ; valid symbols
  .1234 .1234M
; ^^^^^^^^^^^^ - constant



; # Symbols

  ! $ % & * - _ = + | < > . / ?
  ++ --
  blah
  blah/blah
  blah.blah
  blah.blah/blah
  blah.blah/blah.blah
  blah/blah/blah
  blah1000
  blah1000.blah1000
  *blah*
  blah'blah'
  blah'''blah'''
  blah:blah:blah
  blah#blah#
  blah///blah

; ## Breaks

  blah,blah,blah
;     ^ comment.punctuation.comma.clojure
  blah;blah;blah
;     ^ comment.line.clojure punctuation.definition.comment
  blah`blah
;     ^ keyword.operator.macro.clojure
  blah~blah
;     ^ keyword.operator.macro.clojure
  blah@blah
;     ^ keyword.operator.macro.clojure
  blah^blah
;     ^ keyword.operator.macro.clojure
  blah\blah
;     ^ constant.character.clojure

; ## Unaffected

  'blah 'blah:blah
; ^ keyword.operator.macro.clojure
;  ^- keyword.operator.macro.clojure
  [blah blah blah]

; ## Invalid

  //
  blah:
  blah::blah
  /blah
  blah/



; # Keywords

; Basic structure
  :blah
; ^ punctuation.definition.keyword.clojure
; ^^^^^ constant.other.keyword.unqualified.clojure

  :! :$ :% :& :* :- :_ := :+ :| :< :> :. :/ :?
; ^^ constant.other.keyword.unqualified.clojure
;   ^ - constant
;    ^^ constant.other.keyword.unqualified.clojure
;       ^^ constant.other.keyword.unqualified.clojure
;          ^^ constant.other.keyword.unqualified.clojure
;             ^^ constant.other.keyword.unqualified.clojure
;                ^^ constant.other.keyword.unqualified.clojure
;                   ^^ constant.other.keyword.unqualified.clojure
;                      ^^ constant.other.keyword.unqualified.clojure
;                         ^^ constant.other.keyword.unqualified.clojure
;                            ^^ constant.other.keyword.unqualified.clojure
;                               ^^ constant.other.keyword.unqualified.clojure
;                                  ^^ constant.other.keyword.unqualified.clojure
;                                     ^^ constant.other.keyword.unqualified.clojure
;                                        ^^ constant.other.keyword.unqualified.clojure
;                                           ^^ constant.other.keyword.unqualified.clojure
  :++ :--
; ^^^ constant.other.keyword.unqualified.clojure
;    ^ - constant
;     ^^^ constant.other.keyword.unqualified.clojure
  :blah
; ^^^^^ constant.other.keyword.unqualified.clojure
  :blah/blah
; ^^^^^^^^^^ constant.other.keyword.qualified.clojure
;      ^ punctuation.definition.constant.namespace.clojure
  :blah.blah
; ^^^^^^^^^^ constant.other.keyword.unqualified.clojure
  :blah.blah/blah
;  ^^^^^^^^^ meta.namespace.clojure
;           ^ punctuation.definition.constant.namespace.clojure
; ^^^^^^^^^^^^^^^ constant.other.keyword.qualified.clojure
  :blah.blah/blah.blah
;  ^^^^^^^^^ meta.namespace.clojure
; ^^^^^^^^^^^^^^^^^^^^ constant.other.keyword.qualified.clojure
  :blah/blah/blah
;  ^^^^ meta.namespace.clojure
; ^^^^^^^^^^^^^^^ constant.other.keyword.qualified.clojure
  :blah1000
; ^^^^^^^^^ constant.other.keyword.unqualified.clojure
  :blah1000.blah1000
; ^^^^^^^^^^^^^^^^^^ constant.other.keyword.unqualified.clojure
  :*blah*
; ^^^^^^^ constant.other.keyword.unqualified.clojure
  :blah'blah'
; ^^^^^^^^^^^ constant.other.keyword.unqualified.clojure
  :blah'''blah'''
; ^^^^^^^^^^^^^^^ constant.other.keyword.unqualified.clojure
  :blah:blah:blah
; ^^^^^^^^^^^^^^^ constant.other.keyword.unqualified.clojure
  :blah#blah#
; ^^^^^^^^^^^ constant.other.keyword.unqualified.clojure
  ::blah///blah
; ^^ punctuation.definition.keyword.clojure
;   ^^^^ meta.namespace.clojure
;       ^ punctuation.definition.constant.namespace.clojure
; ^^^^^^^^^^^^^ constant.other.keyword.auto-qualified.clojure
  ://blah
; ^^^^^^^ constant.other.keyword.qualified.clojure
;  ^ punctuation.definition.constant.namespace.clojure
  :///
; ^^^^ constant.other.keyword.qualified.clojure
;  ^ punctuation.definition.constant.namespace.clojure
  :/blah/blah
; ^^^^^^^^^^^ constant.other.keyword.qualified.clojure
;  ^ punctuation.definition.constant.namespace.clojure
  :blah//
;  ^^^^ meta.namespace.clojure
; ^^^^^^^ constant.other.keyword.qualified.clojure
;      ^ punctuation.definition.constant.namespace.clojure

; ## These are valid, unlike symbols

  :' :# :### :10 :10.20
; ^^ constant.other.keyword.unqualified.clojure
;   ^ - constant
;    ^^ constant.other.keyword.unqualified.clojure
;       ^^^^ constant.other.keyword.unqualified.clojure
;            ^^^ constant.other.keyword.unqualified.clojure
;                ^^^^^^ constant.other.keyword.unqualified.clojure

; ## Breaks

  :,blah
; ^ - constant
;  ^ comment.punctuation.comma.clojure
  :;blah
; ^ - constant
;  ^ comment.line.clojure punctuation.definition.comment
  :blah,:blah,:blah
; ^^^^^ constant.other.keyword.unqualified.clojure
;      ^ comment.punctuation.comma.clojure
;       ^^^^^ constant.other.keyword.unqualified.clojure
  :blah;:blah;:blah
; ^^^^^ constant.other.keyword.unqualified.clojure
;      ^ comment.line.clojure punctuation.definition.comment
  :blah`blah
; ^^^^^ constant.other.keyword.unqualified.clojure
;      ^ keyword.operator.macro.clojure
  :blah~blah
; ^^^^^ constant.other.keyword.unqualified.clojure
  :blah@blah
;      ^ keyword.operator.macro.clojure
  :blah^blah
; ^^^^^ constant.other.keyword.unqualified.clojure
;      ^ keyword.operator.macro.clojure
  :blah\blah
; ^^^^^ constant.other.keyword.unqualified.clojure
;      ^^ constant.character.clojure

; ## These are invalid, but I couldn't get the regex right

  :
; ^^ - constant
  :::blah
; ^^^^^^^ - constant
  ://
  :10/20
  :blah10/20
  :blah:
  ::blah:
  ::blah::blah
  :/blah
  ::blah/



; # Chars

  \0 \; \,
; ^^ constant.character.clojure
;   ^ - constant.character.clojure
;    ^^ constant.character.clojure
;      ^ - constant.character.clojure
;       ^^ constant.character.clojure
; ^^ constant.character.clojure
  \newline
; ^^^^^^^^ constant.character.clojure
  blah \c blah \c
;      ^^ constant.character.clojure
;        ^ - constant.character.clojure
;              ^^ constant.character.clojure

; ## Invalid but highlight anyway

  \blah100
; ^^ constant.character.clojure
;   ^^^^^^ - constant.character.clojure

; ## Capture exactly one char

  \;;;;
; ^^ constant.character.clojure
;   ^^^ comment.line.clojure punctuation.definition.comment
  \,,
; ^^ constant.character.clojure
;   ^ comment.punctuation.comma.clojure
  \``blah
; ^^ constant.character.clojure
;   ^ keyword.operator.macro.clojure
  \''blah
; ^^ constant.character.clojure
;   ^ keyword.operator.macro.clojure
  \~~blah
; ^^ constant.character.clojure
;   ^ keyword.operator.macro.clojure
  \@@blah
; ^^ constant.character.clojure
;   ^ keyword.operator.macro.clojure
  \~@~@blah
; ^^ constant.character.clojure
;   ^^^ keyword.operator.macro.clojure
  \##{}
; ^^ constant.character.clojure
;   ^^ punctuation.section.braces.begin.clojure
  \^^blah
; ^^ constant.character.clojure
;   ^ keyword.operator.macro.clojure

; ## Breaks

  \a,\b,\c
; ^^ constant.character.clojure
;   ^ comment.punctuation.comma.clojure
;    ^^ constant.character.clojure
  \a;\b;\c
; ^^ constant.character.clojure
;   ^ comment.line.clojure punctuation.definition.comment

; ## Unaffected

  \c (\c) ( \c ) [\c] [ \c ]
; ^^ constant.character.clojure
;    ^ punctuation.section.parens.begin.clojure
;     ^^ constant.character.clojure
;       ^ punctuation.section.parens.end.clojure
;         ^ punctuation.section.parens.begin.clojure
;           ^^ constant.character.clojure
;             ^ - constant.character.clojure
;              ^ punctuation.section.parens.end.clojure



; # Strings

  "blah"
; ^^^^^^ string.quoted.double.clojure
; ^ string.quoted.double.clojure punctuation.definition.string.begin.clojure
;      ^ string.quoted.double.clojure punctuation.definition.string.end.clojure

  "blah \" blah"
; ^^^^^^^^^^^^^^ string.quoted.double.clojure
; ^ string.quoted.double.clojure punctuation.definition.string.begin.clojure
;       ^^ string.quoted.double.clojure constant.character.escape.clojure
;         ^^^^^ string.quoted.double.clojure
;              ^ string.quoted.double.clojure punctuation.definition.string.end.clojure

  "
; ^ string.quoted.double.clojure punctuation.definition.string.begin.clojure
; ^^^^^^^^^^^^^^^^^^^^^^ string.quoted.double.clojure
  blah () [] {} ::blah
; ^^^^^^^^^^^^^^^^^^^^^ string.quoted.double.clojure
  "
; ^ string.quoted.double.clojure punctuation.definition.string.end.clojure

  "
; ^ string.quoted.double.clojure punctuation.definition.string.begin.clojure
  (unclosed paren ->
; ^^^^^^^^^^^^^^^^^^^ string.quoted.double.clojure
  "
; ^ string.quoted.double.clojure punctuation.definition.string.end.clojure

; ## Breaks

  "blah","blah","blah"
; ^^^^^^ string.quoted.double.clojure
;       ^ comment.punctuation.comma.clojure
;        ^^^^^^ string.quoted.double.clojure
;              ^ comment.punctuation.comma.clojure
;               ^^^^^^ string.quoted.double.clojure

  "blah";"blah";"blah"
; ^^^^^^ string.quoted.double.clojure
;       ^ comment.line.clojure punctuation.definition.comment

; ## Unaffected

  '"blah" ("blah") ( "blah" ) ["blah"]
; ^ keyword.operator.macro.clojure
;  ^^^^^^ string.quoted.double.clojure
;         ^ punctuation.section.parens.begin.clojure
;          ^^^^^^ string.quoted.double.clojure
;                ^ punctuation.section.parens.end.clojure
;                  ^ punctuation.section.parens.begin.clojure
;                    ^^^^^^ string.quoted.double.clojure
;                          ^- string.quoted.double.clojure
;                           ^ punctuation.section.parens.end.clojure


; # Regex

  #""
; ^ keyword.operator.macro.clojure
;  ^^ string.regexp.clojure
;  ^ string.regexp.clojure punctuation.definition.string.begin.clojure
;   ^ string.regexp.clojure punctuation.definition.string.end.clojure

  #" blah "
; ^ keyword.operator.macro.clojure
;  ^^^^^^^^ string.regexp.clojure
;  ^ string.regexp.clojure punctuation.definition.string.begin.clojure
;         ^ string.regexp.clojure punctuation.definition.string.end.clojure

  #"blah{1}"
; ^ keyword.operator.macro.clojure
;  ^^^^^^^^^ string.regexp.clojure
;  ^ string.regexp.clojure punctuation.definition.string.begin.clojure
;       ^^^ string.regexp.clojure keyword.operator.quantifier.regexp
;          ^ string.regexp.clojure punctuation.definition.string.end.clojure

  #"
; ^ keyword.operator.macro.clojure
;  ^ string.regexp.clojure punctuation.definition.string.begin.clojure
  blah{1}
; ^^^^ string.regexp.clojure
;     ^^^ string.regexp.clojure keyword.operator.quantifier.regexp
  "
; ^ string.regexp.clojure punctuation.definition.string.end.clojure

  #"
; ^ keyword.operator.macro.clojure
;  ^ string.regexp.clojure punctuation.definition.string.begin.clojure
  \"
; ^^ string.regexp.clojure constant.character.escape.regexp
  (unclosed paren ->
; ^ string.regexp.clojure
  "
; ^ string.regexp.clojure punctuation.definition.string.end.clojure

; ## Tonsky
  #""
; ^^^ string.regexp
; ^^  punctuation.definition.string.begin
;   ^ punctuation.definition.string.end
;    ^ - string.regexp
  #"abc"
; ^^^^^^ string.regexp
; ^^  punctuation.definition.string.begin
;      ^ punctuation.definition.string.end
;       ^ - string.regexp
  #"\\ \07 \077 \0377 \xFF \uFFFF \x{0} \x{FFFFF} \x{10FFFF} \N{white smiling face}"
;   ^^ constant.character.escape
;      ^^^ constant.character.escape
;          ^^^^ constant.character.escape
;               ^^^^^ constant.character.escape
;                     ^^^^ constant.character.escape
;                          ^^^^^^ constant.character.escape
;                                 ^^^^^ constant.character.escape
;                                       ^^^^^^^^^ constant.character.escape
;                                                 ^^^^^^^^^^ constant.character.escape
;                                                            ^^^^^^^^^^^^^^^^^^^^^^ constant.character.escape
  #"\t \n \r \f \a \e \cC \d \D \h \H \s \S \v \V \w \W"
;   ^^ constant.character.escape
;      ^^ constant.character.escape
;         ^^ constant.character.escape
;            ^^ constant.character.escape
;               ^^ constant.character.escape
;                  ^^ constant.character.escape
;                     ^^^ constant.character.escape
;                         ^^ constant.character.escape
;                            ^^ constant.character.escape
;                               ^^ constant.character.escape
;                                  ^^ constant.character.escape
;                                     ^^ constant.character.escape
;                                        ^^ constant.character.escape
;                                           ^^ constant.character.escape
;                                              ^^ constant.character.escape
;                                                 ^^ constant.character.escape
;                                                    ^^ constant.character.escape
  #"\p{IsLatin} \p{L} \b \b{g} \B \A \G \Z \z \R \X \0 \99 \k<gr3> \( \} \""
;   ^^^^^^^^^^^ constant.character.escape
;               ^^^^^ constant.character.escape
;                     ^^ constant.character.escape
;                        ^^^^^ constant.character.escape
;                              ^^ constant.character.escape
;                                 ^^ constant.character.escape
;                                    ^^ constant.character.escape
;                                       ^^ constant.character.escape
;                                          ^^ constant.character.escape
;                                             ^^ constant.character.escape
;                                                ^^ constant.character.escape
;                                                   ^^ constant.character.escape
;                                                      ^^^ constant.character.escape
;                                                          ^^^^^^^ constant.character.escape
;                                                                  ^^ constant.character.escape
;                                                                     ^^ constant.character.escape
;                                                                        ^^ constant.character.escape
  #"\y \x \uABC \p{Is Latin} \k<1gr> "
;   ^^ invalid.illegal.escape.regexp
;      ^^ invalid.illegal.escape.regexp
;         ^^ invalid.illegal.escape.regexp
;               ^^ invalid.illegal.escape.regexp
;                            ^^ invalid.illegal.escape.regexp
  #"[^a-z\[^&&[-a-z-]]]"
;   ^ punctuation.section.brackets.begin
;    ^ keyword.operator.negation.regexp
;         ^ - punctuation.section.brackets
;          ^ - keyword.operator.negation.regexp
;           ^^ keyword.operator.intersection.regexp
;             ^ punctuation.section.brackets.begin
;              ^ - keyword.operator.range.regexp
;                ^ keyword.operator.range.regexp
;                  ^ - keyword.operator.range.regexp
;                   ^^ punctuation.section.brackets.end
;                     ^ - punctuation
  #"a? a* a+ a{1} a{1,} a{1,2}"
;    ^ keyword.operator.quantifier.regexp
;       ^ keyword.operator.quantifier.regexp
;          ^ keyword.operator.quantifier.regexp
;             ^^^ keyword.operator.quantifier.regexp
;                  ^^^^ keyword.operator.quantifier.regexp
;                        ^^^^^ keyword.operator.quantifier.regexp
  #"a?? a*? a+? a{1}? a{1,}? a{1,2}?"
;    ^^ keyword.operator.quantifier.regexp
;        ^^ keyword.operator.quantifier.regexp
;            ^^ keyword.operator.quantifier.regexp
;                ^^^^ keyword.operator.quantifier.regexp
;                      ^^^^^ keyword.operator.quantifier.regexp
;                             ^^^^^^ keyword.operator.quantifier.regexp
  #"a?+ a*+ a++ a{1}+ a{1,}+ a{1,2}+"
;    ^^ keyword.operator.quantifier.regexp
;        ^^ keyword.operator.quantifier.regexp
;            ^^ keyword.operator.quantifier.regexp
;                ^^^^ keyword.operator.quantifier.regexp
;                      ^^^^^ keyword.operator.quantifier.regexp
;                             ^^^^^^ keyword.operator.quantifier.regexp
  #"(x|(\(\||[)|])))"
;   ^ punctuation.section.parens.begin
;     ^ keyword.operator.union.regexp
;      ^ punctuation.section.parens.begin
;        ^ - punctuation.section.parens
;          ^ - keyword.operator
;           ^ keyword.operator.union.regexp
;             ^ - punctuation.section.parens - invalid
;              ^ - keyword.operator - invalid
;                ^^ punctuation.section.parens.end
;                  ^ invalid.illegal.stray-bracket-end
  #"(?<name>a) (?:a) (?idm-suxUa) (?sux-idm:a) (?=a) (?!a) (?<=a) (?<!a) (?>a)"
;   ^ punctuation.section.parens.begin
;    ^^^^^^^ keyword.operator.special.regexp
;            ^ punctuation.section.parens.end
;               ^^ keyword.operator.special.regexp
;                     ^^^^^^^^^ keyword.operator.special.regexp
;                                  ^^^^^^^^^ keyword.operator.special.regexp
;                                               ^^ keyword.operator.special.regexp
;                                                     ^^ keyword.operator.special.regexp
;                                                           ^^^ keyword.operator.special.regexp
;                                                                  ^^^ keyword.operator.special.regexp
;                                                                         ^^ keyword.operator.special.regexp
  #"(abc) \Q (a|b) [^DE] )] \" \E (abc)"
;       ^ punctuation.section.parens.end - constant.character.escape
;         ^^ punctuation.section.quotation.begin
;           ^^^^^^^^^^^^^^^^^^^ constant.character.escape - punctuation - keyword - invalid
;                              ^^ punctuation.section.quotation.end
;                                 ^ punctuation.section.parens.begin - constant.character.escape
  #"\Q ABC" #"(" #"["
; ^^^^^^^^^ string.regexp
;     ^^^^ constant.character.escape
;         ^ punctuation.definition.string.end - constant.character.escape
;          ^ - string.regexp
;           ^^^^ string.regexp
;               ^  - string.regexp
;                ^^^^ string.regexp
;                    ^  - string.regexp

; ## Invalid

  # ""
; ^ - keyword.operator.macro.clojure
;  ^^^- string.regexp.clojure



; # Dispatch

  #inst"0000"
; ^^^^^ keyword.operator.macro.clojure

  #blah blah
; ^^^^^ keyword.operator.macro.clojure
;      ^^^^^^- keyword.operator.macro.clojure

  #blah1000.blah1000/blah1000 blah
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^ keyword.operator.macro.clojure
;                            ^^^^^^- keyword.operator.macro.clojure

  #blah:blah blah
; ^^^^^^^^^^ keyword.operator.macro.clojure
;           ^^^^^^- keyword.operator.macro.clojure

  # inst "0000"
; ^ keyword.operator.macro.clojure
;   ^^^^ keyword.operator.macro.clojure
;       ^- keyword.operator.macro.clojure
;        ^^^^^^ string.quoted.double.clojure

  #
; ^ - keyword.operator.macro.clojure
    inst
    "0000"
;   ^ string.quoted.double.clojure punctuation.definition.string.begin.clojure

  #'blah
; ^^ keyword.operator.macro.clojure
;   ^^^^^- keyword.operator.macro.clojure

  #'
; ^^ keyword.operator.macro.clojure
  ; blah
; ^^^^^^^ comment.line.clojure
  blah
; ^^^^^- keyword.operator.macro.clojure

  #(list % %1)
; ^ keyword.operator.macro.clojure
;  ^- keyword.operator.macro.clojure
;   ^^^^ meta.function-call.clojure variable.function.clojure

  #[]
; ^ -keyword.operator.macro.clojure
;  ^- keyword.operator.macro.clojure

  #_[]
; ^^ comment.block.clojure punctuation.definition.comment.clojure
;   ^- keyword.operator.macro.clojure

  #?[]
; ^^ keyword.operator.macro.clojure
;   ^- keyword.operator.macro.clojure

  #:foo{} #:bar/baz{:a 1} #::quux{:b 2} :end
; ^ keyword.operator.macro.clojure
;  ^ punctuation.definition.keyword.clojure
;  ^^^^ constant.other.keyword.unqualified.clojure
; ^^^^^^^ meta.reader-form.clojure
;        ^ - meta
;         ^^^^^^^^^^^^^^^ meta.reader-form.clojure
;                        ^ - meta
;                         ^^^^^^^^^^^^^ meta.reader-form.clojure
;                                      ^ - meta

  ##NaN ##Inf ##-Inf
; ^^ keyword.operator.macro.clojure
;   ^^^ constant.other.symbolic.clojure
;       ^^ keyword.operator.macro.clojure
;         ^^^ constant.other.symbolic.clojure
;             ^^ keyword.operator.macro.clojure
;               ^^^^ constant.other.symbolic.clojure

  ##
; ^^ - keyword.operator.macro.clojure
  ; blah
; ^^^^^^^ comment.line.clojure
  ##NaN
; ^^ keyword.operator.macro.clojure
;   ^^^ constant.other.symbolic.clojure

; ## Breaks

  #blah\newline
; ^^^^^ - keyword.operator.macro.clojure
;      ^^^^^^^^ constant.character.clojure

  #blah`blah
; ^^^^^ - keyword.operator.macro.clojure
;       ^^^^^- keyword.operator.macro.clojure

  #_0.000692025M
; ^^ punctuation.definition.comment.clojure
;   ^^^^^^^^^^^^ constant.numeric

  #_ 0.000692025M
; ^^ punctuation.definition.comment.clojure
;    ^^^^^^^^^^^^ constant.numeric

  #_blah
; ^^ punctuation.definition.comment.clojure
;   ^^^^- punctuation.definition.comment.clojure

; ## Unaffected

  '#'blah (#'blah blah)
; ^^ keyword.operator.macro.clojure
;    ^^^^^- keyword.operator.macro.clojure
;         ^ punctuation.section.parens.begin.clojure
;          ^^ keyword.operator.macro.clojure
;            ^^^^^^^^^- keyword.operator.macro.clojure
;                     ^ punctuation.section.parens.end.clojure
  '#inst"0000" (#inst"0000" blah)
;  ^^^^^ keyword.operator.macro.clojure
;       ^^^^^^ string.quoted.double.clojure
;              ^ punctuation.section.parens.begin.clojure
;               ^^^^^ keyword.operator.macro.clojure
;                    ^^^^^^ string.quoted.double.clojure

  # :blah{}
; ^ - keyword.operator.macro.clojure
;   ^^^^^ constant.other.keyword.unqualified.clojure

  # ' blah
; ^ - keyword.operator.macro.clojure
;   ^ keyword.operator.macro.clojure
;          ^ comment.line.clojure punctuation.definition.comment

; ## Invalid

  #111[]
; ^ - keyword.operator.macro.clojure
;  ^^^ - constant.numeric
  (blah #) )
;       ^ - keyword.operator.macro.clojure
;          ^ invalid.illegal.stray-bracket-end.clojure

  # #NaN
; ^ - keyword.operator.macro.clojure
;   ^^^^ keyword.operator.macro.clojure

; ## Ignore

  #{}
; ^^ punctuation.section.braces.begin.clojure



; # Quoting and unquoting

; ## Quote

  '100
; ^ keyword.operator.macro.clojure
;  ^^^ constant.numeric

  'true
; ^ keyword.operator.macro.clojure
;  ^^^^ constant.language.clojure

  ':blah
; ^ keyword.operator.macro.clojure
;  ^^^^^ constant.other.keyword.unqualified.clojure

  'blah
; ^ keyword.operator.macro.clojure
;  ^^^^^- keyword.operator.macro.clojure

  ' blah
; ^ keyword.operator.macro.clojure
;  ^^^^^^- keyword.operator.macro.clojure

  '
; ^ keyword.operator.macro.clojure
;  ^- keyword.operator.macro.clojure
    blah
;   ^^^^^- keyword.operator.macro.clojure

  'blah:blah
; ^ keyword.operator.macro.clojure
;  ^^^^^^^^^^- keyword.operator.macro.clojure

  'blah.blah/blah1000
; ^ keyword.operator.macro.clojure
;  ^^^^^^^^^^^^^^^^^^^- keyword.operator.macro.clojure

  '()
; ^ keyword.operator.macro.clojure
;  ^- keyword.operator.macro.clojure

  '(10 20 30)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.clojure
;   ^^ constant.numeric

  '(blah blah)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.clojure
;   ^^^^ meta.function-call.clojure variable.function.clojure

  '(quote blah)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.clojure
;   ^^^^^ keyword.other.clojure

; ## Backquote

  `blah
; ^ keyword.operator.macro.clojure
;  ^^^^^- keyword.operator.macro.clojure

; ## Unquote

  ~blah
; ^ keyword.operator.macro.clojure
;  ^^^^^- keyword.operator.macro.clojure

  ~100
; ^ keyword.operator.macro.clojure
;  ^^^ constant.numeric

  `(blah ~blah)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.clojure
;   ^^^^ meta.function-call.clojure variable.function.clojure
;        ^ keyword.operator.macro.clojure
;         ^^^^- keyword.operator.macro.clojure

  `(blah ~100)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.clojure
;   ^^^^ meta.function-call.clojure variable.function.clojure
;        ^ keyword.operator.macro.clojure
;         ^^^ constant.numeric

; ## Unquote-splicing

  ~@blah
; ^^ keyword.operator.macro.clojure
;   ^^^^^- keyword.operator.macro.clojure

  ~@[10 20 30]
; ^^ keyword.operator.macro.clojure
;   ^ punctuation.section.brackets.begin.clojure
;    ^^ constant.numeric

  `(blah ~@blah)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.clojure
;   ^^^^ meta.function-call.clojure variable.function.clojure
;        ^^ keyword.operator.macro.clojure
;          ^^^^- keyword.operator.macro.clojure

  `(blah ~@[10 20 30])
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.clojure
;   ^^^^ meta.function-call.clojure variable.function.clojure
;        ^^ keyword.operator.macro.clojure
;          ^ punctuation.section.brackets.begin.clojure
;           ^^ constant.numeric

; ## Invalid

  ( ') )
; ^ punctuation.section.parens.begin.clojure
;   ^ keyword.operator.macro.clojure
;      ^ invalid.illegal.stray-bracket-end.clojure
;    ^ punctuation.section.parens.end.clojure

  ( `) )
; ^ punctuation.section.parens.begin.clojure
;   ^ keyword.operator.macro.clojure
;      ^ invalid.illegal.stray-bracket-end.clojure
;    ^ punctuation.section.parens.end.clojure

  ( `) )
; ^ punctuation.section.parens.begin.clojure
;   ^ keyword.operator.macro.clojure
;      ^ invalid.illegal.stray-bracket-end.clojure
;    ^ punctuation.section.parens.end.clojure

  ( ~@) )
; ^ punctuation.section.parens.begin.clojure
;   ^^ keyword.operator.macro.clojure
;       ^ invalid.illegal.stray-bracket-end.clojure
;     ^ punctuation.section.parens.end.clojure



; # Deref

  @100
; ^ keyword.operator.macro.clojure
;  ^^^ constant.numeric

  @true
; ^ keyword.operator.macro.clojure
;  ^^^^ constant.language.clojure

  @blah
; ^ keyword.operator.macro.clojure
;  ^^^^^- keyword.operator.macro.clojure

  @:blah
; ^ keyword.operator.macro.clojure
;  ^^^^^ constant.other.keyword.unqualified.clojure

  @(atom blah)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.clojure
;   ^^^^ meta.function-call.clojure variable.function.clojure

  @@@blah
; ^^^ keyword.operator.macro.clojure
;    ^^^^^- keyword.operator.macro.clojure

  @'blah
; ^^ keyword.operator.macro.clojure
;  ^ keyword.operator.macro.clojure

  @~blah
; ^^ keyword.operator.macro.clojure
;  ^ keyword.operator.macro.clojure

  @#blah[]
; ^^^^^^ keyword.operator.macro.clojure

; ## Breaks

  blah@blah
;     ^ keyword.operator.macro.clojure
;      ^^^^^- keyword.operator.macro.clojure

  100@blah
; ^^^ - constant.numeric
;    ^ keyword.operator.macro.clojure
;     ^^^^^- keyword.operator.macro.clojure

; ## Invalid

  ( @) )
; ^ punctuation.section.parens.begin.clojure
;   ^ keyword.operator.macro.clojure
;      ^ invalid.illegal.stray-bracket-end.clojure
;    ^ punctuation.section.parens.end.clojure



; # Metadata

  ^File
; ^ keyword.operator.macro.clojure
;  ^^^^^- keyword.operator.macro.clojure

  ^File blah
; ^ keyword.operator.macro.clojure
;  ^^^^^^^^^^- keyword.operator.macro.clojure

  ^:private blah
; ^ keyword.operator.macro.clojure
;  ^^^^^^^^ constant.other.keyword.unqualified.clojure

  ^{:private true} blah
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.braces.begin.clojure
;   ^^^^^^^^ constant.other.keyword.unqualified.clojure
;            ^^^^ constant.language.clojure
;                ^ punctuation.section.braces.end.clojure

  ; Consequent metadata is merged
  ^:private ^:dynamic blah
; ^ keyword.operator.macro.clojure
;  ^^^^^^^^ constant.other.keyword.unqualified.clojure
;           ^ keyword.operator.macro.clojure
;            ^^^^^^^^ constant.other.keyword.unqualified.clojure

  ; Useless but accepted by Clojure reader
  ^^^{10 20}{30 40}{:tag File} blah
; ^^^ keyword.operator.macro.clojure
;    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^- keyword.operator.macro.clojure
;    ^ punctuation.section.braces.begin.clojure
;     ^^ constant.numeric
;        ^^ constant.numeric
;          ^ punctuation.section.braces.end.clojure
;           ^ punctuation.section.braces.begin.clojure
;            ^^ constant.numeric
;               ^^ constant.numeric
;                 ^ punctuation.section.braces.end.clojure
;                  ^ punctuation.section.braces.begin.clojure
;                   ^^^^ constant.other.keyword.unqualified.clojure

; ## Breaks

  blah^blah
;     ^ keyword.operator.macro.clojure
;      ^^^^^- keyword.operator.macro.clojure

  100^blah
; ^^^ - constant.numeric
;    ^ keyword.operator.macro.clojure
;     ^^^^^- keyword.operator.macro.clojure

; ## Invalid

  ( ^) )
; ^ punctuation.section.parens.begin.clojure
;   ^ keyword.operator.macro.clojure
;      ^ invalid.illegal.stray-bracket-end.clojure
;    ^ punctuation.section.parens.end.clojure



; # Brackets

  []
; ^ punctuation.section.brackets.begin.clojure
;  ^ punctuation.section.brackets.end.clojure

  [10, 20, 30]
; ^ punctuation.section.brackets.begin.clojure
;  ^^ constant.numeric
;    ^ comment.punctuation.comma.clojure
;      ^^ constant.numeric
;        ^ comment.punctuation.comma.clojure
;          ^^ constant.numeric
;            ^ punctuation.section.brackets.end.clojure

  [10
; ^ punctuation.section.brackets.begin.clojure
;  ^^ constant.numeric
   ; ---
;  ^ comment.line.clojure punctuation.definition.comment
   blah
   #inst"0000"
;  ^^^^^ keyword.operator.macro.clojure
;       ^ string.quoted.double.clojure punctuation.definition.string.begin.clojure
   [20]]
;  ^ punctuation.section.brackets.begin.clojure
;   ^^ constant.numeric
;     ^^ punctuation.section.brackets.end.clojure

; ## Invalid

  [ ] ]
; ^ punctuation.section.brackets.begin.clojure
;   ^ punctuation.section.brackets.end.clojure
;     ^ invalid.illegal.stray-bracket-end.clojure



; # Braces

  #{} }
; ^^ punctuation.section.braces.begin.clojure
;   ^ punctuation.section.braces.end.clojure
;     ^ invalid.illegal.stray-bracket-end.clojure

  #{10, 20, 30}
; ^^ punctuation.section.braces.begin.clojure
;   ^^ constant.numeric
;     ^ comment.punctuation.comma.clojure
;       ^^ constant.numeric
;         ^ comment.punctuation.comma.clojure
;           ^^ constant.numeric
;             ^ punctuation.section.braces.end.clojure

  #{10
; ^^ punctuation.section.braces.begin.clojure
;   ^^ constant.numeric
    ; ---
;   ^ comment.line.clojure punctuation.definition.comment
    blah
    #inst"0000"
;   ^^^^^ keyword.operator.macro.clojure
;        ^ string.quoted.double.clojure punctuation.definition.string.begin.clojure
    {20}}
;   ^ punctuation.section.braces.begin.clojure
;    ^^ constant.numeric
;      ^^ punctuation.section.braces.end.clojure

  {10 20, 30 40}
; ^ punctuation.section.braces.begin.clojure
;  ^^ constant.numeric
;     ^^ constant.numeric
;       ^ comment.punctuation.comma.clojure
;         ^^ constant.numeric
;            ^^ constant.numeric
;              ^ punctuation.section.braces.end.clojure

  {:blah [10 20 30]
; ^ punctuation.section.braces.begin.clojure
;  ^^^^^ constant.other.keyword.unqualified.clojure
;        ^ punctuation.section.brackets.begin.clojure
;         ^^ constant.numeric
;            ^^ constant.numeric
;               ^^ constant.numeric
;                 ^ punctuation.section.brackets.end.clojure
   ; ---
;  ^ comment.line.clojure punctuation.definition.comment
   :blahblah #{10 20 30}}
;  ^^^^^^^^^ constant.other.keyword.unqualified.clojure
;            ^^ punctuation.section.braces.begin.clojure
;              ^^ constant.numeric
;                 ^^ constant.numeric
;                    ^^ constant.numeric
;                      ^^ punctuation.section.braces.end.clojure

; ## Invalid

  #{ } }
; ^^ punctuation.section.braces.begin.clojure
;    ^ punctuation.section.braces.end.clojure
;      ^ invalid.illegal.stray-bracket-end.clojure

  { } }
; ^ punctuation.section.braces.begin.clojure
;   ^ punctuation.section.braces.end.clojure
;     ^ invalid.illegal.stray-bracket-end.clojure



; # Parens

  ()
; ^ punctuation.section.parens.begin.clojure
;  ^ punctuation.section.parens.end.clojure


; ## Highlight one symbol in operator position

  (blah blah true 10 "" [10 20])
; ^ punctuation.section.parens.begin.clojure
;  ^^^^ meta.function-call.clojure variable.function.clojure
;      ^^^^^^^^^^^^^^^^^^^^^^^^- variable.function.clojure
;            ^^^^ constant.language.clojure
;                 ^^ constant.numeric
;                    ^ string.quoted.double.clojure punctuation.definition.string.begin.clojure
;                     ^ string.quoted.double.clojure punctuation.definition.string.end.clojure
;                       ^ punctuation.section.brackets.begin.clojure
;                        ^^ constant.numeric
;                           ^^ constant.numeric
;                             ^ punctuation.section.brackets.end.clojure
;                              ^ punctuation.section.parens.end.clojure

  #(blah blah true 10 "" [10 20])
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.clojure
;   ^^^^ meta.function-call.clojure variable.function.clojure
;       ^^^^^^^^^^^^^^^^^^^^^^^^^- variable.function.clojure
;             ^^^^ constant.language.clojure
;                  ^^ constant.numeric
;                               ^ punctuation.section.parens.end.clojure

; ## Ignore operator

  (true blah :blah)
; ^ punctuation.section.parens.begin.clojure
;       ^^^^ - variable.function.clojure
;  ^^^^ constant.language.clojure

  (10 blah :blah)
; ^ punctuation.section.parens.begin.clojure
;     ^^^^ - variable.function.clojure
;  ^^ constant.numeric

  (:blah blah 10)
; ^ punctuation.section.parens.begin.clojure
;        ^^^^ - variable.function.clojure
;  ^^^^^ constant.other.keyword.unqualified.clojure

  (/ a b)
;  ^ meta.function-call.clojure variable.function.clojure
;    ^ - variable.function.clojure

  (+ a b)
;  ^ meta.function-call.clojure variable.function.clojure
;    ^ - variable.function.clojure

  (- a b)
;  ^ meta.function-call.clojure variable.function.clojure
;    ^ - variable.function.clojure

  (. a b)
;  ^ meta.function-call.clojure variable.function.clojure
;    ^ - variable.function.clojure

  #(true blah 10)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.clojure

; ## Whitespace

  (
; ^ punctuation.section.parens.begin.clojure
    blah
;   ^^^^ meta.function-call.clojure variable.function.clojure
    ; ---
;   ^ comment.line.clojure punctuation.definition.comment
    blah
    :blah
;   ^^^^^ constant.other.keyword.unqualified.clojure
   )
;  ^ punctuation.section.parens.end.clojure

; ## Invalid

  ( ) )
; ^ punctuation.section.parens.begin.clojure
;   ^ punctuation.section.parens.end.clojure
;     ^ invalid.illegal.stray-bracket-end.clojure



; # fn

  (fn [])
;  ^^ keyword.declaration.function.inline.clojure
;     ^ punctuation.section.brackets.begin.clojure
;      ^ punctuation.section.brackets.end.clojure
;       ^ punctuation.section.parens.end.clojure

  (fn declare-noindex [] blah)
;  ^^ keyword.declaration.function.inline.clojure
;     ^^^^^^^^^^^^^^^ entity.name.function.clojure
;                       ^^^^^^^- storage
;                       ^^^^^^^- entity

  (fn declare-noindex
;  ^^ keyword.declaration.function.inline.clojure
;     ^^^^^^^^^^^^^^^ entity.name.function.clojure
;                    ^- entity
    ([] blah)
;    ^^ meta.function.parameters.clojure
    ([_] blah))
;    ^^^ meta.function.parameters.clojure
;             ^ - invalid.illegal.stray-bracket-end.clojure

  ; Invalid but take care anyway
  (fn declare-noindex dont-declare [])
;  ^^ keyword.declaration.function.inline.clojure
;     ^^^^^^^^^^^^^^^ entity.name.function.clojure
;                    ^^^^- storage
;                    ^^^^- entity

(defmacro bound-fn
  [& fntail]
  `(bound-fn* (fn ~@fntail)))
;                 ^^ keyword.operator.macro.clojure
;                   ^^^^^^ meta.reader-form.clojure meta.symbol.clojure
;                         ^^^ meta.sexp.end.clojure punctuation.section.parens.end.clojure

; # defs

; ## Normal def

  (def declare-def)
;  ^^^ keyword.declaration.variable.clojure
;      ^^^^^^^^^^^ entity.name.constant.clojure

  (def declare-def dont-declare)
; ^ punctuation.section.parens.begin.clojure
;  ^^^ keyword.declaration.variable.clojure
;      ^^^^^^^^^^^ entity.name.constant.clojure
;                 ^^^^^^^^^^^^- storage
;                 ^^^^^^^^^^^^- entity

  (def λ nil)
;  ^^^ keyword.declaration.variable.clojure
;      ^ entity.name.constant.clojure
;        ^^^ constant.language.clojure

  (def 👽 nil)
;  ^^^ keyword.declaration.variable.clojure
;      ^ entity.name.constant.clojure
;        ^^^ constant.language.clojure

  (def def nil)
;  ^^^ keyword.declaration.variable.clojure
;      ^^^ entity.name.constant.clojure
;          ^^^ constant.language.clojure

  (
   ; ---
;  ^ comment.line.clojure punctuation.definition.comment
   def
;  ^^^ keyword.declaration.variable.clojure
   ; ---
;  ^ comment.line.clojure punctuation.definition.comment
   declare-def
;  ^^^^^^^^^^^ entity.name.constant.clojure
   dont-declare
;  ^^^^^^^^^^^^^- storage
;  ^^^^^^^^^^^^^- entity
   )

  (defonce declare-defonce)
;  ^^^^^^^ keyword.declaration.variable.clojure
;          ^^^^^^^^^^^^^^^ entity.name.constant.clojure

; ## Declare with metadata

  (def ^:private declare-def nil)
;  ^^^ keyword.declaration.variable.clojure
;      ^ keyword.operator.macro.clojure
;       ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                ^^^^^^^^^^^ entity.name.constant.clojure
;                            ^^^ constant.language.clojure

  (def ^:private declare-def dont-declare)
;  ^^^ keyword.declaration.variable.clojure
;      ^ keyword.operator.macro.clojure
;       ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                ^^^^^^^^^^^ entity.name.constant.clojure
;                           ^^^^^^^^^^^^^- storage
;                           ^^^^^^^^^^^^^- entity

  ; Consequent metadata is merged

  (def ^:private ^:dynamic declare-def nil)
;  ^^^ keyword.declaration.variable.clojure
;      ^ keyword.operator.macro.clojure
;       ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                ^ keyword.operator.macro.clojure
;                 ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                          ^^^^^^^^^^^ entity.name.constant.clojure
;                                      ^^^ constant.language.clojure

  (def ^:private ^:dynamic declare-def dont-declare)
;  ^^^ keyword.declaration.variable.clojure
;      ^ keyword.operator.macro.clojure
;       ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                ^ keyword.operator.macro.clojure
;                 ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                          ^^^^^^^^^^^ entity.name.constant.clojure
;                                     ^^^^^^^^^^^^^- storage
;                                     ^^^^^^^^^^^^^- entity

  (
   def
;  ^^^ keyword.declaration.variable.clojure
   ; ---
   ^
;  ^ keyword.operator.macro.clojure
   ; ---
   {:private
;  ^ punctuation.section.braces.begin.clojure
;   ^^^^^^^^ constant.other.keyword.unqualified.clojure
   ; ---
    true}
;   ^^^^ constant.language.clojure
;       ^ punctuation.section.braces.end.clojure
   ; ---
   declare-def
;  ^^^^^^^^^^^ entity.name.constant.clojure
   ; ---
   dont-declare
;  ^^^^^^^^^^^^^- storage
;  ^^^^^^^^^^^^^- entity
   )

  (defonce ^:private declare-defonce nil)
; ^ punctuation.section.parens.begin.clojure
;  ^^^^^^^ keyword.declaration.variable.clojure
;          ^ keyword.operator.macro.clojure
;           ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                    ^^^^^^^^^^^^^^^ entity.name.constant.clojure
;                                    ^^^ constant.language.clojure

  ; Useless but accepted by Clojure reader
  (^{10 20} def ^:private declare-def dont-declare)
;  ^ keyword.operator.macro.clojure
;   ^ punctuation.section.braces.begin.clojure
;    ^^ constant.numeric
;       ^^ constant.numeric
;         ^ punctuation.section.braces.end.clojure
;           ^^^ keyword.declaration.variable.clojure
;               ^ keyword.operator.macro.clojure
;                ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                         ^^^^^^^^^^^ entity.name.constant.clojure
;                                    ^^^^^^^^^^^^^- storage
;                                    ^^^^^^^^^^^^^- entity

  ; Useless but accepted by Clojure reader
  (def ^^^{10 20}{30 40}{:private true} declare-def dont-declare)
;  ^^^ keyword.declaration.variable.clojure
;      ^^^ keyword.operator.macro.clojure
;         ^ punctuation.section.braces.begin.clojure
;          ^^ constant.numeric
;             ^^ constant.numeric
;               ^ punctuation.section.braces.end.clojure
;                ^ punctuation.section.braces.begin.clojure
;                 ^^ constant.numeric
;                    ^^ constant.numeric
;                      ^ punctuation.section.braces.end.clojure
;                       ^ punctuation.section.braces.begin.clojure
;                        ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                                 ^^^^ constant.language.clojure
;                                     ^ punctuation.section.braces.end.clojure
;                                       ^^^^^^^^^^^ entity.name.constant.clojure
;                                                  ^^^^^^^^^^^^^- storage
;                                                  ^^^^^^^^^^^^^- entity



; ## declare

  (declare declare-noindex)
;  ^^^^^^^ keyword.declaration.variable.clojure
;          ^^^^^^^^^^^^^^^ entity.name.variable.forward-decl.clojure
;         ^^^^^^^^^^^^^^^^^- storage



; ## Don't declare

  (def nil dont-declare)
;  ^^^ keyword.declaration.variable.clojure
;      ^^^ constant.language.clojure
;         ^^^^^^^^^^^^^- storage
;         ^^^^^^^^^^^^^- entity

  (-def dont-declare)
;  ^^^^ meta.function-call.clojure variable.function.clojure
;      ^^^^^^^^^^^^^- storage
;      ^^^^^^^^^^^^^- entity

  (-def def dont-declare)
;  ^^^^ meta.function-call.clojure variable.function.clojure
;      ^^^^^^^^^^^^^^^^^- storage
;      ^^^^^^^^^^^^^^^^^- entity

; ## Invalid

  (def ^ ) )
;  ^^^ keyword.declaration.variable.clojure
;      ^ keyword.operator.macro.clojure
;          ^ invalid.illegal.stray-bracket-end.clojure
;        ^ punctuation.section.parens.end.clojure



; # Function defs

  (defn declare-defn [] dont-declare)
;  ^^^^ keyword.declaration.function.clojure
;       ^^^^^^^^^^^^ entity.name.function.clojure
;                    ^^^^^^^^^^^^^^^- storage
;                    ^^^^^^^^^^^^^^^- entity

  (defn declare-defn [arg & args] dont-declare)
;  ^^^^ keyword.declaration.function.clojure
;       ^^^^^^^^^^^^ entity.name.function.clojure
;                    ^^^^^^^^^^^^ meta.function.parameters.clojure
;                    ^^^^^^^^^^^^^^^^^^^^^^^^^- storage
;                    ^^^^^^^^^^^^^^^^^^^^^^^^^- entity

  (defn ^:private declare-defn [arg & args] dont-declare)
;  ^^^^ keyword.declaration.function.clojure
;       ^ keyword.operator.macro.clojure
;        ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                 ^^^^^^^^^^^^ entity.name.function.clojure
;                              ^^^^^^^^^^^^^^^^^^^^^^^^^- storage
;                              ^^^^^^^^^^^^^^^^^^^^^^^^^- entity

  (defn declare-defn
;  ^^^^ keyword.declaration.function.clojure
;       ^^^^^^^^^^^^ entity.name.function.clojure
    "docstring"
;   ^^^^^^^^^^^ string.quoted.double.clojure
    [arg & args]
;   ^^^^^^^^^^^^- storage
;   ^^^^^^^^^^^^- entity
    dont-declare)
;   ^^^^^^^^^^^^- storage
;   ^^^^^^^^^^^^- entity

  (defn
;  ^^^^ keyword.declaration.function.clojure
    ^:private
;   ^ keyword.operator.macro.clojure
;    ^^^^^^^^ constant.other.keyword.unqualified.clojure
    declare-defn
;   ^^^^^^^^^^^^ entity.name.function.clojure
    "docstring"
;   ^^^^^^^^^^^ string.quoted.double.clojure
    ([] dont-declare)
;    ^^ meta.function.parameters.clojure
;   ^^^^^^^^^^^^^^^^^- storage
;   ^^^^^^^^^^^^^^^^^- entity
    ([_] dont-declare))
;    ^^^ meta.function.parameters.clojure
;   ^^^^^^^^^^^^^^^^^^^- storage
;   ^^^^^^^^^^^^^^^^^^^- entity

  (
   defn
;  ^^^^ keyword.declaration.function.clojure
   declare-defn
;  ^^^^^^^^^^^^ entity.name.function.clojure
   "docstring"
;  ^^^^^^^^^^^ string.quoted.double.clojure
   {:private true}
;   ^^^^^^^^ constant.other.keyword.unqualified.clojure
;            ^^^^ constant.language.clojure
   ([] dont-declare)
;   ^^ meta.function.parameters.clojure
;  ^^^^^^^^^^^^^^^^^- storage
;  ^^^^^^^^^^^^^^^^^- entity
   ([_] dont-declare))
;   ^^ meta.function.parameters.clojure
;  ^^^^^^^^^^^^^^^^^^^- storage
;  ^^^^^^^^^^^^^^^^^^^- entity

  (defn declare-defn [value] {:pre [(int? value)]}
;  ^^^^ keyword.declaration.function.clojure
;       ^^^^^^^^^^^^ entity.name.function.clojure
;                     ^^^^^- storage
;                     ^^^^^- entity
;                             ^^^^ constant.other.keyword.unqualified.clojure
;                                    ^^^^ meta.function-call.clojure variable.function.clojure
    value)
;   ^^^^^- storage
;   ^^^^^- entity

  (defn -main [& args] ,,,)
;       ^^^^^ entity.name.function.clojure

  (defn start [& [port]] ,,,)

  (defn foo [&bar])
;            ^ - keyword

  (defn foo [bar] [baz])
;           ^^^^^ meta.function.parameters.clojure
;                 ^^^^^ - meta.function.parameters.clojure

  (defn foo)
;          ^ meta.sexp.end.clojure punctuation.section.parens.end.clojure

  (def !bang (atom 1))
;      ^^^^^ entity.name.constant.clojure

  (def *db* ,,,)
;      ^^^^ entity.name.constant.clojure

  ; Invalid but take care anyway
  (defn declare-defn dont-declare [] dont-declare)
;  ^^^^ keyword.declaration.function.clojure
;       ^^^^^^^^^^^^ entity.name.function.clojure
;                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^- storage
;                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^- entity

  (defmacro declare-defmacro [])
;  ^^^^^^^^ keyword.declaration.macro.clojure
;           ^^^^^^^^^^^^^^^^ entity.name.function.clojure



; # defmulti / defmethod

  (defmulti declare-multi-fn)
;  ^^^^^^^^ keyword.declaration.function.clojure
;           ^^^^^^^^^^^^^^^^ entity.name.function.clojure

  (defmulti ^:private declare-multi-fn dont-declare-dispatch-fn)
;  ^^^^^^^^ keyword.declaration.function.clojure
;           ^ keyword.operator.macro.clojure
;            ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                     ^^^^^^^^^^^^^^^^ entity.name.function.clojure
;                                     ^^^^^^^^^^^^^^^^^^^^^^^^^- storage
;                                     ^^^^^^^^^^^^^^^^^^^^^^^^^- entity

  (
   defmulti
;  ^^^^^^^^ keyword.declaration.function.clojure
   ^:private
;  ^ keyword.operator.macro.clojure
   declare-multi-fn
;  ^^^^^^^^^^^^^^^^ entity.name.function.clojure
   dont-declare-dispatch-fn
;  ^^^^^^^^^^^^^^^^^^^^^^^^^- storage
;  ^^^^^^^^^^^^^^^^^^^^^^^^^- entity
  )

  ; Invalid but take care anyway
  (defmulti declare-multi-fn nil)
;  ^^^^^^^^ keyword.declaration.function.clojure
;           ^^^^^^^^^^^^^^^^ entity.name.function.clojure
;                            ^^^ constant.language.clojure

  (defmethod dont-declare-multi-fn :dispatch-value [arg & args] [arg] ...)
;                                  ^^^^^^^^^^^^^^^ constant.other.keyword.unqualified.clojure
;                                                  ^^^^^^^^^^^^ meta.function.parameters.clojure
;                                                               ^^^^^ - meta.function.parameters.clojure

  (defmethod dont-declare-multi-fn DispatchType [arg] ...)
;                                  ^^^^^^^^^^^^^- storage
;                                  ^^^^^^^^^^^^^- entity

  (defmethod bat [String String] [x y & xs]
;                ^^^^^^^^^^^^^^^ - meta.function.parameters.clojure
;                                ^^^^^^^^^^ meta.function.parameters.clojure
    ,,,)

  (
   defmethod
;  ^^^^^^^^^ keyword.declaration.function.clojure
   dont-declare-multi-fn
;  ^^^^^^^^^^^^^^^^^^^^^ entity.name.function.clojure
  [])

  (do
    (defmethod ^:foo print-method Foo
      [bar out]
      (print-method (.toString bar) out)))
;                                       ^^ meta.sexp.end - invalid



; # defprotocol

  (defprotocol DeclareProtocol)
;  ^^^^^^^^^^^ storage.type.interface.clojure
;              ^^^^^^^^^^^^^^^ entity.name.type.clojure

  (defprotocol ^:private DeclareProtocol)
;  ^^^^^^^^^^^ storage.type.interface.clojure
;              ^ keyword.operator.macro.clojure
;               ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                        ^^^^^^^^^^^^^^^ entity.name.type.clojure

  (defprotocol ^:private ^:blah DeclareProtocol)
;  ^^^^^^^^^^^ storage.type.interface.clojure
;              ^ keyword.operator.macro.clojure
;               ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                        ^ keyword.operator.macro.clojure
;                         ^^^^^ constant.other.keyword.unqualified.clojure
;                               ^^^^^^^^^^^^^^^ entity.name.type.clojure

  (
   ; ---
;  ^ comment.line.clojure punctuation.definition.comment
   defprotocol
;  ^^^^^^^^^^^ storage.type.interface.clojure
   ; ---
;  ^ comment.line.clojure punctuation.definition.comment
   ^:private
;  ^ keyword.operator.macro.clojure
;   ^^^^^^^^ constant.other.keyword.unqualified.clojure
   ; ---
;  ^ comment.line.clojure punctuation.definition.comment
   DeclareProtocol
;  ^^^^^^^^^^^^^^^ entity.name.type.clojure
   ; ---
;  ^ comment.line.clojure punctuation.definition.comment
   "docstring"
;  ^ string.quoted.double.clojure punctuation.definition.string.begin.clojure
  )

  ; Invalid but take care anyway
  (defprotocol DeclareProtocol dont-declare)
; ^ punctuation.section.parens.begin.clojure
;  ^^^^^^^^^^^ storage.type.interface.clojure
;              ^^^^^^^^^^^^^^^ entity.name.type.clojure
;                             ^^^^^^^^^^^^^- storage
;                             ^^^^^^^^^^^^^- entity

  ; Protocol methods are added to the namespace as functions
  (defprotocol ^:private DeclareProtocol
    ; ---
    (declare-protocol-method [_] [sadas] dont-declare)
;    ^^^^^^^^^^^^^^^^^^^^^^^ entity.name.function.clojure
;                               ^^^^^^^^^^^^^- storage
;                               ^^^^^^^^^^^^^- entity
    ; ---
    (^File declare-protocol-method [_] dont-declare))
;    ^ keyword.operator.macro.clojure
;     ^^^^^- storage
;     ^^^^^- entity
;     ^^^^^- variable.function
;          ^^^^^^^^^^^^^^^^^^^^^^^ entity.name.function.clojure
;                                     ^^^^^^^^^^^^^- storage
;                                     ^^^^^^^^^^^^^- entity

  ; Invalid but take care anyway
  (defprotocol DeclareProtocol
    (declare-protocol-method dont-declare [_]))
;    ^^^^^^^^^^^^^^^^^^^^^^^ entity.name.function.clojure
;                           ^^^^^^^^^^^^^^- storage
;                           ^^^^^^^^^^^^^^- entity


; # definterface

  (definterface DeclareInterface)
;  ^^^^^^^^^^^^ storage.type.interface.clojure
;               ^^^^^^^^^^^^^^^^ entity.name.type.clojure

  (definterface ^:private DeclareInterface)
;  ^^^^^^^^^^^^ storage.type.interface.clojure
;               ^ keyword.operator.macro.clojure
;                ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                         ^^^^^^^^^^^^^^^^ entity.name.type.clojure

  (
   definterface
;  ^^^^^^^^^^^^ storage.type.interface.clojure
   ^:private
;  ^ keyword.operator.macro.clojure
   DeclareInterface
;  ^^^^^^^^^^^^^^^^ entity.name.type.clojure
   "docstring"
;  ^^^^^^^^^^^ string.quoted.double.clojure
  )

  ; Interface methods should have the same visual style as other function
  ; and method declarations, but shouldn't be added to the symbol index,
  ; since they're not added to the namespace as functions
  (definterface DeclareInterface
    (declare-noindex [_])
;    ^^^^^^^^^^^^^^^ entity.name.function.clojure
    (declare-noindex [_]))
;    ^^^^^^^^^^^^^^^ entity.name.function.clojure

  ; Invalid but take care anyway
  (definterface DeclareInterface dont-declare)
; ^ punctuation.section.parens.begin.clojure
;  ^^^^^^^^^^^^ storage.type.interface.clojure
;               ^^^^^^^^^^^^^^^^ entity.name.type.clojure
;                               ^^^^^^^^^^^^^- storage
;                               ^^^^^^^^^^^^^- entity

; # deftype

  (deftype DeclareType [])
;  ^^^^^^^ storage.type.class.clojure
;          ^^^^^^^^^^^ entity.name.type.clojure

  (deftype-custom DeclareWithCustomDeftype)
;  ^^^^^^^^^^^^^^ - storage.type.class.clojure
;                 ^^^^^^^^^^^^^^^^^^^^^^^^ - entity.name.type.clojure

  (deftype ^:private DeclareType [])
;  ^^^^^^^ storage.type.class.clojure
;          ^ keyword.operator.macro.clojure
;           ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                    ^^^^^^^^^^^ entity.name.type.clojure
;                                ^^ meta.function.parameters.clojure

  (
   ; ---
   deftype
;  ^^^^^^^ storage.type.class.clojure
   ; ---
   ^:private
;  ^ keyword.operator.macro.clojure
   ; ---
   ^:blah
;  ^ keyword.operator.macro.clojure
;   ^^^^^ constant.other.keyword.unqualified.clojure
   ; ---
   DeclareType
;  ^^^^^^^^^^^ entity.name.type.clojure
   ; ---
   [])

  ; Similarly to definterface, type methods should have the standard visual
  ; style of function declarations, but not added to the symbol index,
  ; since they're not added to the namespace.
  (deftype DeclareType [foo]
    Foo
    (bar ^:quux [_])
  ;  ^^^ entity.name.function.clojure
  ;      ^ keyword.operator.macro.clojure
  ;       ^^^^^ constant.other.keyword.unqualified.clojure
    Bar
    (baz [_]))
;    ^^^ entity.name.function.clojure

  ; Scope the implemented protocols/interfaces
  (deftype DeclareType [fields]
;  ^^^^^^^ storage.type.class.clojure
;          ^^^^^^^^^^^ entity.name.type.clojure
    package.ImplementedInterface
;   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
    (declare-noindex [_])
;    ^^^^^^^^^^^^^^^ entity.name.function.clojure
    namespace/ImplementedProtocol
;   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
    (declare-noindex [_]))
;    ^^^^^^^^^^^^^^^ entity.name.function.clojure


(deftype GrowingMap [^IFn make ^:unsynchronized-mutable inner]
;^^^^^^^ storage.type.class.clojure
;        ^^^^^^^^^^ entity.name.type.clojure
;                   ^ punctuation.section.brackets.begin.clojure
;                    ^ keyword.operator.macro.clojure
;                               ^^^^^^^^^^^^^^^^^^^^^^^ constant.other.keyword.unqualified.clojure
  ILookup
  (valAt [this key]
;  ^^^^^ entity.name.function.clojure
;        ^^^^^^^^^^ meta.function.parameters.clojure
;       ^^^^^^^^^^^- storage
;       ^^^^^^^^^^^- entity
    (let [dict @this]
;    ^^^ keyword.declaration.variable.clojure
      (if (contains? dict key)
        (get dict key)
        (locking this
          (if (contains? inner key)
            (get inner key)
            (get (set! inner (assoc inner key (make inner key))) key))))))
  (valAt [this key fallback] (get @this key fallback))
;  ^^^^^ entity.name.function.clojure
;                             ^^^ meta.function-call.clojure variable.function.clojure

  Seqable
  (seq [this] (seq @this))

  IFn
  (invoke [this a] (.valAt this a))
  (invoke [this a b] (.valAt this a b))
  (applyTo [this args]
    (case (count args)
      1 (.invoke this (first args))
      2 (.invoke this (first args) (second args))
      (throw (new ArityException (count args) (.getName ^Class (type this))))))

  IDeref
  (deref [this]
    (or inner
        (locking this
          (or inner
              (let [dict (make)]
                (when-not (map? dict)
                  (throw (new Exception "GrowingMap initer failed to produce a map")))
                (set! inner dict)))))))

(defn new-growing-map
  ([make] (new-growing-map make nil))
  ([make init] {:pre [(ifn? make) (or (nil? init) (map? init))]}
   (new GrowingMap make init)))



; # defrecord

  (defrecord DeclareRecord)
;  ^^^^^^^^^ storage.type.class.clojure
;            ^^^^^^^^^^^^^ entity.name.type.clojure

  (defrecord-custom DeclareWithCustomDefrecord)
;  ^^^^^^^^^^^^^^^^ - storage.type.class.clojure
;                   ^^^^^^^^^^^^^^^^^^^^^^^^^^ - entity.name.type.clojure

  (defrecord ^:private DeclareRecord [])
;  ^^^^^^^^^ storage.type.class.clojure
;            ^ keyword.operator.macro.clojure
;             ^^^^^^^^ constant.other.keyword.unqualified.clojure
;                      ^^^^^^^^^^^^^ entity.name.type.clojure

  (
   ; ---
   defrecord
;  ^^^^^^^^^ storage.type.class.clojure
   ; ---
   ^:private
;  ^ keyword.operator.macro.clojure
   ; ---
   ^:blah
;  ^ keyword.operator.macro.clojure
   ; ---
   DeclareRecord
;  ^^^^^^^^^^^^^ entity.name.type.clojure
   ; ---
   [])

  ; Same reasoning as for definterface and deftype
  (defrecord DeclareRecord [fields]
;                          ^^^^^^^^ meta.function.parameters.clojure
    Foo
    (bar ^:baz [_])
;    ^^^ entity.name.function.clojure
;        ^ keyword.operator.macro.clojure
;         ^^^^ constant.other.keyword.unqualified.clojure
    Quux
    (zot [_]))
;    ^^^ entity.name.function.clojure

  ; Scope the implemented protocols/interfaces
  (defrecord DeclareRecord [fields]
;  ^^^^^^^^^ storage.type.class.clojure
;            ^^^^^^^^^^^^^ entity.name.type.clojure
    package.ImplementedInterface
;   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
    (declare-noindex [_])
;    ^^^^^^^^^^^^^^^ entity.name.function.clojure
    namespace/ImplementedProtocol
;   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
    (declare-noindex [_]))
;    ^^^^^^^^^^^^^^^ entity.name.function.clojure



(defrecord Srv [^Server jetty session-store state-store]
  component/Lifecycle

  (start [this]
;  ^^^^^ entity.name.function.clojure
;       ^^^^^^^^^^^- storage
;       ^^^^^^^^^^^- entity
    (let [port    (Long/parseLong (getenv "LOCAL_PORT"))
;    ^^^ keyword.declaration.variable.clojure
          this    (component/stop this)
          handler (new-handler this)
          options {:port port
                   :join? false
                   :send-server-version? false}
          jetty   (run-jetty handler options)]
      (assoc this :jetty jetty)))

  (stop [this]
    (when jetty (.stop jetty))
    (assoc this :jetty nil)))

(defn new-srv [prev-sys]
  (when-let [^Server jetty (-> prev-sys :srv :jetty)] (.stop jetty))
  (new Srv
       nil
       (or (-> prev-sys :srv :session-store)
           (util/expiring-session-store 72 {:time-unit :hours
                                            :expiration-policy :access}))
       (or (-> prev-sys :srv :state-store)
           (em/expiring-map 1 {:time-unit :hours :expiration-policy :access}))))



; # reify

  (reify
;  ^^^^^ meta.function-call.clojure variable.function.clojure
    clojure.lang.IDeref
;   ^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
    (deref [_] nil)
;    ^^^^^ entity.name.function.clojure
;              ^^^ constant.language.clojure
    clojure.lang.Seqable
;   ^^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
    (seq [_] nil))
;    ^^^ entity.name.function.clojure
;            ^^^ constant.language.clojure



; # proxy

  (proxy [clojure.lang.IDeref clojure.lang.Seqable] []
;  ^^^^^ meta.function-call.clojure variable.function.clojure
;         ^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
;                             ^^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
;         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^- storage
;         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^- variable
    (deref [] nil)
;    ^^^^^ entity.name.function.clojure
;             ^^^ constant.language.clojure
    (seq [] nil))
;    ^^^ entity.name.function.clojure
;           ^^^ constant.language.clojure



; # extend-protocol

  (extend-protocol clojure.lang.IDeref
;                  ^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
;  ^^^^^^^^^^^^^^^ meta.function-call.clojure variable.function.clojure
    String
;   ^^^^^^ entity.other.inherited-class.clojure
    (deref [this] this)
;    ^^^^^ entity.name.function.clojure
    Srv
    (deref [_] nil))
;    ^^^^^ entity.name.function.clojure
;              ^^^ constant.language.clojure



; # extend-type

  (extend-type String
;              ^^^^^^ entity.other.inherited-class.clojure
;  ^^^^^^^^^^^ meta.function-call.clojure variable.function.clojure
    clojure.lang.IDeref
;   ^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
    (deref [this] this)
;    ^^^^^ entity.name.function.clojure
    clojure.lang.IFn
    (invoke [this] nil))
;    ^^^^^^ entity.name.function.clojure
;                  ^^^ constant.language.clojure



; # ns

  (ns foo.bar)
;  ^^ keyword.declaration.namespace.clojure
;     ^^^^^^^ entity.name.namespace.clojure

  (ns ^:baz foo.bar)
;     ^^^^^ - entity.name.namespace.clojure
;     ^ keyword.operator.macro.clojure
;      ^^^^ constant.other.keyword.unqualified.clojure
;           ^^^^^^^ entity.name.namespace.clojure

  (ns ^{:baz true} foo.bar)
;     ^ keyword.operator.macro.clojure
;       ^^^^ constant.other.keyword.unqualified.clojure
;            ^^^^ constant.language.clojure
;                  ^^^^^^^ entity.name.namespace.clojure

  (ns ^{:config '{:some-keyword some-symbol}} foo.bar)
;     ^ keyword.operator.macro.clojure
;       ^^^^^^^ constant.other.keyword.unqualified.clojure
;               ^ keyword.operator.macro.clojure
;                               ^^^^^^^^^^^ meta.symbol.clojure
;                                             ^^^^^^^ entity.name.namespace.clojure

  (ns foo.bar "baz")
;             ^^^^^ string.quoted.double.clojure

  (ns foo.bar
    (:require
;    ^^^^^^^^ meta.statement.require.clojure
     [baz.quux]
     qux.zot
;    ^^^^^^^ - variable.function.clojure
     ))

  (ns foo.bar
    (:import
;    ^^^^^^^ meta.statement.import.clojure
     (java.time LocalDate)))
;    ^ meta.sexp.begin.clojure punctuation.section.parens.begin.clojure
;     ^^^^^^^^^ - meta.function-call.clojure
;     ^^^^^^^^^ - variable.function.clojure
;                        ^ meta.sexp.end.clojure punctuation.section.parens.end.clojure
  (ns foo.bar
    (:require
;    ^^^^^^^ meta.statement.require.clojure
     (foo.bar :as [foo])))
;    ^ meta.sexp.begin.clojure punctuation.section.parens.begin.clojure
;     ^^^^^^^ - meta.function-call.clojure
;     ^^^^^^^ - variable.function.clojure
;             ^^^ constant.other.keyword.unqualified.clojure
;                      ^ meta.sexp.end.clojure punctuation.section.parens.end.clojure

  (ns foo.bar (:import :require))
;              ^^^^^^^ meta.statement.import.clojure
;                      ^^^^^^^^ - meta.statement.require.clojure

  (ns foo.bar (:requires [baz.quux]))
;              ^^^^^^^^^ - meta.statement.require.clojure


; # deftest

  (deftest foo (is (= 3 (+ 1 2))))
;  ^^^^^^^ keyword.declaration.function.clojure
;          ^^^ meta.test-var.clojure

  (test/deftest ^:slow foo)
;  ^^^^^^^^^^^^ keyword.declaration.function.clojure
;                      ^^^ meta.test-var.clojure



; # Qualified symbols

  foo.bar/
; ^^^^^^^ meta.namespace.clojure
;        ^ punctuation.accessor.clojure

  foo.bar/baz
; ^^^^^^^ meta.namespace.clojure
;        ^ punctuation.accessor.clojure
;        ^^^^ - meta.namespace.clojure



; # Map namespace syntax

  #:blah/blah{}
; ^ keyword.operator.macro.clojure
;  ^ punctuation.definition.keyword.clojure
;   ^^^^ meta.namespace
;       ^ punctuation.definition.constant.namespace
;  ^^^^^^^^^^ constant.other.keyword.qualified.clojure

  #::blah{}
; ^ keyword.operator.macro.clojure
;  ^^ punctuation.definition.keyword.clojure
;  ^^^^^^ constant.other.keyword.auto-qualified.clojure

  #::blah/blah{}
; ^ keyword.operator.macro.clojure
;  ^^ punctuation.definition.keyword.clojure
;        ^ punctuation.definition.constant.namespace
;  ^^^^^^ constant.other.keyword.auto-qualified.clojure



; # Tagged literals

 (foo #bar/baz [1 2 3] [4 5 6])
;     ^^^^^^^^ keyword.operator.macro.clojure
;         ^ punctuation.definition.symbol.namespace.clojure
;     ^^^^^^^^^^^^^^^^ meta.reader-form.clojure
;                     ^ - meta.reader-form.clojure



; # Quoted

  '100
; ^ keyword.operator.macro.clojure

  ' foo
; ^ keyword.operator.macro.clojure

  '(1 2 3)
; ^ keyword.operator.macro.clojure

  `foo
; ^ keyword.operator.macro.clojure
;  ^^^ meta.symbol.clojure - keyword

  ~foo
; ^ keyword.operator.macro.clojure
;  ^^^ meta.symbol.clojure - keyword

  `(foo ~bar)
; ^ keyword.operator.macro.clojure
;   ^^^ meta.function-call.clojure variable.function.clojure
;       ^ keyword.operator.macro.clojure
;        ^^^ meta.symbol.clojure - keyword

  ~@foo ~[1 2 3]
; ^^ keyword.operator.macro.clojure
;   ^^^ meta.symbol.clojure - keyword
;       ^ keyword.operator.macro.clojure
;        ^ meta.sexp.begin.clojure
;              ^ meta.sexp.end.clojure

  #'foo.bar/baz
; ^^ keyword.operator.macro.clojure
;          ^ punctuation.accessor.clojure


; # Reader conditionals

  #?(:clj (def x 1))
; ^^ keyword.operator.macro
;   ^ punctuation.section.parens.begin.clojure
;    ^^^^ constant.other.keyword.unqualified.clojure



; # S-expression prefixes

  #(inc 1)
; ^ keyword.operator.macro

  @(atom foo)
; ^ keyword.operator.macro

  #{1 2 3}
; ^ keyword.operator.macro

  #_(1 2 3)
; ^^ keyword.operator.macro

  #?@(:default (+ 1 2 3))
; ^^^ keyword.operator.macro


; # Reader forms

; ## Symbols

  a b
; ^ meta.reader-form.clojure
;  ^ - meta
;   ^ meta.reader-form.clojure

; ## Strings

  "a" "b"
; ^^^ meta.reader-form.clojure
;    ^ - meta
;     ^^^ meta.reader-form.clojure

; ## Numbers

  123 123N 1/2 1.2 1.2M +0x1234af -2r1010 +1234.1234E10M ##-Inf
; ^^^ meta.reader-form.clojure
;    ^ - meta
;     ^^^^ meta.reader-form.clojure
;         ^ - meta
;          ^^^ meta.reader-form.clojure
;                 ^ - meta
;                  ^^^^ meta.reader-form.clojure
;                      ^ - meta
;                       ^^^^^^^^^ meta.reader-form.clojure
;                                ^ - meta
;                                 ^^^^^^^ meta.reader-form.clojure
;                                        ^ - meta
;                                         ^^^^^^^^^^^^^^ meta.reader-form.clojure
;                                                       ^ - meta
;                                                        ^^^^^^ meta.reader-form.clojure

; ## Keywords

  :foo :foo/bar ::foo ::foo/bar
; ^^^^ meta.reader-form.clojure
;     ^ - meta
;      ^^^^^^^^ meta.reader-form.clojure
;              ^ - meta
;               ^^^^^ meta.reader-form.clojure
;                    ^ - meta
;                     ^^^^^^^^^ meta.reader-form.clojure

; ## Macro characters

  'foo 'bar
; ^ keyword.operator.macro.clojure
;     ^ - meta
;      ^ keyword.operator.macro.clojure

  \newline \space
; ^^^^^^^^ meta.reader-form.clojure
;         ^ - meta
;          ^^^^^^ meta.reader-form.clojure

  @foo @bar
; ^ keyword.operator.macro.clojure
;  ^^^ meta.reader-form.clojure
;     ^ - meta
;      ^ keyword.operator.macro.clojure
;       ^^^ meta.reader-form.clojure



; ## Dispatch macro

  #"\s" #"[1-9]"
; ^^^^^ meta.reader-form.clojure
;      ^ - meta
;       ^^^^^^^^ meta.reader-form.clojure

  #inst "2018-03-28T10:48:00.000" #uuid "3b8a31ed-fd89-4f1b-a00f-42e3d60cf5ce"
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.reader-form.clojure
;                                ^ - meta
;                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.reader-form.clojure

  #foo/bar {:a {:b [:c]}} [1 2 3]
; ^^^^^^^^^^^^^^^^^^^^^^^ meta.reader-form.clojure
;                        ^ - meta.reader-form.clojure



; # S-expressions

  (+ 1 2) (- 3 4)
; ^ meta.sexp.begin.clojure
;       ^ meta.sexp.end.clojure
;        ^ - meta

  '(1 2) '(3 4)
; ^ keyword.operator.macro.clojure
;  ^ meta.sexp.begin.clojure
;      ^ meta.sexp.end.clojure
;       ^ - meta
;        ^ keyword.operator.macro.clojure

  [1 2] [3 4]
; ^ meta.sexp.begin.clojure
;     ^ meta.sexp.end.clojure
;      ^ - meta

  {:a 1} {:b 2}
; ^ meta.sexp.begin.clojure
;      ^ meta.sexp.end.clojure
;       ^ - meta

  #{1 2} #{3 4}
; ^ keyword.operator.macro.clojure
;  ^ meta.sexp.begin.clojure
;      ^ meta.sexp.end.clojure
;       ^ - meta

  #_(1 2) (3 4)
; ^^ keyword.operator.macro.clojure punctuation.definition.comment.clojure
;   ^ meta.sexp.begin.clojure
;       ^ meta.sexp.end.clojure
;        ^ - meta
;         ^^^^^ - meta.discarded.clojure


; # Special forms

  (def x 1)
;  ^^^ meta.special-form.clojure keyword.declaration.variable.clojure

  (if test then else)
;  ^^ meta.special-form.clojure keyword.control.conditional.if.clojure

  (do expr*)
;  ^^ meta.special-form.clojure keyword.other.clojure

  (let [x 1] [x x])
;  ^^^ meta.special-form.clojure keyword.declaration.variable.clojure
;      ^^^^^ meta.binding-vector.clojure
;            ^^^^^ - meta.binding-vector.clojure

  (quote form)
;  ^^^^^ meta.special-form.clojure keyword.other.clojure

  (var symbol)
;  ^^^ meta.special-form.clojure keyword.other.clojure

  (fn name? [x 1] expr*)
;  ^^ meta.special-form.clojure keyword.declaration.function.inline.clojure

  (loop [x 1]
;  ^^^^ meta.special-form.clojure keyword.control.loop.clojure
    (recur (inc x)))
;    ^^^^^ meta.special-form.clojure keyword.control.flow.recur.clojure

  (throw (ex-info "Boom!" {:foo :bar}))
;  ^^^^^ meta.special-form.clojure keyword.control.flow.throw.clojure

  (try ,,, (catch Exception _ ,,,) (finally ,,,))
;  ^^^ meta.special-form.clojure keyword.control.exception.try.clojure
;           ^^^^^ keyword.control.exception.catch.clojure
;                                   ^^^^^^^ keyword.control.exception.finally.clojure

  (monitor-enter expr) (monitor-exit expr)
;  ^^^^^^^^^^^^^ meta.special-form.clojure keyword.other.clojure
;                       ^^^^^^^^^^^^ meta.special-form.clojure keyword.other.clojure



; # Destructuring

  (defn foo
    [[x y & xs :as bar] ys]
;   ^^^^^^^^^^^^^^^^^^^^^^^ meta.function.parameters.clojure
;              ^^^ constant.other.keyword.unqualified.clojure
    ,,,)

  (defn configure
    [val & {:keys [debug verbose] :or {debug false, verbose false}}]
;   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.function.parameters.clojure
;           ^^^^^ constant.other.keyword.unqualified.clojure
;                                 ^^^ constant.other.keyword.unqualified.clojure
;                  ^^^^^ meta.symbol.clojure
;                                            ^^^^^ constant.language.clojure
;                                                 ^ comment.punctuation.comma.clojure
    ,,,)

  (fn foo
    [[x y & xs :as bar] ys]
;   ^^^^^^^^^^^^^^^^^^^^^^^ meta.function.parameters.clojure
;                         ^ - invalid.illegal.stray-bracket-end.clojure
;              ^^^ constant.other.keyword.unqualified.clojure
    ,,,)

    (fn configure
      [val & {:keys [debug verbose] :or {debug false, verbose false}}]
  ;   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.function.parameters.clojure
  ;           ^^^^^ constant.other.keyword.unqualified.clojure
  ;                                 ^^^ constant.other.keyword.unqualified.clojure
  ;                  ^^^^^ meta.symbol.clojure
  ;                                            ^^^^^ constant.language.clojure
  ;                                                 ^ comment.punctuation.comma.clojure
      ,,,)

  (defn x
    [y]
    (fn [z]))
;           ^ -  invalid.illegal.stray-bracket-end.clojure

  (fn
    ()
;    ^ meta.sexp.end.clojure punctuation.section.parens.end.clojure
    ([x] ,,,))
;   ^ meta.sexp.begin.clojure punctuation.section.parens.begin.clojure

  (defn x
    ()
;    ^ meta.sexp.end.clojure punctuation.section.parens.end.clojure
    ([y] ,,,))
;   ^ meta.sexp.begin.clojure punctuation.section.parens.begin.clojure

  (let)
; ^ meta.sexp.begin.clojure punctuation.section.parens.begin.clojure
;     ^ meta.sexp.end.clojure punctuation.section.parens.end.clojure

  (let (foo)) (inc 1)
;      ^ meta.sexp.begin.clojure punctuation.section.parens.begin.clojure
;       ^^^ meta.function-call.clojure variable.function.clojure
;          ^^ meta.sexp.end.clojure punctuation.section.parens.end.clojure
;             ^ meta.sexp.begin.clojure punctuation.section.parens.begin.clojure
;              ^^^ meta.function-call.clojure variable.function.clojure
;                  ^ constant.numeric.integer.decimal.clojure
;                   ^ meta.sexp.end.clojure punctuation.section.parens.end.clojure
