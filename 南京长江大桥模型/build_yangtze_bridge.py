"""在 Blender 后台重建南京长江大桥；主生成器保留在相邻的 景点建模工具 目录。"""
from pathlib import Path
import runpy,sys
extra=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
sys.argv=[sys.argv[0],'--','yangtze-bridge']+extra
runpy.run_path(str(Path(__file__).resolve().parents[1]/'景点建模工具/build_bridge.py'),run_name='__main__')
