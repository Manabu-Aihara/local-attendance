import sys
# sys.path.append(os.path.abspath(".."))
import pathlib
packagedir = pathlib.Path(__file__).resolve().parent.parent.parent
print(packagedir)
sys.path.append(str(packagedir))