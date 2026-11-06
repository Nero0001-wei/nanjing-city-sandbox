from pathlib import Path
import sys,runpy
source=Path(__file__).resolve().parents[1]/'景点建模工具'/'build_landmark.py'
extra=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
sys.argv=[str(source),'--','yuejiang']+extra
runpy.run_path(str(source),run_name='__main__')
