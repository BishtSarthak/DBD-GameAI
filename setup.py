from setuptools import find_packages, setup

setup(
    name="DBD-GameAI",
    version="0.0.1",
    description="Writing code to play Dead By Daylight",
    url="https://github.com/BishtSarthak/DBD-GameAI",
    author="BishtSarthak",
    author_email="bisht.bits@gmail.com",
    packages=find_packages(exclude=["test", ".github"]),
)
