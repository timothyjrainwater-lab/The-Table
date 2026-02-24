/**
 * NotebookRadial — right-click tool-selection panel for the notebook.
 *
 * Doctrine authority: DOCTRINE_04_TABLE_UI_MEMO_V4 §8 (MARK wedge only);
 *   TABLE_METAPHOR_AND_PLAYER_ARTIFACTS.md §Part 2 §5.
 *
 * Tools: Pen / Brush / Eraser / Text / Cancel.
 * Colors: 6 ink colors.
 * Sizes: 3 stroke sizes (thin / normal / thick).
 * No game-action wedges (no ROLL / CAST / ATTACK — DOCTRINE_04 §8 hard ban).
 * HTML overlay — appears at cursor position, dismisses on selection or Escape.
 */

export type RadialTool = 'pen' | 'brush' | 'eraser' | 'text' | null;

export interface RadialSelection {
  tool:  RadialTool;
  color: string;   // hex
  size:  number;   // 0 = tool default
}

const INK_COLORS = [
  { label: '●', hex: '#1a0e06', title: 'Ink (dark brown)' },
  { label: '●', hex: '#1a1a6e', title: 'Blue' },
  { label: '●', hex: '#8b1a1a', title: 'Red' },
  { label: '●', hex: '#1a5c1a', title: 'Green' },
  { label: '●', hex: '#4a2a7a', title: 'Purple' },
  { label: '●', hex: '#7a4a10', title: 'Amber' },
];

const TOOL_SIZES = [
  { label: 'Fine',   size: 1.2,  title: 'Fine stroke' },
  { label: 'Normal', size: 0,    title: 'Normal (tool default)' },
  { label: 'Thick',  size: 8,    title: 'Thick stroke' },
];

export class NotebookRadial {
  private _el:       HTMLDivElement;
  private _visible   = false;
  private _onSelect: (sel: RadialSelection) => void;

  // Current color/size state — persists across radial opens
  private _color: string = '#1a0e06';
  private _size:  number = 0;

  constructor(onSelect: (sel: RadialSelection) => void) {
    this._onSelect = onSelect;
    this._el = document.createElement('div');
    this._el.id = 'nb-radial';
    Object.assign(this._el.style, {
      display:       'none',
      position:      'fixed',
      width:         '220px',
      background:    'rgba(22, 14, 6, 0.96)',
      border:        '1.5px solid #a08040',
      borderRadius:  '8px',
      boxShadow:     '0 6px 28px rgba(0,0,0,0.8)',
      zIndex:        '9999',
      pointerEvents: 'auto',
      userSelect:    'none',
      padding:       '8px',
      fontFamily:    'Georgia, serif',
    });

    this._buildPanel();
    document.body.appendChild(this._el);

    // Dismiss on outside click
    document.addEventListener('pointerdown', (ev) => {
      if (this._visible && !this._el.contains(ev.target as Node)) {
        this.hide();
      }
    });
    // Dismiss on Escape
    document.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape' && this._visible) { this.hide(); this._onSelect({ tool: null, color: this._color, size: this._size }); }
    });
  }

  show(screenX: number, screenY: number): void {
    this._el.style.left    = `${Math.min(screenX - 10, window.innerWidth  - 240)}px`;
    this._el.style.top     = `${Math.min(screenY - 10, window.innerHeight - 220)}px`;
    this._el.style.display = 'block';
    this._visible = true;
  }

  hide(): void {
    this._el.style.display = 'none';
    this._visible = false;
  }

  get isVisible(): boolean { return this._visible; }

  private _buildPanel(): void {
    // --- Section label helper ---
    const sectionLabel = (text: string): HTMLDivElement => {
      const d = document.createElement('div');
      d.textContent = text;
      Object.assign(d.style, {
        color: '#a08040', fontSize: '9px', letterSpacing: '0.08em',
        marginBottom: '4px', marginTop: '6px', textTransform: 'uppercase',
      });
      return d;
    };

    // --- Tool buttons ---
    this._el.appendChild(sectionLabel('Tool'));
    const toolRow = document.createElement('div');
    Object.assign(toolRow.style, { display: 'flex', gap: '4px', flexWrap: 'wrap' });

    const tools: { label: string; tool: RadialTool; cancel?: boolean }[] = [
      { label: '✏ Pen',    tool: 'pen'    },
      { label: '🖌 Brush', tool: 'brush'  },
      { label: '⊘ Erase',  tool: 'eraser' },
      { label: 'T Text',   tool: 'text'   },
      { label: '✕ Cancel', tool: null, cancel: true },
    ];

    tools.forEach(({ label, tool, cancel }) => {
      const btn = this._makeBtn(label, cancel ? 'rgba(80,20,10,0.85)' : 'rgba(50,32,10,0.9)');
      btn.addEventListener('pointerdown', (ev) => {
        ev.stopPropagation();
        this.hide();
        this._onSelect({ tool, color: this._color, size: this._size });
      });
      toolRow.appendChild(btn);
    });
    this._el.appendChild(toolRow);

    // --- Color swatches ---
    this._el.appendChild(sectionLabel('Color'));
    const colorRow = document.createElement('div');
    Object.assign(colorRow.style, { display: 'flex', gap: '5px', alignItems: 'center' });

    let activeColorSwatch: HTMLButtonElement | null = null;

    INK_COLORS.forEach(({ hex, title }) => {
      const swatch = document.createElement('button');
      Object.assign(swatch.style, {
        width: '22px', height: '22px', borderRadius: '50%',
        background: hex, border: '2px solid #555', cursor: 'pointer', padding: '0',
        outline: 'none', flexShrink: '0',
      });
      swatch.title = title;
      if (hex === this._color) {
        swatch.style.border = '2px solid #d4b878';
        activeColorSwatch = swatch;
      }
      swatch.addEventListener('pointerdown', (ev) => {
        ev.stopPropagation();
        this._color = hex;
        // Update borders
        if (activeColorSwatch) activeColorSwatch.style.border = '2px solid #555';
        swatch.style.border = '2px solid #d4b878';
        activeColorSwatch = swatch;
      });
      colorRow.appendChild(swatch);
    });
    this._el.appendChild(colorRow);

    // --- Size buttons ---
    this._el.appendChild(sectionLabel('Size'));
    const sizeRow = document.createElement('div');
    Object.assign(sizeRow.style, { display: 'flex', gap: '4px' });

    let activeSizeBtn: HTMLButtonElement | null = null;

    TOOL_SIZES.forEach(({ label, size, title }) => {
      const btn = this._makeBtn(label, 'rgba(50,32,10,0.9)', '36px');
      btn.title = title;
      if (size === this._size) {
        btn.style.borderColor = '#d4b878';
        activeSizeBtn = btn;
      }
      btn.addEventListener('pointerdown', (ev) => {
        ev.stopPropagation();
        this._size = size;
        if (activeSizeBtn) activeSizeBtn.style.borderColor = '#7a5a20';
        btn.style.borderColor = '#d4b878';
        activeSizeBtn = btn;
      });
      sizeRow.appendChild(btn);
    });
    this._el.appendChild(sizeRow);
  }

  private _makeBtn(label: string, bg: string, width = '54px'): HTMLButtonElement {
    const btn = document.createElement('button');
    btn.textContent = label;
    Object.assign(btn.style, {
      width, height: '26px', fontSize: '11px', fontFamily: 'Georgia, serif',
      background: bg, color: '#d4b878', border: '1px solid #7a5a20',
      borderRadius: '4px', cursor: 'pointer', padding: '2px 4px',
      whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
      lineHeight: '1.2',
    });
    btn.addEventListener('pointerenter', () => {
      btn.style.background = 'rgba(100,70,20,0.95)';
      btn.style.borderColor = '#d4b878';
    });
    btn.addEventListener('pointerleave', () => {
      btn.style.background = bg;
      // Don't reset border — may be active
    });
    return btn;
  }
}
