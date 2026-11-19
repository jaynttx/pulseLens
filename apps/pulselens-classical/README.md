# PulseLens Classical

The signal-processing baseline of PulseLens. It estimates heart rate (plus breathing rate and variability) from a webcam using the **POS** (Plane-Orthogonal-to-Skin) rPPG algorithm, with no neural network for the pulse itself. Everything runs in the browser; no video is recorded or uploaded.

## What it does

1. MediaPipe FaceLandmarker tracks the face and picks forehead and cheek regions.
2. The average skin colour (R, G, B) of each region is recorded every frame.
3. POS projects the colour trace onto a plane orthogonal to the skin tone, so lighting and motion cancel out and the pulse remains.
4. The pulse is detrended and bandpassed to 40–200 bpm; FFT and autocorrelation estimate the BPM, and a Kalman filter smooths it.

## How to run

From the repository root, double-click `start-classical.bat`, or:

```bash
cd apps/pulselens-classical
npm install
npm run dev
# open http://localhost:5173/pulse/
```

Other scripts: `npm run build` (production build), `npx vitest run` (unit tests), `npm run test:e2e` (Playwright).

## Main files

| File | Role |
|---|---|
| `src/lib/detection/face-tracker.ts` | Face landmarks → forehead/cheek ROIs, skin-pixel filtering |
| `src/lib/detection/rppg.ts` | POS pulse extraction (`computePosPulse`) and BPM estimation |
| `src/lib/detection/signal.ts` | Detrend, Hamming window, FFT, bandpass, peak finding |
| `src/lib/detection/spatial-beamformer.ts` | Weights face regions by signal quality |
| `src/lib/detection/vitals-fusion.ts` | Kalman filters for heart and breathing rate |
| `src/lib/detection/breathing.ts` | Breathing-rate detection |
| `src/lib/engine/` | Camera, frame loop, WebGL2 colour/motion amplification |
| `src/lib/components/` | Svelte UI |

Method: W. Wang, A. C. den Brinker, S. Stuijk, G. de Haan, *"Algorithmic Principles of Remote PPG"*, IEEE TBME, 2017.
