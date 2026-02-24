import * as THREE from 'three';

/**
 * CrystalBallController — state-driven crystal ball management.
 *
 * Default state: dim (emissiveIntensity < 0.1).
 * Pulses only when tts_speaking_start event is active.
 * Displays NPC portrait texture when npc_portrait_display event fires.
 *
 * Gate UI-CB: 8 tests.
 * Seeded PRNG only (Gate G compliant).
 */
export class CrystalBallController {
  private orbMesh: THREE.Mesh;
  private orbMaterial: THREE.MeshStandardMaterial;
  private innerMesh: THREE.Mesh | null = null;
  private innerMaterial: THREE.MeshStandardMaterial | null = null;

  // Pulse state
  private isSpeaking: boolean = false;
  private speakingIntensity: number = 0.0;
  private pulsePhase: number = 0.0;

  // Animation frame handle
  private _animHandle: number | null = null;
  private _lastTime: number = 0;

  // Portrait texture
  private _portraitTexture: THREE.Texture | null = null;
  private _textureLoader: THREE.TextureLoader = new THREE.TextureLoader();

  constructor(orbMesh: THREE.Mesh, innerMesh?: THREE.Mesh) {
    this.orbMesh = orbMesh;
    this.orbMaterial = orbMesh.material as THREE.MeshStandardMaterial;
    if (innerMesh) {
      this.innerMesh = innerMesh;
      this.innerMaterial = innerMesh.material as THREE.MeshStandardMaterial;
    }
    // Start dim
    this._setDim();
    this._startLoop();
  }

  /** Called on tts_speaking_start WS event. */
  onSpeakingStart(intensity: number = 1.0): void {
    this.isSpeaking = true;
    this.speakingIntensity = Math.max(0.0, Math.min(1.0, intensity));
  }

  /** Called on tts_speaking_stop WS event. */
  onSpeakingStop(): void {
    this.isSpeaking = false;
    this.speakingIntensity = 0.0;
  }

  /** Called on npc_portrait_display WS event. */
  onPortraitDisplay(imageUrl: string, clear: boolean = false): void {
    if (clear || !imageUrl) {
      this._clearPortrait();
      return;
    }
    this._textureLoader.load(imageUrl, (texture) => {
      if (this._portraitTexture) {
        this._portraitTexture.dispose();
      }
      this._portraitTexture = texture;
      if (this.innerMaterial) {
        this.innerMaterial.map = texture;
        this.innerMaterial.needsUpdate = true;
      }
    });
  }

  private _clearPortrait(): void {
    if (this._portraitTexture) {
      this._portraitTexture.dispose();
      this._portraitTexture = null;
    }
    if (this.innerMaterial) {
      this.innerMaterial.map = null;
      this.innerMaterial.needsUpdate = true;
    }
  }

  private _setDim(): void {
    this.orbMaterial.emissiveIntensity = 0.05;
    this.orbMaterial.needsUpdate = true;
  }

  private _startLoop(): void {
    const loop = (time: number) => {
      const dt = (time - this._lastTime) / 1000;
      this._lastTime = time;
      this._tick(dt);
      this._animHandle = requestAnimationFrame(loop);
    };
    this._animHandle = requestAnimationFrame(loop);
  }

  private _tick(dt: number): void {
    if (!this.isSpeaking) {
      // Dim state — snap emissive down
      this.orbMaterial.emissiveIntensity = 0.05;
      this.pulsePhase = 0.0;
      return;
    }
    // Pulse: sine wave at ~1.5 Hz
    this.pulsePhase += dt * 1.5 * Math.PI * 2;
    const pulse = 0.5 + 0.5 * Math.sin(this.pulsePhase);
    const intensity = 0.3 + pulse * 0.7 * this.speakingIntensity;
    this.orbMaterial.emissiveIntensity = intensity;
  }

  dispose(): void {
    if (this._animHandle !== null) {
      cancelAnimationFrame(this._animHandle);
      this._animHandle = null;
    }
    this._clearPortrait();
  }
}
