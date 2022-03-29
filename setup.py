import os
import re
from setuptools import setup

__name__ = 'conffu'

version_fn = os.path.join(__name__, "_version.py")
__version__ = "unknown"
try:
    version_line = open(version_fn, "rt").read()
except EnvironmentError:
    pass  # no version file
else:
    version_regex = r"^__version__ = ['\"]([^'\"]*)['\"]"
    m = re.search(version_regex, version_line, re.M)
    if m:
        __version__ = m.group(1)
    else:
        print(f'unable to find version in {version_fn}')
        raise RuntimeError(f'If {version_fn} exists, it is required to be well-formed')

with open("README.md", "r") as rm:
    long_description = rm.read()

setup(
    name=__name__,
    packages=['conffu'],
    version=__version__,
    license='MIT',
    author="BMT, Jaap van der Velde",
    author_email="jaap.vandervelde@bmtglobal.com",
    description="A simple, but powerful JSON, XML and command line configuration package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://gitlab.com/Jaap.vanderVelde/conffu',
    download_url='https://gitlab.com/Jaap.vanderVelde/conffu/repository/archive.zip?ref='+__version__,
    keywords=['package', 'download', 'json', 'configuration', 'CLI', 'parameters'],
    install_requires=[],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.4',
    ],
    extras_require={
        'xml': ['lxml>=4.6.0'],
        'dev': ['mkdocs']
    },
    python_requires='>=3.4',
    include_package_data=False
)
