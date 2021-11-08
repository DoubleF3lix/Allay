import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

setuptools.setup(
    name="allay",
    version="1.0.2",
    description="A parser to convert a descriptive text format into minecraft text components",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DoubleF3lix/Allay/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
