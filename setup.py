import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="conffu",
    packages=['conffu'],
    version="2.0.0",
    license='MIT',
    author="BMT, Jaap van der Velde",
    author_email="jaap.vandervelde@bmtglobal.com",
    description="A simple, but powerful JSON, XML and command line configuration package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/jaapvandervelde/conffu',
    download_url='https://github.com/jaapvandervelde/gohlkegrabber/archive/v0.2.8.tar.gz',
    keywords=['package', 'download', 'gohlke', 'wheel'],
    extras_requires={
        'lxml>=4.6.0': 'xml'
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
