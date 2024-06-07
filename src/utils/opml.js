
// 使用DOMParser解析OPML
function parseOPML(opmlContent) {
  const parser = new DOMParser();
  const xmlDoc = parser.parseFromString(opmlContent, "text/xml");

  // 检查是否有解析错误
  if (xmlDoc.getElementsByTagName("parsererror").length > 0) {
    console.error("OPML解析错误");
    return;
  }

  // 提取outline元素
  const outlines = xmlDoc.getElementsByTagName("outline");
  const outlineData = [];

  for (let i = 0; i < outlines.length; i++) {
    const outline = outlines[i];
    const text = outline.getAttribute("text");
    const title = outline.getAttribute("title");
    const type = outline.getAttribute("type");
    const xmlUrl = outline.getAttribute("xmlUrl");
    const htmlUrl = outline.getAttribute("htmlUrl");
    const children = outline.getElementsByTagName("outline");

    // 如果有子项，递归处理
    if (children.length > 0) {
      outlineData.push({
        text,
        children: parseOutlines(children),
      });
    } else {
      outlineData.push({
        text,title,type,xmlUrl,htmlUrl
      });
    }
  }

  return outlineData;
}

// 解析子项
function parseOutlines(children) {
  const childData = [];
  for (let i = 0; i < children.length; i++) {
    const child = children[i];
    childData.push({
      text: child.getAttribute("text"),
      title: child.getAttribute("title"),
      type: child.getAttribute("type"),
      xmlUrl: child.getAttribute("xmlUrl"),
      htmlUrl: child.getAttribute("htmlUrl")
    });
  }
  return childData;
}

export { parseOPML };