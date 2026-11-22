const deck = document.querySelector('.deck');
const query = selector => deck.querySelector(selector);
const mode = new URLSearchParams(location.search).get('mode') === 'pitch' ? 'pitch' : 'booth';
const loop = mode === 'booth';
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const player = query('[data-player]');
const chrome = query('[data-chrome]');
const audio = query('[data-narration]');
const caption = query('[data-caption]');
const advance = query('[data-progress]');
const play = query('[data-play]');
const prev = query('[data-prev]');
const next = query('[data-next]');
const select = query('[data-chapter]');
const sound = query('[data-sound]');
const expand = query('[data-expand]');
const count = query('[data-count]');
const clock = query('[data-clock]');
const announce = query('[data-announce]');
const progress = advance.parentElement;

let duration = 0;
const chapters = Array.from(query('[data-deck="' + mode + '"]').children, slide => {
  const length = Number(slide.dataset.seconds) * 1000;
  const chapter = {
    slide,
    title: slide.querySelector('h2').textContent,
    label: slide.querySelector('.deck-kicker').textContent,
    start: duration,
    length,
    cues: Array.from(slide.querySelectorAll('[data-cue]'), cue => ({
      at: Number(cue.dataset.cue),
      text: cue.textContent,
    })),
  };
  duration += length;
  return chapter;
});
const target = chapters.findIndex(chapter => '#' + chapter.slide.id === location.hash);
let index = Math.max(0, target);
let elapsed = 0;
let running = false;
let finished = false;
let enabled = false;
let lastTick = null;
let frame = 0;
let audioAttempt = 0;

query('[data-deck="' + (loop ? 'pitch' : 'booth') + '"]').hidden = true;
for (const [i, chapter] of chapters.entries()) {
  select.add(new Option(chapter.label, String(i)));
}
query('[data-view="' + mode + '"]').setAttribute('aria-current', 'page');
deck.dataset.mode = mode;
deck.dataset.ready = '';
chrome.hidden = false;
query('[data-copy]').hidden = false;
expand.hidden = !document.fullscreenEnabled;

function formatTime(ms) {
  const secs = Math.floor(ms / 1000);
  return Math.floor(secs / 60) + ':' + String(secs % 60).padStart(2, '0');
}

function renderProgress() {
  const chapter = chapters[index];
  const cue = chapter.cues.findLast(cue => cue.at <= elapsed) ?? chapter.cues[0];
  if (caption.textContent !== cue.text) caption.textContent = cue.text;
  const time = chapter.start + elapsed;
  const fraction = time / duration;
  advance.style.transform = 'scaleX(' + fraction.toFixed(4) + ')';
  progress.setAttribute('aria-valuenow', String(Math.floor(fraction * 100)));
  const label = formatTime(time) + ' / ' + formatTime(duration);
  if (clock.textContent !== label) clock.textContent = label;
}

function showChapter(speak = false) {
  for (const [i, item] of chapters.entries()) item.slide.hidden = i !== index;
  query('.deck-stage').scrollTop = 0;
  select.value = String(index);
  count.textContent = (index + 1) + ' / ' + chapters.length;
  prev.disabled = !loop && index === 0;
  next.disabled = !loop && index === chapters.length - 1;
  if (speak) announce.textContent = '第 ' + (index + 1) + ' 章，' + chapters[index].title;
  renderProgress();
}

function audioOff(message) {
  enabled = false;
  audioAttempt += 1;
  audio.pause();
  sound.textContent = '开启旁白';
  announce.textContent = message;
}

function syncAudio() {
  const attempt = ++audioAttempt;
  if (!enabled || !running || document.hidden) {
    audio.pause();
    return;
  }
  const file = './media/' + chapters[index].slide.id + '.m4a';
  if (audio.getAttribute('src') !== file) audio.src = file;
  const offset = elapsed / 1000;
  if (Number.isFinite(audio.duration) && offset >= audio.duration) {
    audio.pause();
    return;
  }
  audio.currentTime = offset;
  audio.play().catch(error => {
    if (attempt === audioAttempt && error.name !== 'AbortError') {
      audioOff('旁白暂不可用，继续播放字幕。');
    }
  });
}

function activeClock() {
  cancelAnimationFrame(frame);
  lastTick = null;
  if (running && !document.hidden) frame = requestAnimationFrame(tick);
  syncAudio();
}

function setPlaying(value) {
  running = value;
  play.textContent = running ? '暂停' : finished ? '再看一遍' : '播放';
  activeClock();
}

function seek(chapter, speak, offset = 0) {
  index = chapter;
  elapsed = offset;
  finished = false;
  if (speak) setPlaying(false);
  showChapter(speak);
}

function tick(now) {
  if (!running || document.hidden) return;
  if (lastTick !== null) elapsed += now - lastTick;
  lastTick = now;
  while (elapsed >= chapters[index].length) {
    const carry = elapsed - chapters[index].length;
    if (index === chapters.length - 1 && !loop) {
      elapsed = chapters[index].length;
      finished = true;
      renderProgress();
      setPlaying(false);
      announce.textContent = '路演播放完毕。';
      return;
    }
    seek((index + 1) % chapters.length, false, carry);
    syncAudio();
  }
  renderProgress();
  if (enabled && !audio.paused && !audio.seeking && Math.abs(audio.currentTime - elapsed / 1000) > 0.45) {
    audio.currentTime = elapsed / 1000;
  }
  frame = requestAnimationFrame(tick);
}

function togglePlayback() {
  if (finished) seek(0, false);
  setPlaying(!running);
}

function move(delta) {
  const candidate = index + delta;
  if (loop) seek((candidate + chapters.length) % chapters.length, true);
  else if (candidate >= 0 && candidate < chapters.length) seek(candidate, true);
}

async function toggleFullscreen() {
  try {
    if (document.fullscreenElement === deck) await document.exitFullscreen();
    else await deck.requestFullscreen();
  } catch {
    announce.textContent = '当前窗口暂时无法进入全屏。';
  }
}

play.addEventListener('click', togglePlayback);
prev.addEventListener('click', () => move(-1));
next.addEventListener('click', () => move(1));
select.addEventListener('change', () => seek(Number(select.value), true));
query('[data-restart]').addEventListener('click', () => {
  seek(0, true);
  setPlaying(true);
});
sound.addEventListener('click', () => {
  if (enabled) {
    audioOff('旁白已关闭。');
  } else {
    enabled = true;
    sound.textContent = '关闭旁白';
    if (finished) seek(0, false);
    setPlaying(true);
    if (enabled) announce.textContent = '旁白已开启。';
  }
});
audio.addEventListener('error', () => {
  if (enabled && audio.error) audioOff('旁白暂不可用，继续播放字幕。');
});
expand.addEventListener('click', toggleFullscreen);
document.addEventListener('fullscreenchange', () => {
  expand.textContent = document.fullscreenElement === deck ? '退出全屏' : '全屏';
});
document.addEventListener('visibilitychange', activeClock);
reducedMotion.addEventListener('change', event => {
  if (event.matches && running) setPlaying(false);
});
player.addEventListener('focusin', event => {
  if (running && event.target.matches('a, select, [data-copy]')) setPlaying(false);
});
query('.deck-stage').addEventListener('pointerover', event => {
  if (running && event.pointerType === 'mouse' && event.target.closest('a, button')) setPlaying(false);
});
document.addEventListener('keydown', event => {
  if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || event.repeat) return;
  if (event.target.closest('input, select, textarea, [contenteditable]')) return;
  switch (event.key) {
    case 'ArrowLeft': move(-1); break;
    case 'ArrowRight': move(1); break;
    case 'Home': seek(0, true); break;
    case 'End': seek(chapters.length - 1, true); break;
    case ' ':
      if (event.target.closest('a, button')) return;
      togglePlayback();
      break;
    case 'f': case 'F':
      if (!document.fullscreenEnabled) return;
      toggleFullscreen();
      break;
    default: return;
  }
  event.preventDefault();
});

query('[data-copy]').addEventListener('click', async () => {
  const prompt = query('#demo-prompt');
  const status = query('.copy-status');
  try {
    await navigator.clipboard.writeText(prompt.textContent);
    status.textContent = '已复制。';
  } catch {
    const range = document.createRange();
    range.selectNodeContents(prompt);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    status.textContent = '提示词已选中，按 Ctrl+C 或长按复制。';
  }
});

showChapter();
if (loop && target === -1 && !reducedMotion.matches) setPlaying(true);
