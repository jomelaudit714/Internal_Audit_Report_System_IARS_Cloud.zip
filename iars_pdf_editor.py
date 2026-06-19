"""IARS PDF textbox editor v2.4.

Fixes in this version:
- one persistent component state for all PDF pages
- browser-local backup while typing, so page changes cannot discard text
- tighter text padding and single-line labels
- automatic font fitting after typing/resizing
- Fit text toolbar action
- component registration repeated safely on every Streamlit rerun
"""
from __future__ import annotations

from typing import Any

import streamlit as st


EDITOR_HTML = r"""
<div class="iars-pdf-editor">
  <div class="editor-toolbar">
    <div class="toolbar-group">
      <button type="button" id="zoom-out" title="Zoom out">−</button>
      <span id="zoom-label">100%</span>
      <button type="button" id="zoom-in" title="Zoom in">+</button>
      <button type="button" id="zoom-fit" title="Fit width">Fit width</button>
    </div>
    <div class="toolbar-group">
      <button type="button" id="fit-text" disabled>Fit text</button>
      <button type="button" id="duplicate-box" disabled>Duplicate</button>
      <button type="button" id="delete-box" class="danger" disabled>Delete</button>
      <button type="button" id="clear-page" class="danger-light">Clear page</button>
    </div>
    <div class="toolbar-group status-group">
      <span id="editor-status">Double-right-click the PDF to add a textbox.</span>
    </div>
  </div>
  <div class="editor-viewport" id="editor-viewport">
    <div class="page-stage" id="page-stage">
      <img id="page-image" alt="PDF page preview" draggable="false" />
      <div class="box-layer" id="box-layer"></div>
    </div>
  </div>
</div>
"""


EDITOR_CSS = r"""
:host {
  display: block;
  width: 100%;
  height: 100%;
  font-family: var(--st-font, Arial, sans-serif);
  color: var(--st-text-color, #1f2937);
}

.iars-pdf-editor {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--st-text-color, #111827) 20%, transparent);
  border-radius: 10px;
  background: var(--st-background-color, #ffffff);
}

.editor-toolbar {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 8px 10px;
  border-bottom: 1px solid color-mix(in srgb, var(--st-text-color, #111827) 18%, transparent);
  background: var(--st-secondary-background-color, #f3f4f6);
  z-index: 20;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-group {
  min-width: 260px;
  flex: 1 1 320px;
}

#editor-status {
  font-size: 0.84rem;
  line-height: 1.25;
  color: color-mix(in srgb, var(--st-text-color, #111827) 72%, transparent);
}

button {
  appearance: none;
  border: 1px solid color-mix(in srgb, var(--st-text-color, #111827) 28%, transparent);
  border-radius: 6px;
  padding: 5px 10px;
  background: var(--st-background-color, #ffffff);
  color: var(--st-text-color, #111827);
  cursor: pointer;
  font: inherit;
  font-size: 0.84rem;
  font-weight: 600;
}

button:hover:not(:disabled) {
  border-color: var(--st-primary-color, #ff4b4b);
}

button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

button.danger {
  color: #b91c1c;
  border-color: #fca5a5;
  background: #fef2f2;
}

button.danger-light {
  color: #991b1b;
}

#zoom-label {
  min-width: 45px;
  text-align: center;
  font-size: 0.84rem;
  font-variant-numeric: tabular-nums;
}

.editor-viewport {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  padding: 18px;
  background: #d7dbe0;
  overscroll-behavior: contain;
}

.page-stage {
  position: relative;
  margin: 0 auto;
  width: 100%;
  max-width: none;
  background: #ffffff;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.22);
  transform-origin: top center;
  user-select: none;
  touch-action: none;
}

#page-image {
  display: block;
  width: 100%;
  height: auto;
  pointer-events: none;
  user-select: none;
}

.box-layer {
  position: absolute;
  inset: 0;
  overflow: hidden;
  touch-action: none;
}

.tag-box {
  position: absolute;
  box-sizing: border-box;
  min-width: 34px;
  min-height: 16px;
  border: 1px solid #111827;
  background: rgba(255, 255, 255, 0.96);
  color: #111827;
  z-index: 3;
}

.tag-box.selected {
  outline: 2px dashed #2563eb;
  outline-offset: 2px;
  z-index: 5;
}

.tag-box.highlight {
  background: rgba(254, 249, 195, 0.96);
}

.tag-box.plain {
  border-color: transparent;
  background: transparent;
}

.drag-strip {
  position: absolute;
  left: -1px;
  top: -18px;
  width: 48px;
  height: 16px;
  box-sizing: border-box;
  border-radius: 4px 4px 0 0;
  cursor: move;
  background: #2563eb;
  color: #ffffff;
  display: none;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 700;
  line-height: 16px;
  z-index: 12;
  user-select: none;
}

.tag-box.selected .drag-strip {
  display: flex;
}

.drag-strip::after {
  content: "move";
}

.tag-text {
  position: absolute;
  inset: 0;
  box-sizing: border-box;
  padding: 1px 3px;
  overflow-x: auto;
  overflow-y: hidden;
  outline: none;
  white-space: nowrap;
  user-select: text;
  cursor: text;
  line-height: 1.05;
  scrollbar-width: none;
}

.tag-text::-webkit-scrollbar {
  display: none;
}

.tag-text:empty::before {
  content: "Type here";
  color: #6b7280;
  font-style: italic;
  pointer-events: none;
}

.resize-handle {
  position: absolute;
  width: 9px;
  height: 9px;
  box-sizing: border-box;
  border: 1px solid #ffffff;
  background: #2563eb;
  display: none;
  z-index: 14;
}

.tag-box.selected .resize-handle {
  display: block;
}

.resize-handle[data-dir="nw"] { left: -6px; top: -6px; cursor: nwse-resize; }
.resize-handle[data-dir="n"]  { left: calc(50% - 4px); top: -6px; cursor: ns-resize; }
.resize-handle[data-dir="ne"] { right: -6px; top: -6px; cursor: nesw-resize; }
.resize-handle[data-dir="e"]  { right: -6px; top: calc(50% - 4px); cursor: ew-resize; }
.resize-handle[data-dir="se"] { right: -6px; bottom: -6px; cursor: nwse-resize; }
.resize-handle[data-dir="s"]  { left: calc(50% - 4px); bottom: -6px; cursor: ns-resize; }
.resize-handle[data-dir="sw"] { left: -6px; bottom: -6px; cursor: nesw-resize; }
.resize-handle[data-dir="w"]  { left: -6px; top: calc(50% - 4px); cursor: ew-resize; }

.context-hint {
  position: fixed;
  z-index: 1000;
  padding: 5px 8px;
  border-radius: 5px;
  background: rgba(17, 24, 39, 0.94);
  color: white;
  font-size: 12px;
  pointer-events: none;
  transform: translate(8px, 8px);
}
"""


EDITOR_JS = r"""
export default function(component) {
  const { parentElement, data, setStateValue } = component;
  const root = parentElement.querySelector('.iars-pdf-editor');
  const viewport = parentElement.querySelector('#editor-viewport');
  const stage = parentElement.querySelector('#page-stage');
  const image = parentElement.querySelector('#page-image');
  const layer = parentElement.querySelector('#box-layer');
  const status = parentElement.querySelector('#editor-status');
  const zoomLabel = parentElement.querySelector('#zoom-label');
  const fitTextButton = parentElement.querySelector('#fit-text');
  const deleteButton = parentElement.querySelector('#delete-box');
  const duplicateButton = parentElement.querySelector('#duplicate-box');
  const clearButton = parentElement.querySelector('#clear-page');
  const zoomInButton = parentElement.querySelector('#zoom-in');
  const zoomOutButton = parentElement.querySelector('#zoom-out');
  const zoomFitButton = parentElement.querySelector('#zoom-fit');

  const pageNumber = Number(data?.page_number ?? 1);
  const pageKey = String(pageNumber);
  const storageKey = String(data?.storage_key ?? 'iars_pdf_editor_backup');
  const pythonEditor = data?.editor ?? {};

  function readLocalEditor() {
    try {
      const raw = window.localStorage.getItem(storageKey);
      return raw ? JSON.parse(raw) : null;
    } catch (_) {
      return null;
    }
  }

  const localEditor = readLocalEditor();
  const pythonUpdated = Number(pythonEditor?.updated_at ?? 0);
  const localUpdated = Number(localEditor?.updated_at ?? 0);
  let editor = localEditor && localUpdated > pythonUpdated ? localEditor : pythonEditor;

  let pages = editor?.pages && typeof editor.pages === 'object'
    ? structuredClone(editor.pages)
    : {};

  // Migration support for the v2.2 single-page state shape.
  if (Array.isArray(editor?.boxes) && !Array.isArray(pages[pageKey])) {
    pages[pageKey] = structuredClone(editor.boxes);
  }

  let boxes = Array.isArray(pages[pageKey]) ? structuredClone(pages[pageKey]) : [];
  let selectedId = Number(editor?.active_page ?? pageNumber) === pageNumber
    ? (editor?.selected_id ?? null)
    : null;
  let zoom = Number(data?.zoom ?? 1);
  let operation = null;
  let lastRightClick = { time: 0, x: 0, y: 0 };
  let contextHint = null;
  let lastSnapshot = null;

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const makeId = () => `tag_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  const currentBox = () => boxes.find((box) => box.id === selectedId) ?? null;

  function normalizeText(value) {
    return String(value ?? '').replace(/[\r\n]+/g, ' ').replace(/\s+/g, ' ').trim();
  }

  function normalizedBoxes() {
    return boxes.map((box) => ({
      id: String(box.id),
      x_pct: Number(box.x_pct),
      y_pct: Number(box.y_pct),
      w_pct: Number(box.w_pct),
      h_pct: Number(box.h_pct),
      text: normalizeText(box.text),
      style: String(box.style ?? 'Box'),
      font_size: Number(box.font_size ?? 11),
      base_font_size: Number(box.base_font_size ?? 11),
    }));
  }

  function snapshot() {
    pages[pageKey] = normalizedBoxes();
    lastSnapshot = {
      pages: structuredClone(pages),
      selected_id: selectedId,
      active_page: pageNumber,
      updated_at: Date.now(),
    };
    return lastSnapshot;
  }

  function saveLocal() {
    const value = snapshot();
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(value));
    } catch (_) {
      // Browser storage may be disabled; Streamlit state remains the fallback.
    }
    return value;
  }

  function commit(message = 'Saved.') {
    const value = saveLocal();
    setStateValue('editor', value);
    setStatus(message);
  }

  function setStatus(message) {
    status.textContent = message;
  }

  function setZoom(nextZoom) {
    zoom = clamp(nextZoom, 0.6, 2.5);
    stage.style.width = `${zoom * 100}%`;
    zoomLabel.textContent = `${Math.round(zoom * 100)}%`;
  }

  function fitWidth() {
    zoom = 1;
    stage.style.width = '100%';
    zoomLabel.textContent = 'Fit';
    viewport.scrollLeft = 0;
  }

  function refreshSelectionStyles() {
    layer.querySelectorAll('.tag-box').forEach((element) => {
      element.classList.toggle('selected', element.dataset.boxId === selectedId);
    });
    const disabled = !selectedId;
    deleteButton.disabled = disabled;
    duplicateButton.disabled = disabled;
    fitTextButton.disabled = disabled;
  }

  function selectBox(id) {
    selectedId = id;
    refreshSelectionStyles();
  }

  function showContextHint(clientX, clientY, message) {
    if (contextHint) contextHint.remove();
    contextHint = document.createElement('div');
    contextHint.className = 'context-hint';
    contextHint.textContent = message;
    contextHint.style.left = `${clientX}px`;
    contextHint.style.top = `${clientY}px`;
    document.body.appendChild(contextHint);
    window.setTimeout(() => {
      if (contextHint) {
        contextHint.remove();
        contextHint = null;
      }
    }, 800);
  }

  function fitFontToBox(box) {
    if (!box || !stage.getBoundingClientRect().width) return;
    const stageRect = stage.getBoundingClientRect();
    const text = normalizeText(box.text);
    const baseSize = Number(box.base_font_size ?? 11);
    const availableWidth = Math.max(1, (box.w_pct / 100) * stageRect.width - 6);
    const availableHeight = Math.max(1, (box.h_pct / 100) * stageRect.height - 2);
    let size = Math.min(baseSize, Math.max(6, availableHeight * 0.78));

    if (text) {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.font = `${size}px Arial, sans-serif`;
        const measured = Math.max(1, ctx.measureText(text).width);
        if (measured > availableWidth) {
          size = Math.max(6, size * (availableWidth / measured));
        }
      }
    }
    box.font_size = Math.round(size * 10) / 10;
  }

  function fitSelectedToText() {
    const box = currentBox();
    if (!box) return;
    const stageRect = stage.getBoundingClientRect();
    const element = layer.querySelector(`[data-box-id="${box.id}"]`);
    const textElement = element?.querySelector('.tag-text');
    if (!stageRect.width || !stageRect.height || !textElement) return;

    const baseSize = Number(box.base_font_size ?? 11);
    textElement.style.fontSize = `${baseSize}px`;
    const desiredWidthPx = clamp(textElement.scrollWidth + 8, 34, stageRect.width * 0.75);
    const desiredHeightPx = clamp(Math.max(baseSize + 6, 18), 16, 40);
    box.w_pct = Math.min((desiredWidthPx / stageRect.width) * 100, 100 - box.x_pct);
    box.h_pct = Math.min((desiredHeightPx / stageRect.height) * 100, 100 - box.y_pct);
    fitFontToBox(box);
    renderBoxes();
    commit('Textbox fitted closely to its text.');
  }

  function createBoxAt(clientX, clientY) {
    const rect = stage.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const xPct = clamp(((clientX - rect.left) / rect.width) * 100, 0, 96);
    const yPct = clamp(((clientY - rect.top) / rect.height) * 100, 0, 97);
    const defaultWidthPct = clamp((180 / rect.width) * 100, 15, 28);
    const defaultHeightPct = clamp((24 / rect.height) * 100, 1.6, 3.4);
    const box = {
      id: makeId(),
      x_pct: xPct,
      y_pct: yPct,
      w_pct: Math.min(defaultWidthPct, 99 - xPct),
      h_pct: Math.min(defaultHeightPct, 99 - yPct),
      text: '',
      style: 'Box',
      font_size: 11,
      base_font_size: 11,
    };
    boxes.push(box);
    selectedId = box.id;
    renderBoxes();
    commit('Textbox added and saved. Click inside to type.');
    window.setTimeout(() => {
      const text = layer.querySelector(`[data-box-id="${box.id}"] .tag-text`);
      if (text) text.focus({ preventScroll: true });
    }, 50);
  }

  function boxStyleClass(style) {
    if (style === 'Highlight Box') return ' highlight';
    if (style === 'Plain Text') return ' plain';
    return '';
  }

  function renderBoxes() {
    layer.replaceChildren();
    boxes.forEach((box) => {
      fitFontToBox(box);
      const boxElement = document.createElement('div');
      boxElement.className = `tag-box${box.id === selectedId ? ' selected' : ''}${boxStyleClass(box.style)}`;
      boxElement.dataset.boxId = box.id;
      boxElement.style.left = `${box.x_pct}%`;
      boxElement.style.top = `${box.y_pct}%`;
      boxElement.style.width = `${box.w_pct}%`;
      boxElement.style.height = `${box.h_pct}%`;

      const dragStrip = document.createElement('div');
      dragStrip.className = 'drag-strip';
      dragStrip.title = 'Drag to reposition';
      dragStrip.addEventListener('pointerdown', (event) => startDrag(event, box.id));

      const textElement = document.createElement('div');
      textElement.className = 'tag-text';
      textElement.contentEditable = 'true';
      textElement.spellcheck = false;
      textElement.tabIndex = 0;
      textElement.style.fontSize = `${box.font_size ?? 11}px`;
      textElement.innerText = normalizeText(box.text);
      textElement.addEventListener('pointerdown', (event) => {
        event.stopPropagation();
        selectBox(box.id);
      });
      textElement.addEventListener('click', (event) => {
        event.stopPropagation();
        selectBox(box.id);
        textElement.focus({ preventScroll: true });
      });
      textElement.addEventListener('focus', () => selectBox(box.id));
      textElement.addEventListener('input', () => {
        box.text = textElement.innerText;
        fitFontToBox(box);
        textElement.style.fontSize = `${box.font_size}px`;
        saveLocal();
        setStatus('Typing saved locally. Click outside or change page to sync.');
      });
      textElement.addEventListener('paste', (event) => {
        event.preventDefault();
        const pasted = normalizeText(event.clipboardData?.getData('text/plain') ?? '');
        document.execCommand('insertText', false, pasted);
      });
      textElement.addEventListener('blur', () => {
        box.text = normalizeText(textElement.innerText);
        textElement.innerText = box.text;
        fitFontToBox(box);
        commit('Text saved.');
      });
      textElement.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          box.text = normalizeText(textElement.innerText);
          textElement.blur();
        }
        if (event.key === 'Escape') {
          textElement.blur();
        }
      });

      boxElement.addEventListener('pointerdown', (event) => {
        if (event.target === boxElement) selectBox(box.id);
      });

      boxElement.appendChild(dragStrip);
      boxElement.appendChild(textElement);

      ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'].forEach((direction) => {
        const handle = document.createElement('div');
        handle.className = 'resize-handle';
        handle.dataset.dir = direction;
        handle.title = `Resize ${direction}`;
        handle.addEventListener('pointerdown', (event) => startResize(event, box.id, direction));
        boxElement.appendChild(handle);
      });

      layer.appendChild(boxElement);
    });
    refreshSelectionStyles();
  }

  function startDrag(event, id) {
    event.preventDefault();
    event.stopPropagation();
    selectBox(id);
    const box = boxes.find((item) => item.id === id);
    const rect = stage.getBoundingClientRect();
    operation = {
      type: 'drag', id, pointerId: event.pointerId,
      startX: event.clientX, startY: event.clientY,
      startBox: structuredClone(box), stageWidth: rect.width, stageHeight: rect.height,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function startResize(event, id, direction) {
    event.preventDefault();
    event.stopPropagation();
    selectBox(id);
    const box = boxes.find((item) => item.id === id);
    const rect = stage.getBoundingClientRect();
    operation = {
      type: 'resize', id, direction, pointerId: event.pointerId,
      startX: event.clientX, startY: event.clientY,
      startBox: structuredClone(box), stageWidth: rect.width, stageHeight: rect.height,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function updateOperation(event) {
    if (!operation) return;
    const box = boxes.find((item) => item.id === operation.id);
    if (!box) return;
    const dxPct = ((event.clientX - operation.startX) / operation.stageWidth) * 100;
    const dyPct = ((event.clientY - operation.startY) / operation.stageHeight) * 100;
    const start = operation.startBox;

    if (operation.type === 'drag') {
      box.x_pct = clamp(start.x_pct + dxPct, 0, 100 - start.w_pct);
      box.y_pct = clamp(start.y_pct + dyPct, 0, 100 - start.h_pct);
    } else {
      const dir = operation.direction;
      let x = start.x_pct;
      let y = start.y_pct;
      let w = start.w_pct;
      let h = start.h_pct;
      const minW = Math.max(2.5, (34 / operation.stageWidth) * 100);
      const minH = Math.max(1.2, (16 / operation.stageHeight) * 100);

      if (dir.includes('e')) w = clamp(start.w_pct + dxPct, minW, 100 - start.x_pct);
      if (dir.includes('s')) h = clamp(start.h_pct + dyPct, minH, 100 - start.y_pct);
      if (dir.includes('w')) {
        x = clamp(start.x_pct + dxPct, 0, start.x_pct + start.w_pct - minW);
        w = start.w_pct + (start.x_pct - x);
      }
      if (dir.includes('n')) {
        y = clamp(start.y_pct + dyPct, 0, start.y_pct + start.h_pct - minH);
        h = start.h_pct + (start.y_pct - y);
      }
      box.x_pct = x;
      box.y_pct = y;
      box.w_pct = w;
      box.h_pct = h;
      fitFontToBox(box);
    }

    const element = layer.querySelector(`[data-box-id="${box.id}"]`);
    if (element) {
      element.style.left = `${box.x_pct}%`;
      element.style.top = `${box.y_pct}%`;
      element.style.width = `${box.w_pct}%`;
      element.style.height = `${box.h_pct}%`;
      const textElement = element.querySelector('.tag-text');
      if (textElement) textElement.style.fontSize = `${box.font_size}px`;
    }
  }

  function finishOperation() {
    if (!operation) return;
    const finishedType = operation.type;
    operation = null;
    commit(finishedType === 'resize' ? 'Textbox resized and saved.' : 'Textbox repositioned and saved.');
  }

  function deleteSelected() {
    if (!selectedId) return;
    boxes = boxes.filter((box) => box.id !== selectedId);
    selectedId = null;
    renderBoxes();
    commit('Textbox deleted.');
  }

  function duplicateSelected() {
    const original = currentBox();
    if (!original) return;
    const duplicate = structuredClone(original);
    duplicate.id = makeId();
    duplicate.x_pct = clamp(original.x_pct + 2, 0, 100 - original.w_pct);
    duplicate.y_pct = clamp(original.y_pct + 2, 0, 100 - original.h_pct);
    boxes.push(duplicate);
    selectedId = duplicate.id;
    renderBoxes();
    commit('Textbox duplicated and saved.');
  }

  function clearPage() {
    if (boxes.length && !window.confirm('Remove all textboxes from this page?')) return;
    boxes = [];
    selectedId = null;
    renderBoxes();
    commit('All textboxes on this page were removed.');
  }

  function flushFocusedText() {
    const focused = layer.querySelector('.tag-text:focus');
    if (!focused) return false;
    const boxElement = focused.closest('.tag-box');
    const box = boxes.find((item) => item.id === boxElement?.dataset?.boxId);
    if (!box) return false;
    box.text = normalizeText(focused.innerText);
    focused.innerText = box.text;
    fitFontToBox(box);
    commit('Text saved before leaving the page.');
    return true;
  }

  function handleDocumentPointerDown(event) {
    const focused = layer.querySelector('.tag-text:focus');
    if (!focused) return;
    const path = event.composedPath?.() ?? [];
    if (!path.includes(focused)) flushFocusedText();
  }

  function handleContextMenu(event) {
    if (event.target.closest('.tag-box')) return;
    event.preventDefault();
    const now = performance.now();
    const distance = Math.hypot(event.clientX - lastRightClick.x, event.clientY - lastRightClick.y);
    if (now - lastRightClick.time <= 650 && distance <= 28) {
      lastRightClick = { time: 0, x: 0, y: 0 };
      createBoxAt(event.clientX, event.clientY);
    } else {
      lastRightClick = { time: now, x: event.clientX, y: event.clientY };
      showContextHint(event.clientX, event.clientY, 'Right-click again to add a textbox');
      setStatus('Right-click the same spot once more to add a textbox.');
    }
  }

  function handleKeydown(event) {
    const editing = event.composedPath().some(
      (node) => node?.classList?.contains?.('tag-text')
    );
    if (!editing && (event.key === 'Delete' || event.key === 'Backspace')) {
      event.preventDefault();
      deleteSelected();
    }
    if (!editing && event.key === 'Escape') selectBox(null);
  }

  layer.addEventListener('contextmenu', handleContextMenu);
  layer.addEventListener('pointerdown', (event) => {
    if (event.target === layer) selectBox(null);
  });
  document.addEventListener('pointerdown', handleDocumentPointerDown, true);
  window.addEventListener('pointermove', updateOperation);
  window.addEventListener('pointerup', finishOperation);
  window.addEventListener('pointercancel', finishOperation);
  window.addEventListener('pagehide', flushFocusedText);
  window.addEventListener('keydown', handleKeydown);
  fitTextButton.addEventListener('click', fitSelectedToText);
  deleteButton.addEventListener('click', deleteSelected);
  duplicateButton.addEventListener('click', duplicateSelected);
  clearButton.addEventListener('click', clearPage);
  zoomInButton.addEventListener('click', () => setZoom(zoom + 0.1));
  zoomOutButton.addEventListener('click', () => setZoom(zoom - 0.1));
  zoomFitButton.addEventListener('click', fitWidth);

  image.onload = () => {
    stage.style.aspectRatio = `${image.naturalWidth} / ${image.naturalHeight}`;
    setZoom(zoom);
    renderBoxes();
  };
  image.src = data?.image_data ?? '';
  setStatus(`Page ${pageNumber}. Double-right-click the PDF to add a textbox.`);
  renderBoxes();

  // If the browser-local copy is newer, immediately restore it to Streamlit.
  if (localEditor && localUpdated > pythonUpdated) {
    window.setTimeout(() => setStateValue('editor', snapshot()), 0);
  } else {
    saveLocal();
  }

  return () => {
    flushFocusedText();
    layer.removeEventListener('contextmenu', handleContextMenu);
    document.removeEventListener('pointerdown', handleDocumentPointerDown, true);
    window.removeEventListener('pointermove', updateOperation);
    window.removeEventListener('pointerup', finishOperation);
    window.removeEventListener('pointercancel', finishOperation);
    window.removeEventListener('pagehide', flushFocusedText);
    window.removeEventListener('keydown', handleKeydown);
    if (contextHint) contextHint.remove();
  };
}
"""


def _register_pdf_editor_component():
    """Register the Components v2 editor during every Streamlit script run.

    Streamlit rebuilds its component registry on each rerun, while imported Python
    modules remain cached. A module-level registration therefore exists only on
    the first run and causes "Component ... is not registered" after an upload
    or page change. Registering here keeps the component available on every run.
    """
    return st.components.v2.component(
        name="iars_pdf_textbox_editor_v24",
        html=EDITOR_HTML,
        css=EDITOR_CSS,
        js=EDITOR_JS,
        isolate_styles=True,
    )


def _read_editor_state(component_state: Any, default: dict[str, Any]) -> dict[str, Any]:
    if component_state is None:
        return default
    if isinstance(component_state, dict):
        value = component_state.get("editor", default)
    else:
        value = getattr(component_state, "editor", default)
    return value if isinstance(value, dict) else default


def pdf_textbox_editor(
    *,
    image_data: str,
    page_number: int,
    storage_key: str,
    key: str,
    height: int = 920,
):
    """Mount one persistent editor instance for all pages of one PDF."""
    initial_editor: dict[str, Any] = {
        "pages": {},
        "selected_id": None,
        "active_page": int(page_number),
        "updated_at": 0,
    }
    current_editor = _read_editor_state(st.session_state.get(key), initial_editor)

    component = _register_pdf_editor_component()

    return component(
        data={
            "image_data": image_data,
            "editor": current_editor,
            "page_number": int(page_number),
            "storage_key": storage_key,
            "zoom": 1.0,
        },
        default={"editor": current_editor},
        key=key,
        on_editor_change=lambda: None,
        width="stretch",
        height=height,
    )
