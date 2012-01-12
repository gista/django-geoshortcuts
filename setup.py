#!/usr/bin/python

from distutils.core import setup

readme = file('README','rb').read()

classifiers = [
	'Development Status :: 4 - Beta',
	'Framework :: Django',
	'Intended Audience :: Developers',
	'Intended Audience :: Science/Research',
	'License :: OSI Approved :: GNU GPL 2 License',
	'Operating System :: OS Independent',
	'Programming Language :: Python',
	'Topic :: Scientific/Engineering :: GIS',
]

setup(
	name='geoshortcuts',
	version='0.1',
	description='set of shortcuts for GeoDjango applications',
	author='Gista s.r.o.',
	author_email='info@gista.sk',
	url='https://github.com/gista/django-geoshortcuts',
	long_description=readme,
	packages=['geoshortcuts',],
	classifiers=classifiers
)
