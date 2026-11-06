# 南京眼模型交付

采用与南京城市沙盘一致的微缩建筑风格；建筑本身不含树木。先生成 imagegen 三视图，再用 Blender 5.2.1 建模。此为场景概念模型，非测绘复原。

- `南京眼_分组可编辑_带材质.blend`：桥墩、梁架、桥塔、索缆、栏杆灯具分组可编辑；摄影棚单独成组，贴图已打包。
- `web/南京眼_网页版.blend`：合并网格、材质及顶点接触阴影；包含摄影棚与三台相机。
- `web/南京眼_网页版.glb`：最终 30,356 个三角面，3,096,500 字节，5 个材质，2 张内嵌 1024 贴图，保留 COLOR_0 顶点 AO。导出不含摄影棚、灯光和相机。
- `web/`：独立 PNG 贴图、实模三视图、web-model-stats.json。生成器也保存在 Blender Text 数据块中。
- `../南京眼效果图/`：内置 imagegen 生成的概念三视图和完整提示词。概念图与最终模型渲染分开保存；南京眼最终模型额外补齐两岸落地台阶。

## 重建

从项目根目录执行：

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python 南京眼模型/build_nanjing_eye.py
```

追加 `-- --geometry-only` 可只检查修改器应用后的三角面数。保留相邻的 `景点建模工具/build_bridge.py` 和 `geometry.py`。生成器会更新该模型目录，不自动覆盖网页资源；确认后复制 GLB 并同步网页 manifest、缓存版本。

Blender 原生为长轴 +X、Z-up；GLB 为长轴 +X、Y-up。网页使用等比缩放 0.3229860731394905，摆放以 `sandbox-app/src/landmark-placement.js` 为准。调整后须重验桥端和道路／地面的接缝。网页效果与验收记录见 `../景点建模工具/桥梁交付说明.md`。
