# 夫子庙 · 无树木带材质模型

表现对象：大成殿双檐灰瓦、朱红格扇、两侧庑廊与石庭。这是同风格微缩概念模型，不是测绘复原。

- 分组可编辑源文件：夫子庙_分组可编辑_带材质.blend
- 网页 Blender：web/夫子庙_网页版.blend
- 最终 GLB：web/夫子庙_网页版.glb
- 实模渲染：web/夫子庙_实模_侧前方.png、正面.png、侧面.png
- 统计与 SHA-256：web/web-model-stats.json
- 效果图与完整提示词：../夫子庙效果图/
- 本次采用内置 imagegen 生成效果图，再用 Blender 5.2.1 LTS 建模、赋材质、烘焙顶点 AO 和导出。

最终 GLB：36,974 三角面；2,710,900 字节；13 个材质；4 张内嵌贴图。原占位模型为 4,758 面、207,868 字节。GLB 使用索引网格，保留 COLOR_0 顶点明暗；玻璃材质使用不透明浅色表面，避免多层透明排序开销。

Blender 为 Z-up、正面 -Y，GLB 为 Y-up、正面 +Z，底部原点。网页保留原地理锚点，等比缩放 0.44，无额外偏移。01–05 为建筑分组，06 为摄影棚；贴图已打包，摄影棚不会导出至 GLB。

重建：保留上级“景点建模工具”目录及本目录的 web/贴图，在 Blender 后台运行 build_fuzimiao.py；追加 -- --geometry-only 可只核查网格。共用生成器 build_landmark.py、old_city_landmarks.py 与 geometry.py 已随项目保存，并嵌入 Blender 文本数据。
