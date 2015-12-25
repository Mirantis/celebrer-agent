#!/bin/bash

export DEBFULLNAME="Alexey Galkin"
export DEBEMAIL="agalkin@mirantis.com"
export CELEBRER_VERSION=$(cat setup.cfg | grep version | awk {' print $3 '})

apt-get -y update
apt-get -y install build-essential autoconf automake autotools-dev dh-make debhelper devscripts fakeroot xutils lintian pbuilder python-setuptools dh-autoreconf python-pbr

cd ..
mv celebrer-agent celebrer-agent-$CELEBRER_VERSION
cd celebrer-agent-$CELEBRER_VERSION
dh_make -e agalkin@mirantis.com -c apache -s -y --createorig
DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -rfakeroot -us -uc