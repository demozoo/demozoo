var shownelementid="";
var lasthiddenid="";
function hidemenu ()
{
    if (shownelementid != "") {
        document.getElementById(shownelementid).style.visibility="hidden";
    }
    lasthiddenid = shownelementid;
    shownelementid = "";
}

function showmenu (menuid)
{
    // if we've only just hidden the element, don't re-show it
    if (lasthiddenid != menuid) {
        document.getElementById(menuid).style.visibility="visible";
        shownelementid=menuid;
    }
}