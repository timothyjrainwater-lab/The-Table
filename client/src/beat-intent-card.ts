/**
 * BeatIntent card — a TableObject that displays the latest BeatIntent as a
 * 3D text card on the table surface.
 *
 * Clicking the card (without drag) sends a DeclareActionIntent REQUEST.
 * Dragging the card moves it to a new position with zone constraints.
 *
 * Authority: WO-UI-01 (original), WO-UI-02 (TableObject promotion).
 */

import * as THREE from 'three';
import { WsBridge } from './ws-bridge';
import { TableObject, TableObjectPosition } from './table-object';

let cardCounter = 0;

export class BeatIntentCard implements TableObject {
  readonly id: string;
  readonly kind = 'card';
  position: TableObjectPosition;
  zone: string;
  pickable = true;
  readonly object3D: THREE.Mesh;

  private textCanvas: HTMLCanvasElement;
  private textCtx: CanvasRenderingContext2D;
  private texture: THREE.CanvasTexture;
  private bridge: WsBridge;
  private currentBeatId: string | null = null;

  // Pick visual state
  private baseMaterial: THREE.MeshStandardMaterial;

  constructor(scene: THREE.Scene, bridge: WsBridge, id?: string) {
    this.id = id ?? `card_${++cardCounter}`;
    this.bridge = bridge;

    // Canvas for text rendering
    this.textCanvas = document.createElement('canvas');
    this.textCanvas.width = 512;
    this.textCanvas.height = 256;
    this.textCtx = this.textCanvas.getContext('2d')!;
    this.texture = new THREE.CanvasTexture(this.textCanvas);

    // Card geometry — a flat rectangle on the table
    const geo = new THREE.PlaneGeometry(3, 1.5);
    this.baseMaterial = new THREE.MeshStandardMaterial({
      map: this.texture,
      side: THREE.DoubleSide,
    });
    this.object3D = new THREE.Mesh(geo, this.baseMaterial);
    this.object3D.rotation.x = -Math.PI / 2;
    this.object3D.position.set(0, 0.05, 3); // Start in player zone
    this.object3D.name = 'beat_intent_card';

    this.position = { x: 0, y: 0.05, z: 3 };
    this.zone = 'player';

    scene.add(this.object3D);
    this.renderText('Waiting for BeatIntent...', '', '');
  }

  // Alias for backward compat with main.ts raycast hit detection
  get mesh(): THREE.Mesh {
    return this.object3D as THREE.Mesh;
  }

  // -----------------------------------------------------------------------
  // TableObject lifecycle
  // -----------------------------------------------------------------------

  onSpawn(): void {
    // Already added to scene in constructor
  }

  onPick(): void {
    // Slight elevation + emissive glow
    this.object3D.position.y = this.position.y + 0.1;
    this.baseMaterial.emissive.setHex(0x333355);
    this.baseMaterial.emissiveIntensity = 0.5;
  }

  onDrag(position: TableObjectPosition): void {
    this.object3D.position.set(position.x, position.y, position.z);
  }

  onDrop(zone: string): void {
    // Settle back to table surface height
    this.object3D.position.set(this.position.x, this.position.y, this.position.z);
    this.baseMaterial.emissive.setHex(0x000000);
    this.baseMaterial.emissiveIntensity = 0;
  }

  onDestroy(): void {
    if (this.object3D.parent) {
      this.object3D.parent.remove(this.object3D);
    }
    this.baseMaterial.dispose();
    (this.object3D as THREE.Mesh).geometry.dispose();
    this.texture.dispose();
  }

  // -----------------------------------------------------------------------
  // BeatIntent data
  // -----------------------------------------------------------------------

  update(beatType: string, pacingMode: string, beatId: string, targetHandles: string[]): void {
    this.currentBeatId = beatId;
    const handles = targetHandles.length > 0 ? targetHandles.join(', ') : '(none)';
    this.renderText(
      `Beat: ${beatType}`,
      `Pacing: ${pacingMode}`,
      `Targets: ${handles}`
    );
  }

  getBeatId(): string | null {
    return this.currentBeatId;
  }

  sendDeclareAction(): void {
    if (!this.currentBeatId) return;
    this.bridge.send({
      msg_type: 'player_action',
      msg_id: crypto.randomUUID(),
      timestamp: Date.now() / 1000,
      action_type: 'declare_action_intent',
      payload: {
        type: 'DECLARE_ACTION_INTENT',
        action_kind: 'interact',
        source_ref: this.currentBeatId,
      },
    });
  }

  // -----------------------------------------------------------------------
  // Text rendering
  // -----------------------------------------------------------------------

  private renderText(line1: string, line2: string, line3: string): void {
    const ctx = this.textCtx;
    const w = this.textCanvas.width;
    const h = this.textCanvas.height;

    // Background
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, w, h);

    // Border
    ctx.strokeStyle = '#7b7bff';
    ctx.lineWidth = 3;
    ctx.strokeRect(4, 4, w - 8, h - 8);

    // Text
    ctx.fillStyle = '#c8c8d0';
    ctx.font = '24px Consolas, monospace';
    ctx.textAlign = 'center';
    ctx.fillText(line1, w / 2, 70);
    ctx.font = '18px Consolas, monospace';
    ctx.fillStyle = '#9090a0';
    ctx.fillText(line2, w / 2, 120);
    ctx.fillText(line3, w / 2, 160);

    // Instruction
    ctx.fillStyle = '#ffe066';
    ctx.font = '14px Consolas, monospace';
    ctx.fillText('[ click to declare action ]', w / 2, 220);

    this.texture.needsUpdate = true;
  }
}
