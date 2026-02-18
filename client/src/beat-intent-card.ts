/**
 * BeatIntent display — renders the latest BeatIntent as a 3D text card
 * on the table surface.
 *
 * Clicking the card sends a DeclareActionIntent REQUEST over WebSocket.
 */

import * as THREE from 'three';
import { WsBridge } from './ws-bridge';

export class BeatIntentCard {
  readonly mesh: THREE.Mesh;
  private textCanvas: HTMLCanvasElement;
  private textCtx: CanvasRenderingContext2D;
  private texture: THREE.CanvasTexture;
  private bridge: WsBridge;
  private currentBeatId: string | null = null;

  constructor(scene: THREE.Scene, bridge: WsBridge) {
    this.bridge = bridge;

    // Canvas for text rendering
    this.textCanvas = document.createElement('canvas');
    this.textCanvas.width = 512;
    this.textCanvas.height = 256;
    this.textCtx = this.textCanvas.getContext('2d')!;
    this.texture = new THREE.CanvasTexture(this.textCanvas);

    // Card geometry — a flat rectangle on the table
    const geo = new THREE.PlaneGeometry(3, 1.5);
    const mat = new THREE.MeshStandardMaterial({
      map: this.texture,
      side: THREE.DoubleSide,
    });
    this.mesh = new THREE.Mesh(geo, mat);
    this.mesh.rotation.x = -Math.PI / 2;
    this.mesh.position.set(0, 0.05, 0); // Slightly above table surface
    this.mesh.name = 'beat_intent_card';
    scene.add(this.mesh);

    this.renderText('Waiting for BeatIntent...', '', '');
  }

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
