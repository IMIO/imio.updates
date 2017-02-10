from setuptools import setup, find_packages
import os

version = '0.1'

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

setup(name='imio.updates',
      version=version,
      description="Helpers to update plone instances",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='',
      author_email='',
      url='https://github.com/imio/imio.updates',
      license='gpl',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=['imio'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'imio.pyutils >= 0.6',
          'ipdb',
      ],
      dependency_links=[
#          'git://github.com/IMIO/imio.pyutils.git#egg=imio.pyutils'
          'https://github.com/IMIO/imio.pyutils/zipball/master#egg=imio.pyutils-0.6'
      ],
      entry_points="""
      [console_scripts]
      update_instances = imio.updates.update_instances:main
      """,
      )
