#!/bin/sh
origname='app'

if [ -z $1 ]; then
    echo 'usage: ./rename_pkg.sh <new_name>'
    exit 1
fi

if [ $1 == $origname ]; then
    echo 'nothing to do'
    exit
fi
newname=$1

git ls-files -X .gitignore -co | grep -v \.md | tr '\n' '\0' | xargs -0 perl -i -pe "s/$origname/$newname/g" 2>/dev/null

mv $origname $newname
mv docs/source/$origname.rst docs/source/$newname.rst
