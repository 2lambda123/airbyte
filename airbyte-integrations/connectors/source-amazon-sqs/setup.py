#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


from setuptools import find_packages, setup

MAIN_REQUIREMENTS = ["airbyte-cdk", "boto3"]

TEST_REQUIREMENTS = ["requests-mock~=1.9.3", "pytest-mock~=3.6.1", "pytest~=6.1", "moto[sqs, iam]"]

setup(
    name="source_amazon_sqs",
    description="Source implementation for Amazon Sqs.",
    author="Alasdair Brown",
    author_email="airbyte@alasdairb.com",
    packages=find_packages(),
    install_requires=MAIN_REQUIREMENTS,
    package_data={"": ["*.json"]},
    extras_require={
        "tests": TEST_REQUIREMENTS,
    },
)
