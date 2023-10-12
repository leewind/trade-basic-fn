from setuptools import setup, find_packages

setup(
    name="breadt",
    version="0.1.88",
    description="Basic Module For Quant",
    # packages=find_packages(include=["base", "trader"]),
    packages=["breadt"],
    install_requires=[
        "loguru",
        "pika",
        "pymysql",
        "redis",
        "sqlalchemy",
        "pandas",
        "clickhouse-connect",
    ],
)
