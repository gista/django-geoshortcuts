#!/usr/bin/python

from distutils.core import setup

readme = file('README','rb').read()

classifiers = [
	'Development Status :: 4 - Beta',
	'Framework :: Django',
	'Intended Audience :: Developers',
	'Intended Audience :: Science/Research',
	'License :: OSI Approved :: GNU General Public License version 2.0 (GPL-2)',
	'Operating System :: OS Independent',
	'Programming Language :: Python',
	'Topic :: Scientific/Engineering :: GIS',
]

setup(
	name='geoshortcuts',
	version='0.1',
	description='set of shortcuts for GeoDjango applications',
	author='Marcel Dancak, Ivan Mincik, Matus Valo',
	author_email='info@gista.sk',
	url='https://github.com/gista/django-geoshortcuts',
	long_description=readme,
	packages=['geoshortcuts',],
	classifiers=classifiers
)
