const DOS437Ctrls="cp437_C0",DOS437En="cp_437",ISO88591="iso_8859_1",Win1252EN="cp_1252",unbsp=" ";class CharacterSet{constructor(t=""){this.set=t}get(){switch(this.set){case DOS437Ctrls:return this._cp437C0();case DOS437En:return this._cp437();case ISO88591:return this._iso88591();case Win1252EN:return this._cp1252();default:throw new Error(`Unknown character set: "${this.set}"`)}}_cp437Table(){this.set0=Array.from("␀☺☻♥♦♣♠•◘○◙♂♀♪♫☼"),this.set1=Array.from("►◄↕‼¶§▬↨↑↓→←∟↔▲▼"),this.set8=Array.from("ÇüéâäàåçêëèïîìÄÅ"),this.set9=Array.from("ÉæÆôöòûùÿÖÜ¢£¥₧ƒ"),this.setA=Array.from("áíóúñÑªº¿⌐¬½¼¡«»"),this.setB=Array.from("░▒▓│┤╡╢╖╕╣║╗╝╜╛┐"),this.setC=Array.from("└┴┬├─┼╞╟╚╔╩╦╠═╬╧"),this.setD=Array.from("╨╤╥╙╘╒╓╫╪┘┌█▄▌▐▀"),this.setE=Array.from("αßΓπΣσµτΦΘΩδ∞φε∩"),this.setF=Array.from(`≡±≥≤⌠⌡÷≈°∙·√ⁿ²■${unbsp}`)}_cp437C0(){return this._cp437Table(),[...this.set0,...this.set1]}_cp437(){return this._cp437Table(),this.set8.concat(this.set9,this.setA,this.setB,this.setC,this.setD,this.setE,this.setF)}_iso88591(){var s;let r=[];for(let t=0;t<=255;t++)r=(s=t)<32||(126<s&&s<160||255<s)?[...r," "]:[...r,String.fromCharCode(t)];return r}_cp1252Table(){return this.set8=["€","","‚","ƒ","„","…","†","‡","ˆ","‰","Š","‹","Œ","","Ž",""],this.set9=["","‘","’","“","”","•","–","—","˜","™","š","›","œ","","ž","Ÿ"],[...this.set8,...this.set9]}_cp1252(){let s=[];for(let t=0;t<=255;t++)128!==t?s=[...s,String.fromCharCode(t)]:(s=[...s,...this._cp1252Table()],t=159);return s}}export{DOS437Ctrls,DOS437En,ISO88591,Win1252EN,CharacterSet};
/*! RetroTxt for Demozoo v1.0.0 (2021-06-24); © Ben Garrett - LGPL-3.0 */
