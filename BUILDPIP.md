## How to build pip package

For the complete release, tagging and documentation-deployment process, see
[RELEASING.md](RELEASING.md).

1. Update mimosa/**init**.py to latest version number
2. `pip install --upgrade build`
3. `python -m build`
4. `pip install --upgrade twine`
5. `twine upload --repository testpypi dist/*` (token set in `.pypirc` or in keyring)
6. `twine upload dist/*`
