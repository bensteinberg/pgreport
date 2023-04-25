pgreport
========

This is an experiment in semi-automating reports of transcription
errors to Project Gutenberg, based on commits to a Standard Ebooks
repository. The default output is modeled on the example in [the SE
page on reporting upstream
errors](https://standardebooks.org/contribute/report-errors-upstream),
but see also the [PG page on reporting
errata](https://gutenberg.org/help/errata.html), which prefers a
somewhat different format; you can select this format with the option
`--style PG`.

Installation
------------

```
pipx install git+https://github.com/bensteinberg/pgreport.git
```

Usage
-----

You must have the SE repo in question on your machine. Find the hash
of the commit you want to report, and run something like

```
pgr --repo path/to/repo --commit 234abcd
```

You can then copy the output, paste it into your email client, and
send it to the appropriate address, found in the links above. You
_must_ confirm that the report is correct. This program does not have
a mechanism for sending reports directly; it would be too easy to
automate it incorrectly and swamp PG or someone else with bad error
reports.

Notes
-----

An open question is what kinds of reports should be sent to PG: OCR
transcription errors, definitely, but what about typos in the original
source? SE says that

> Gutenberg will happily take fixes for spelling, accents, and missing
> or surplus paragraph breaks.

Depending on the outcome of some reports I submit, I may add a feature
for specifying the type of error reported.

This program does not currently have a mechanism for generating error
reports for sources other than PG.

This program already undoes curly quotes for comparison with PG source
text, but may need to undo other typographical changes made for
SE—maybe using SE tooling? Something like the reverse of [typogrify()](https://github.com/standardebooks/tools/blob/6396a5cca8ca4903df2d081cbc8a84a464272c10/se/typography.py#L60-L360).

At the moment, there is one change per report, but a future version
could allow for multiple changes.

A possible enhancement is to try to confirm that the line for the
change is correctly identified in the PG text file by measuring the
Levenshtein distance between the source and correction. This may not
be worth the effort, since each change requires human review in any
case.
