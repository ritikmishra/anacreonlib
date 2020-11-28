import setuptools
from setuptools import setup

with open("README.md", "r") as f:
    long_desc_contents = f.read()

setup(
    name="anacreonlib",
    version="2.0.0a6",
    description="""This library provides a Python interface to the API of Anacreon 3, which is an online 4X game 
      produced by Kronosaur Productions, LLC.""",
    long_description=long_desc_contents,
    long_description_content_type="text/markdown",
    url="https://github.com/ritikmishra/anacreonlib",
    author="Ritik Mishra",
    author_email="ritik.mishra314@gmail.com",
    license="MIT",
    packages=setuptools.find_packages(),
    install_requires=["uplink[aiohttp]", "pydantic"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        # "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        # "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.8",
    test_suite="tests",
)
