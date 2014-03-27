from setuptools import setup, find_packages
import os

version = '0.1dev'

long_description = (
    open('README.txt').read()
    + '\n' +
    'Contributors\n'
    '============\n'
    + '\n' +
    open('CONTRIBUTORS.txt').read()
    + '\n' +
    open('CHANGES.txt').read()
    + '\n')

setup(name='simpletrace',
      version=version,
      description="Decorators and function for tracing individual function/method calls, or all methods of a class / functions of a module.",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='Sune Broendum Woeller',
      author_email='sune@woeller.dk',
      url='https://github.com/sunew/simpletrace',
      license='gpl',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
#      namespace_packages=['simpletrace'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
