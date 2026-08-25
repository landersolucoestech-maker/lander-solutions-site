'use strict';
const __partFs=require('fs');
const __partPath=require('path');
const __partPrefix=__filename+'.part';
const __partSource=__partFs.readdirSync(__dirname).filter((name)=>name.startsWith(__partPath.basename(__partPrefix))).sort().map((name)=>__partFs.readFileSync(__partPath.join(__dirname,name),'utf8')).join('');
new Function('require','__dirname','__filename',__partSource)(require,__dirname,__filename);
