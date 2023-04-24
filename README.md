pgreport
========

This is an experiment in semi-automating reports of transcription
errors to Project Gutenberg, based on commits to a Standard Ebooks
repository. The output is modeled on the example in [the SE page on reporting
upstream
errors](https://standardebooks.org/contribute/report-errors-upstream). See
also the [PG page on reporting
errata](https://gutenberg.org/help/errata.html).

Installation
------------

```
pipx install git+https://github.com/bensteinberg/pgreport.git
```

Usage
-----

You must have the SE repo in question on your machine; a future
version may be able to use a remote. Find the hash of the commit you
want to report, and run something like

```
pgr --repo path/to/repo --commit 234abcd
```

You can then copy the output, paste it into your email client, and
send it to the appropriate address, found in the links above. You
_must_ confirm that the report is correct.

Notes
-----

This program does not have a mechanism for sending reports directly;
it would be too easy to automate it incorrectly and swamp PG or
someone else with bad error reports.

An open question is what kinds of reports should be sent to PG: OCR
transcription errors, definitely, but what about typos in the original
source? SE says that

> Gutenberg will happily take fixes for spelling, accents, and missing
> or surplus paragraph breaks.

Depending on the outcome of some reports I submit, I may add a feature
for specifying the type of error reported.

This program does not currently have a mechanism for generating error
reports for sources other than PG.
