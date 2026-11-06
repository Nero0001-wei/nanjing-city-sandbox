// Positions from the project's cached OSM snapshot (z12, origin 3398/1661).
// Heights/radii are artistic relief in scene/source-pixel units, NOT a DEM.
// Sources and limits are recorded in 景观优化/交付说明.md.
export const CITY_HILLS=[
  {id:'yuhuatai',name:'雨花台',source:'way/62381499',p:[363,599],height:6.5,radius:[34,30],angle:-.18},
  {id:'juhuatai',name:'菊花台',source:'way/587966197',p:[291,655],height:3.8,radius:[20,23],angle:.25},
  {id:'wutaishan',name:'五台山',source:'way/782612166',p:[335,429],height:3.2,radius:[18,20],angle:-.3},
  {id:'qingliangshan',name:'清凉山',source:'node/5524009852',p:[301.37,423.25],height:4.5,radius:[18,25],angle:.25},
  {id:'gulin',name:'古林公园丘陵',source:'way/89638712',p:[278.2,367.38],height:4.2,radius:[18,22],angle:-.2},
  {id:'beijige',name:'北极阁',source:'way/91828655',p:[386,390],height:3.1,radius:[15,15],angle:0},
  {id:'jiuhuashan',name:'九华山',source:'way/91828656',p:[437.09,391.36],height:4.4,radius:[16,16],angle:0},
  {id:'fuguishan',name:'富贵山',source:'node/11886580934',p:[474.27,399.41],height:5,radius:[19,24],angle:.4},
  {id:'hongshan',name:'红山',source:'way/62344632',p:[422,278],height:7.2,radius:[21,29],angle:-.2},
  {id:'mufushan',name:'幕府山南麓',source:'way/62344629',p:[404,178],height:8.4,radius:[65,31],angle:-.12},
];
export function cityHillHeight(p){
  let high=0,rest=0;
  for(const hill of CITY_HILLS){
    const dx=p[0]-hill.p[0],dy=p[1]-hill.p[1],c=Math.cos(hill.angle),s=Math.sin(hill.angle);
    const x=(dx*c+dy*s)/hill.radius[0],y=(-dx*s+dy*c)/hill.radius[1],r2=x*x+y*y;
    if(r2>=1)continue;
    // Compact smooth support: no long Gaussian tails lifting unrelated districts.
    const h=hill.height*(1-r2)**2*(1+.1*x-.06*y);
    if(h>high){rest+=high;high=h;}else rest+=h;
  }
  return high+rest*.18;
}
