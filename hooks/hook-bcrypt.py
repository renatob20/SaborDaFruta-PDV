
from PyInstaller.utils.hooks import collect_all, collect_submodules
datas, binaries, hiddenimports = collect_all('bcrypt')
hiddenimports += collect_submodules('bcrypt')
hiddenimports += ['bcrypt._bcrypt', '_cffi_backend']
