# How PulseLens works

## 1. The physics: why a camera can see your pulse

- Each heartbeat pushes a wave of blood into the small blood vessels (capillaries) of the face.
- Haemoglobin in the blood absorbs light, most strongly **green** light.
- So with every beat, the skin gets very slightly darker, then lighter again. The change is **under 1%** of pixel brightness.
- Averaging thousands of skin pixels cancels the random camera noise and leaves this tiny periodic signal. That signal is the **blood volume pulse (BVP)**.
- Heart rate = how often the BVP wave repeats. A peak at **1.39 Hz** means 1.39 × 60 ≈ **83 bpm**.

## 2. The shared pipeline

```
Webcam frame (30 fps)
   │
   ▼
Face detection / landmarks  ──►  Region of interest (ROI): forehead, cheeks
   │
   ▼
Average R, G, B over skin pixels  ──►  3 numbers per frame = a "colour trace"
   │
   ▼
Pulse extraction  ◄── this is where the two methods differ
   │                 PulseLens Classical: POS formula
   │                 PulseLens Deep: state-space neural network
   ▼
Blood-volume-pulse waveform
   │
   ▼
Bandpass 0.67–3.33 Hz (= 40–200 bpm)  ──►  removes lighting drift + noise
   │
   ▼
FFT / power spectral density  ──►  highest peak frequency × 60 = heart rate
```

## 3. PulseLens Classical: POS (`apps/pulselens-classical`)

**Paper:** W. Wang, A. C. den Brinker, S. Stuijk, G. de Haan, *"Algorithmic Principles of Remote PPG"*, IEEE TBME, 2017. POS = **Plane-Orthogonal-to-Skin**. PulseLens Classical uses POS, implemented in `computePosPulse()` in `rppg.ts`. POS improves on the earlier CHROM method (de Haan & Jeanne, 2013) from the same group.

**Idea:** brightness changes caused by lighting or movement scale R, G and B **together**, along the "skin-tone direction". The pulse changes them **differently**, mostly green. POS projects the colour onto a plane **orthogonal to the skin tone**, so the shared change cancels out and the pulse remains.

For each short sliding window of frames (exactly as in `computePosPulse()`):

1. **Normalise** each channel by its mean in the window: `Rn = R/mean(R)`, and the same for G and B. This removes skin colour and brightness level.
2. **Project** onto two axes orthogonal to the skin tone:
   `S1 = Gn − Bn`
   `S2 = Gn + Bn − 2·Rn`
3. **Combine** them: `h = S1 + α·S2`, with `α = std(S1) / std(S2)`. α tunes the mix automatically, so the leftover distortion in S1 and S2 cancels out.
4. **Overlap-add:** normalise h and add it into the full pulse signal. The windows slide one frame at a time.

Then the signal is detrended and bandpassed to 40–200 bpm. **Two estimators** give the BPM:
- **FFT peak** (frequency domain)
- **Autocorrelation peak** (time domain: how many seconds until the signal repeats itself)

If they agree within 10%, they're averaged. Otherwise the more confident one wins.

**Where it is in the code:**

| Step | File |
|---|---|
| Face landmarks → forehead/cheek ROIs, skin-pixel filtering | `src/lib/detection/face-tracker.ts` |
| POS pulse extraction + FFT/autocorrelation fusion | `src/lib/detection/rppg.ts` (`computePosPulse`, `computeBpm`) |
| Weighting face regions by quality | `src/lib/detection/spatial-beamformer.ts` |
| Detrend, Hamming window, FFT, bandpass, peak finding, autocorrelation | `src/lib/detection/signal.ts` |
| Kalman filter, combining HR + breathing | `src/lib/detection/vitals-fusion.ts` |
| Breathing rate | `src/lib/detection/breathing.ts` |
| The "orange glow" visual (temporal bandpass amplification, WebGL2) | `src/lib/engine/renderer.ts`, `shaders.ts` |

**Extra signal-processing tricks:**
- **Detrend:** remove slow drift (e.g. auto-exposure changes).
- **Hamming window:** taper the edges of the window before the FFT to reduce spectral leakage.
- **Noise floor rejection:** accept a peak only if it is more than 2× the median spectral power.
- **Parabolic interpolation:** estimate the peak between FFT bins for finer resolution.
- **Kalman filter:** tracks [rate, rate-change] over time. It trusts high-quality measurements more and rejects outliers beyond 3σ, so the number doesn't jump around.

## 4. PulseLens Deep: state-space model (`apps/pulselens-deep`)

**Model:** PulseLens Deep uses the pretrained FacePhys state-space model. Paper: Wang et al., *"FacePhys: State of the Heart Learning"*, arXiv:2512.06275, 2025. Reports a 49% error reduction over prior methods, a 3.6 MB memory footprint and 9.46 ms per-frame latency (the authors' own claims).

**Idea:** instead of a hand-designed formula like POS, a neural network **learns** from labelled videos (faces recorded alongside a contact pulse sensor) how to turn face pixels into the pulse wave. It learns to ignore motion, lighting and shadows on its own.

**Why a state-space model (SSM)?**
- An SSM keeps a small **hidden state** (a memory vector) and updates it every frame: `h_t = A·h_{t-1} + B·x_t`, `y_t = C·h_t`.
- The cost per frame is **constant**. A transformer would have to look back over *all* past frames, so it gets slower and uses more memory as time goes on.
- This is why a ~4 MB model runs in real time in a browser.
- The model treats the heart dynamics as continuous-time equations, so it copes with irregular frame timing (dropped frames).

**What the UI panels show:**

| Panel | Meaning |
|---|---|
| **Heart rate** | Estimated heart rate, zone badge and session Min/Avg/Max/HRV* |
| **Signal quality** | Signal Quality Index, 0–1, from a separate small model (`sqi_model.tflite`). Higher = more trustworthy. |
| **Latency / FPS** | Inference time per frame / frames per second |
| **Face ROI** | The cropped face the model sees |
| **Attention map** | Attention heatmap: red = the skin regions the model relies on most (usually forehead and cheeks, not eyes or hair) |
| **Heart state trajectory** | The model's hidden state projected to 2D (`proj.tflite`). It loops because the heartbeat repeats. |
| **SSM 1–4 / Projection** | Switch which hidden-state layer is shown |
| **Frequency spectrum (PSD)** | Power spectral density of the pulse. The peak in Hz × 60 = BPM. |
| **Pulse waveform (BVP)** | The predicted blood volume pulse |
| **Heart-rate trend** | Heart rate over the last 5 minutes |

**Where it is in the code:**

| Step | File |
|---|---|
| Webcam, BlazeFace face detection, ROI crop, starting the workers | `main.js` |
| Running the SSM frame by frame (LiteRT, WebAssembly) | `inference_worker.js` |
| PSD → heart rate | `psd_worker.js` (+ `models/psd_model.tflite`) |
| Drawing the plots | `plot_worker.js` |
| Offline support | `sw.js`, `manifest.json` |
| Model weights | `models/model.tflite` (SSM), `proj.tflite`, `sqi_model.tflite`, `psd_model.tflite`, `state.gz` (initial hidden state), `blaze_face_short_range.tflite` (face detector) |

**Web Workers:** inference, PSD and plotting each run in a separate background thread, so the video never freezes.

## 5. PulseLens Classical vs PulseLens Deep: summary

| | PulseLens Classical (POS) | PulseLens Deep (SSM) |
|---|---|---|
| Needs training data? | No, it's a fixed formula | Yes, labelled face videos |
| Explainable? | Fully: each step is maths | Partly: attention map and hidden state help |
| Motion / lighting robustness | Moderate | Better (learned) |
| Compute | Very light | Light (~4 MB, few ms per frame) |
| Failure mode | Breaks with motion and light changes | Can fail on conditions unlike its training data |

## 6. Viva questions and answers

**How can a camera see a pulse?**
Blood volume in the face changes with each beat, which changes how much light the skin absorbs, mostly green light. The change is below 1%, so we average many skin pixels and filter to the heart-rate band.

**Why bandpass 0.67–3.33 Hz?**
That's 40–200 bpm, the physiological range. It removes slow lighting drift below it and noise above it.

**How do you get BPM from the signal?**
FFT, then find the highest peak in the band. Peak frequency in Hz × 60 = bpm.

**How long must I sit still?**
Frequency resolution = 1 / window length. A 10 s window gives 0.1 Hz bins = 6 bpm, so the reading settles after several seconds. Interpolation and the Kalman filter refine it.

**What does POS do?**
It normalises R, G and B, then projects them onto a plane orthogonal to the skin-tone direction (S1 = G−B, S2 = G+B−2R) and mixes them as h = S1 + α·S2. Changes that scale all channels together (lighting, motion) cancel out, and the pulse remains.

**POS vs CHROM?**
Both come from the same Philips/TU Eindhoven group. CHROM (2013) uses fixed colour-difference signals. POS (2017) derives its projection plane from first principles (orthogonal to skin tone), which makes it more robust. PulseLens Classical uses POS.

**Why a state-space model instead of a CNN or transformer?**
It carries a fixed-size hidden state, so cost per frame is constant and memory is tiny. That allows real-time streaming in a browser. A transformer's cost grows with sequence length.

**Did you train the model?**
No. PulseLens Deep uses the authors' pretrained FacePhys model. Our work is the comparison against a classical baseline and a reference sensor, under controlled conditions.

**What datasets are used for rPPG?**
Face videos with a synchronised contact pulse sensor, e.g. UBFC-rPPG, PURE, RLAP.

**How did you evaluate it?**
Mean absolute error (MAE), RMSE and bias in bpm against a smartwatch or phone PPG, across four conditions: good light, dim light, motion/talking, after exercise. See `benchmark/`.

**MAE vs RMSE?**
MAE = average size of the error. RMSE squares the errors first, so big misses count more. If RMSE is much larger than MAE, there are occasional large failures.

**Where does it fail?**
Motion, flicker, dim light, makeup or beards covering skin, darker skin tones (lower signal-to-noise, a real fairness issue), and heavily compressed video.

**What's the attention map?**
The skin regions the model weights most when predicting the pulse. It should focus on well-perfused, well-lit skin: forehead and cheeks.

**What's the SQI?**
Signal Quality Index, a confidence score. Low SQI means don't trust the reading (e.g. you moved).

**Is this medical-grade?**
No. It's a research project, and smartwatches are only approximate references themselves.

**Real-world uses?**
Telehealth check-ups, driver drowsiness and stress monitoring, neonatal monitoring without wires, and fitness apps.

**Privacy?**
Everything runs on-device in the browser. No video leaves the computer.
