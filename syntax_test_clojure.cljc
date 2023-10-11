; SYNTAX TEST "Packages/Tutkain/Clojure (Tutkain).sublime-syntax"

; # Comments and whitespace

  ;blah
; ^ comment.line.edn punctuation.definition.comment
;  ^^^^ comment.line.edn

  ;;; blah
; ^^^ comment.line.edn punctuation.definition.comment
;    ^^^^^ comment.line.edn

  blah;blah;blah
; ^^^^- comment
;     ^ comment.line.edn

  #!blah
; ^^ comment.line.edn punctuation.definition.comment
;   ^^^^^ comment.line.edn
  #! blah
; ^^ comment.line.edn punctuation.definition.comment
;   ^^^^^^ comment.line.edn
  #!#!#! blah
; ^^ comment.line.edn punctuation.definition.comment
;   ^^^^^^^^^^ comment.line.edn

  blah,blah, blah
;     ^ punctuation.comma.edn
;     ^ comment.punctuation.comma.edn
;      ^- comment
;          ^ punctuation.comma.edn
;          ^ comment.punctuation.comma.edn
;           ^- comment

; ## Include end-of-line

; ; blah
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ comment.line.edn



; # Constants

  true false nil
; ^^^^ constant.language.edn
;     ^ - constant
;      ^^^^^ constant.language.edn
;           ^ - constant
;            ^^^ constant.language.edn

; ## Breaks

  true,false,nil
; ^^^^ constant.language.edn
;     ^ comment.punctuation.comma.edn
;      ^^^^^ constant.language.edn
  true;false;nil
; ^^^^ constant.language.edn
;     ^ comment.line.edn punctuation.definition.comment

; ## Unaffected

  'nil (true) (nil)
; ^ keyword.operator.macro.clojure
;  ^^^ constant.language.edn
;      ^ punctuation.section.parens.begin.edn
;       ^^^^ constant.language.edn
;           ^ punctuation.section.parens.end.edn
;      ^^^^^^ meta.sexp.list.edn
;            ^ -meta.sexp
;             ^^^^^ meta.sexp.list.edn
;                  ^ -meta.sexp

; ## No highlighting

  nill nil- -nil nil?
; ^^^^^^^^^^^^^^^^^^^ - constant



; # Numbers

  1234 1234N +1234 +1234N -1234 -1234N
; ^^^^ constant.numeric.integer.decimal.edn
;     ^ - constant
;      ^^^^^ constant.numeric.integer.decimal.edn
;          ^ storage.type.numeric.edn
;           ^ - constant
;            ^ punctuation.definition.numeric.sign.edn
;            ^^^^^ constant.numeric.integer.decimal.edn
;                 ^ - constant
;                  ^ punctuation.definition.numeric.sign.edn
;                  ^^^^^^ constant.numeric.integer.decimal.edn
;                       ^ storage.type.numeric.edn
;                        ^ - constant
;                         ^ punctuation.definition.numeric.sign.edn
;                         ^^^^^ constant.numeric.integer.decimal.edn
;                              ^ - constant
;                               ^ punctuation.definition.numeric.sign.edn
;                               ^^^^^^ constant.numeric.integer.decimal.edn
;                                    ^ storage.type.numeric.edn
  0x1234af 0x1234afN 0X1234AF 0X1234AFN
; ^^ punctuation.definition.numeric.base.edn
; ^^^^^^^^ constant.numeric.integer.hexadecimal.edn
;         ^ - constant
;          ^^ punctuation.definition.numeric.base.edn
;          ^^^^^^^^^ constant.numeric.integer.hexadecimal.edn
;                  ^ storage.type.numeric.edn
;                   ^ - constant
;                    ^^ punctuation.definition.numeric.base.edn
;                    ^^^^^^^^ constant.numeric.integer.hexadecimal.edn
;                            ^ - constant
;                             ^^ punctuation.definition.numeric.base.edn
;                             ^^^^^^^^^ constant.numeric.integer.hexadecimal.edn
;                                     ^ storage.type.numeric.edn
  +0x1234af +0x1234afN +0X1234AF +0X1234AFN
; ^ punctuation.definition.numeric.sign.edn
;  ^^ punctuation.definition.numeric.base.edn
; ^^^^^^^^^ constant.numeric.integer.hexadecimal.edn
;          ^ - constant
;           ^ punctuation.definition.numeric.sign.edn
;            ^^ punctuation.definition.numeric.base.edn
;           ^^^^^^^^^^ constant.numeric.integer.hexadecimal.edn
;                    ^ storage.type.numeric.edn
;                     ^ - constant
;                      ^ punctuation.definition.numeric.sign.edn
;                       ^^ punctuation.definition.numeric.base.edn
;                       ^^^^^^^^ constant.numeric.integer.hexadecimal.edn
;                               ^ - constant
;                                ^ punctuation.definition.numeric.sign.edn
;                                 ^^ punctuation.definition.numeric.base.edn
;                                ^^^^^^^^^^ constant.numeric.integer.hexadecimal.edn
;                                         ^ storage.type.numeric.edn
  -0x1234af -0x1234afN -0X1234AF -0X1234AFN
; ^ punctuation.definition.numeric.sign.edn
;  ^^ punctuation.definition.numeric.base.edn
; ^^^^^^^^^ constant.numeric.integer.hexadecimal.edn
;          ^ - constant
;           ^ punctuation.definition.numeric.sign.edn
;            ^^ punctuation.definition.numeric.base.edn
;           ^^^^^^^^^^ constant.numeric.integer.hexadecimal.edn
;                    ^ storage.type.numeric.edn
;                     ^ - constant
;                      ^ punctuation.definition.numeric.sign.edn
;                       ^^ punctuation.definition.numeric.base.edn
;                      ^^^^^^^^^ constant.numeric.integer.hexadecimal.edn
;                               ^ - constant
;                                ^ punctuation.definition.numeric.sign.edn
;                                 ^^ punctuation.definition.numeric.base.edn
;                                ^^^^^^^^^^ constant.numeric.integer.hexadecimal.edn
;                                         ^ storage.type.numeric.edn
  2r1010 16r1234af 32r1234az 2R1010 16R1234AF 32R1234AZ
; ^^ punctuation.definition.numeric.base.edn
; ^^^^^^ constant.numeric.integer.other.edn
;       ^ - constant
;        ^^^ punctuation.definition.numeric.base.edn
;        ^^^^^^^^^ constant.numeric.integer.other.edn
;                 ^ - constant
;                  ^^^ punctuation.definition.numeric.base.edn
;                  ^^^^^^^^^ constant.numeric.integer.other.edn
;                           ^ - constant
;                            ^^ punctuation.definition.numeric.base.edn
;                            ^^^^^^ constant.numeric.integer.other.edn
;                                  ^ - constant
;                                   ^^^ punctuation.definition.numeric.base.edn
;                                   ^^^^^^^^^ constant.numeric.integer.other.edn
;                                            ^ - constant
;                                             ^^^ punctuation.definition.numeric.base.edn
;                                             ^^^^^^^^^ constant.numeric.integer.other.edn
  +2r1010 +16r1234af +32r1234az +2R1010 +16R1234AF +32R1234AZ
; ^ punctuation.definition.numeric.sign.edn
;  ^^ punctuation.definition.numeric.base.edn
; ^^^^^^^ constant.numeric.integer.other.edn
;        ^ - constant
;         ^ punctuation.definition.numeric.sign.edn
;          ^^^ punctuation.definition.numeric.base.edn
;         ^^^^^^^^^^ constant.numeric.integer.other.edn
;                   ^ - constant
;                    ^ punctuation.definition.numeric.sign.edn
;                     ^^^ punctuation.definition.numeric.base.edn
;                    ^^^^^^^^^^ constant.numeric.integer.other.edn
;                              ^ - constant
;                               ^ punctuation.definition.numeric.sign.edn
;                                ^^ punctuation.definition.numeric.base.edn
;                               ^^^^^^^ constant.numeric.integer.other.edn
;                                      ^ - constant
;                                       ^ punctuation.definition.numeric.sign.edn
;                                        ^^^ punctuation.definition.numeric.base.edn
;                                        ^^^^^^^^^ constant.numeric.integer.other.edn
;                                                 ^ - constant
;                                                  ^ punctuation.definition.numeric.sign.edn
;                                                   ^^^ punctuation.definition.numeric.base.edn
;                                                  ^^^^^^^^^^ constant.numeric.integer.other.edn
  -2r1010 -16r1234af -32r1234az -2R1010 -16R1234AF -32R1234AZ
; ^ punctuation.definition.numeric.sign.edn
;  ^^ punctuation.definition.numeric.base.edn
; ^^^^^^^ constant.numeric.integer.other.edn
;        ^ - constant
;         ^ punctuation.definition.numeric.sign.edn
;          ^^^ punctuation.definition.numeric.base.edn
;          ^^^^^^^^^ constant.numeric.integer.other.edn
;                   ^ - constant
;                    ^ punctuation.definition.numeric.sign.edn
;                     ^^^ punctuation.definition.numeric.base.edn
;                    ^^^^^^^^^^ constant.numeric.integer.other.edn
;                              ^ - constant
;                               ^ punctuation.definition.numeric.sign.edn
;                                ^^ punctuation.definition.numeric.base.edn
;                               ^^^^^^^ constant.numeric.integer.other.edn
;                                      ^ - constant
;                                       ^ punctuation.definition.numeric.sign.edn
;                                        ^^^ punctuation.definition.numeric.base.edn
;                                       ^^^^^^^^^^ constant.numeric.integer.other.edn
;                                                 ^ - constant
;                                                  ^ punctuation.definition.numeric.sign.edn
;                                                   ^^^ punctuation.definition.numeric.base.edn
;                                                  ^^^^^^^^^^ constant.numeric.integer.other.edn
  0/10 10/20 30/0
; ^^^^ constant.numeric.rational.decimal.edn
;  ^ punctuation.separator.rational.edn
;     ^ - constant
;      ^^^^^ constant.numeric.rational.decimal.edn
;        ^ punctuation.separator.rational.edn
;           ^ - constant
;            ^^^^ constant.numeric.rational.decimal.edn
;              ^ punctuation.separator.rational.edn
  +0/10 +10/20 +30/0
; ^^^^^ constant.numeric.rational.decimal.edn
; ^ punctuation.definition.numeric.sign.edn
;   ^ punctuation.separator.rational.edn
;      ^ - constant
;       ^^^^^^ constant.numeric.rational.decimal.edn
;       ^ punctuation.definition.numeric.sign.edn
;          ^ punctuation.separator.rational.edn
;             ^ - constant
;              ^^^^^ constant.numeric.rational.decimal.edn
;              ^ punctuation.definition.numeric.sign.edn
;                 ^ punctuation.separator.rational.edn
  -0/10 -10/20 -30/0
; ^^^^^ constant.numeric.rational.decimal.edn
; ^ punctuation.definition.numeric.sign.edn
;   ^ punctuation.separator.rational.edn
;      ^ - constant
;       ^^^^^^ constant.numeric.rational.decimal.edn
;       ^ punctuation.definition.numeric.sign.edn
;          ^ punctuation.separator.rational.edn
;             ^ - constant
;              ^^^^^ constant.numeric.rational.decimal.edn
;              ^ punctuation.definition.numeric.sign.edn
;                 ^ punctuation.separator.rational.edn
  1234M 1234.0M 1234.1234M
; ^^^^^ constant.numeric.float.decimal.edn
;     ^ storage.type.numeric.edn
;      ^ - constant
;       ^^^^^^^ constant.numeric.float.decimal.edn
;           ^ punctuation.separator.decimal.edn
;             ^ storage.type.numeric.edn
;              ^ - constant
;               ^^^^^^^^^^ constant.numeric.float.decimal.edn
;                   ^ punctuation.separator.decimal.edn
;                        ^ storage.type.numeric.edn
  +1234M +1234.0M +1234.1234M
; ^^^^^^ constant.numeric.float.decimal.edn
; ^ punctuation.definition.numeric.sign.edn
;      ^ storage.type.numeric.edn
;       ^ - constant
;        ^^^^^^^^ constant.numeric.float.decimal.edn
;        ^ punctuation.definition.numeric.sign.edn
;             ^ punctuation.separator.decimal.edn
;               ^ storage.type.numeric.edn
;                ^ - constant
;                 ^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                 ^ punctuation.definition.numeric.sign.edn
;                      ^ punctuation.separator.decimal.edn
;                           ^ storage.type.numeric.edn
  -1234M -1234.0M -1234.1234M
; ^^^^^^ constant.numeric.float.decimal.edn
; ^ punctuation.definition.numeric.sign.edn
;      ^ storage.type.numeric.edn
;       ^ - constant
;        ^^^^^^^^ constant.numeric.float.decimal.edn
;        ^ punctuation.definition.numeric.sign.edn
;             ^ punctuation.separator.decimal.edn
;               ^ storage.type.numeric.edn
;                ^ - constant
;                 ^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                 ^ punctuation.definition.numeric.sign.edn
;                      ^ punctuation.separator.decimal.edn
;                           ^ storage.type.numeric.edn
  1234e10 1234E10M 1234.1234e10M 1234.1234E10M
; ^^^^^^^ constant.numeric.float.decimal.edn
;        ^ - constant
;         ^^^^^^^ constant.numeric.float.decimal.edn
;                ^ storage.type.numeric.edn
;                 ^ - constant
;                  ^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                      ^ punctuation.separator.decimal.edn
;                              ^ storage.type.numeric.edn
;                               ^ - constant
;                                ^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                                    ^ punctuation.separator.decimal.edn
;                                            ^ storage.type.numeric.edn
  +1234e10 +1234E10M +1234.1234e10M +1234.1234E10M
; ^^^^^^^^ constant.numeric.float.decimal.edn
; ^ punctuation.definition.numeric.sign.edn
;         ^ - constant
;          ^^^^^^^^^ constant.numeric.float.decimal.edn
;          ^ punctuation.definition.numeric.sign.edn
;                  ^ storage.type.numeric.edn
;                   ^ - constant
;                    ^^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                    ^ punctuation.definition.numeric.sign.edn
;                         ^ punctuation.separator.decimal.edn
;                                 ^ storage.type.numeric.edn
;                                  ^ - constant
;                                   ^^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                                   ^ punctuation.definition.numeric.sign.edn
;                                        ^ punctuation.separator.decimal.edn
;                                                ^ storage.type.numeric.edn
  -1234e10 -1234E10M -1234.1234e10M -1234.1234E10M
; ^^^^^^^^ constant.numeric.float.decimal.edn
; ^ punctuation.definition.numeric.sign.edn
;         ^ - constant
;          ^^^^^^^^^ constant.numeric.float.decimal.edn
;          ^ punctuation.definition.numeric.sign.edn
;                  ^ storage.type.numeric.edn
;                   ^ - constant
;                    ^^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                    ^ punctuation.definition.numeric.sign.edn
;                         ^ punctuation.separator.decimal.edn
;                                 ^ storage.type.numeric.edn
;                                  ^ - constant
;                                   ^^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                                   ^ punctuation.definition.numeric.sign.edn
;                                        ^ punctuation.separator.decimal.edn
;                                                ^ storage.type.numeric.edn
  1234.1234e+10 1234.1234E+10 1234.1234e-10 1234.1234E-10
; ^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;     ^ punctuation.separator.decimal.edn
;              ^ - constant
;               ^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                   ^ punctuation.separator.decimal.edn
;                            ^ - constant
;                             ^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                                 ^ punctuation.separator.decimal.edn
;                                          ^ - constant
;                                           ^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                                               ^ punctuation.separator.decimal.edn
  +1234.1234e+10M +1234.1234E+10M +1234.1234e-10M +1234.1234E-10M
; ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
; ^ punctuation.definition.numeric.sign.edn
;      ^ punctuation.separator.decimal.edn
;               ^ storage.type.numeric.edn
;                ^ - constant
;                 ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                 ^ punctuation.definition.numeric.sign.edn
;                      ^ punctuation.separator.decimal.edn
;                               ^ storage.type.numeric.edn
;                                ^ - constant
;                                 ^ punctuation.definition.numeric.sign.edn
;                                 ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                                      ^ punctuation.separator.decimal.edn
;                                               ^ storage.type.numeric.edn
;                                                ^ - constant
;                                                 ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                                                 ^ punctuation.definition.numeric.sign.edn
;                                                      ^ punctuation.separator.decimal.edn
;                                                               ^ storage.type.numeric.edn
  -1234.1234e+10M -1234.1234E+10M -1234.1234e-10M -1234.1234E-10M
; ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
; ^ punctuation.definition.numeric.sign.edn
;      ^ punctuation.separator.decimal.edn
;               ^ storage.type.numeric.edn
;                ^ - constant
;                 ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                 ^ punctuation.definition.numeric.sign.edn
;                      ^ punctuation.separator.decimal.edn
;                               ^ storage.type.numeric.edn
;                                ^ - constant
;                                 ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                                 ^ punctuation.definition.numeric.sign.edn
;                                      ^ punctuation.separator.decimal.edn
;                                               ^ storage.type.numeric.edn
;                                                ^ - constant
;                                                 ^^^^^^^^^^^^^^^ constant.numeric.float.decimal.edn
;                                                 ^ punctuation.definition.numeric.sign.edn
;                                                      ^ punctuation.separator.decimal.edn
;                                                               ^ storage.type.numeric.edn

; ## Breaks

  10,20,30
; ^^ constant.numeric
;   ^ comment.punctuation.comma.edn
;    ^^ constant.numeric
  10;20;30
; ^^ constant.numeric
;   ^ comment.line.edn punctuation.definition.comment
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
; ^ punctuation.section.parens.begin.edn
;  ^^ constant.numeric
;            ^ punctuation.section.brackets.begin.edn
;             ^^ constant.numeric

  ([100 200])
; ^ punctuation.section.parens.begin.edn
;  ^ punctuation.section.brackets.begin.edn
;   ^^^ constant.numeric
;       ^^^ constant.numeric
;          ^ punctuation.section.brackets.end.edn
;           ^ punctuation.section.parens.end.edn
  ([0x10 0x20])
; ^ punctuation.section.parens.begin.edn
;  ^ punctuation.section.brackets.begin.edn
;   ^^^^ constant.numeric
;        ^^^^ constant.numeric
;            ^ punctuation.section.brackets.end.edn
;             ^ punctuation.section.parens.end.edn
  ([2r100 16r200])
; ^ punctuation.section.parens.begin.edn
;  ^ punctuation.section.brackets.begin.edn
;   ^^^^^ constant.numeric
;         ^^^^^^ constant.numeric
;               ^ punctuation.section.brackets.end.edn
;                ^ punctuation.section.parens.end.edn
  ([10/20 30/40])
; ^ punctuation.section.parens.begin.edn
;  ^ punctuation.section.brackets.begin.edn
;   ^^^^^ constant.numeric
;         ^^^^^ constant.numeric
;              ^ punctuation.section.brackets.end.edn
;               ^ punctuation.section.parens.end.edn
  ([100.100 200.200])
; ^ punctuation.section.parens.begin.edn
;  ^ punctuation.section.brackets.begin.edn
;   ^^^^^^^ constant.numeric
;           ^^^^^^^ constant.numeric
;                  ^ punctuation.section.brackets.end.edn
;                   ^ punctuation.section.parens.end.edn
  ([1e+10 2e-20])
; ^ punctuation.section.parens.begin.edn
;  ^ punctuation.section.brackets.begin.edn
;   ^^^^^ constant.numeric
;         ^^^^^ constant.numeric
;              ^ punctuation.section.brackets.end.edn
;               ^ punctuation.section.parens.end.edn

; ## Invalid numbers

  01234 +01234 -01234 '01234
; ^^^^^ invalid.deprecated.edn
;      ^- invalid
;       ^^^^^^ invalid.deprecated.edn
;              ^^^^^^ invalid.deprecated.edn
;                     ^ keyword.operator.macro.clojure
;                      ^^^^^ invalid.deprecated.edn
  01234N +01234N -01234N '01234N
; ^^^^^^ invalid.deprecated.edn
;       ^- invalid
;        ^^^^^^^ invalid.deprecated.edn
;                ^^^^^^^ invalid.deprecated.edn
;                        ^ keyword.operator.macro.clojure
  10-20 10+20 1234n 1234m
; ^^^^^^^^^^^^^^^^^^^^^^^ - constant
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
;     ^ comment.punctuation.comma.edn
  blah;blah;blah
;     ^ comment.line.edn punctuation.definition.comment
  blah`blah
;     ^ keyword.operator.macro.clojure
  blah~blah
;     ^ keyword.operator.macro.clojure
  blah@blah
;     ^ keyword.operator.macro.clojure
  blah^blah
;     ^ keyword.operator.macro.clojure
  blah\blah
;     ^ - constant.character.clojure

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
; ^ punctuation.definition.keyword.edn
; ^^^^^ constant.other.keyword.unqualified.edn

  :! :$ :% :& :* :- :_ := :+ :| :< :> :. :/ :?
; ^^ constant.other.keyword.unqualified.edn
;   ^ - constant
;    ^^ constant.other.keyword.unqualified.edn
;       ^^ constant.other.keyword.unqualified.edn
;          ^^ constant.other.keyword.unqualified.edn
;             ^^ constant.other.keyword.unqualified.edn
;                ^^ constant.other.keyword.unqualified.edn
;                   ^^ constant.other.keyword.unqualified.edn
;                      ^^ constant.other.keyword.unqualified.edn
;                         ^^ constant.other.keyword.unqualified.edn
;                            ^^ constant.other.keyword.unqualified.edn
;                               ^^ constant.other.keyword.unqualified.edn
;                                  ^^ constant.other.keyword.unqualified.edn
;                                     ^^ constant.other.keyword.unqualified.edn
;                                        ^^ constant.other.keyword.qualified.edn
;                                           ^^ constant.other.keyword.unqualified.edn
  :++ :--
; ^^^ constant.other.keyword.unqualified.edn
;    ^ - constant
;     ^^^ constant.other.keyword.unqualified.edn
  :blah
; ^^^^^ constant.other.keyword.unqualified.edn
  :blah/blah
; ^^^^^^^^^^ constant.other.keyword.qualified.edn
;      ^ punctuation.accessor.edn punctuation.definition.constant.namespace.edn
  :blah.blah
; ^^^^^^^^^^ constant.other.keyword.unqualified.edn
  :blah.blah/blah
;  ^^^^^^^^^ meta.namespace.edn
;           ^ punctuation.accessor.edn punctuation.definition.constant.namespace.edn
; ^^^^^^^^^^^^^^^ constant.other.keyword.qualified.edn
  :blah.blah/blah.blah
;  ^^^^^^^^^ meta.namespace.edn
; ^^^^^^^^^^^^^^^^^^^^ constant.other.keyword.qualified.edn
  :blah/blah/blah
;  ^^^^ meta.namespace.edn
; ^^^^^^^^^^^^^^^ constant.other.keyword.qualified.edn
  :blah1000
; ^^^^^^^^^ constant.other.keyword.unqualified.edn
  :blah1000.blah1000
; ^^^^^^^^^^^^^^^^^^ constant.other.keyword.unqualified.edn
  :*blah*
; ^^^^^^^ constant.other.keyword.unqualified.edn
  :blah'blah'
; ^^^^^^^^^^^ constant.other.keyword.unqualified.edn
  :blah'''blah'''
; ^^^^^^^^^^^^^^^ constant.other.keyword.unqualified.edn
  :blah:blah:blah
; ^^^^^^^^^^^^^^^ constant.other.keyword.unqualified.edn
  :blah#blah#
; ^^^^^^^^^^^ constant.other.keyword.unqualified.edn
  ::blah///blah
; ^^ punctuation.definition.keyword.clojure
;   ^^^^ meta.namespace.clojure
;       ^ punctuation.accessor.clojure punctuation.definition.constant.namespace.clojure
; ^^^^^^^^^^^^^ constant.other.keyword.auto-qualified.clojure
  ://blah
; ^^^^^^^ constant.other.keyword.qualified.edn
;  ^ punctuation.accessor.edn punctuation.definition.constant.namespace.edn
  :///
; ^^^^ constant.other.keyword.qualified.edn
;  ^ punctuation.accessor.edn punctuation.definition.constant.namespace.edn
  :/blah/blah
; ^^^^^^^^^^^ constant.other.keyword.qualified.edn
;  ^ punctuation.accessor.edn punctuation.definition.constant.namespace.edn
  :blah//
;  ^^^^ meta.namespace.edn
; ^^^^^^^ constant.other.keyword.qualified.edn
;      ^ punctuation.accessor.edn punctuation.definition.constant.namespace.edn

; ## These are valid, unlike symbols

  :' :# :### :10 :10.20
; ^^ constant.other.keyword.unqualified.edn
;   ^ - constant
;    ^^ constant.other.keyword.unqualified.edn
;       ^^^^ constant.other.keyword.unqualified.edn
;            ^^^ constant.other.keyword.unqualified.edn
;                ^^^^^^ constant.other.keyword.unqualified.edn

; ## Breaks

  :,blah
; ^ - constant
;  ^ comment.punctuation.comma.edn
  :;blah
; ^ - constant
;  ^ comment.line.edn punctuation.definition.comment
  :blah,:blah,:blah
; ^^^^^ constant.other.keyword.unqualified.edn
;      ^ comment.punctuation.comma.edn
;       ^^^^^ constant.other.keyword.unqualified.edn
  :blah;:blah;:blah
; ^^^^^ constant.other.keyword.unqualified.edn
;      ^ comment.line.edn punctuation.definition.comment
  :blah`blah
; ^^^^^ constant.other.keyword.unqualified.edn
;      ^ keyword.operator.macro.clojure
  :blah~blah
; ^^^^^ - constant.other.keyword.unqualified.edn
  :blah@blah
;      ^ keyword.operator.macro.clojure
  :blah^blah
; ^^^^^ - constant.other.keyword.unqualified.edn
;      ^ keyword.operator.macro.clojure
  :blah\blah
; ^^^^^ - constant.other.keyword.unqualified.edn
;      ^^ - constant.character.clojure

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
; ^^ punctuation.definition.keyword.clojure
;       ^ punctuation.accessor.clojure punctuation.definition.constant.namespace.clojure
; ^^^^^^^ constant.other.keyword.auto-qualified.clojure



; # Chars

  \0 \; \,
; ^^ constant.character.edn
;   ^ - constant.character.edn
;    ^^ constant.character.edn
;      ^ - constant.character.edn
;       ^^ constant.character.edn
; ^^ constant.character.edn
  \newline
; ^^^^^^^^ constant.character.edn
  blah \c blah \c
;      ^^ constant.character.edn
;        ^ - constant.character.edn
;              ^^ constant.character.edn

; ## Invalid but highlight anyway

  \blah100
; ^^^^^^^^ constant.character.edn invalid.illegal.character.edn

; ## Capture exactly one char

  \;;;;
; ^^ constant.character.edn
;   ^^^ comment.line.edn punctuation.definition.comment
  \,,
; ^^ constant.character.edn
;   ^ comment.punctuation.comma.edn
  \``blah
; ^^^^^^^ constant.character.edn invalid.illegal.character.edn
  \''blah
; ^^^^^^^ constant.character.edn invalid.illegal.character.edn
  \~~blah
; ^^^^^^^ constant.character.edn invalid.illegal.character.edn
  \@@blah
; ^^^^^^^ constant.character.edn invalid.illegal.character.edn
  \~@~@blah
; ^^^^^^^ constant.character.edn invalid.illegal.character.edn
  \##{}
; ^^ constant.character.edn
;    ^ punctuation.section.braces.begin.edn
;     ^ punctuation.section.braces.end.edn
  \^^blah
; ^^^^^^^ constant.character.edn invalid.illegal.character.edn

; ## Breaks

  \a,\b,\c
; ^^ constant.character.edn
;   ^ comment.punctuation.comma.edn
;    ^^ constant.character.edn
  \a;\b;\c
; ^^ constant.character.edn
;   ^ comment.line.edn punctuation.definition.comment

; ## Unaffected

  \c (\c) ( \c ) [\c] [ \c ]
; ^^ constant.character.edn
;    ^ punctuation.section.parens.begin.edn
;     ^^ constant.character.edn
;       ^ punctuation.section.parens.end.edn
;         ^ punctuation.section.parens.begin.edn
;           ^^ constant.character.edn
;             ^ - constant.character.edn
;              ^ punctuation.section.parens.end.edn



; # Strings

  "blah"
; ^^^^^^ string.quoted.double.edn
; ^ string.quoted.double.edn punctuation.definition.string.begin.edn
;      ^ string.quoted.double.edn punctuation.definition.string.end.edn

  "blah \" blah"
; ^^^^^^^^^^^^^^ string.quoted.double.edn
; ^ string.quoted.double.edn punctuation.definition.string.begin.edn
;       ^^ string.quoted.double.edn constant.character.escape.edn
;         ^^^^^ string.quoted.double.edn
;              ^ string.quoted.double.edn punctuation.definition.string.end.edn

  "
; ^ string.quoted.double.edn punctuation.definition.string.begin.edn
; ^^^^^^^^^^^^^^^^^^^^^^ string.quoted.double.edn
  blah () [] {} ::blah
; ^^^^^^^^^^^^^^^^^^^^^ string.quoted.double.edn
  "
; ^ string.quoted.double.edn punctuation.definition.string.end.edn

  "
; ^ string.quoted.double.edn punctuation.definition.string.begin.edn
  (unclosed paren ->
; ^^^^^^^^^^^^^^^^^^^ string.quoted.double.edn
  "
; ^ string.quoted.double.edn punctuation.definition.string.end.edn

; ## Breaks

  "blah","blah","blah"
; ^^^^^^ string.quoted.double.edn
;       ^ comment.punctuation.comma.edn
;        ^^^^^^ string.quoted.double.edn
;              ^ comment.punctuation.comma.edn
;               ^^^^^^ string.quoted.double.edn

  "blah";"blah";"blah"
; ^^^^^^ string.quoted.double.edn
;       ^ comment.line.edn punctuation.definition.comment

; ## Unaffected

  '"blah" ("blah") ( "blah" ) ["blah"]
; ^ keyword.operator.macro.clojure
;  ^^^^^^ string.quoted.double.edn
;         ^ punctuation.section.parens.begin.edn
;          ^^^^^^ string.quoted.double.edn
;                ^ punctuation.section.parens.end.edn
;                  ^ punctuation.section.parens.begin.edn
;                    ^^^^^^ string.quoted.double.edn
;                          ^- string.quoted.double.edn
;                           ^ punctuation.section.parens.end.edn


; # Regex

  #""
; ^ keyword.operator.macro.edn
;  ^^ string.regexp.edn
;  ^ string.regexp.edn punctuation.definition.string.begin.edn
;   ^ string.regexp.edn punctuation.definition.string.end.edn

  #" blah "
; ^ keyword.operator.macro.edn
;  ^^^^^^^^ string.regexp.edn
;  ^ string.regexp.edn punctuation.definition.string.begin.edn
;         ^ string.regexp.edn punctuation.definition.string.end.edn

  #"blah{1}"
; ^ keyword.operator.macro.edn
;  ^^^^^^^^^ string.regexp.edn
;  ^ string.regexp.edn punctuation.definition.string.begin.edn
;       ^^^ string.regexp.edn keyword.operator.quantifier.regexp
;          ^ string.regexp.edn punctuation.definition.string.end.edn

  #"
; ^ keyword.operator.macro.edn
;  ^ string.regexp.edn punctuation.definition.string.begin.edn
  blah{1}
; ^^^^ string.regexp.edn
;     ^^^ string.regexp.edn keyword.operator.quantifier.regexp
  "
; ^ string.regexp.edn punctuation.definition.string.end.edn

  #"
; ^ keyword.operator.macro.edn
;  ^ string.regexp.edn punctuation.definition.string.begin.edn
  \"
; ^^ string.regexp.edn constant.character.escape.regexp
  (unclosed paren ->
; ^ string.regexp.edn
  "
; ^ string.regexp.edn punctuation.definition.string.end.edn

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
;  ^^^- string.regexp.edn



; # Dispatch

  #inst"0000"
; ^^^^^ keyword.operator.macro.edn

  #blah blah
; ^^^^^ keyword.operator.macro.edn
;      ^^^^^^- keyword.operator.macro.edn

  #blah1000.blah1000/blah1000 blah
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^ keyword.operator.macro.edn
;                            ^^^^^^- keyword.operator.macro.edn

  #blah:blah blah
; ^^^^^^^^^^ keyword.operator.macro.edn
;           ^^^^^^- keyword.operator.macro.edn

  # inst "0000"
; ^ keyword.operator.macro.edn
;   ^^^^ keyword.operator.macro.edn
;       ^- keyword.operator.macro.edn
;        ^^^^^^ string.quoted.double.edn

  #
; ^ - keyword.operator.macro.clojure
    inst
    "0000"
;   ^ string.quoted.double.edn punctuation.definition.string.begin.edn

  #'blah
; ^^ keyword.operator.macro.clojure
;   ^^^^^- keyword.operator.macro.clojure

  #'
; ^^ keyword.operator.macro.clojure
  ; blah
; ^^^^^^^ comment.line.edn
  blah
; ^^^^^- keyword.operator.macro.clojure

  #(list % %1)
; ^ keyword.operator.macro.clojure
;  ^- keyword.operator.macro.clojure
;   ^^^^ meta.function-call.clojure variable.function.clojure
;  ^^^^^^^^^^^ meta.sexp.list.edn
;             ^ -meta.sexp

  #[]
; ^ -keyword.operator.macro.clojure
;  ^- keyword.operator.macro.clojure

  #_[]
; ^^ punctuation.definition.comment.edn
;   ^- keyword.operator.macro.edn
; ^^^ comment.block.edn comment.discard.edn

  #?[]
; ^^ keyword.operator.macro.clojure
;   ^- keyword.operator.macro.clojure

  #:foo{} #:bar/baz{:a 1} #::quux{:b 2} :end
; ^ keyword.operator.macro.edn
;  ^ punctuation.definition.keyword.edn
;  ^^^^ constant.other.keyword.unqualified.edn
;        ^ - meta
;         ^ keyword.operator.macro.edn
;          ^ constant.other.keyword.unqualified.edn punctuation.definition.keyword.edn
;           ^^^ meta.namespace.edn
;              ^^^^ invalid
;                  ^ punctuation.section.braces.begin.edn - meta.namespace - invalid
;                       ^ punctuation.section.braces.end.edn - meta.namespace - invalid
;                        ^ - meta
;                                      ^ - meta

  ##NaN ##Inf ##-Inf
; ^^ keyword.operator.macro.edn
;   ^^^ constant.other.symbolic.edn
;       ^^ keyword.operator.macro.edn
;         ^^^ constant.other.symbolic.edn
;             ^^ keyword.operator.macro.edn
;               ^^^^ constant.other.symbolic.edn

  ##
; ^^ - keyword.operator.macro.clojure
  ; blah
; ^^^^^^^ comment.line.edn
  ##NaN
; ^^ keyword.operator.macro.edn
;   ^^^ constant.other.symbolic.edn

; ## Breaks

  #blah\newline
; ^^^^^ - keyword.operator.macro.clojure
;      ^^^^^^^^ - constant.character.clojure

  #blah`blah
; ^^^^^ - keyword.operator.macro.clojure
;       ^^^^^- keyword.operator.macro.clojure

  #_0.000692025M
; ^^ punctuation.definition.comment.edn
;   ^^^^^^^^^^^^ constant.numeric
; ^^^^^^^^^^^^^^ comment.discard.edn

  #_ 0.000692025M
; ^^ punctuation.definition.comment.edn
;    ^^^^^^^^^^^^ constant.numeric
; ## FIXME: Ought to have comment.discard.edn, I think.

  #_blah
; ^^ punctuation.definition.comment.edn
;   ^^^^- punctuation.definition.comment.edn
; ^^^^^^ comment.discard.edn

; ## Unaffected

  '#'blah (#'blah blah)
; ^^ keyword.operator.macro.clojure
;    ^^^^^- keyword.operator.macro.clojure
;         ^ punctuation.section.parens.begin.edn
;          ^^ keyword.operator.macro.clojure
;            ^^^^^^^^^- keyword.operator.macro.clojure
;                     ^ punctuation.section.parens.end.edn
  '#inst"0000" (#inst"0000" blah)
;  ^^^^^ keyword.operator.macro.edn
;       ^^^^^^ string.quoted.double.edn
;              ^ punctuation.section.parens.begin.edn
;               ^^^^^ keyword.operator.macro.edn
;                    ^^^^^^ string.quoted.double.edn

  # :blah{}
; ^ - keyword.operator.macro.clojure
;   ^^^^^ constant.other.keyword.unqualified.edn

  # ' blah
; ^ - keyword.operator.macro.clojure
;   ^ keyword.operator.macro.clojure
;          ^ comment.line.edn punctuation.definition.comment

; ## Invalid

  #111[]
; ^ - keyword.operator.macro.clojure
;  ^^^ - constant.numeric
  (blah #) )
;       ^ - keyword.operator.macro.clojure
;          ^ invalid.illegal.stray-bracket-end.edn

  # #NaN
; ^ - keyword.operator.macro.edn
;   ^^^^ keyword.operator.macro.edn

; ## Ignore

  #{}
; ^ keyword.operator.macro.edn
;  ^ punctuation.section.braces.begin.edn



; # Quoting and unquoting

; ## Quote

  '100
; ^ keyword.operator.macro.clojure
;  ^^^ constant.numeric

  'true
; ^ keyword.operator.macro.clojure
;  ^^^^ constant.language.edn

  ':blah
; ^ keyword.operator.macro.clojure
;  ^^^^^ constant.other.keyword.unqualified.edn

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
;  ^ punctuation.section.parens.begin.edn
;   ^^ constant.numeric

  '(blah blah)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.edn
;   ^^^^ meta.function-call.clojure variable.function.clojure

  '(quote blah)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.edn
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
;  ^ punctuation.section.parens.begin.edn
;   ^^^^ meta.function-call.clojure variable.function.clojure
;        ^ keyword.operator.macro.clojure
;         ^^^^- keyword.operator.macro.clojure

  `(blah ~100)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.edn
;   ^^^^ meta.function-call.clojure variable.function.clojure
;        ^ keyword.operator.macro.clojure
;         ^^^ constant.numeric

; ## Unquote-splicing

  ~@blah
; ^^ keyword.operator.macro.clojure
;   ^^^^^- keyword.operator.macro.clojure

  ~@[10 20 30]
; ^^ keyword.operator.macro.clojure
;   ^ punctuation.section.brackets.begin.edn
;    ^^ constant.numeric

  `(blah ~@blah)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.edn
;   ^^^^ meta.function-call.clojure variable.function.clojure
;        ^^ keyword.operator.macro.clojure
;          ^^^^- keyword.operator.macro.clojure

  `(blah ~@[10 20 30])
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.edn
;   ^^^^ meta.function-call.clojure variable.function.clojure
;        ^^ keyword.operator.macro.clojure
;          ^ punctuation.section.brackets.begin.edn
;           ^^ constant.numeric

; ## Invalid

  ( ') )
; ^ punctuation.section.parens.begin.edn
;   ^ keyword.operator.macro.clojure
;      ^ invalid.illegal.stray-bracket-end.edn
;    ^ punctuation.section.parens.end.edn

  ( `) )
; ^ punctuation.section.parens.begin.edn
;   ^ keyword.operator.macro.clojure
;      ^ invalid.illegal.stray-bracket-end.edn
;    ^ punctuation.section.parens.end.edn

  ( `) )
; ^ punctuation.section.parens.begin.edn
;   ^ keyword.operator.macro.clojure
;      ^ invalid.illegal.stray-bracket-end.edn
;    ^ punctuation.section.parens.end.edn

  ( ~@) )
; ^ punctuation.section.parens.begin.edn
;   ^^ keyword.operator.macro.clojure
;       ^ invalid.illegal.stray-bracket-end.edn
;     ^ punctuation.section.parens.end.edn



; # Deref

  @100
; ^ keyword.operator.macro.clojure
;  ^^^ constant.numeric

  @true
; ^ keyword.operator.macro.clojure
;  ^^^^ constant.language.edn

  @blah
; ^ keyword.operator.macro.clojure
;  ^^^^^- keyword.operator.macro.clojure

  @:blah
; ^ keyword.operator.macro.clojure
;  ^^^^^ constant.other.keyword.unqualified.edn

  @(atom blah)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.edn
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
; ^ keyword.operator.macro.clojure
;  ^^^^^ keyword.operator.macro.edn

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
; ^ punctuation.section.parens.begin.edn
;   ^ keyword.operator.macro.clojure
;      ^ invalid.illegal.stray-bracket-end.edn
;    ^ punctuation.section.parens.end.edn



; # Metadata

  ^File
; ^ keyword.operator.macro.clojure
;  ^^^^^- keyword.operator.macro.clojure

  ^File blah
; ^ keyword.operator.macro.clojure
;  ^^^^^^^^^^- keyword.operator.macro.clojure

  ^:private blah
; ^ keyword.operator.macro.clojure
;  ^^^^^^^^ constant.other.keyword.unqualified.edn

  ^{:private true} blah
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.braces.begin.edn
;   ^^^^^^^^ constant.other.keyword.unqualified.edn
;            ^^^^ constant.language.edn
;                ^ punctuation.section.braces.end.edn

  ; Consequent metadata is merged
  ^:private ^:dynamic blah
; ^ keyword.operator.macro.clojure
;  ^^^^^^^^ constant.other.keyword.unqualified.edn
;           ^ keyword.operator.macro.clojure
;            ^^^^^^^^ constant.other.keyword.unqualified.edn

  ; Useless but accepted by Clojure reader
  ^^^{10 20}{30 40}{:tag File} blah
; ^^^ keyword.operator.macro.clojure
;    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^- keyword.operator.macro.clojure
;    ^ punctuation.section.braces.begin.edn
;     ^^ constant.numeric
;        ^^ constant.numeric
;          ^ punctuation.section.braces.end.edn
;           ^ punctuation.section.braces.begin.edn
;            ^^ constant.numeric
;               ^^ constant.numeric
;                 ^ punctuation.section.braces.end.edn
;                  ^ punctuation.section.braces.begin.edn
;                   ^^^^ constant.other.keyword.unqualified.edn

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
; ^ punctuation.section.parens.begin.edn
;   ^ keyword.operator.macro.clojure
;      ^ invalid.illegal.stray-bracket-end.edn
;    ^ punctuation.section.parens.end.edn



; # Brackets

  []
; ^ punctuation.section.brackets.begin.edn
;  ^ punctuation.section.brackets.end.edn

  [10, 20, 30]
; ^ punctuation.section.brackets.begin.edn
;  ^^ constant.numeric
;    ^ comment.punctuation.comma.edn
;      ^^ constant.numeric
;        ^ comment.punctuation.comma.edn
;          ^^ constant.numeric
;            ^ punctuation.section.brackets.end.edn

  [10
; ^ punctuation.section.brackets.begin.edn
;  ^^ constant.numeric
   ; ---
;  ^ comment.line.edn punctuation.definition.comment
   blah
   #inst"0000"
;  ^^^^^ keyword.operator.macro.edn
;       ^ string.quoted.double.edn punctuation.definition.string.begin.edn
   [20]]
;  ^ punctuation.section.brackets.begin.edn
;   ^^ constant.numeric
;     ^^ punctuation.section.brackets.end.edn

; ## Invalid

  [ ] ]
; ^ punctuation.section.brackets.begin.edn
;   ^ punctuation.section.brackets.end.edn
;     ^ invalid.illegal.stray-bracket-end.edn



; # Braces

  #{} }
; ^ keyword.operator.macro.edn
;  ^ punctuation.section.braces.begin.edn
;   ^ punctuation.section.braces.end.edn
;     ^ invalid.illegal.stray-bracket-end.edn

  #{10, 20, 30}
; ^ keyword.operator.macro.edn
;  ^ punctuation.section.braces.begin.edn
;   ^^ constant.numeric
;     ^ comment.punctuation.comma.edn
;       ^^ constant.numeric
;         ^ comment.punctuation.comma.edn
;           ^^ constant.numeric
;             ^ punctuation.section.braces.end.edn

  #{10
; ^ keyword.operator.macro.edn
;  ^ punctuation.section.braces.begin.edn
;   ^^ constant.numeric
    ; ---
;   ^ comment.line.edn punctuation.definition.comment
    blah
    #inst"0000"
;   ^^^^^ keyword.operator.macro.edn
;        ^ string.quoted.double.edn punctuation.definition.string.begin.edn
    {20}}
;   ^ punctuation.section.braces.begin.edn
;    ^^ constant.numeric
;      ^^ punctuation.section.braces.end.edn

  {10 20, 30 40}
; ^ punctuation.section.braces.begin.edn
;  ^^ constant.numeric
;     ^^ constant.numeric
;       ^ comment.punctuation.comma.edn
;         ^^ constant.numeric
;            ^^ constant.numeric
;              ^ punctuation.section.braces.end.edn

  {:blah [10 20 30]
; ^ punctuation.section.braces.begin.edn
;  ^^^^^ constant.other.keyword.unqualified.edn
;        ^ punctuation.section.brackets.begin.edn
;         ^^ constant.numeric
;            ^^ constant.numeric
;               ^^ constant.numeric
;                 ^ punctuation.section.brackets.end.edn
   ; ---
;  ^ comment.line.edn punctuation.definition.comment
   :blahblah #{10 20 30}}
;  ^^^^^^^^^ constant.other.keyword.unqualified.edn
;            ^ keyword.operator.macro.edn
;             ^ punctuation.section.braces.begin.edn
;              ^^ constant.numeric
;                 ^^ constant.numeric
;                    ^^ constant.numeric
;                      ^^ punctuation.section.braces.end.edn

; ## Invalid

  #{ } }
; ^ keyword.operator.macro.edn
;  ^ punctuation.section.braces.begin.edn
;    ^ punctuation.section.braces.end.edn
;      ^ invalid.illegal.stray-bracket-end.edn

  { } }
; ^ punctuation.section.braces.begin.edn
;   ^ punctuation.section.braces.end.edn
;     ^ invalid.illegal.stray-bracket-end.edn



; # Parens

  ()
; ^ punctuation.section.parens.begin.edn
;  ^ punctuation.section.parens.end.edn


; ## Highlight one symbol in operator position

  (blah blah true 10 "" [10 20])
; ^ punctuation.section.parens.begin.edn
;  ^^^^ meta.function-call.clojure variable.function.clojure
;      ^^^^^^^^^^^^^^^^^^^^^^^^- variable.function.clojure
;            ^^^^ constant.language.edn
;                 ^^ constant.numeric
;                    ^ string.quoted.double.edn punctuation.definition.string.begin.edn
;                     ^ string.quoted.double.edn punctuation.definition.string.end.edn
;                       ^ punctuation.section.brackets.begin.edn
;                        ^^ constant.numeric
;                           ^^ constant.numeric
;                             ^ punctuation.section.brackets.end.edn
;                              ^ punctuation.section.parens.end.edn

  #(blah blah true 10 "" [10 20])
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.edn
;   ^^^^ meta.function-call.clojure variable.function.clojure
;       ^^^^^^^^^^^^^^^^^^^^^^^^^- variable.function.clojure
;             ^^^^ constant.language.edn
;                  ^^ constant.numeric
;                               ^ punctuation.section.parens.end.edn

; ## Ignore operator

  (true blah :blah)
; ^ punctuation.section.parens.begin.edn
;       ^^^^ - variable.function.clojure
;  ^^^^ constant.language.edn

  (10 blah :blah)
; ^ punctuation.section.parens.begin.edn
;     ^^^^ - variable.function.clojure
;  ^^ constant.numeric

  (:blah blah 10)
; ^ punctuation.section.parens.begin.edn
;        ^^^^ - variable.function.clojure
;  ^^^^^ constant.other.keyword.unqualified.edn

  (/ a b)
;  ^ meta.function-call.clojure variable.function.clojure
;    ^ - variable.function.clojure

  (+ a b)
;  ^ meta.function-call.clojure variable.function.clojure
;    ^ - variable.function.clojure

  (- a b)
;  ^ meta.function-call.clojure variable.function.clojure
;    ^ - variable.function.clojure

  #(true blah 10)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.edn

; ## Whitespace

  (
; ^ punctuation.section.parens.begin.edn
    blah
;   ^^^^ meta.function-call.clojure variable.function.clojure
    ; ---
;   ^ comment.line.edn punctuation.definition.comment
    blah
    :blah
;   ^^^^^ constant.other.keyword.unqualified.edn
   )
;  ^ punctuation.section.parens.end.edn

; ## Invalid

  ( ) )
; ^ punctuation.section.parens.begin.edn
;   ^ punctuation.section.parens.end.edn
;     ^ invalid.illegal.stray-bracket-end.edn



; # fn

  (fn)
; ^^^^ meta.sexp.list.edn
;     ^ -meta.sexp

  (fn [])
;  ^^ keyword.declaration.function.inline.clojure
;     ^ punctuation.section.brackets.begin.edn
;      ^ punctuation.section.brackets.end.edn
;       ^ punctuation.section.parens.end.edn
;     ^^ meta.sexp.vector.edn meta.function.parameters.clojure
;       ^ -meta.sexp.vector.edn & -meta.function.parameters.clojure
; ^^^^^^^ meta.sexp.list.edn
;        ^ -meta.sexp

  (fn [x y] (* x y 1))
;     ^^^^^ meta.sexp.list.edn meta.sexp.vector.edn meta.function.parameters.clojure
;          ^ -meta.sexp.vector.edn & -meta.function.parameters.clojure
; ^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                     ^ -meta.sexp


  (fn ())
;     ^^ meta.sexp.list.edn meta.sexp.list.edn
; ^^^^^^^ meta.sexp.list.edn
;        ^ -meta.sexp

  (fn ([{:keys [foo]}]))
;        ^^^^^ constant.other.keyword.unqualified.edn
;      ^^^^^^^^^^^^^^^ meta.function.parameters.clojure
;      ^^^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn meta.sexp.vector.edn
;     ^^^^^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
; ^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                       ^ -meta.sexp


  (fn
    ([x] (recur x 2))
;    ^^^ meta.sexp.list.edn meta.sexp.vector.edn meta.function.parameters.clojure
;       ^ -meta.sexp.vector.edn & -meta.function.parameters.clojure
;   ^^^^^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
    ([x y] (* x y 1)))
;    ^^^^^ meta.sexp.list.edn meta.sexp.vector.edn meta.function.parameters.clojure
;         ^ -meta.sexp.vector -meta.function.parameters
;   ^^^^^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
;                     ^ -meta.sexp
; ^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn


  (fn declare-noindex [] blah)
;  ^^ keyword.declaration.function.inline.clojure
;     ^^^^^^^^^^^^^^^ entity.name.function.clojure
;                       ^^^^^^^- storage
;                       ^^^^^^^- entity
;                     ^^ meta.sexp.vector.edn meta.function.parameters.clojure
;                       ^ -meta.sexp.vector.edn & -meta.function.parameters.clojure
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                             ^ -meta.sexp

  (fn foo ())
;         ^^ meta.sexp.list.edn meta.sexp.list.edn meta.function-body.clojure
;           ^ -meta.function-body
; ^^^^^^^^^^^ meta.sexp.list.edn
;            ^ -meta.sexp

  (fn declare-noindex
;  ^^ keyword.declaration.function.inline.clojure
;     ^^^^^^^^^^^^^^^ entity.name.function.clojure
;                    ^- entity
    ([] blah)
;    ^^ meta.function.parameters.clojure
;    ^^ meta.sexp.list.edn meta.sexp.vector.edn
;      ^ -meta.sexp.vector.edn
;   ^^^^^^^^^ meta.sexp.list meta.sexp.list.edn
    ([_] blah))
;    ^^^ meta.function.parameters.clojure
;    ^^^ meta.sexp.list.edn meta.sexp.vector.edn
;       ^ -meta.sexp.vector.edn
;   ^^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
;             ^ - invalid.illegal.stray-bracket-end.edn

  ; Invalid but take care anyway
  (fn declare-noindex dont-declare [])
;  ^^ keyword.declaration.function.inline.clojure
;     ^^^^^^^^^^^^^^^ entity.name.function.clojure
;                    ^^^^- storage
;                    ^^^^- entity
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                     ^ -meta.sexp

(defmacro bound-fn
  [& fntail]
  `(bound-fn* (fn ~@fntail)))
;                 ^^ keyword.operator.macro.clojure
;                   ^^^^^^ meta.reader-form.edn meta.symbol.edn
;                         ^^^ punctuation.section.parens.end.edn

; # defs

; ## Normal def

  (def)
; ^^^^^ meta.sexp.list.edn
;      ^ -meta.sexp

  (def declare-def)
;  ^^^ keyword.declaration.variable.clojure
;      ^^^^^^^^^^^ entity.name.constant.clojure
; ^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                  ^ -meta.sexp

  (def declare-def dont-declare)
; ^ punctuation.section.parens.begin.edn
;  ^^^ keyword.declaration.variable.clojure
;      ^^^^^^^^^^^ entity.name.constant.clojure
;                 ^^^^^^^^^^^^- storage
;                 ^^^^^^^^^^^^- entity
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                               ^ -meta.sexp

  (def λ nil)
;  ^^^ keyword.declaration.variable.clojure
;      ^ entity.name.constant.clojure
;        ^^^ constant.language.edn
; ^^^^^^^^^^^ meta.sexp.list.edn
;            ^ -meta.sexp

  (def 👽 nil)
;  ^^^ keyword.declaration.variable.clojure
;      ^ entity.name.constant.clojure
;        ^^^ constant.language.edn
; ^^^^^^^^^^^ meta.sexp.list.edn
;            ^ -meta.sexp

  (def def nil)
;  ^^^ keyword.declaration.variable.clojure
;      ^^^ entity.name.constant.clojure
;          ^^^ constant.language.edn
; ^^^^^^^^^^^^^ meta.sexp.list.edn
;              ^ -meta.sexp

  (
   ; ---
;  ^ comment.line.edn punctuation.definition.comment
   def
;  ^^^ keyword.declaration.variable.clojure
   ; ---
;  ^ comment.line.edn punctuation.definition.comment
   declare-def
;  ^^^^^^^^^^^ entity.name.constant.clojure
   dont-declare
;  ^^^^^^^^^^^^^- storage
;  ^^^^^^^^^^^^^- entity
   )
;   ^ -meta.sexp

  (defonce declare-defonce)
;  ^^^^^^^ keyword.declaration.variable.clojure
;          ^^^^^^^^^^^^^^^ entity.name.constant.clojure
; ^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                          ^ -meta.sexp

; ## Declare with metadata

  (def ^:private declare-def nil)
;  ^^^ keyword.declaration.variable.clojure
;      ^ keyword.operator.macro.clojure
;       ^^^^^^^^ constant.other.keyword.unqualified.edn
;                ^^^^^^^^^^^ entity.name.constant.clojure
;                            ^^^ constant.language.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                ^ -meta.sexp

  (def ^:private declare-def dont-declare)
;  ^^^ keyword.declaration.variable.clojure
;      ^ keyword.operator.macro.clojure
;       ^^^^^^^^ constant.other.keyword.unqualified.edn
;                ^^^^^^^^^^^ entity.name.constant.clojure
;                           ^^^^^^^^^^^^^- storage
;                           ^^^^^^^^^^^^^- entity
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                         ^ -meta.sexp

  ; Consequent metadata is merged

  (def ^:private ^:dynamic declare-def nil)
;  ^^^ keyword.declaration.variable.clojure
;      ^ keyword.operator.macro.clojure
;       ^^^^^^^^ constant.other.keyword.unqualified.edn
;                ^ keyword.operator.macro.clojure
;                 ^^^^^^^^ constant.other.keyword.unqualified.edn
;                          ^^^^^^^^^^^ entity.name.constant.clojure
;                                      ^^^ constant.language.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                          ^ -meta.sexp

  (def ^:private ^:dynamic declare-def dont-declare)
;  ^^^ keyword.declaration.variable.clojure
;      ^ keyword.operator.macro.clojure
;       ^^^^^^^^ constant.other.keyword.unqualified.edn
;                ^ keyword.operator.macro.clojure
;                 ^^^^^^^^ constant.other.keyword.unqualified.edn
;                          ^^^^^^^^^^^ entity.name.constant.clojure
;                                     ^^^^^^^^^^^^^- storage
;                                     ^^^^^^^^^^^^^- entity
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                                   ^ -meta.sexp

  (
   def
;  ^^^ keyword.declaration.variable.clojure
   ; ---
   ^
;  ^ keyword.operator.macro.clojure
   ; ---
   {:private
;  ^ punctuation.section.braces.begin.edn
;   ^^^^^^^^ constant.other.keyword.unqualified.edn
   ; ---
    true}
;   ^^^^ constant.language.edn
;       ^ punctuation.section.braces.end.edn
   ; ---
   declare-def
;  ^^^^^^^^^^^ entity.name.constant.clojure
   ; ---
   dont-declare
;  ^^^^^^^^^^^^^- storage
;  ^^^^^^^^^^^^^- entity
   )

  (defonce ^:private declare-defonce nil)
; ^ punctuation.section.parens.begin.edn
;  ^^^^^^^ keyword.declaration.variable.clojure
;          ^ keyword.operator.macro.clojure
;           ^^^^^^^^ constant.other.keyword.unqualified.edn
;                    ^^^^^^^^^^^^^^^ entity.name.constant.clojure
;                                    ^^^ constant.language.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                        ^ -meta.sexp

  ; Useless but accepted by Clojure reader
  (^{10 20} def ^:private declare-def dont-declare)
;  ^ keyword.operator.macro.clojure
;   ^ punctuation.section.braces.begin.edn
;    ^^ constant.numeric
;       ^^ constant.numeric
;         ^ punctuation.section.braces.end.edn
;           ^^^ keyword.declaration.variable.clojure
;               ^ keyword.operator.macro.clojure
;                ^^^^^^^^ constant.other.keyword.unqualified.edn
;                         ^^^^^^^^^^^ entity.name.constant.clojure
;                                    ^^^^^^^^^^^^^- storage
;                                    ^^^^^^^^^^^^^- entity
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                                  ^ -meta.sexp

  ; Useless but accepted by Clojure reader
  (def ^^^{10 20}{30 40}{:private true} declare-def dont-declare)
;  ^^^ keyword.declaration.variable.clojure
;      ^^^ keyword.operator.macro.clojure
;         ^ punctuation.section.braces.begin.edn
;          ^^ constant.numeric
;             ^^ constant.numeric
;               ^ punctuation.section.braces.end.edn
;                ^ punctuation.section.braces.begin.edn
;                 ^^ constant.numeric
;                    ^^ constant.numeric
;                      ^ punctuation.section.braces.end.edn
;                       ^ punctuation.section.braces.begin.edn
;                        ^^^^^^^^ constant.other.keyword.unqualified.edn
;                                 ^^^^ constant.language.edn
;                                     ^ punctuation.section.braces.end.edn
;                                       ^^^^^^^^^^^ entity.name.constant.clojure
;                                                  ^^^^^^^^^^^^^- storage
;                                                  ^^^^^^^^^^^^^- entity
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                                                ^ -meta.sexp



; ## declare

  (declare)
; ^^^^^^^^^ meta.sexp.list.edn
;          ^ -meta.sexp

  (declare declare-noindex)
;  ^^^^^^^ keyword.declaration.variable.clojure
;          ^^^^^^^^^^^^^^^ entity.name.function.forward-decl.clojure
;         ^^^^^^^^^^^^^^^^^- storage
; ^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                          ^ -meta.sexp



; ## Don't declare

  (def nil dont-declare)
;  ^^^ keyword.declaration.variable.clojure
;      ^^^ constant.language.edn
;         ^^^^^^^^^^^^^- storage
;         ^^^^^^^^^^^^^- entity
; ^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                       ^ -meta.sexp

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
;          ^ invalid.illegal.stray-bracket-end.edn
;        ^ punctuation.section.parens.end.edn
; ^^^^^^^^ meta.sexp.list.edn
;         ^ -meta.sexp



; # Function defs

  (defn)
; ^^^^^^ meta.sexp.list.edn
;       ^ -meta.sexp

  (defn f [])
;         ^^ meta.sexp.list.edn meta.sexp.vector.edn meta.function.parameters.clojure
; ^^^^^^^^^^^ meta.sexp.list.edn
;            ^ -meta.sexp

  (defn f ([a]) [a])
;          ^^^ meta.sexp.list.edn meta.sexp.list.edn meta.sexp.vector.edn
;               ^^^ meta.sexp.list.edn meta.sexp.vector.edn
;         ^^^^^ meta.sexp.list.edn meta.sexp.list.edn
; ^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                   ^ -meta.sexp


  (defn declare-defn [] dont-declare)
;  ^^^^ keyword.declaration.function.clojure
;       ^^^^^^^^^^^^ entity.name.function.clojure
;                    ^^^^^^^^^^^^^^^- storage
;                    ^^^^^^^^^^^^^^^- entity
;                    ^^ meta.function.parameters.clojure
;                    ^^ meta.sexp.vector.edn
;                      ^ -meta.sexp.vector.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                    ^ -meta.sexp

  (defn declare-defn [arg & args] dont-declare)
;  ^^^^ keyword.declaration.function.clojure
;       ^^^^^^^^^^^^ entity.name.function.clojure
;                    ^^^^^^^^^^^^ meta.function.parameters.clojure
;                    ^^^^^^^^^^^^^^^^^^^^^^^^^- storage
;                    ^^^^^^^^^^^^^^^^^^^^^^^^^- entity
;                    ^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.vector.edn
;                                ^ meta.sexp.list.edn - meta.sexp.vector.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                              ^ -meta.sexp

  (defn ^:private declare-defn [arg & args] dont-declare)
;  ^^^^ keyword.declaration.function.clojure
;       ^ keyword.operator.macro.clojure
;        ^^^^^^^^ constant.other.keyword.unqualified.edn
;                 ^^^^^^^^^^^^ entity.name.function.clojure
;                              ^^^^^^^^^^^^^^^^^^^^^^^^^- storage
;                              ^^^^^^^^^^^^^^^^^^^^^^^^^- entity
;                              ^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.vector.edn
;                                          ^ -meta.sexp.vector
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                                        ^ -meta.sexp

  (defn declare-defn
;  ^^^^ keyword.declaration.function.clojure
;       ^^^^^^^^^^^^ entity.name.function.clojure
    "docstring"
;   ^^^^^^^^^^^ string.quoted.double.edn
    [arg & args]
;   ^^^^^^^^^^^^- storage
;   ^^^^^^^^^^^^- entity
    dont-declare)
;   ^^^^^^^^^^^^- storage
;   ^^^^^^^^^^^^- entity
;                ^ -meta.sexp

  (defn
;  ^^^^ keyword.declaration.function.clojure
    ^:private
;   ^ keyword.operator.macro.clojure
;    ^^^^^^^^ constant.other.keyword.unqualified.edn
    declare-defn
;   ^^^^^^^^^^^^ entity.name.function.clojure
    "docstring"
;   ^^^^^^^^^^^ string.quoted.double.edn
    ([] dont-declare)
;    ^^ meta.function.parameters.clojure
;   ^^^^^^^^^^^^^^^^^- storage
;   ^^^^^^^^^^^^^^^^^- entity
;   ^^^^^^^^^^^^^^^^^ meta.function-body.clojure
;                    ^ -meta.function-body.clojure
    ([_] dont-declare))
;    ^^^ meta.function.parameters.clojure
;   ^^^^^^^^^^^^^^^^^^^- storage
;   ^^^^^^^^^^^^^^^^^^^- entity
;                      ^ -meta.sexp

  (
   defn
;  ^^^^ keyword.declaration.function.clojure
   declare-defn
;  ^^^^^^^^^^^^ entity.name.function.clojure
   "docstring"
;  ^^^^^^^^^^^ string.quoted.double.edn
   {:private true}
;   ^^^^^^^^ constant.other.keyword.unqualified.edn
;            ^^^^ constant.language.edn
   ([] dont-declare)
;   ^^ meta.function.parameters.clojure
;  ^^^^^^^^^^^^^^^^^- storage
;  ^^^^^^^^^^^^^^^^^- entity
   ([_] dont-declare))
;   ^^ meta.function.parameters.clojure
;  ^^^^^^^^^^^^^^^^^^^- storage
;  ^^^^^^^^^^^^^^^^^^^- entity
;                     ^ -meta.sexp

  (defn declare-defn [value] {:pre [(int? value)]}
;  ^^^^ keyword.declaration.function.clojure
;       ^^^^^^^^^^^^ entity.name.function.clojure
;                     ^^^^^- storage
;                     ^^^^^- entity
;                             ^^^^ constant.other.keyword.unqualified.edn
;                                    ^^^^ meta.function-call.clojure variable.function.clojure
;                            ^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.map.edn
;                                  ^^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.map.edn meta.sexp.vector.edn
    value)
;   ^^^^^- storage
;   ^^^^^- entity
;         ^ -meta.sexp

  (defn -main [& args] ,,,)
;       ^^^^^ entity.name.function.clojure
;                          ^ -meta.sexp

  (defn start [& [port]] ,,,)
;                            ^ -meta.sexp

  (defn foo [&bar])
;            ^ - keyword
;                  ^ -meta.sexp

  (defn foo [bar] [baz])
;           ^^^^^ meta.function.parameters.clojure
;                 ^^^^^ - meta.function.parameters.clojure
;                       ^ -meta.sexp

  (defn foo)
;          ^ punctuation.section.parens.end.edn
; ^^^^^^^^^^ meta.sexp.list.edn
;           ^ -meta.sexp

  ; # Gotta take care of these to have slurping work
  (defn f ([x]) 1)
;               ^ meta.reader-form.edn constant.numeric.integer.decimal.edn
  (defn f ([x]) "f")
;               ^^^ meta.reader-form.edn string.quoted.double.edn
  (defn f ([x]) x)
;               ^ meta.reader-form.edn meta.symbol.edn
  (defn f ([x]) :foo)
;               ^ meta.reader-form.edn constant.other.keyword.unqualified.edn punctuation.definition.keyword.edn
;                ^^^ meta.reader-form.edn constant.other.keyword.unqualified.edn
  (defn f ([x]) @foo)
;               ^ keyword.operator.macro.clojure
;                ^^^ meta.reader-form.edn meta.symbol.edn
  (defn f ([x]) #foo/bar)
;               ^^^^^^^^ meta.tagged-element.edn keyword.operator.macro.edn
;                       ^ -meta.tagged-element.edn
;                       ^ -meta.reader-form.edn
  (defn f ([x]) , true)
;               ^ punctuation.comma.edn comment.punctuation.comma.edn
;                 ^^^^ meta.reader-form.edn constant.language.edn

  (defn f ([a]) (b (c)))
;                  ^ punctuation.section.parens.begin.edn
;                      ^ -invalid

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
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                            ^ -meta.sexp.list.edn

  (defmulti ^:private declare-multi-fn dont-declare-dispatch-fn)
;  ^^^^^^^^ keyword.declaration.function.clojure
;           ^ keyword.operator.macro.clojure
;            ^^^^^^^^ constant.other.keyword.unqualified.edn
;                     ^^^^^^^^^^^^^^^^ entity.name.function.clojure
;                                     ^^^^^^^^^^^^^^^^^^^^^^^^^- storage
;                                     ^^^^^^^^^^^^^^^^^^^^^^^^^- entity
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                                               ^ -meta.sexp.list.edn

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
;                            ^^^ constant.language.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                ^ -meta.sexp.list.edn

  (defmethod dont-declare-multi-fn :dispatch-value [arg & args] [arg] ...)
;                                  ^^^^^^^^^^^^^^^ constant.other.keyword.unqualified.edn
;                                                  ^^^^^^^^^^^^ meta.function.parameters.clojure
;                                                               ^^^^^ - meta.function.parameters.clojure
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                                                         ^ -meta.sexp.list.edn

  (defmethod dont-declare-multi-fn DispatchType [arg] ...)
;                                  ^^^^^^^^^^^^^- storage
;                                  ^^^^^^^^^^^^^- entity
;  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                                         ^ -meta.sexp.list.edn

  (defmethod bat [String String] [x y & xs] ,,,)
;                ^^^^^^^^^^^^^^^ - meta.function.parameters.clojure
;                                ^^^^^^^^^^ meta.function.parameters.clojure
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                               ^ -meta.sexp


  (
   defmethod
;  ^^^^^^^^^ keyword.declaration.function.clojure
   dont-declare-multi-fn
;  ^^^^^^^^^^^^^^^^^^^^^ entity.name.function.clojure
  [])

  (do
    (defmethod ^:foo print-method Foo
      ;; comment
;     ^^^^^^^^^^ comment.line.edn
      ^:baz [bar out]
;     ^ keyword.operator.macro.clojure
;      ^^^^ constant.other.keyword.unqualified.edn
      (print-method (.toString bar) out)))
;                                       ^^ punctuation.section.parens.end.edn - invalid
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                         ^ -meta.sexp.list.edn

  (defmethod event-handler :default
    #?@(:clj  [[{:keys [event uid]}]
;   ^^^ keyword.operator.macro.clojure
;       ^^^^ constant.other.keyword.unqualified.edn
;; Not sure how to retain the meta.function.parameters.clojure scope in this case...
               (debugf "Unhandled event %s in session %s" event uid)]
        :cljs [[{:keys [event]}]
               (debugf "Unhandled event %s" event)]))
;                                                   ^ punctuation.section.parens.end.edn - invalid
;  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                                    ^ -meta.sexp.list.edn

  (defmethod event-handler)
;                         ^ punctuation.section.parens.end.edn - invalid
;                          ^ -meta.sexp

  (defmethod event-handler :)
;                           ^ punctuation.section.parens.end.edn - invalid
;                            ^ -meta.sexp

  (#_defmethod #_event-handler #_:foo #_[bar] #_baz)
;  ^^^^^^^^^^^ comment.discard.edn
;              ^^^^^^^^^^^^^^^ comment.discard.edn
;                              ^^^^^^ comment.discard.edn
;                                     ^^^^^^^ comment.discard.edn
;                                             ^^^^^ comment.discard.edn
;                                                   ^ -meta.sexp

  (defmethod)
;           ^ punctuation.section.parens.end.edn - invalid
; ^^^^^^^^^^^ meta.sexp.list.edn
;            ^ -meta.sexp

; # defprotocol

  (defprotocol)
; ^ punctuation.section.parens.begin.edn
; ^^^^^^^^^^^^^ meta.sexp.list.edn
;             ^ punctuation.section.parens.end.edn
;              ^ -meta.sexp.list.edn

  (defprotocol DeclareProtocol)
;  ^^^^^^^^^^^ storage.type.interface.clojure
;              ^^^^^^^^^^^^^^^ entity.name.type.clojure
; ^ punctuation.section.parens.begin.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                             ^ punctuation.section.parens.end.edn - invalid
;                              ^ -meta.sexp.list.edn


  (defprotocol ^:private DeclareProtocol)
;  ^^^^^^^^^^^ storage.type.interface.clojure
;              ^ keyword.operator.macro.clojure
;               ^^^^^^^^ constant.other.keyword.unqualified.edn
;                        ^^^^^^^^^^^^^^^ entity.name.type.clojure

  (defprotocol ^:private ^:blah DeclareProtocol)
;  ^^^^^^^^^^^ storage.type.interface.clojure
;              ^ keyword.operator.macro.clojure
;               ^^^^^^^^ constant.other.keyword.unqualified.edn
;                        ^ keyword.operator.macro.clojure
;                         ^^^^^ constant.other.keyword.unqualified.edn
;                               ^^^^^^^^^^^^^^^ entity.name.type.clojure

  (
   ; ---
;  ^ comment.line.edn punctuation.definition.comment
   defprotocol
;  ^^^^^^^^^^^ storage.type.interface.clojure
   ; ---
;  ^ comment.line.edn punctuation.definition.comment
   ^:private
;  ^ keyword.operator.macro.clojure
;   ^^^^^^^^ constant.other.keyword.unqualified.edn
   ; ---
;  ^ comment.line.edn punctuation.definition.comment
   DeclareProtocol
;  ^^^^^^^^^^^^^^^ entity.name.type.clojure
   ; ---
;  ^ comment.line.edn punctuation.definition.comment
   "docstring"
;  ^ string.quoted.double.edn punctuation.definition.string.begin.edn
  )

  ; Invalid but take care anyway
  (defprotocol DeclareProtocol dont-declare)
; ^ punctuation.section.parens.begin.edn
;  ^^^^^^^^^^^ storage.type.interface.clojure
;              ^^^^^^^^^^^^^^^ entity.name.type.clojure
;                             ^^^^^^^^^^^^^- storage
;                             ^^^^^^^^^^^^^- entity
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                           ^ -meta.sexp

  ; Protocol methods are added to the namespace as functions
  (defprotocol ^:private DeclareProtocol
    ; ---
    (declare-protocol-method [_] [sadas] dont-declare)
;    ^^^^^^^^^^^^^^^^^^^^^^^ entity.name.function.clojure
;                               ^^^^^^^^^^^^^^^^^^^^^ - storage
;                               ^^^^^^^^^^^^^^^^^^^^^ - entity
;                                                    ^ punctuation.section.parens.end.edn
;   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                            ^^^ meta.sexp.list.edn meta.sexp.list.edn meta.sexp.vector.edn
;                                ^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn meta.sexp.vector.edn
    ; ---
    (^File declare-protocol-method [_] dont-declare))
;    ^ keyword.operator.macro.clojure
;     ^^^^^- storage
;     ^^^^^- entity
;     ^^^^^- variable.function
;          ^^^^^^^^^^^^^^^^^^^^^^^ entity.name.function.clojure
;                                     ^^^^^^^^^^^^^- storage
;                                     ^^^^^^^^^^^^^- entity
;                                                   ^ punctuation.section.parens.end.edn
;                                                    ^ -meta.sexp

  ; Invalid but take care anyway
  (defprotocol DeclareProtocol
    (declare-protocol-method dont-declare [_]))
;    ^^^^^^^^^^^^^^^^^^^^^^^ entity.name.function.clojure
;                           ^^^^^^^^^^^^^^- storage
;                           ^^^^^^^^^^^^^^- entity

  (defprotocol Showable ())
; ^ punctuation.section.parens.begin.edn
;                       ^ punctuation.section.parens.begin.edn
;                        ^ punctuation.section.parens.end.edn
;                       ^^ meta.sexp.list.edn meta.sexp.list.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                          ^ -meta.sexp

  (defprotocol Foo (bar [baz {:keys [quux]}]))
;                        ^^^ meta.symbol.edn
;                           ^ -meta.symbol
;                             ^^^^^ constant.other.keyword
;                                  ^ -constant.other.keyword
;                                           ^ -meta.function.parameters


; # definterface

  (definterface DeclareInterface)
;  ^^^^^^^^^^^^ storage.type.interface.clojure
;               ^^^^^^^^^^^^^^^^ entity.name.type.clojure

  (definterface ^:private DeclareInterface)
;  ^^^^^^^^^^^^ storage.type.interface.clojure
;               ^ keyword.operator.macro.clojure
;                ^^^^^^^^ constant.other.keyword.unqualified.edn
;                         ^^^^^^^^^^^^^^^^ entity.name.type.clojure

  (
   definterface
;  ^^^^^^^^^^^^ storage.type.interface.clojure
   ^:private
;  ^ keyword.operator.macro.clojure
   DeclareInterface
;  ^^^^^^^^^^^^^^^^ entity.name.type.clojure
   "docstring"
;  ^^^^^^^^^^^ string.quoted.double.edn
  )

  ; Interface methods should have the same visual style as other function
  ; and method declarations, but shouldn't be added to the symbol index,
  ; since they're not added to the namespace as functions
  (definterface DeclareInterface
    (declare-noindex [_] "foo")
;    ^^^^^^^^^^^^^^^ entity.name.function.clojure
;                        ^^^^^ string.quoted.double.edn
    (declare-noindex [_]))
;    ^^^^^^^^^^^^^^^ entity.name.function.clojure

  ; Invalid but take care anyway
  (definterface DeclareInterface dont-declare)
; ^ punctuation.section.parens.begin.edn
;  ^^^^^^^^^^^^ storage.type.interface.clojure
;               ^^^^^^^^^^^^^^^^ entity.name.type.clojure
;                               ^^^^^^^^^^^^^- storage
;                               ^^^^^^^^^^^^^- entity

; # deftype

  (deftype DeclareType [])
;  ^^^^^^^ storage.type.class.clojure
;          ^^^^^^^^^^^ entity.name.type.clojure
;                      ^ punctuation.section.brackets.begin.edn
;                       ^ punctuation.section.brackets.end.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                         ^ -meta.sexp

  (deftype-custom DeclareWithCustomDeftype)
;  ^^^^^^^^^^^^^^ - storage.type.class.clojure
;                 ^^^^^^^^^^^^^^^^^^^^^^^^ - entity.name.type.clojure

  (deftype ^:private DeclareType [])
;  ^^^^^^^ storage.type.class.clojure
;          ^ keyword.operator.macro.clojure
;           ^^^^^^^^ constant.other.keyword.unqualified.edn
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
;   ^^^^^ constant.other.keyword.unqualified.edn
   ; ---
   DeclareType
;  ^^^^^^^^^^^ entity.name.type.clojure
   ; ---
   [])

  ; Similarly to definterface, type methods should have the standard visual
  ; style of function declarations, but not added to the symbol index,
  ; since they're not added to the namespace.
  (deftype DeclareType [foo]
  ;                    ^ meta.function.parameters.clojure punctuation.section.brackets.begin.edn
  ;                     ^^^ meta.reader-form.edn meta.symbol.edn
  ;                        ^ meta.function.parameters.clojure punctuation.section.brackets.end.edn
    Foo
    (bar ^:quux [_])
  ;  ^^^ entity.name.function.clojure
  ;      ^ keyword.operator.macro.clojure
  ;       ^^^^^ constant.other.keyword.unqualified.edn
    Bar
    (^void baz [_]))
;    ^ keyword.operator.macro.clojure
;     ^^^^ meta.symbol.edn
;         ^ -meta.symbol
;          ^^^ entity.name.function.clojure

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
;                   ^ punctuation.section.brackets.begin.edn
;                    ^ keyword.operator.macro.clojure
;                               ^^^^^^^^^^^^^^^^^^^^^^^ constant.other.keyword.unqualified.edn
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
;                                     ^ punctuation.section.parens.end.edn

(defn new-growing-map
  ([make] (new-growing-map make nil))
  ([make init] {:pre [(ifn? make) (or (nil? init) (map? init))]}
   (new GrowingMap make init)))

 (deftype #_Foo #_[bar] #_(baz [quux]))
;         ^^^^^ comment.block.edn comment.discard.edn
;               ^^^^^^^ comment.block.edn comment.discard.edn
;                       ^^^^^^^^^^^^^^ comment.block.edn comment.discard.edn
;                                     ^ punctuation.section.parens.end.edn


; # defrecord

  (defrecord DeclareRecord)
;  ^^^^^^^^^ storage.type.class.clojure
;            ^^^^^^^^^^^^^ entity.name.type.clojure

  (defrecord-custom DeclareWithCustomDefrecord)
;  ^^^^^^^^^^^^^^^^ - storage.type.class.clojure
;                   ^^^^^^^^^^^^^^^^^^^^^^^^^^ - entity.name.type.clojure

  (defrecord ^:private DeclareRecord [_])
;  ^^^^^^^^^ storage.type.class.clojure
;            ^ keyword.operator.macro.clojure
;             ^^^^^^^^ constant.other.keyword.unqualified.edn
;                      ^^^^^^^^^^^^^ entity.name.type.clojure
;                                    ^ punctuation.section.brackets.begin.edn
;                                     ^ meta.function.parameters.clojure
;                                      ^ punctuation.section.brackets.end.edn
;                                       ^ punctuation.section.parens.end.edn
;                                    ^^^ meta.sexp.vector.edn
;                                       ^ -meta.sexp.vector.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                        ^ -meta.sexp.list.edn

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
;  ^^ meta.sexp.list.edn meta.sexp.vector.edn meta.function.parameters.clojure
;     ^ -meta.sexp

  ; Same reasoning as for definterface and deftype
  (defrecord DeclareRecord [fields]
;                          ^^^^^^^^ meta.function.parameters.clojure
    Foo
    (bar ^:baz [_])
;    ^^^ entity.name.function.clojure
;        ^ keyword.operator.macro.clojure
;         ^^^^ constant.other.keyword.unqualified.edn
;              ^^^ meta.sexp.list.edn meta.sexp.list.edn meta.sexp.vector.edn
;   ^^^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
    Quux
    (zot [_]))
;    ^^^ entity.name.function.clojure
;        ^^^ meta.sexp.list.edn meta.sexp.list.edn meta.sexp.vector.edn
;   ^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
; ^^^^^^^^^^^^ meta.sexp.list.edn

  ; Scope the implemented protocols/interfaces
  (defrecord DeclareRecord [fields]
;  ^^^^^^^^^ storage.type.class.clojure
;            ^^^^^^^^^^^^^ entity.name.type.clojure
    package.ImplementedInterface
;   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
    (declare-noindex [_])
;    ^^^^^^^^^^^^^^^ entity.name.function.clojure
;                    ^^^ meta.sexp.list.edn meta.sexp.list.edn meta.sexp.vector.edn
;   ^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
    namespace/ImplementedProtocol
;   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
    (declare-noindex [_]))
;    ^^^^^^^^^^^^^^^ entity.name.function.clojure
;                    ^^^ meta.sexp.list.edn meta.sexp.list.edn meta.sexp.vector.edn
;   ^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
;                         ^ -meta.sexp



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
;                                                                               ^ -meta.sexp



; # reify

  (reify clojure.lang.IDeref (deref))
;                            ^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                    ^ -meta.sexp


  (reify clojure.lang.IDeref (deref [_] nil))
;                                   ^^^ meta.sexp.list.edn meta.sexp.list.edn meta.sexp.vector.edn
;                            ^^^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                            ^ -meta.sexp

  (reify
;  ^^^^^ meta.function-call.clojure variable.function.clojure
    clojure.lang.IDeref
;   ^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
    (deref [_] nil)
;    ^^^^^ entity.name.function.clojure
;              ^^^ constant.language.edn
;   ^^^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
    clojure.lang.Seqable
;   ^^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
    (seq [_] nil))
;    ^^^ entity.name.function.clojure
;            ^^^ constant.language.edn
;   ^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
; ^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                 ^ -meta.sexp

  (do
    (reify Foo
      (bar [{:keys [baz quux]}] ,,,))
;            ^^^^^ constant.other.keyword.unqualified.edn
;                  ^ meta.function.parameters.clojure punctuation.section.brackets.begin.edn
;                           ^ meta.function.parameters.clojure punctuation.section.brackets.end.edn
;                            ^ meta.function.parameters.clojure punctuation.section.braces.end.edn
;                                   ^ punctuation.section.parens.end.edn - invalid

    (println "Hello, world!"))
;            ^^^^^^^^^^^^^^^ string.quoted.double.edn
;                            ^ punctuation.section.parens.end.edn - invalid

; # proxy

  (proxy)
; ^^^^^^^ meta.sexp.list.edn
;        ^ -meta.sexp

  (proxy [])
; ^ punctuation.section.parens.begin.edn
;        ^^ meta.sexp.list.edn meta.sexp.vector.edn
; ^^^^^^^^^^ meta.sexp.list.edn
;          ^ punctuation.section.parens.end.edn
;           ^ -meta.sexp

  (proxy [] [])
; ^ punctuation.section.parens.begin.edn
;        ^^ meta.sexp.list.edn meta.sexp.vector.edn
;           ^^ meta.sexp.list.edn meta.sexp.vector.edn
; ^^^^^^^^^^^^^ meta.sexp.list.edn
;             ^ punctuation.section.parens.end.edn
;              ^ -meta.sexp

; invalid, but ought to be pareditable
  (proxy [foo bar] (baz [quux] quux))
; ^ punctuation.section.parens.begin.edn
;        ^ meta.sexp.list.edn meta.sexp.vector.edn punctuation.section.brackets.begin.edn
;                ^ meta.sexp.list.edn meta.sexp.vector.edn punctuation.section.brackets.end.edn
;                       ^^^^^^ meta.sexp.list.edn meta.sexp.list.edn meta.sexp.vector.edn
;                  ^^^^^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                    ^ -meta.sexp

  (proxy [foo bar] [] (baz [quux] quux))
; ^ punctuation.section.parens.begin.edn
;        ^ punctuation.section.brackets.begin.edn
;                ^ punctuation.section.brackets.end.edn
;        ^^^^^^^^^ meta.sexp.vector.edn
;                  ^^ meta.sexp.list.edn meta.sexp.vector.edn meta.function.parameters.clojure
;                    ^ -meta.sexp.vector & -meta.function.parameters
;                     ^ punctuation.section.parens.begin.edn
;                                     ^ punctuation.section.parens.end.edn
;                     ^^^^^^^^^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
;                          ^ punctuation.section.brackets.begin.edn
;                               ^ punctuation.section.brackets.end.edn
;                          ^^^^^^ meta.sexp.list.edn meta.sexp.list.edn meta.sexp.vector.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                       ^ -meta.sexp

  (proxy ^:foo
;  ^^^^^ meta.function-call.clojure variable.function.clojure
;        ^ keyword.operator.macro.clojure
;         ^^^^ constant.other.keyword.unqualified.edn
         [clojure.lang.IDeref
;        ^ punctuation.section.brackets.begin.edn
;         ^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
;         ^^^^^^^^^^^^^^^^^^^^^ - storage
;         ^^^^^^^^^^^^^^^^^^^^^ - variable
          ;; comment
;         ^^^^^^^^^^ comment.line.edn
          clojure.lang.Seqable] [(foo)]
;         ^^^^^^^^^^^^^^^^^^^^ entity.other.inherited-class.clojure
;         ^^^^^^^^^^^^^^^^^^^^ - storage
;         ^^^^^^^^^^^^^^^^^^^^ - variable
;                             ^ punctuation.section.brackets.end.edn
;                               ^ punctuation.section.brackets.begin.edn
;                                ^ punctuation.section.parens.begin.edn
;                                 ^^^ meta.function-call.clojure variable.function.clojure
;                                    ^ punctuation.section.parens.end.edn
    (deref [] nil)
;    ^^^^^ entity.name.function.clojure
;             ^^^ constant.language.edn
    (seq [] nil))
;    ^^^ entity.name.function.clojure
;           ^^^ constant.language.edn
;               ^ punctuation.section.parens.end.edn

  (proxy [java.io.Writer] []
    (write
     ([x] ,,,)
     ([x off len] ,,,)))
;                     ^^ punctuation.section.parens.end.edn - invalid


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
;              ^^^ constant.language.edn

  (extend-protocol #_clojure.lang.IDeref #_String #_(deref [this] ,,,))
;                  ^^^^^^^^^^^^^^^^^^^^^ comment.discard.edn
;                                        ^^^^^^^^ comment.discard.edn
;                                                 ^^^^^^^^ comment.discard.edn

  (extend-protocol Foo ^:foo nil)
;                      ^ keyword.operator.macro.clojure
;                       ^ punctuation.definition.keyword.edn
;                       ^^^^ constant.other.keyword.unqualified.edn
;                           ^ -constant.other.keyword
;                            ^^^ constant.language.edn


  (extend-protocol Foo #?)
;                      ^^ keyword.operator.macro
;                        ^ punctuation.section.parens.end.edn

  (extend-protocol Foo
    #?(:clj Bar :cljs Baz)
;   ^^ keyword.operator.macro
;     ^ punctuation.section.parens.begin
;      ^ constant.other.keyword.unqualified punctuation.definition.keyword
;       ^^^ constant.other.keyword.unqualified
;          ^ -constant.other.keyword
;           ^^^ entity.other.inherited-class.clojure meta.reader-form
;               ^ constant.other.keyword.unqualified punctuation.definition.keyword
;                ^^^^ constant.other.keyword.unqualified
;                    ^ -constant.other.keyword
;                     ^^^ entity.other.inherited-class.clojure meta.reader-form
;                        ^ punctuation.section.parens.end.edn
    (quux [this] ,,,))

  (extend-protocol Foo
    ; one
;   ^^^^^^ comment.line.edn
    #?(; two
;      ^^^^^ comment.line.edn
       :clj ^:m Bar :cljs Baz
       ; three
;      ^^^^^^^ comment.line.edn
       )
    ; four
;   ^^^^^^ comment.line.edn
    ,,,)

  (extend-protocol Foo #?(nil))
;                         ^^^ constant.language.edn

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
;                  ^^^ constant.language.edn



; # ns

  (ns foo.bar)
; ^ punctuation.section.parens.begin.edn
;  ^^ keyword.declaration.namespace.clojure
;     ^^^^^^^ entity.name.namespace.clojure
;            ^ punctuation.section.parens.end.edn
; ^^^^^^^^^^^^ meta.sexp.list.edn
;             ^ -meta.sexp.list.edn

  (ns ^:baz foo.bar)
; ^ punctuation.section.parens.begin.edn
;     ^^^^^ - entity.name.namespace.clojure
;     ^ keyword.operator.macro.clojure
;      ^^^^ constant.other.keyword.unqualified.edn
;           ^^^^^^^ entity.name.namespace.clojure
;                  ^ punctuation.section.parens.end.edn
; ^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                   ^ -meta.sexp.list.edn

  (ns ^{:baz true} foo.bar)
; ^ punctuation.section.parens.begin.edn
;     ^ keyword.operator.macro.clojure
;       ^^^^ constant.other.keyword.unqualified.edn
;            ^^^^ constant.language.edn
;                  ^^^^^^^ entity.name.namespace.clojure
;                         ^ punctuation.section.parens.end.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;      ^^^^^^^^^^^ meta.sexp.map.edn
;                          ^ -meta.sexp.list.edn

  (ns ^{:config '{:some-keyword some-symbol}} foo.bar)
; ^ punctuation.section.parens.begin.edn
;     ^ keyword.operator.macro.clojure
;       ^^^^^^^ constant.other.keyword.unqualified.edn
;               ^ keyword.operator.macro.clojure
;                               ^^^^^^^^^^^ meta.symbol.edn
;                                             ^^^^^^^ entity.name.namespace.clojure
;                                                    ^ punctuation.section.parens.end.edn
;                                                     ^ -meta.sexp.list.edn
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.map.edn
;                ^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.map.edn meta.sexp.map.edn

  (ns foo.bar "baz")
;             ^^^^^ string.quoted.double.edn

  (ns foo.bar
    (:require
;    ^ punctuation.definition.keyword.clojure
;    ^^^^^^^^ meta.statement.require.clojure
     [baz.quux]
     qux.zot
;    ^^^^^^^ meta.symbol.edn - variable.function.clojure
     ))

  (ns foo.bar
    (:import
;    ^ punctuation.definition.keyword.clojure
;    ^^^^^^^ meta.statement.import.clojure
     (java.time LocalDate)))
;    ^ punctuation.section.parens.begin.edn
;     ^^^^^^^^^ - meta.function-call.clojure
;     ^^^^^^^^^ - variable.function.clojure
;                        ^ punctuation.section.parens.end.edn
  (ns foo.bar
    (:require
;    ^^^^^^^ meta.statement.require.clojure
     (foo.bar :as [foo])))
;    ^ punctuation.section.parens.begin.edn
;     ^^^^^^^ - meta.function-call.clojure
;     ^^^^^^^ - variable.function.clojure
;             ^ punctuation.definition.keyword.edn
;             ^^^ constant.other.keyword.unqualified.edn
;                      ^ punctuation.section.parens.end.edn

  (ns foo.bar (:import :require))
;              ^^^^^^^ meta.statement.import.clojure
;                      ^^^^^^^^ - meta.statement.require.clojure

  (ns foo.bar (:requires [baz.quux]))
;              ^^^^^^^^^ - meta.statement.require.clojure


  (ns foo.bar
    (:require
     #_[baz.quux :as qux]))
;    ^^^^^^^^^^^^^^^^^^^^ comment.block.edn comment.discard.edn

  (ns foo.bar
    (:import
     #_(baz.quux Qux)))
;    ^^^^^^^^^^^^^^^^ comment.block.edn comment.discard.edn

  (ns foo.bar
    (:refer-clojure :exclude [map]))
 ;                  ^^^^^^^^ constant.other.keyword.unqualified.edn
 ;   ^ punctuation.definition.keyword.clojure

  (ns foo.bar {:no-doc true} (:require [baz.quux :as qux]))
;             ^ meta.sexp.map.edn punctuation.section.braces.begin.edn
;              ^^^^^^^ constant.other.keyword.unqualified.edn
;                            ^ punctuation.section.parens.begin.edn
;                             ^ constant.other.keyword.unqualified.clojure punctuation.definition.keyword.clojure

(ns foo.bar #?(:clj (:require [baz.quux :as qux]) :bb (:require [baz2.quux2 :as qux2])))
;           ^^ keyword.operator.macro
;             ^ punctuation.section.parens.begin.edn
;              ^ constant.other.keyword.unqualified.edn punctuation.definition.keyword.edn


; # in-ns

  (in-ns)
;  ^^^^^ meta.reader-form.clojure meta.symbol.clojure keyword.declaration.namespace.clojure
;       ^ punctuation.section.parens.end.edn
; ^^^^^^^ meta.sexp.list.edn
;        ^ -meta.sexp

  (in-ns 'foo.bar)
;  ^^^^^ meta.reader-form.clojure meta.symbol.clojure keyword.declaration.namespace.clojure
;       ^ - meta.reader-form & -keyword
;        ^ keyword.operator.macro.clojure
;         ^^^^^^^ meta.reader-form.clojure meta.symbol.clojure entity.name.namespace.clojure
;                ^ punctuation.section.parens.end.edn
; ^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                 ^ -meta.sexp


; # deftest

  (deftest)
; ^^^^^^^^^ meta.sexp.list.edn
;          ^ -meta.sexp

  (deftest foo (is (= 3 (+ 1 2))))
;  ^^^^^^^ keyword.declaration.function.clojure
;          ^^^ meta.test-var.clojure
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                 ^ -meta.sexp.list.edn

  (test/deftest ^:slow foo)
;  ^^^^^^^^^^^^ keyword.declaration.function.clojure
;                      ^^^ meta.test-var.clojure
; ^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                          ^ -meta.sexp.list.edn



; # Qualified symbols

  foo.bar/
; ^^^^^^^ meta.namespace.edn
;        ^ punctuation.accessor.edn

  foo.bar/baz
; ^^^^^^^ meta.namespace.edn
;        ^ punctuation.accessor.edn
;        ^^^^ - meta.namespace.edn



; # Map namespace syntax

  #::foo
; ^ keyword.operator.macro.clojure
;  ^^ punctuation.definition.keyword.clojure - meta.namespace
;    ^^^ meta.namespace.clojure
;  ^^^^^ constant.other.keyword.auto-qualified.clojure

  #::foo{}
; ^ keyword.operator.macro.clojure
;  ^^ punctuation.definition.keyword.clojure - meta.namespace
;    ^^^ meta.namespace.clojure
;  ^^^^^ constant.other.keyword.auto-qualified.clojure
;       ^ punctuation.section.braces.begin.edn - constant
;        ^ punctuation.section.braces.end.edn - constant

  #::foo {}
; ^ keyword.operator.macro.clojure
;  ^^ punctuation.definition.keyword.clojure - meta.namespace
;    ^^^ meta.namespace.clojure
;  ^^^^^ constant.other.keyword.auto-qualified.clojure
;       ^ - meta.namespace
;        ^ punctuation.section.braces.begin.edn - constant
;         ^ punctuation.section.braces.end.edn - constant

  #::foo/{}
; ^ keyword.operator.macro.clojure
;  ^^ punctuation.definition.keyword.clojure - meta.namespace
;    ^^^ meta.namespace.clojure
;  ^^^^^ constant.other.keyword.auto-qualified.clojure
;       ^ invalid.illegal.edn
;        ^ punctuation.section.braces.begin.edn - illegal
;         ^ punctuation.section.braces.end.edn - illegal

  #::foo/bar{}
; ^ keyword.operator.macro.clojure
;  ^^ punctuation.definition.keyword.clojure - meta.namespace
;    ^^^ meta.namespace.clojure
;  ^^^^^ constant.other.keyword.auto-qualified.clojure
;       ^^^^ invalid.illegal.edn
;           ^ punctuation.section.braces.begin.edn - illegal
;            ^ punctuation.section.braces.end.edn - illegal



; # Tagged literals

 (foo #bar/baz [1 2 3] [4 5 6])
;     ^^^^^^^^ keyword.operator.macro.edn
;         ^ punctuation.definition.symbol.namespace.edn
;                     ^ - meta.reader-form.edn



; # Quoted

  '100
; ^ keyword.operator.macro.clojure

  ' foo
; ^ keyword.operator.macro.clojure

  '(1 2 3)
; ^ keyword.operator.macro.clojure

  `foo
; ^ keyword.operator.macro.clojure
;  ^^^ meta.symbol.edn - keyword

  ~foo
; ^ keyword.operator.macro.clojure
;  ^^^ meta.symbol.edn - keyword

  `(foo ~bar)
; ^ keyword.operator.macro.clojure
;   ^^^ meta.function-call.clojure variable.function.clojure
;       ^ keyword.operator.macro.clojure
;        ^^^ meta.symbol.edn - keyword

  ~@foo ~[1 2 3]
; ^^ keyword.operator.macro.clojure
;   ^^^ meta.symbol.edn - keyword
;       ^ keyword.operator.macro.clojure
;        ^ punctuation.section.brackets.begin.edn
;              ^ punctuation.section.brackets.end.edn

  #'foo.bar/baz
; ^^ keyword.operator.macro.clojure
;          ^ punctuation.accessor.edn


; # Reader conditionals

  #?(:clj (def x 1))
; ^^ keyword.operator.macro
;   ^ punctuation.section.parens.begin.edn
;    ^^^^ constant.other.keyword.unqualified.edn
;         ^^^^^^^^^ meta.sexp.list.edn meta.sexp.list.edn
;   ^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                   ^ -meta.sexp

(defn excluded?
  #?(:cljs {:tag boolean})
; ^^ keyword.operator.macro
;   ^ punctuation.section.parens.begin.edn
;    ^^^^^ constant.other.keyword.unqualified.edn
;          ^ punctuation.section.braces.begin.edn
;           ^^^^ constant.other.keyword.unqualified.edn
;                ^^^^^^^ meta.symbol.edn
;                       ^ punctuation.section.braces.end.edn
;                        ^ punctuation.section.parens.end.edn
  [env sym]
; ^^^^^^^^^ meta.function.parameters.clojure
  ,,,)



; # S-expression prefixes

  #(inc 1)
; ^ keyword.operator.macro

  @(atom foo)
; ^ keyword.operator.macro

  #{1 2 3}
; ^ keyword.operator.macro

  #_(1 2 3)
; ^ keyword.operator.macro
;  ^ punctuation.definition.comment.edn
; ^^^^^^^^ comment.discard.edn

  #?@(:default (+ 1 2 3))
; ^^^ keyword.operator.macro


; # Reader forms

; ## Symbols

  a b
; ^ meta.reader-form.edn
;  ^ - meta
;   ^ meta.reader-form.edn

; ## Strings

  "a" "b"
; ^^^ meta.reader-form.edn
;    ^ - meta
;     ^^^ meta.reader-form.edn

; ## Numbers

  123 123N 1/2 1.2 1.2M +0x1234af -2r1010 +1234.1234E10M ##-Inf
; ^^^ meta.reader-form.edn
;    ^ - meta
;     ^^^^ meta.reader-form.edn
;         ^ - meta
;          ^^^ meta.reader-form.edn
;                 ^ - meta
;                  ^^^^ meta.reader-form.edn
;                      ^ - meta
;                       ^^^^^^^^^ meta.reader-form.edn
;                                ^ - meta
;                                 ^^^^^^^ meta.reader-form.edn
;                                        ^ - meta
;                                         ^^^^^^^^^^^^^^ meta.reader-form.edn
;                                                       ^ - meta
;                                                        ^^^^^^ meta.reader-form.edn

; ## Keywords

  :foo :foo/bar ::foo ::foo/bar
; ^^^^ meta.reader-form.edn
;     ^ - meta
;      ^^^^^^^^ meta.reader-form.edn
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
; ^^^^^^^^ meta.reader-form.edn
;         ^ - meta
;          ^^^^^^ meta.reader-form.edn

  @foo @bar
; ^ keyword.operator.macro.clojure
;  ^^^ meta.reader-form.edn
;     ^ - meta
;      ^ keyword.operator.macro.clojure
;       ^^^ meta.reader-form.edn



; ## Dispatch macro

  #"\s" #"[1-9]"
; ^^^^^ meta.reader-form.edn
;      ^ - meta
;       ^^^^^^^^ meta.reader-form.edn

  #inst "2018-03-28T10:48:00.000" #uuid "3b8a31ed-fd89-4f1b-a00f-42e3d60cf5ce"
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.tagged-element.edn
;                                ^ - meta
;                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.tagged-element.edn

  #foo/bar {:a {:b [:c]}} [1 2 3]
; ^^^^^^^^ keyword.operator.macro.edn
; ^^^^^^^^ meta.tagged-element.tag.edn
;         ^ -meta.tagged-element.tag
;          ^^^^^^^^^^^^^^ meta.tagged-element.element.edn
; ^^^^^^^^^^^^^^^^^^^^^^^ meta.tagged-element.edn
;                        ^ -meta



; # S-expressions

  (+ 1 2) (- 3 4)
; ^ punctuation.section.parens.begin.edn
;       ^ punctuation.section.parens.end.edn
;        ^ - meta

  '(1 2) '(3 4)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.edn
;      ^ punctuation.section.parens.end.edn
;       ^ - meta
;        ^ keyword.operator.macro.clojure

  [1 2] [3 4]
; ^ punctuation.section.brackets.begin.edn
;     ^ punctuation.section.brackets.end.edn
;      ^ - meta

  {:a 1} {:b 2}
; ^ punctuation.section.braces.begin.edn
;      ^ punctuation.section.braces.end.edn
;       ^ - meta

  #{1 2} #{3 4}
; ^ keyword.operator.macro.edn
;  ^ punctuation.section.braces.begin.edn
;      ^ punctuation.section.braces.end.edn
;       ^ - meta

  #_(1 2) (3 4)
; ^ keyword.operator.macro.edn
;  ^ punctuation.definition.comment.edn
;   ^ punctuation.section.parens.begin.edn
;       ^ punctuation.section.parens.end.edn
;        ^ - meta
; ^^^^^^^ comment.discard.edn
;         ^^^^^ - comment.discard.edn


; # Special forms

  (. System (getProperties))
;  ^ meta.special-form.clojure keyword.other.clojure
; ^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                           ^ -meta.sexp

  (new java.util.HashMap)
;  ^^^ meta.special-form.clojure keyword.other.clojure
; ^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                        ^ -meta.sexp

  (set! *warn-on-reflection* true)
;  ^^^^ meta.special-form.clojure keyword.other.clojure
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                 ^ -meta.sexp

  (def x 1)
;  ^^^ meta.special-form.clojure keyword.declaration.variable.clojure
; ^^^^^^^^^ meta.sexp.list.edn
;          ^ -meta.sexp

  (if test then else)
;  ^^ meta.special-form.clojure keyword.control.conditional.if.clojure
; ^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                    ^ -meta.sexp

  (do expr*)
;  ^^ meta.special-form.clojure keyword.other.clojure
; ^^^^^^^^^^ meta.sexp.list.edn
;           ^ -meta.sexp

  (let [x 1] [x x])
;  ^^^ meta.special-form.clojure keyword.declaration.variable.clojure
;      ^^^^^ meta.binding-vector.clojure
;            ^^^^^ - meta.binding-vector.clojure
;  ^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                  ^ -meta.sexp

  [(let)]
;       ^ punctuation.section.brackets.end.edn - invalid
;  ^^^^^ meta.sexp.vector.edn meta.sexp.list.edn
; ^^^^^^^ meta.sexp.vector.edn
;        ^ -meta.sexp

  (quote form)
;  ^^^^^ meta.special-form.clojure keyword.other.clojure
;  ^^^^^^^^^^^ meta.sexp.list.edn
;             ^ -meta.sexp

  (var symbol)
;  ^^^ meta.special-form.clojure keyword.other.clojure
; ^^^^^^^^^^^^ meta.sexp.list.edn
;             ^ -meta.sexp

  (fn name? [x 1] expr*)
;  ^^ meta.special-form.clojure keyword.declaration.function.inline.clojure
; ^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                       ^ -meta.sexp

  (loop [x 1]
;  ^^^^ meta.special-form.clojure keyword.control.loop.clojure
    (recur (inc x)))
;    ^^^^^ meta.special-form.clojure keyword.control.flow.recur.clojure
; ^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                   ^ -meta.sexp

  (throw (ex-info "Boom!" {:foo :bar}))
;  ^^^^^ meta.special-form.clojure keyword.control.flow.throw.clojure
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                      ^ -meta.sexp

  (try ,,, (catch Exception _ ,,,) (finally ,,,))
;  ^^^ meta.special-form.clojure keyword.control.exception.try.clojure
;           ^^^^^ keyword.control.exception.catch.clojure
;                                   ^^^^^^^ keyword.control.exception.finally.clojure
; ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                                ^ -meta.sexp

  (monitor-enter expr) (monitor-exit expr)
;  ^^^^^^^^^^^^^ meta.special-form.clojure keyword.other.clojure
;                       ^^^^^^^^^^^^ meta.special-form.clojure keyword.other.clojure
; ^^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                     ^ -meta.sexp
;                      ^^^^^^^^^^^^^^^^^^^ meta.sexp.list.edn
;                                         ^ -meta.sexp



; # Destructuring

  (defn foo
    [[x y & xs :as bar] ys]
;   ^^^^^^^^^^^^^^^^^^^^^^^ meta.function.parameters.clojure
;              ^^^ constant.other.keyword.unqualified.edn
    ,,,)

  (defn configure
    [val & {:keys [debug verbose] :or {debug false, verbose false}}]
;   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.function.parameters.clojure
;           ^^^^^ constant.other.keyword.unqualified.edn
;                                 ^^^ constant.other.keyword.unqualified.edn
;                  ^^^^^ meta.symbol.edn
;                                            ^^^^^ constant.language.edn
;                                                 ^ comment.punctuation.comma.edn
    ,,,)

  (fn foo
    [[x y & xs :as bar] ys]
;   ^^^^^^^^^^^^^^^^^^^^^^^ meta.function.parameters.clojure
;                         ^ - invalid.illegal.stray-bracket-end.edn
;              ^^^ constant.other.keyword.unqualified.edn
    ,,,)

    (fn configure
      [val & {:keys [debug verbose] :or {debug false, verbose false}}]
  ;   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.function.parameters.clojure
  ;           ^^^^^ constant.other.keyword.unqualified.edn
  ;                                 ^^^ constant.other.keyword.unqualified.edn
  ;                  ^^^^^ meta.symbol.edn
  ;                                            ^^^^^ constant.language.edn
  ;                                                 ^ comment.punctuation.comma.edn
      ,,,)

  (foo (fn bar [{:keys [db]} _]))
;  ^^^ meta.function-call.clojure variable.function.clojure
;       ^^ meta.special-form.clojure keyword.declaration.function.inline.clojure
;          ^^^ entity.name.function.clojure
;              ^^^^^^^^^^^^^^^^ meta.function.parameters.clojure
;                              ^ punctuation.section.parens.end.edn
;                               ^ punctuation.section.parens.end.edn - invalid.illegal.stray-bracket-edn.edn

  (defn x
    [y]
    (fn [z]))
;           ^ -  invalid.illegal.stray-bracket-end.edn

  (fn
    ()
;    ^ punctuation.section.parens.end.edn
    ([x] ,,,))
;   ^ punctuation.section.parens.begin.edn

  (defn x
    ()
;    ^ punctuation.section.parens.end.edn
    ([y] ,,,))
;   ^ punctuation.section.parens.begin.edn

  (let)
; ^ punctuation.section.parens.begin.edn
;     ^ punctuation.section.parens.end.edn

  (let (foo)) (inc 1)
;      ^ punctuation.section.parens.begin.edn
;       ^^^ meta.function-call.clojure variable.function.clojure
;          ^^ punctuation.section.parens.end.edn
;             ^ punctuation.section.parens.begin.edn
;              ^^^ meta.function-call.clojure variable.function.clojure
;                  ^ constant.numeric.integer.decimal.edn
;                   ^ punctuation.section.parens.end.edn

; ^ -meta.sexp
