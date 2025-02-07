from setuptools import setup, find_packages

version = '0.3.dev0'

long_description = (
    open('README.rst').read()
    + '\n' +
    'Contributors\n'
    '============\n'
    + '\n' +
    open('CONTRIBUTORS.txt').read()
    + '\n' +
    open('CHANGES.rst').read()
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
      author='Stéphan Geulette',
      author_email='stephan.geulette@imio.be',
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
          'imio.pyutils >= 1.0.4',
          'six',
      ],
      # python_requires=">=3.10",
      dependency_links=[
#          'git://github.com/IMIO/imio.pyutils.git#egg=imio.pyutils'
          'https://github.com/IMIO/imio.pyutils/zipball/master#egg=imio.pyutils-1.0.4'
      ],
      entry_points={
          'console_scripts': [
              'update_instances = imio.updates.update_instances:main',
          ]
      },
      )
