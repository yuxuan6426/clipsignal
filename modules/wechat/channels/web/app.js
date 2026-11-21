const $ = id => document.getElementById(id);
const tab = crypto.randomUUID();
let videos = [];
let current = null;
let cursor = null;
let paired = false;
let generation = 0;
let playbackState = "idle";

function notice(message = "") {
  $("status").textContent = message;
  $("status").hidden = !message;
}

async function api(route, body) {
  const options = {headers: {"X-View-Id": tab}};
  if (body !== undefined) {
    options.method = "POST";
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch("/api/v1/" + route, options);
  const result = await response.json();
  if (!response.ok) {
    const message = result.message ?? (response.status === 401
      ? "请从启动脚本给出的链接打开工作台。" : "请求失败，请检查输入或重新打开页面。");
    throw Object.assign(new Error(message), {code: result.code});
  }
  return result;
}

function element(tag, text, cls) {
  const item = document.createElement(tag);
  item.textContent = text;
  if (cls) item.className = cls;
  return item;
}

function run(action) {
  return async event => {
    notice();
    try {
      await action(event);
    } catch (error) {
      notice(error.message);
    }
  };
}

function renderList() {
  const entries = videos.map(video => {
    const li = element("li", "");
    const name = element("button", video.title);
    name.append(element("small", video.author));
    name.setAttribute("aria-current", String(current?.id === video.id));
    name.addEventListener("click", run(() => showVideo(video.id)));
    li.append(name);
    return li;
  });
  $("videos").replaceChildren(...entries);
  $("count").textContent = String(entries.length);
  $("library-empty").hidden = entries.length !== 0;
  const index = videos.findIndex(video => video.id === current?.id);
  $("previous").disabled = index <= 0;
  $("next").disabled = index < 0 || index >= videos.length - 1;
}

function profile(title, ...content) {
  $("profile-title").textContent = title;
  $("profile-body").replaceChildren(...content);
  if (!$("profile").open) $("profile").showModal();
}

function workShareAction(creator, work) {
  const control = element("div", "", "work-share-action");
  const button = element("button", "获取微信作品链接");
  const status = element("span", creator.source === "socialdatax" ? "可能消耗 SocialDataX 积分" : "");
  status.setAttribute("role", "status");
  button.addEventListener("click", async () => {
    button.disabled = true;
    status.textContent = "正在校验作品归属…";
    try {
      const result = await api("creator-work-link", {creator_id: creator.id, video_id: work.id});
      const link = element("a", "打开微信作品");
      link.href = result.share_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      control.replaceChildren(link);
      link.focus();
    } catch (error) {
      status.textContent = error.message;
      button.disabled = false;
    }
  });
  control.append(button, status);
  return control;
}

async function showProfile(creator) {
  if (creator.profile_status !== "linked") {
    profile(creator.nickname, "当前来源只提供作品作者的显示资料。");
    return;
  }
  const {items} = await api("creator-videos?" + new URLSearchParams({creator_id: creator.id}));
  const content = [];
  if (creator.bio) content.push(element("div", creator.bio));
  if (creator.profile_url) {
    const link = element("a", "打开微信视频号主页");
    link.href = creator.profile_url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    content.push(link);
  }
  const works = element("div", items.length ? "公开作品" : "暂无该账号的可用公开作品。");
  const list = element("ul", "", "profile-works");
  for (const item of items) {
    const row = element("li", "");
    const button = element("button", item.title);
    button.addEventListener("click", run(async () => {
      await showVideo(item.id);
      $("profile").close();
    }));
    row.append(button);
    if (item.creator_id === creator.id) row.append(workShareAction(creator, item));
    list.append(row);
  }
  if (items.length) works.append(list);
  content.push(works);
  profile(creator.nickname, ...content);
}

async function showCreator(creatorId) {
  const creator = await api("creator?" + new URLSearchParams({creator_id: creatorId}));
  await showProfile(creator);
}

async function loadList(query = "") {
  const params = new URLSearchParams({q: query});
  const [search, creators] = await Promise.all([api("videos?" + params), query ? api("creators?" + params) : {items: []}]);
  videos = search.items;
  $("library-empty").textContent = query ? "没有找到匹配的作品。" : "读取的作品会出现在这里。";
  renderList();
  $("creator-heading").hidden = !creators.items.length;
  $("creators").replaceChildren(...creators.items.map(creator => {
    const li = element("li", "");
    const link = element("button", creator.nickname);
    link.addEventListener("click", run(() => showCreator(creator.id)));
    li.append(link);
    return li;
  }));
}

function renderComments(page, videoId, replace) {
  const rows = page.items.map(comment => {
    const li = element("li", "", "comment");
    const name = element("button", comment.author, "plain");
    const args = new URLSearchParams({video_id: videoId, comment_id: comment.id});
    name.addEventListener("click", run(async () => {
      try {
        const identity = await api("commenter?" + args);
        await showProfile(identity);
      } catch (error) {
        profile(comment.author, error.message);
      }
    }));
    const metadata = element("div", "", "meta");
    for (const value of [comment.time_display, comment.likes_display && "赞 " + comment.likes_display]) {
      if (value) metadata.append(element("small", value));
    }
    if (comment.reply_count) {
      const replies = element("button", comment.reply_count + " 条回复");
      replies.addEventListener("click", run(async () => {
        const result = await api("replies?" + args);
        notice(result.reason ?? "暂无回复。");
      }));
      metadata.append(replies);
    }
    li.append(name, element("p", comment.text), metadata);
    return li;
  });
  if (replace) $("comments").replaceChildren(...rows);
  else $("comments").append(...rows);
  const empty = !$("comments").childElementCount;
  $("comments-empty").hidden = !empty;
  $("coverage").textContent = page.reason ?? (empty ? "暂无评论。" : "");
  $("coverage").hidden = !$("coverage").textContent;
  cursor = page.next_cursor;
  $("more").hidden = !cursor;
}

function renderCover(value) {
  const cover = $("cover");
  cover.hidden = true;
  cover.removeAttribute("src");
  if (!value) return;
  try {
    const url = new URL(value);
    if (url.origin === "https://finder.video.qq.com" && !url.username && !url.password) cover.src = url.href;
  } catch {
    // The preview frame remains visible when the source supplies no usable image.
  }
}

async function showVideo(reference) {
  const request = ++generation;
  const video = await api("video?" + new URLSearchParams({reference}));
  const comments = await api("comments?" + new URLSearchParams({reference: video.id}));
  if (request !== generation) return false;
  current = video;
  playbackState = video.playback === "unavailable" ? "unavailable" : "idle";
  history.replaceState(null, "", "/?" + new URLSearchParams({v: video.id}));
  $("detail").hidden = false;
  $("author").textContent = video.author;
  const published = video.published_display || "";
  const date = /^\d{4}-\d{2}-\d{2}T/.test(published) ? new Date(published) : null;
  $("published").textContent = date && !isNaN(date) ? date.toLocaleString("zh-CN") : published;
  $("source").textContent = video.data_source || ({
    wechat_public_preview: "微信公开预览",
    wechat_uia: "微信窗口快照",
    authorized_import: "授权导入",
    socialdatax: "SocialDataX",
  }[video.source] ?? "");
  $("title").textContent = video.title;
  $("title").hidden = false;
  $("stage-title").hidden = true;
  $("description").textContent = video.description === video.title ? "" : video.description;
  $("play-note").textContent = video.share_url
    ? "打开分享入口，按微信的提示继续播放。"
    : video.playback === "unavailable" ? "授权记录未提供分享链接。" : "回到微信的独立视频号窗口继续播放。";
  $("share-link").hidden = !video.share_url;
  $("focus-search").hidden = true;
  renderCover(video.cover_url);
  if (video.share_url) $("share-link").href = video.share_url;
  else $("share-link").removeAttribute("href");
  $("refresh").hidden = $("refresh").disabled = video.source !== "wechat_uia";
  renderList();
  renderComments(comments, video.id, true);
  if (video.comment_count_display && comments.coverage === "unavailable") {
    $("coverage").textContent = "微信显示 " + video.comment_count_display + " 条评论。" + $("coverage").textContent;
    $("coverage").hidden = false;
  }
  return true;
}

function state() {
  return {video_id: current?.id ?? null, playlist: videos.map(item => item.id), playback_state: playbackState};
}

async function heartbeat() {
  if (!paired) return;
  try {
    const {command} = await api("view/tick", state());
    if (command && paired) {
      if (command.creator_id) {
        await showCreator(command.creator_id);
        if (paired) await api("view/ack", {...state(), command_id: command.id, creator_id: command.creator_id});
      } else if (await showVideo(command.video_id) && paired) {
        await api("view/ack", {...state(), command_id: command.id});
      }
    }
  } catch (error) {
    paired = false;
    renderPair();
    notice(error.message);
  } finally {
    if (paired) window.setTimeout(heartbeat, 500);
  }
}

function renderPair() {
  $("pair").setAttribute("aria-pressed", String(paired));
  $("pair").textContent = paired ? "关闭 Agent 联动" : "开启 Agent 联动";
}

$("search").addEventListener("submit", run(async event => {
  event.preventDefault();
  const value = $("query").value.trim();
  const button = $("search").querySelector("button");
  button.disabled = true;
  button.textContent = "处理中…";
  try {
    if (/^https:\/\//i.test(value)) {
      await showVideo(value);
      await loadList();
    } else if (value.length <= 250) {
      await loadList(value);
    } else {
      notice("搜索词最多 250 个字符。");
    }
  } finally {
    button.disabled = false;
    button.textContent = "搜索";
  }
}));
$("focus-search").addEventListener("click", () => $("query").focus());
$("cover").addEventListener("load", event => { event.currentTarget.hidden = false; });
$("cover").addEventListener("error", event => { event.currentTarget.hidden = true; });
$("capture").addEventListener("submit", run(async event => {
  event.preventDefault();
  const button = $("capture").querySelector("button");
  button.disabled = true;
  notice("正在读取微信中已展开的评论面板…");
  try {
    const video = await api("capture", {share_url: $("share").value.trim() || null});
    $("share").value = $("query").value = "";
    await loadList();
    await showVideo(video.id);
    notice("已读取当前作品。");
  } finally {
    button.disabled = false;
  }
}));
$("refresh").addEventListener("click", run(async () => {
  const videoId = current.id;
  $("refresh").disabled = true;
  try {
    await api("capture", {refresh_id: videoId});
    if (videoId === current?.id) await showVideo(videoId);
  } finally {
    if (videoId === current?.id) $("refresh").disabled = false;
  }
}));
$("pair").addEventListener("click", run(async () => {
  if (paired) {
    await api("view/unpair", {});
    paired = false;
  } else {
    await api("view/pair", state());
    paired = true;
    void heartbeat();
  }
  renderPair();
}));
$("author").addEventListener("click", run(() => showCreator(current.creator_id)));
$("share-link").addEventListener("click", () => { playbackState = "native_handoff"; });
$("more").addEventListener("click", run(async () => {
  const reference = current.id;
  const nextCursor = cursor;
  const page = await api("comments?" + new URLSearchParams({reference, cursor: nextCursor}));
  if (reference === current?.id && nextCursor === cursor) renderComments(page, reference, false);
}));
for (const [id, delta] of [["previous", -1], ["next", 1]]) {
  $(id).addEventListener("click", run(async () => {
    const index = videos.findIndex(video => video.id === current?.id);
    const target = videos[index + delta];
    if (target) await showVideo(target.id);
  }));
}

await run(async () => {
  const key = new URLSearchParams(location.hash.slice(1)).get("connect");
  if (key) {
    history.replaceState(null, "", location.pathname + location.search);
    await api("session", {key});
  }
  await loadList();
  const videoId = new URLSearchParams(location.search).get("v");
  if (videoId) await showVideo(videoId);
})();
