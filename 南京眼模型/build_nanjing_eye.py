"""在 Blender 后台重建南京眼；主生成器保留在相邻的 景点建模工具 目录。"""
from pathlib import Path
import runpy,sys
extra=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
sys.argv=[sys.argv[0],'--','nanjing-eye']+extra
runpy.run_path(str(Path(__file__).resolve().parents[1]/'景点建模工具/build_bridge.py'),run_name='__main__')
