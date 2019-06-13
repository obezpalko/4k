#!/bin/sh
for p in *.patch; do
	patch -p0 < $p
done
