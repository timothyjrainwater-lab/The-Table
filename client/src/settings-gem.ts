import * as THREE from 'three';

const GEM_COLOR   = 0xcc1111;  // deep red
const GEM_GLOW    = 0xff3333;
const HOLD_MS     = 1500;

/**
 * SettingsGem — small red gemstone on table surface.
 *
 * Single tap → toggle settings overlay open/close.
 * Hold 1.5 s → reset all settings to defaults and close overlay.
 *
 * Doctrine §3: settings overlay is minimal HTML DOM (not Three.js).
 * Gate G compliant — deterministic only (no Math.random).
 * Gate: 3 regression tests in tests/test_ui_gate_gem.py
 */
export class SettingsGem {
  readonly mesh: THREE.Mesh;
  private _mat: THREE.MeshStandardMaterial;
  private _isOpen: boolean = false;
  private _holdTimer: ReturnType<typeof setTimeout> | null = null;
  private _overlayEl: HTMLElement | null = null;

  // Settings state (persisted in-memory; future: localStorage)
  volume: number   = 0.8;
  ttsVoice: string = 'npc_elderly';
  uiScale: number  = 1.0;

  constructor() {
    const geo = new THREE.OctahedronGeometry(0.08, 0);
    this._mat = new THREE.MeshStandardMaterial({
      color:             GEM_COLOR,
      emissive:          new THREE.Color(GEM_GLOW),
      emissiveIntensity: 0.3,
      roughness:         0.1,
      metalness:         0.8,
    });
    this.mesh          = new THREE.Mesh(geo, this._mat);
    this.mesh.name     = 'settings_gem';
    this.mesh.position.set(5.2, 0.08, 5.2);  // player shelf far-right corner, clear of dice station
    this.mesh.castShadow = true;
  }

  // -------------------------------------------------------------------------
  // Pointer event API — called by main.ts raycast handlers
  // -------------------------------------------------------------------------

  /** Called on pointerdown hit. Starts 1.5 s hold timer. */
  onPointerDown(): void {
    this._holdTimer = setTimeout(() => {
      this._holdTimer = null;
      this.resetDefaults();
    }, HOLD_MS);
  }

  /**
   * Called on pointerup hit.
   * If the hold timer is still running (short tap), cancel it and toggle.
   * If hold already fired, do nothing.
   */
  onPointerUp(): void {
    if (this._holdTimer !== null) {
      clearTimeout(this._holdTimer);
      this._holdTimer = null;
      this.toggle();
    }
  }

  // -------------------------------------------------------------------------
  // State transitions
  // -------------------------------------------------------------------------

  toggle(): void {
    if (this._isOpen) this.close();
    else               this.open();
  }

  open(): void {
    this._isOpen = true;
    this._mat.emissiveIntensity = 0.8;
    this._showOverlay();
  }

  close(): void {
    this._isOpen = false;
    this._mat.emissiveIntensity = 0.3;
    this._hideOverlay();
  }

  resetDefaults(): void {
    this.volume   = 0.8;
    this.ttsVoice = 'npc_elderly';
    this.uiScale  = 1.0;
    this.close();
  }

  get isOpen(): boolean { return this._isOpen; }

  // -------------------------------------------------------------------------
  // DOM overlay
  // -------------------------------------------------------------------------

  private _showOverlay(): void {
    let el = document.getElementById('settings-overlay');
    if (!el) {
      el = document.createElement('div');
      el.id = 'settings-overlay';
      el.style.cssText = [
        'position:fixed',
        'top:50%',
        'left:50%',
        'transform:translate(-50%,-50%)',
        'background:rgba(10,8,4,0.92)',
        'border:1px solid #8a6a3a',
        'border-radius:6px',
        'padding:20px 28px',
        'color:#d4b878',
        'font-family:Georgia,serif',
        'font-size:14px',
        'z-index:50',
        'min-width:260px',
        'pointer-events:auto',
      ].join(';');
      el.innerHTML = `
        <div style="font-size:16px;margin-bottom:14px;letter-spacing:0.06em">SETTINGS</div>
        <label>Volume<br>
          <input id="s-volume" type="range" min="0" max="1" step="0.05"
            value="${this.volume}" style="width:200px">
        </label><br><br>
        <label>TTS Voice<br>
          <select id="s-voice">
            <option value="npc_elderly">Narrator (elderly)</option>
            <option value="dm_narrator">DM Narrator</option>
            <option value="npc_female">NPC Female</option>
            <option value="npc_male">NPC Male</option>
          </select>
        </label><br><br>
        <label>UI Scale<br>
          <select id="s-scale">
            <option value="0.8">Small</option>
            <option value="1.0" selected>Normal</option>
            <option value="1.2">Large</option>
          </select>
        </label><br><br>
        <button id="s-close"
          style="background:#3a2a1a;color:#d4b878;border:1px solid #8a6a3a;border-radius:4px;padding:4px 16px;cursor:pointer;font-family:Georgia,serif">
          Close
        </button>
      `;
      document.body.appendChild(el);

      // Wire close button
      document.getElementById('s-close')!.addEventListener('click', () => this.close());

      // Sync volume changes back to state
      document.getElementById('s-volume')!.addEventListener('input', (ev) => {
        this.volume = parseFloat((ev.target as HTMLInputElement).value);
      });

      // Sync voice changes back to state
      document.getElementById('s-voice')!.addEventListener('change', (ev) => {
        this.ttsVoice = (ev.target as HTMLSelectElement).value;
      });

      // Sync scale changes back to state
      document.getElementById('s-scale')!.addEventListener('change', (ev) => {
        this.uiScale = parseFloat((ev.target as HTMLSelectElement).value);
      });
    }
    el.style.display = 'block';
    this._overlayEl = el;
  }

  private _hideOverlay(): void {
    if (this._overlayEl) this._overlayEl.style.display = 'none';
  }
}
