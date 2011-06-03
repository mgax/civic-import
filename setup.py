from setuptools import setup, find_packages

setup(
    name="civic-import",
    packages=find_packages(),
    install_requires=[
        'sparql-client',
        'rdflib',
        'MySQL-python',
        'Unidecode',
    ],
)
