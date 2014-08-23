from setuptools import setup

setup(
    name='irc-toolkit',
    version='0.1.0',
    author='Kyle Fuller',
    author_email='inbox@kylefuller.co.uk',
    packages=['irctk'],
    entry_points={},
    install_requires=['zokket >= 1.2.1'],
    url='https://github.com/kylef/irctk/',
    license='BSD',
    description='A Python IRC client library',
    long_description=open('README.md').read(),
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries',
    ]
)

