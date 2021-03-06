import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'pyramid_debugtoolbar',
    'waitress',
    # PyBit and dependencies
    'pybit',
    'psycopg2',
    'amqplib',
    'jsonpickle',
    'bottle'
    ]

setup(name='acmeio',
      version='0.0',
      description='acmeio',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='https://github.com/connexions/acmeio',
      license='AGPL',  # See also LICENSE.txt
      keywords='web pyramid pylons',
      packages=find_packages(exclude=['*.test*']),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=(
                'mock',
                'pika',
                'WebTest',
                ),
      test_suite="acmeio.tests",
      entry_points="""\
      [paste.app_factory]
      main = acmeio:main
      """,
      )
