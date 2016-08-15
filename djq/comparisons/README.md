# Comparisons of `djq`'s mappings
This directory contains some code to compare what `djq` returns
against other tools.  All of the code here is experimental: it works
but it's not particularly sorted out.

## Spreadsheet comparisons
Currently the only comparison is against the spreadsheet which is
provided with the DREQ.  This lives in [`xlsx`](xlsx/).  You will need
to install [openpyxl](https://pypi.python.org/pypi/openpyxl) to use
it.  The script to run is `xlsxcompare.py`: `djqxlsx.py` is a module
which deals with loading results from the spreadsheet and `djq`
itself.  This code explicitly uses `djq.variables.cv_invert_varmip` as
that's the only implementation which makes sense in this context.

If running `xlsxcompare.py` doesn't print `OK` (and return an exit
code of zero) then something is wrong.