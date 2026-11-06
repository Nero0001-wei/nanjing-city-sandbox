# 阅江楼模型

2026-10-30。根据对应 imagegen 三视图制作的同风格建筑概念模型，无树木。

- 分组可编辑文件：`阅江楼_分组可编辑_带材质.blend`。建筑分为基础、主体、屋顶、门窗装饰、栏杆；摄影棚独立为第 06 组。
- 网页文件：`web/阅江楼_网页版.blend`、`web/阅江楼_网页版.glb`。GLB 仅包含建筑，已内嵌材质、贴图和顶点 AO。
- 实模渲染：`web/` 内的正面、侧面、侧前方 PNG。AI 概念图在 `../阅江楼效果图/`；完整提示词为其中的 `imagegen-prompt.txt`。
- 最终导出：**39,622 三角面**，**3,372,468 bytes**，10 个材质，4 张内嵌图片。
- Blender 使用 Z-up、正面 -Y；GLB 使用 Y-up、正面 +Z。底面原点为中心，统一缩放 0.28，地图视觉偏移 [4.9, 0, 0.65]，单位为场景单位。
- 材质贴图同时保留在 `web/`，打开 Blender 无需原电脑临时目录。请保留 GLB 的 `COLOR_0` 顶点 AO。

重新生成（在项目根目录运行，需要 Blender 的 bpy/numpy 环境）：

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python 阅江楼模型/build_yuejiang.py
```

入口依赖 `../景点建模工具/build_landmark.py`、`geometry.py` 和 `north_landmarks.py`。生成器校验最终 GLB 的面数，超过 40,000 即报错；不会自动替换网页文件。网页使用 `sandbox-app/public/models/yuejiang.glb`，同步时同时更新 manifest 和场景版本号。

源文件中的模型说明、摄影棚和生成脚本供继续编辑使用；这是沙盘概念建筑，不是测绘复原。
