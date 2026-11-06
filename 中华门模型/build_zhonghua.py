from pathlib import Path
import runpy, sys
sys.argv=[__file__,'--','zhonghua']
runpy.run_path(str(Path(__file__).resolve().parents[1]/'景点建模工具'/'build_landmark.py'),run_name='__main__')
