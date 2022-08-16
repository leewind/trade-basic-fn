from setuptools import setup, find_packages

setup(
    name="breadt",
    version="0.1.19",
    description="Basic Module For Quant",
    # packages=find_packages(include=["base", "trader"]),
    packages=["breadt"],
    install_requires=["loguru"],
)
