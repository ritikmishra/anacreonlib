import setuptools
from setuptools import setup

with open("README.rst", "r") as f:
    long_desc_contents = f.read()

with open("VERSION", "r") as f:
    version = f.read().strip()

setup(
    name="anacreonlib",
    version=version,
    description="""This library provides a Python interface to the API of Anacreon 3, which is an online 4X game 
      produced by Kronosaur Productions, LLC.""",
    long_description=long_desc_contents,
    long_description_content_type="text/markdown",
    url="https://github.com/ritikmishra/anacreonlib",
    author="Ritik Mishra",
    author_email="ritik.mishra314@gmail.com",
    license="MIT",
    packages=setuptools.find_packages(),
    package_data={"anacreonlib": ["py.typed", "anacreon_async_client.pyi"]},
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
