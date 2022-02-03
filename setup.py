import os
import re

from setuptools import find_packages, setup

with open('README.md', 'r', encoding='utf-8') as fp:
    readme = fp.read()

with open('requirements.txt', 'r', encoding='utf-8') as fp:
    requirements = [
        s.split('#')[0]
        for s in fp.read().splitlines()
        if s.split('#')[0].strip()
    ]

with open(os.path.join(os.path.dirname(__file__), 'pyease_grpc', '__init__.py')) as fp:
    VERSION = re.match(r'__version__\s+=\s+["\'](.*?)["\']', fp.read(), re.S).group(1)

setup(
    version=VERSION,
    name='pyease-grpc',
    author='Sudipto Chandra',
    author_email='dipu.sudipta@gmail.com',
    packages=find_packages(exclude=['tests*']),
    description='Easy gRPC-web client in python',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/dipu-bd/pyease-grpc',
    keywords=[
        'grpc',
        'protobuf',
        'grpc-web',
        'requests',
    ],
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        'Development Status :: 1 - Planning',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
