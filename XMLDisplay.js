function setUpControlPanel() {
    let btnExpandAll = CompatibleGetElementByID("btnExpandAll")
    let btnCollapseAll = CompatibleGetElementByID("btnCollapseAll")
    let btnExpandToDepth2 = CompatibleGetElementByID("btnExpandToDepth2")
    let btnExpandToDepth3 = CompatibleGetElementByID("btnExpandToDepth3")
    let btnScrollToTop = CompatibleGetElementByID("btnScrollToTop")
    let btnScrollToBottom = CompatibleGetElementByID("btnScrollToBottom")
    btnExpandAll.onclick = function () {
        expandUpToDepthOf(document.documentElement, Number.MAX_VALUE)
    }
    btnExpandToDepth2.onclick = function () {
        collapseDownToDepthOf(document.documentElement, 1)
        expandUpToDepthOf(document.documentElement, 2)
    }
    btnExpandToDepth3.onclick = function () {
        collapseDownToDepthOf(document.documentElement, 1)
        expandUpToDepthOf(document.documentElement, 3)
    }
    btnCollapseAll.onclick = function () {
        collapseDownToDepthOf(document.documentElement, 1)
    }
    btnScrollToTop.onclick = function () {
        window.scrollTo(0, 0)
    }
    btnScrollToBottom.onclick = function () {
        let XMLHolder = CompatibleGetElementByID("XMLHolder")
        if (XMLHolder) {
            window.scrollTo(0, XMLHolder.scrollHeight);
        }
    }
}

function LoadXML(ParentElementID, URL) {
    var xmlHolderElement = GetParentElement(ParentElementID);
    if (xmlHolderElement == null) {
        return false;
    }
    ToggleElementVisibility(xmlHolderElement);
    return RequestURL(URL, URLReceiveCallback, ParentElementID);
}

function LoadXMLDom(ParentElementID, xmlDoc) {
    if (xmlDoc) {
        var xmlHolderElement = GetParentElement(ParentElementID);
        if (xmlHolderElement == null) {
            return false;
        }
        while (xmlHolderElement.childNodes.length) {
            childElement = xmlHolderElement.childNodes.item(xmlHolderElement.childNodes.length - 1);
            xmlHolderElement.removeChild(childElement);
        }
        var Result = ShowXML(xmlHolderElement, xmlDoc.documentElement, 0);
        return Result;
    } else {
        return false;
    }
}

function LoadXMLString(ParentElementID, XMLString) {
    xmlDoc = CreateXMLDOM(XMLString);
    return LoadXMLDom(ParentElementID, xmlDoc);
}

////////////////////////////////////////////////////////////
// HELPER FUNCTIONS - SHOULD NOT BE DIRECTLY CALLED BY USERS
////////////////////////////////////////////////////////////
function GetParentElement(ParentElementID) {
    if (typeof (ParentElementID) == 'string') {
        return document.getElementById(ParentElementID);
    } else if (typeof (ParentElementID) == 'object') {
        return ParentElementID;
    } else {
        return null;
    }
}

function URLReceiveCallback(httpRequest, xmlHolderElement) {
    try {
        if (httpRequest.readyState == 4) {
            if (httpRequest.status == 200) {
                var xmlDoc = httpRequest.responseXML;
                if (xmlHolderElement && xmlHolderElement != null) {
                    // xmlHolderElement.innerHTML = '';
                    return LoadXMLDom(xmlHolderElement, xmlDoc);
                }
            } else {
                return false;
            }
        }
    } catch (e) {
        return false;
    }
}

function RequestURL(url, callback, ExtraData) { // based on: http://developer.mozilla.org/en/docs/AJAX:Getting_Started
    var httpRequest;
    if (window.XMLHttpRequest) { // Mozilla, Safari, ...
        httpRequest = new XMLHttpRequest();
        if (httpRequest.overrideMimeType) {
            httpRequest.overrideMimeType('text/xml');
        }
    } else if (window.ActiveXObject) { // IE
        try {
            httpRequest = new ActiveXObject("Msxml2.XMLHTTP");
        } catch (e) {
            try {
                httpRequest = new ActiveXObject("Microsoft.XMLHTTP");
            } catch (e) {
            }
        }
    }
    if (!httpRequest) {
        return false;
    }
    httpRequest.onreadystatechange = function () {
        callback(httpRequest, ExtraData);
    };
    httpRequest.open('GET', url, true);
    httpRequest.send('');
    return true;
}

function CreateXMLDOM(XMLStr) {
    if (window.ActiveXObject) {
        xmlDoc = new ActiveXObject("Microsoft.XMLDOM");
        xmlDoc.loadXML(XMLStr);
        return xmlDoc;
    } else if (document.implementation && document.implementation.createDocument) {
        var parser = new DOMParser();
        return parser.parseFromString(XMLStr, "text/xml");
    } else {
        return null;
    }
}

var IDCounter = 1;
var NestingIndent = 30;

function ShowXML(xmlHolderElement, RootNode, indent) {
    if (RootNode == null || xmlHolderElement == null) {
        return false;
    }
    var Result = true;
    var TagEmptyElement = document.createElement('div');
    if (RootNode.getAttribute("depth")) {
        TagEmptyElement.setAttribute("depth", RootNode.getAttribute("depth"))
    }
    TagEmptyElement.className = 'Element';
    TagEmptyElement.style.position = 'relative';
    TagEmptyElement.style.left = NestingIndent + 'px';
    if (RootNode.childNodes.length == 0) {
        var onClickListener = function () {
            //no-op
            event.cancelBubble = true;
        }
        AddTextNode(TagEmptyElement, '<', 'Utility', onClickListener, RootNode);
        AddTextNode(TagEmptyElement, RootNode.nodeName, 'NodeName', onClickListener, RootNode)
        for (var i = 0; RootNode.attributes && i < RootNode.attributes.length; ++i) {
            CurrentAttribute = RootNode.attributes.item(i);
            AddTextNode(TagEmptyElement, ' ' + CurrentAttribute.nodeName, 'AttributeName', onClickListener, RootNode);
            AddTextNode(TagEmptyElement, '=', 'Utility', onClickListener, RootNode);
            AddTextNode(TagEmptyElement, '"' + CurrentAttribute.nodeValue + '"', 'AttributeValue', onClickListener, RootNode);
        }
        AddTextNode(TagEmptyElement, ' />', onClickListener, RootNode);
        xmlHolderElement.appendChild(TagEmptyElement);
        xmlHolderElement.appendChild(document.createElement('br'));
        //SetVisibility(TagEmptyElement,true);
    } else { // mo child nodes
        var onClickListener = function () {
            ToggleElementVisibility(this);
            event.cancelBubble = true;
        };
        AddTextNode(TagEmptyElement, '+', 'NavIcon', onClickListener, RootNode);
        AddTextNode(TagEmptyElement, '<', 'Utility', onClickListener, RootNode);
        AddTextNode(TagEmptyElement, RootNode.nodeName, 'NodeName', onClickListener, RootNode)
        for (var i = 0; RootNode.attributes && i < RootNode.attributes.length; ++i) {
            CurrentAttribute = RootNode.attributes.item(i);
            AddTextNode(TagEmptyElement, ' ' + CurrentAttribute.nodeName, 'AttributeName', onClickListener, RootNode);
            AddTextNode(TagEmptyElement, '=', 'Utility', onClickListener, RootNode);
            AddTextNode(TagEmptyElement, '"' + CurrentAttribute.nodeValue + '"', 'AttributeValue', onClickListener, RootNode);
        }

        AddTextNode(TagEmptyElement, '> ... </', 'Utility', onClickListener, RootNode);
        AddTextNode(TagEmptyElement, RootNode.nodeName, 'NodeName', onClickListener, RootNode);
        AddTextNode(TagEmptyElement, '>', 'Utility', onClickListener, RootNode);

        TagEmptyElement.id = 'div_empty_' + IDCounter;

        xmlHolderElement.appendChild(TagEmptyElement);
        SetVisibility(TagEmptyElement, false);
        //----------------------------------------------

        var TagElement = document.createElement('div');
        if (RootNode.getAttribute("depth")) {
            TagElement.setAttribute("depth", RootNode.getAttribute("depth"), RootNode)
        }
        TagElement.className = 'Element';
        TagElement.style.position = 'relative';
        TagElement.style.left = NestingIndent + 'px';
        AddTextNode(TagElement, '-', 'NavIcon', onClickListener, RootNode);
        TagElement.id = "div_content_" + IDCounter;

        ++IDCounter;
        AddTextNode(TagElement, '<', 'Utility', onClickListener, RootNode);
        AddTextNode(TagElement, RootNode.nodeName, 'NodeName', onClickListener, RootNode);

        for (var i = 0; RootNode.attributes && i < RootNode.attributes.length; ++i) {
            CurrentAttribute = RootNode.attributes.item(i);
            AddTextNode(TagElement, ' ' + CurrentAttribute.nodeName, 'AttributeName', onClickListener, RootNode);
            AddTextNode(TagElement, '=', 'Utility', onClickListener, RootNode);
            AddTextNode(TagElement, '"' + CurrentAttribute.nodeValue + '"', 'AttributeValue', onClickListener, RootNode);
        }
        AddTextNode(TagElement, '>', 'Utility', onClickListener, RootNode);
        TagElement.appendChild(document.createElement('br'));
        var NodeContent = null;
        for (var i = 0; RootNode.childNodes && i < RootNode.childNodes.length; ++i) {
            if (RootNode.childNodes.item(i).nodeName != '#text') {
                Result &= ShowXML(TagElement, RootNode.childNodes.item(i), indent + 1);
            } else {
                NodeContent = RootNode.childNodes.item(i).nodeValue;
            }
        }
        if (RootNode.nodeValue) {
            NodeContent = RootNode.nodeValue;
        }
        if (NodeContent) {
            var ContentElement = document.createElement('div');
            ContentElement.style.position = 'relative';
            ContentElement.style.left = NestingIndent + 'px';
            AddTextNode(ContentElement, NodeContent, 'NodeValue', onClickListener, RootNode);
            TagElement.appendChild(ContentElement);
        }
        AddTextNode(TagElement, '  </', 'Utility', onClickListener, RootNode);
        AddTextNode(TagElement, RootNode.nodeName, 'NodeName', onClickListener, RootNode);
        AddTextNode(TagElement, '>', 'Utility', onClickListener, RootNode);
        xmlHolderElement.appendChild(TagElement);
    }

    // if (indent==0) { ToggleElementVisibility(TagElement.childNodes(0)); } - uncomment to collapse the external element
    return Result;
}

function AddTextNode(ParentNode, Text, Class, onClickListener, RootNode) {
    NewNode = document.createElement('span');
    if (Class) {
        NewNode.className = Class;
    }
    if (Text) {
        NewNode.appendChild(document.createTextNode(Text));
    }
    if (ParentNode) {
        ParentNode.appendChild(NewNode);
    }
    NewNode.onclick = onClickListener;
    if (RootNode && RootNode.getAttribute("priority")) {
        if (parseInt(RootNode.getAttribute("priority")) < 5) {
            NewNode.style.cssText = "color:red;"
        } else {
            NewNode.style.cssText = "color:orange;"
        }
    }
    return NewNode;
}

function CompatibleGetElementByID(id) {
    if (!id) {
        return null;
    }
    if (document.getElementById) { // DOM3 = IE5, NS6
        return document.getElementById(id);
    } else {
        if (document.layers) { // Netscape 4
            return document.id;
        } else { // IE 4
            return document.all.id;
        }
    }
}

function SetVisibility(HTMLElement, Visible) {
    if (!HTMLElement) {
        return;
    }
    var VisibilityStr = (Visible) ? 'block' : 'none';
    if (document.getElementById) { // DOM3 = IE5, NS6
        HTMLElement.style.display = VisibilityStr;
    } else {
        if (document.layers) { // Netscape 4
            HTMLElement.display = VisibilityStr;
        } else { // IE 4
            HTMLElement.id.style.display = VisibilityStr;
        }
    }
}

function ToggleElementVisibility(Element) {
    if (!Element) {
        return;
    }
    Element = Element.parentNode;
    try {
        ElementType = Element.id.slice(0, Element.id.lastIndexOf('_') + 1);
        ElementID = parseInt(Element.id.slice(Element.id.lastIndexOf('_') + 1));
    } catch (e) {
        return;
    }
    var ElementToHide = null;
    var ElementToShow = null;
    if (ElementType == 'div_content_') {
        ElementToHide = 'div_content_' + ElementID;
        ElementToShow = 'div_empty_' + ElementID;
    } else if (ElementType == 'div_empty_') {
        ElementToShow = 'div_content_' + ElementID;
        ElementToHide = 'div_empty_' + ElementID;
    }
    ElementToHide = CompatibleGetElementByID(ElementToHide);
    ElementToShow = CompatibleGetElementByID(ElementToShow);
    SetVisibility(ElementToHide, false);
    SetVisibility(ElementToShow, true);
}

/** 展开xml节点，直到depth深度的节点已经显示出来*/
function expandUpToDepthOf(node, depth) {
    if (node.tagName.toLowerCase() == "div" && node.getAttribute("depth") && node.id && node.getAttribute("depth") <= depth - 1) {
        if (node.id.startsWith("div_content_")) {
            SetVisibility(node, true)
        } else if (node.id.startsWith("div_empty_")) {
            SetVisibility(node, false)
        }
    }
    for (var i = 0; i < node.childNodes.length; i++) {
        if (node.childNodes[i].nodeType === 1 && node.childNodes[i].childNodes.length > 0) {
            expandUpToDepthOf(node.childNodes[i], depth)
        }
    }
}

/** 收起xml节点，直到depth深度的节点已经被收起*/
function collapseDownToDepthOf(node, depth) {
    if (node.tagName.toLowerCase() == "div" && node.getAttribute("depth") && node.id && node.getAttribute("depth") >= depth) {
        if (node.id.startsWith("div_content_")) {
            SetVisibility(node, false)
        } else if (node.id.startsWith("div_empty_")) {
            SetVisibility(node, true)
        }
    }
    for (var i = 0; i < node.childNodes.length; i++) {
        if (node.childNodes[i].nodeType === 1 && node.childNodes[i].childNodes.length > 0) {
            collapseDownToDepthOf(node.childNodes[i], depth)
        }
    }
}

