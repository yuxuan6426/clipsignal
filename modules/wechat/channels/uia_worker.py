"""Read the public accessibility tree of a single WeChat Channels window."""

import json

import psutil
import win32gui
import win32process
from comtypes import COMError
from comtypes.client import CreateObject, GetModule

uia = GetModule("UIAutomationCore.dll")
automation = CreateObject(uia.CUIAutomation, interface=uia.IUIAutomation)
MAX_NODES = 3500
ROLES = {
    getattr(uia, f"UIA_{name}ControlTypeId"): name
    for name in ("Text", "Button", "Image", "Group", "Pane", "Edit", "Document", "Hyperlink")
}


def channels_document():
    processes = {p.info["pid"] for p in psutil.process_iter(["pid", "name"])
                 if (p.info["name"] or "").casefold() == "wechatappex.exe"}
    window_handles = []
    win32gui.EnumWindows(
        lambda handle, _: window_handles.append(handle)
        if win32gui.IsWindowVisible(handle) and win32process.GetWindowThreadProcessId(handle)[1] in processes
        else None, None)
    condition = automation.CreateAndCondition(
        automation.CreatePropertyCondition(uia.UIA_NamePropertyId, "视频号"),
        automation.CreatePropertyCondition(uia.UIA_ControlTypePropertyId, uia.UIA_DocumentControlTypeId),
    )
    documents = []
    for handle in window_handles:
        try:
            root = automation.ElementFromHandle(handle)
            document = root.FindFirst(uia.TreeScope_Descendants, condition)
            if document:
                inner = document.FindFirst(uia.TreeScope_Descendants, condition)
                documents.append(inner or document)
        except COMError:
            continue
    return documents[0] if len(documents) == 1 else None


def snapshot(document):
    walker = automation.ControlViewWalker
    cache = automation.CreateCacheRequest()
    cache.AddProperty(uia.UIA_ControlTypePropertyId)
    cache.AddProperty(uia.UIA_NamePropertyId)
    nodes = []

    def visit(parent, parent_index, depth):
        if depth > 30 or len(nodes) >= MAX_NODES:
            return
        child = walker.GetFirstChildElementBuildCache(parent, cache)
        while child and len(nodes) < MAX_NODES:
            role = ROLES.get(child.CachedControlType, "Other")
            # The probe reads names for the required controls, never the values of editable fields.
            name = child.CachedName if role in {"Text", "Image", "Button", "Hyperlink"} else ""
            index = len(nodes)
            nodes.append({"parent": parent_index, "role": role, "name": name})
            if role != "Edit":
                visit(child, index, depth + 1)
            child = walker.GetNextSiblingElementBuildCache(child, cache)

    visit(document, -1, 0)
    return nodes


if __name__ == "__main__":
    document = channels_document()
    result = {"result": "ok", "nodes": snapshot(document)} if document else {"result": "channels_window_required"}
    print(json.dumps(result, ensure_ascii=False))
