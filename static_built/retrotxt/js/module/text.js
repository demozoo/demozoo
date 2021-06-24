import{CharacterSet,DOS437Ctrls,DOS437En,ISO88591,Win1252EN}from"./charset.js";class LegacyText{constructor(e="",t={codepage:"",displayControls:null}){if("string"!=typeof e)throw new Error(`text parameter must be text, not ${typeof e}`);"codepage"in t||(t.codepage=""),"displayControls"in t||(t.displayControls=null),this.text=e,this.codepage=t.codepage,this.errorCharacter="�",this.displayControls=`${t.displayControls}`||"false",this.asciiTable=[],this.extendedTable=[]}normalize(){this._characterTable();let t="";for(let e=0;e<this.text.length;e++)t+=this._fromCharCode(this.text.charCodeAt(e));return t}_characterTable(){this.asciiTable=new CharacterSet(DOS437Ctrls).get();const e=new CharacterSet(`${this.codepage}`);this.extendedTable=e.get()}_fromCharCode(e){if(0===e)return" ";if(65533===e)return" ";if(0<=e&&e<=31){if(27===e)return this.asciiTable[e];if("true"===this.displayControls)switch(e){case 9:return"\t";case 10:case 13:return"\n";default:return this.codepage===DOS437En?this.asciiTable[e]:" "}if(this.codepage===DOS437En)return`${String.fromCharCode(e)}`;switch(e){case 9:return"\t";case 10:case 13:return"\n"}return" "}if(32<=e&&e<=126)return`${String.fromCharCode(e)}`;if(127===e&&"true"==`${this.displayControls}`)return"⌂";switch(this.codepage){case DOS437En:return this._lookupCp437(e);case ISO88591:case Win1252EN:return this._lookupCharCode(e);default:throw new Error(`Unknown code page: "${this.codepage}"`)}}_lookupCp437(e){return 160<=e&&e<=255?this.extendedTable[e-128]:""}_lookupCharCode(e){return 128<=e&&e<=255?this.extendedTable[e]:""}}export{DOS437En,ISO88591,Win1252EN,LegacyText};
/*! RetroTxt for Demozoo v1.0.0 (2021-06-24); © Ben Garrett - LGPL-3.0 */
