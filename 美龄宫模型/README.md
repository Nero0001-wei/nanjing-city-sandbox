# 美龄宫模型

无树木微缩建筑概念模型，最终 GLB 为 37,268 个三角面，网页等比缩放 0.47。

- 美龄宫_分组可编辑_带材质.blend：基础、主体、屋顶/城墙、门窗、栏杆分组；贴图打包，含三台相机及摄影棚。
- web/美龄宫_网页版.blend：合并网页模型，附烘焙顶点 AO。
- web/美龄宫_网页版.glb：包含材质、内嵌贴图和顶点阴影；不依赖外部文件。
- web/ 中三张“实模”PNG：Blender 实际模型渲染，包括侧前方、正面、侧面。
- ../美龄宫效果图/：内置 imagegen 生成的效果图及完整提示词。
- ../景点建模工具/：共用生成源码和详细交付说明。源码也已存入 Blender 文本数据块。

重新生成：从本目录运行

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python build_meiling.py

坐标：Blender Z-up、正面 -Y；glTF Y-up、正面 +Z。COLOR_0 为接触阴影，网页加载时应保留，不应再重复烘焙到颜色贴图中。
