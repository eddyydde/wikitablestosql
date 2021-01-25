import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="wikitablestosql",
    version="1.0.0",
    author="Eddy Khalil",
    license='MIT',
    author_email="",
    description="A script to extract all raw wikitables from wikipedia dumps and process them into a sqlite3 database.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': ['wikitablestosql=wikitablestosql.wikitablestosql:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    install_requires=['defusedxml'],
)
