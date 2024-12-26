from setuptools import setup, find_packages

setup(
    name="fastmcp_http",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "mcp",
        "flask[async]",
    ],
    author="Aradrareness",
    author_email="",
    description="A client and server solution for interacting with FastMCP services via HTTP",
    url="https://github.com/ARadRareness/mcp-registry",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
