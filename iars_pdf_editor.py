"""IARS PDF textbox editor v2.2 using Streamlit Components v2.

The component is implemented with native browser pointer events, so dragging and
resizing happen entirely in the frontend and do not rerun Streamlit until the
interaction is completed.
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
  min-width: 64px;
  min-height: 28px;
  border: 2px solid #111827;
  background: rgba(255, 255, 255, 0.94);
  color: #111827;
  z-index: 3;
}

.tag-box.selected {
  outline: 2px dashed #2563eb;
  outline-offset: 3px;
  z-index: 5;
}

.tag-box.highlight {
  background: rgba(254, 249, 195, 0.94);
}

.tag-box.plain {
  border-color: transparent;
  background: transparent;
}

.drag-strip {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  height: 15px;
  cursor: move;
  background: transparent;
  z-index: 2;
}

.tag-box.selected .drag-strip::after {
  content: "⋮⋮ move";
  position: absolute;
  top: -20px;
  left: -2px;
  padding: 1px 5px;
  border-radius: 4px;
  background: #2563eb;
  color: #ffffff;
  font-size: 10px;
  line-height: 15px;
  white-space: nowrap;
  pointer-events: none;
}

.tag-text {
  position: absolute;
  inset: 0;
  box-sizing: border-box;
  padding: 15px 7px 5px 7px;
  overflow: auto;
  outline: none;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  user-select: text;
  cursor: text;
  line-height: 1.18;
}

.tag-text:empty::before {
  content: "Click here and type, e.g. Task ID: 001";
  color: #6b7280;
  font-style: italic;
  pointer-events: none;
}

.resize-handle {
  position: absolute;
  width: 11px;
  height: 11px;
  box-sizing: border-box;
  border: 1px solid #ffffff;
  background: #2563eb;
  display: none;
  z-index: 10;
}

.tag-box.selected .resize-handle {
  display: block;
}

.resize-handle[data-dir="nw"] { left: -7px; top: -7px; cursor: nwse-resize; }
.resize-handle[data-dir="n"]  { left: calc(50% - 5px); top: -7px; cursor: ns-resize; }
.resize-handle[data-dir="ne"] { right: -7px; top: -7px; cursor: nesw-resize; }
.resize-handle[data-dir="e"]  { right: -7px; top: calc(50% - 5px); cursor: ew-resize; }
.resize-handle[data-dir="se"] { right: -7px; bottom: -7px; cursor: nwse-resize; }
.resize-handle[data-dir="s"]  { left: calc(50% - 5px); bottom: -7px; cursor: ns-resize; }
.resize-handle[data-dir="sw"] { left: -7px; bottom: -7px; cursor: nesw-resize; }
.resize-handle[data-dir="w"]  { left: -7px; top: calc(50% - 5px); cursor: ew-resize; }

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
  const deleteButton = parentElement.querySelector('#delete-box');
  const duplicateButton = parentElement.querySelector('#duplicate-box');
  const clearButton = parentElement.querySelector('#clear-page');
  const zoomInButton = parentElement.querySelector('#zoom-in');
  const zoomOutButton = parentElement.querySelector('#zoom-out');
  const zoomFitButton = parentElement.querySelector('#zoom-fit');

  let editor = data?.editor ?? { boxes: [], selected_id: null };
  let boxes = Array.isArray(editor.boxes) ? structuredClone(editor.boxes) : [];
  let selectedId = editor.selected_id ?? null;
  let zoom = Number(data?.zoom ?? 1);
  let operation = null;
  let lastRightClick = { time: 0, x: 0, y: 0 };
  let contextHint = null;

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const makeId = () => `tag_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  const currentBox = () => boxes.find((box) => box.id === selectedId) ?? null;

  function normalizedBoxes() {
    return boxes.map((box) => ({
      id: String(box.id),
      x_pct: Number(box.x_pct),
      y_pct: Number(box.y_pct),
      w_pct: Number(box.w_pct),
      h_pct: Number(box.h_pct),
      text: String(box.text ?? ''),
      style: String(box.style ?? 'Box'),
      font_size: Number(box.font_size ?? 11),
    }));
  }

  function commit() {
    setStateValue('editor', {
      boxes: normalizedBoxes(),
      selected_id: selectedId,
    });
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
    deleteButton.disabled = !selectedId;
    duplicateButton.disabled = !selectedId;
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

  function createBoxAt(clientX, clientY) {
    const rect = stage.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const xPct = clamp(((clientX - rect.left) / rect.width) * 100, 0, 92);
    const yPct = clamp(((clientY - rect.top) / rect.height) * 100, 0, 94);
    const box = {
      id: makeId(),
      x_pct: xPct,
      y_pct: yPct,
      w_pct: Math.min(32, 98 - xPct),
      h_pct: Math.min(7, 98 - yPct),
      text: '',
      style: 'Box',
      font_size: 11,
    };
    boxes.push(box);
    selectedId = box.id;
    renderBoxes();
    commit();
    window.setTimeout(() => {
      const text = layer.querySelector(`[data-box-id="${box.id}"] .tag-text`);
      if (text) text.focus();
    }, 40);
    setStatus('Textbox added. Click inside to type; drag the top strip to move; drag blue handles to resize.');
  }

  function boxStyleClass(style) {
    if (style === 'Highlight Box') return ' highlight';
    if (style === 'Plain Text') return ' plain';
    return '';
  }

  function renderBoxes() {
    layer.replaceChildren();
    boxes.forEach((box) => {
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
      textElement.innerText = box.text ?? '';
      textElement.addEventListener('pointerdown', (event) => {
        // Do not rebuild the box DOM here. Replacing the contenteditable element
        // during pointerdown prevents the browser from placing the caret.
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
      });
      textElement.addEventListener('blur', () => {
        box.text = textElement.innerText.trim();
        commit();
      });
      textElement.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault();
          box.text = textElement.innerText.trim();
          textElement.blur();
        }
        if (event.key === 'Escape') {
          textElement.blur();
        }
      });

      boxElement.addEventListener('pointerdown', (event) => {
        if (event.target === boxElement) {
          selectBox(box.id);
        }
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
      const minW = Math.max(4, (64 / operation.stageWidth) * 100);
      const minH = Math.max(2.5, (28 / operation.stageHeight) * 100);

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
    }

    const element = layer.querySelector(`[data-box-id="${box.id}"]`);
    if (element) {
      element.style.left = `${box.x_pct}%`;
      element.style.top = `${box.y_pct}%`;
      element.style.width = `${box.w_pct}%`;
      element.style.height = `${box.h_pct}%`;
    }
  }

  function finishOperation() {
    if (!operation) return;
    operation = null;
    commit();
  }

  function deleteSelected() {
    if (!selectedId) return;
    boxes = boxes.filter((box) => box.id !== selectedId);
    selectedId = null;
    renderBoxes();
    commit();
    setStatus('Textbox deleted.');
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
    commit();
    setStatus('Textbox duplicated.');
  }

  function clearPage() {
    if (boxes.length && !window.confirm('Remove all textboxes from this page?')) return;
    boxes = [];
    selectedId = null;
    renderBoxes();
    commit();
    setStatus('All textboxes on this page were removed.');
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
    if (!editing && event.key === 'Escape') {
      selectBox(null);
    }
  }

  layer.addEventListener('contextmenu', handleContextMenu);
  layer.addEventListener('pointerdown', (event) => {
    if (event.target === layer) selectBox(null);
  });
  window.addEventListener('pointermove', updateOperation);
  window.addEventListener('pointerup', finishOperation);
  window.addEventListener('pointercancel', finishOperation);
  window.addEventListener('keydown', handleKeydown);
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
    if (selectedId) {
      window.setTimeout(() => {
        const selectedText = layer.querySelector(`[data-box-id="${selectedId}"] .tag-text`);
        if (selectedText && !selectedText.innerText.trim()) selectedText.focus();
      }, 60);
    }
  };
  image.src = data?.image_data ?? '';
  setStatus(data?.status_text ?? 'Double-right-click the PDF to add a textbox.');
  renderBoxes();

  return () => {
    layer.removeEventListener('contextmenu', handleContextMenu);
    window.removeEventListener('pointermove', updateOperation);
    window.removeEventListener('pointerup', finishOperation);
    window.removeEventListener('pointercancel', finishOperation);
    window.removeEventListener('keydown', handleKeydown);
    if (contextHint) contextHint.remove();
  };
}
"""


_PDF_EDITOR_COMPONENT = st.components.v2.component(
    name="iars_pdf_textbox_editor_v22",
    html=EDITOR_HTML,
    css=EDITOR_CSS,
    js=EDITOR_JS,
    isolate_styles=True,
)


def pdf_textbox_editor(
    *,
    image_data: str,
    initial_boxes: list[dict[str, Any]] | None = None,
    key: str,
    height: int = 920,
):
    """Mount the editor and return the Streamlit component result."""
    initial_editor = {
        "boxes": initial_boxes or [],
        "selected_id": None,
    }
    component_state = st.session_state.get(key, {})
    try:
        current_editor = component_state.get("editor", initial_editor)
    except AttributeError:
        current_editor = getattr(component_state, "editor", initial_editor)

    return _PDF_EDITOR_COMPONENT(
        data={
            "image_data": image_data,
            "editor": current_editor,
            "zoom": 1.0,
            "status_text": "Double-right-click the PDF to add a textbox.",
        },
        default={"editor": current_editor},
        key=key,
        on_editor_change=lambda: None,
        width="stretch",
        height=height,
    )
