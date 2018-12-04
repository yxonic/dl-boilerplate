#!/bin/sh
origname='app'
if [ -z $1 ]; then
    echo 'please provide a new name'
    exit 1
fi
newname=$1

find docs/source $origname tests \( ! -name *.pyc \) -type f -exec perl -i -pe "s/$origname/$newname/g" {} +
perl -i -pe "s/$origname/$newname/g" docs/Makefile * .* 2>/dev/null
mv $origname $newname
mv docs/source/$origname.rst docs/source/$newname.rst
