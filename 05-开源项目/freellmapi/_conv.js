const fs = require('fs');
const src = 'D:/codespace/freellmapi/_run2_src.txt';
const out = 'D:/codespace/freellmapi/run_freellmapi2.bat';
let s = fs.readFileSync(src, 'latin1');
// normalize to LF then to CRLF
s = s.replace(/\r\n/g, '\n').replace(/\n/g, '\r\n');
if (!s.startsWith('\r\n')) s = s; // no BOM
fs.writeFileSync(out, s, 'latin1');
console.log('written', out, 'len', s.length);
