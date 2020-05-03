from setuptools import setup

with open('VERSION', 'r') as fp:
    version = fp.read().strip()

setup(
    name='irc-toolkit',
    version=version,
    author='Kyle Fuller',
    author_email='inbox@kylefuller.co.uk',
    packages=['irctk'],
    entry_points={},
    install_requires=[],
    url='https://github.com/kylef/irctk/',
    license='BSD',
    description='A Python IRC client library',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries',
    ]
)

