var _____WB$wombat$assign$function_____ = function(name) {return (self._wb_wombat && self._wb_wombat.local_init && self._wb_wombat.local_init(name)) || self[name]; };
if (!self.__WB_pmw) { self.__WB_pmw = function(obj) { this.__WB_source = obj; return this; } }
{
  let window = _____WB$wombat$assign$function_____("window");
  let self = _____WB$wombat$assign$function_____("self");
  let document = _____WB$wombat$assign$function_____("document");
  let location = _____WB$wombat$assign$function_____("location");
  let top = _____WB$wombat$assign$function_____("top");
  let parent = _____WB$wombat$assign$function_____("parent");
  let frames = _____WB$wombat$assign$function_____("frames");
  let opener = _____WB$wombat$assign$function_____("opener");

var isIE=(navigator.appVersion.indexOf("MSIE")!=-1)?true:false;var isWin=(navigator.appVersion.toLowerCase().indexOf("win")!=-1)?true:false;var isOpera=(navigator.userAgent.indexOf("Opera")!=-1)?true:false;function ControlVersion(){var a;var b;var c;try{b=new ActiveXObject("ShockwaveFlash.ShockwaveFlash.7");a=b.GetVariable("$version")}catch(c){}if(!a){try{b=new ActiveXObject("ShockwaveFlash.ShockwaveFlash.6");a="WIN 6,0,21,0";b.AllowScriptAccess="always";a=b.GetVariable("$version")}catch(c){}}if(!a){try{b=new ActiveXObject("ShockwaveFlash.ShockwaveFlash.3");a=b.GetVariable("$version")}catch(c){}}if(!a){try{b=new ActiveXObject("ShockwaveFlash.ShockwaveFlash.3");a="WIN 3,0,18,0"}catch(c){}}if(!a){try{b=new ActiveXObject("ShockwaveFlash.ShockwaveFlash");a="WIN 2,0,0,11"}catch(c){a=-1}}return a}function GetSwfVer(){var g=-1;if(navigator.plugins!=null&&navigator.plugins.length>0){if(navigator.plugins["Shockwave Flash 2.0"]||navigator.plugins["Shockwave Flash"]){var f=navigator.plugins["Shockwave Flash 2.0"]?" 2.0":"";var a=navigator.plugins["Shockwave Flash"+f].description;var e=a.split(" ");var c=e[2].split(".");var h=c[0];var b=c[1];var d=e[3];if(d==""){d=e[4]}if(d[0]=="d"){d=d.substring(1)}else{if(d[0]=="r"){d=d.substring(1);if(d.indexOf("d")>0){d=d.substring(0,d.indexOf("d"))}}}var g=h+"."+b+"."+d}}else{if(navigator.userAgent.toLowerCase().indexOf("webtv/2.6")!=-1){g=4}else{if(navigator.userAgent.toLowerCase().indexOf("webtv/2.5")!=-1){g=3}else{if(navigator.userAgent.toLowerCase().indexOf("webtv")!=-1){g=2}else{if(isIE&&isWin&&!isOpera){g=ControlVersion()}}}}}return g}function DetectFlashVer(f,d,c){versionStr=GetSwfVer();if(versionStr==-1){return false}else{if(versionStr!=0){if(isIE&&isWin&&!isOpera){tempArray=versionStr.split(" ");tempString=tempArray[1];versionArray=tempString.split(",")}else{versionArray=versionStr.split(".")}var e=versionArray[0];var a=versionArray[1];var b=versionArray[2];if(e>parseFloat(f)){return true}else{if(e==parseFloat(f)){if(a>parseFloat(d)){return true}else{if(a==parseFloat(d)){if(b>=parseFloat(c)){return true}}}}}return false}}}function AC_AddExtension(b,a){return b}function AC_Generateobj(e,d,a){var c="";if(isIE&&isWin&&!isOpera){c+="<object ";for(var b in e){c+=b+'="'+e[b]+'" '}c+=">";for(var b in d){c+='<param name="'+b+'" value="'+d[b]+'" /> '}c+="</object>"}else{c+="<embed ";for(var b in a){c+=b+'="'+a[b]+'" '}c+="> </embed>"}document.write(c)}function AC_FL_RunContent(){var a=AC_GetArgs(arguments,".swf","movie","clsid:d27cdb6e-ae6d-11cf-96b8-444553540000","application/x-shockwave-flash");AC_Generateobj(a.objAttrs,a.params,a.embedAttrs)}function AC_SW_RunContent(){var a=AC_GetArgs(arguments,".dcr","src","clsid:166B1BCA-3F9C-11CF-8075-444553540000",null);AC_Generateobj(a.objAttrs,a.params,a.embedAttrs)}function AC_GetArgs(b,e,g,d,h){var a=new Object();a.embedAttrs=new Object();a.params=new Object();a.objAttrs=new Object();for(var c=0;c<b.length;c=c+2){var f=b[c].toLowerCase();switch(f){case"classid":break;case"pluginspage":a.embedAttrs[b[c]]=b[c+1];break;case"src":case"movie":b[c+1]=AC_AddExtension(b[c+1],e);a.embedAttrs.src=b[c+1];a.params[g]=b[c+1];break;case"onafterupdate":case"onbeforeupdate":case"onblur":case"oncellchange":case"onclick":case"ondblclick":case"ondrag":case"ondragend":case"ondragenter":case"ondragleave":case"ondragover":case"ondrop":case"onfinish":case"onfocus":case"onhelp":case"onmousedown":case"onmouseup":case"onmouseover":case"onmousemove":case"onmouseout":case"onkeypress":case"onkeydown":case"onkeyup":case"onload":case"onlosecapture":case"onpropertychange":case"onreadystatechange":case"onrowsdelete":case"onrowenter":case"onrowexit":case"onrowsinserted":case"onstart":case"onscroll":case"onbeforeeditfocus":case"onactivate":case"onbeforedeactivate":case"ondeactivate":case"type":case"codebase":case"id":a.objAttrs[b[c]]=b[c+1];break;case"width":case"height":case"align":case"vspace":case"hspace":case"class":case"title":case"accesskey":case"name":case"tabindex":a.embedAttrs[b[c]]=a.objAttrs[b[c]]=b[c+1];break;default:a.embedAttrs[b[c]]=a.params[b[c]]=b[c+1]}}a.objAttrs.classid=d;if(h){a.embedAttrs.type=h}return a};

}
/*
     FILE ARCHIVED ON 22:36:18 Dec 24, 2020 AND RETRIEVED FROM THE
     INTERNET ARCHIVE ON 12:46:26 Dec 15, 2024.
     JAVASCRIPT APPENDED BY WAYBACK MACHINE, COPYRIGHT INTERNET ARCHIVE.

     ALL OTHER CONTENT MAY ALSO BE PROTECTED BY COPYRIGHT (17 U.S.C.
     SECTION 108(a)(3)).
*/
/*
playback timings (ms):
  captures_list: 1.266
  exclusion.robots: 0.057
  exclusion.robots.policy: 0.041
  esindex: 0.015
  cdx.remote: 14.527
  LoadShardBlock: 997.046 (3)
  PetaboxLoader3.resolve: 1371.979 (3)
  PetaboxLoader3.datanode: 81.118 (4)
  load_resource: 459.704
*/