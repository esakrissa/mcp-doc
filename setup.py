from setuptools import setup, find_packages

setup(
    name="mcp-doc",
    packages=find_packages(),
    include_package_data=True,
    package_data={"": ["*.txt", "*.md"]},
    entry_points={
        "console_scripts": [
            "mcp-doc=mcp_doc.cli:main",
        ],
    },
) 