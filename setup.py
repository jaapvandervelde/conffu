import setuptools
from conffu import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="conffu",
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
    extras_require={
        'xml': ['lxml>=4.6.0']
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
    python_requires='>=3.7',
)
