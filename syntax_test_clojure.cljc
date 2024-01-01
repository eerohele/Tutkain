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

  #";,"
;   ^^ string.regexp & -comment

  #"(;,)"
;    ^^ string.regexp & -comment

  #"[;,]"
;    ^^ string.regexp & -comment

  #"\Q ;, \E"
;      ^^ string.regexp & -comment

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
;   ^^^^ -variable.function.clojure

  '(quote blah)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.edn
;   ^^^^^ meta.reader-form meta.symbol

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
;   ^^^^ (meta.reader-form.edn meta.symbol.edn) - variable
;        ^ keyword.operator.macro.clojure
;         ^^^^- keyword.operator.macro.clojure
;  ^^^^^^^^^^^^ meta.sexp.list.edn

  `(blah ~100)
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.edn
;   ^^^^ -variable
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
;   ^^^^ -meta.function-call.clojure
;   ^^^^ -variable.function.clojure
;        ^^ keyword.operator.macro.clojure
;          ^^^^- keyword.operator.macro.clojure

  `(blah ~@[10 20 30])
; ^ keyword.operator.macro.clojure
;  ^ punctuation.section.parens.begin.edn
;   ^^^^ -meta.function-call.clojure
;   ^^^^ -variable.function.clojure
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
;  ^^^^ - variable.function.clojure
;       ^^^^ - variable.function.clojure
;  ^^^^ constant.language.edn

  (false blah :blah)
; ^ punctuation.section.parens.begin.edn
;  ^^^^^ - variable.function.clojure
;        ^^^^ - variable.function.clojure
;  ^^^^^ constant.language.edn

  (nil blah :blah)
; ^ punctuation.section.parens.begin.edn
;  ^^^ - variable.function.clojure
;      ^^^^ - variable.function.clojure
;  ^^^ constant.language.edn

  (10 blah :blah)
; ^ punctuation.section.parens.begin.edn
;     ^^^^ - variable.function.clojure
;  ^^ constant.numeric

  (:blah blah 10)
; ^ punctuation.section.parens.begin.edn
;        ^^^^ - variable.function.clojure
;  ^^^^^ constant.other.keyword.unqualified.edn

  (^:private foo [x] ...)
;  ^ keyword.operator.macro.clojure
;   ^ punctuation.definition.keyword.edn
;   ^^^^^^^^ constant.other.keyword.unqualified.edn
;            ^^^ variable.function.clojure

  (; foo
;  ^ comment.line.edn punctuation.definition.comment.edn
;  ^^^^^^ comment.line.edn
    bar)
;   ^^^ variable.function.clojure

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


(defmacro bound-fn
  [& fntail]
  `(bound-fn* (fn ~@fntail)))
;                 ^^ keyword.operator.macro.clojure
;                   ^^^^^^ meta.reader-form.edn meta.symbol.edn
;                         ^^^ punctuation.section.parens.end.edn

  (def 👽 nil)
;      ^ meta.reader-form meta.symbol

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
;   ^^^ -meta.function-call.clojure
;   ^^^ -variable.function.clojure
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
