# Contactless Heart-Rate Estimation from a Webcam

**A deep state-space model (FacePhys) vs classical signal processing (POS), benchmarked against a smartwatch.**

A normal webcam can measure your heart rate. With every heartbeat, a little more blood flows into the skin of your face, and its colour changes very slightly, too little for the eye to see but enough for a camera. This technique is called **remote photoplethysmography (rPPG)**.

This project runs two rPPG systems side by side, entirely in the browser and on-device:

| | `apps/facephys-deep` | `apps/pulse-classical` |
|---|---|---|
| Approach | Deep learning: a ~4 MB **state-space model** (SSM) | Classical signal processing: **POS** algorithm (Plane-Orthogonal-to-Skin) |
| Face tracking | MediaPipe BlazeFace | MediaPipe FaceLandmarker |
| Heart rate from | Model-predicted pulse wave → PSD peak | RGB trace → POS projection → bandpass → FFT + autocorrelation → Kalman filter |
| Extras | Attention heatmap, hidden-state trajectory, signal quality (SQI), HRV | Breathing rate, HRV, live motion/colour amplification |
| Runtime | LiteRT (TFLite) + WebAssembly | TypeScript + WebGL2 |

Our contribution is the **benchmark** (`benchmark/`): both methods are compared against a reference heart rate (smartwatch or phone PPG) under different conditions, reporting MAE, RMSE and bias.

---

## Repository structure

```
contactless-heart-rate/
├── apps/
│   ├── facephys-deep/          Deep-learning rPPG (static web app)
│   │   ├── index.html          UI (Windows-95 style)
│   │   ├── main.js             Webcam → face detection → ROI crop → workers
│   │   ├── inference_worker.js Runs the SSM (models/model.tflite) frame by frame
│   │   ├── psd_worker.js       Power spectral density → heart rate
│   │   ├── plot_worker.js      Draws waveforms, heatmap, state trajectory
│   │   ├── sw.js               Service worker (offline support)
│   │   └── models/             model.tflite, proj, sqi, psd, state, face detector
│   └── pulse-classical/        Classical rPPG (Svelte + Vite app)
│       └── src/lib/
│           ├── detection/
│           │   ├── face-tracker.ts      MediaPipe landmarks → forehead/cheek ROIs
│           │   ├── rppg.ts              POS pulse extraction + FFT/autocorrelation BPM
│           │   ├── signal.ts            Detrend, Hamming, FFT, bandpass, peak finding
│           │   ├── spatial-beamformer.ts Weights face regions by signal quality
│           │   ├── vitals-fusion.ts     Kalman filters for HR + breathing
│           │   ├── rate-tracker.ts      Rate smoothing
│           │   └── breathing.ts         Breathing-rate detection
│           ├── engine/         Camera, frame loop, WebGL2 motion amplification
│           ├── utils/          Maths helpers, constants
│           └── components/     UI (Svelte)
├── benchmark/
│   ├── results.csv             Fill in your measurements here
│   ├── analyze.py              Computes MAE / RMSE / bias + charts
│   └── requirements.txt
├── docs/
│   └── HOW_IT_WORKS.md         Full explanation of both pipelines + viva Q&A
├── start-facephys.bat          Run deep demo   → http://localhost:8001
├── start-pulse.bat             Run classical   → http://localhost:5173/pulse/
└── start-all.bat               Run both
```

---

## Requirements

- Windows, macOS or Linux with a **webcam**
- **Google Chrome** or Edge
- **Python 3.9+** (to serve FacePhys and run the benchmark)
- **Node.js 18+** (to run pulse)
- Internet on the **first** run (both apps download the MediaPipe/LiteRT runtimes from a CDN; FacePhys works offline afterwards via its service worker)

## How to run

### Windows (double-click)
- `start-facephys.bat` opens **http://localhost:8001**
- `start-pulse.bat` opens **http://localhost:5173/pulse/** (runs `npm install` the first time)
- `start-all.bat` runs both

### Manually (any OS)
```bash
# Deep model
cd apps/facephys-deep
python -m http.server 8001
# open http://localhost:8001

# Classical
cd apps/pulse-classical
npm install
npm run dev
# open http://localhost:5173/pulse/
```

The browser only allows webcam access on `localhost` or `https`, so open the apps via `localhost`, not by double-clicking `index.html`.

### Tips for a good reading
Face a light source (lamp or window in front of you, not behind), sit still for 20–30 seconds, and don't talk.

## Running the benchmark

The two apps can't use the webcam at the same time, so run **one app at a time**, each with its **own** reference reading.

1. For each condition (good light, dim light, moving/talking, after exercise) and each trial:
   - Run **FacePhys** (http://localhost:8001) for ~30 s while taking a smartwatch or phone heart-rate reading. Note the app's BPM as `facephys_bpm` and the watch reading as `ref_facephys_bpm`.
   - Close FacePhys (or stop its camera), then run **pulse** for ~30 s with a fresh watch reading. Note pulse's **Avg** value as `pulse_bpm` and the watch reading as `ref_pulse_bpm`.
2. Fill the numbers into `benchmark/results.csv` (columns: `condition,trial,ref_facephys_bpm,facephys_bpm,ref_pulse_bpm,pulse_bpm`). A row can have only one app filled in; empty cells are skipped.
3. Each method is scored against its own reference: FacePhys error = `facephys_bpm − ref_facephys_bpm`, pulse error = `pulse_bpm − ref_pulse_bpm`.
4. Run:
   ```bash
   cd benchmark
   pip install -r requirements.txt
   python analyze.py
   ```
5. Results go to `benchmark/output/`: `summary.csv`, `error_by_condition.png`, `agreement.png`.

## Limitations

- Sensitive to motion, dim or flickering light, low-quality webcams and video compression.
- Lower signal-to-noise on darker skin tones, a known fairness issue in rPPG research.
- The reference (smartwatch or phone) is itself approximate.
- **Not a medical device.**

## Credits

This project builds on, and redistributes for academic use, the following open-source work. All credit for the two apps goes to their authors.

- **FacePhys-Demo** by Kegang Wang: https://github.com/KegangWangCCNU/FacePhys-Demo (MIT License with Privacy Protection Addendum, see `apps/facephys-deep/LICENSE`)
  Paper: K. Wang, J. Tang, Y. Wang, X. Liu, Y. Fan, J. Ji, Y. Shi, D. McDuff, *"FacePhys: State of the Heart Learning"*, arXiv:2512.06275, 2025.
- **pulse** by Sean Reid: https://github.com/sean-reid/pulse (no license file published; included here for academic evaluation only)
  Method: W. Wang, A. C. den Brinker, S. Stuijk, G. de Haan, *"Algorithmic Principles of Remote PPG"* (POS), IEEE TBME, 2017. (pulse's own README says CHROM; the code in `rppg.ts → computePosPulse()` implements POS.)
- Google **MediaPipe** and **LiteRT** runtimes.

Our own work: the repository integration, launch scripts, the benchmark protocol and analysis (`benchmark/`), and the documentation (`docs/`).
