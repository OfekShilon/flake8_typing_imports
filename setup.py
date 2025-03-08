from setuptools import setup

setup(
    name='flake8-typing-imports',
    version='0.1.0',
    description='Flake8 extension to suggest moving type-only imports to TYPE_CHECKING blocks',
    author='Ofek Shilon',
    author_email='ofekshilon@gmail.com',
    py_modules=['flake8_typing_imports'],
    install_requires=[
        'flake8>=3.8.0',
    ],
    entry_points={
        'flake8.extension': [
            'TYP = flake8_typing_imports:TypeCheckingImportChecker',
        ],
    },
    classifiers=[
        'Framework :: Flake8',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
