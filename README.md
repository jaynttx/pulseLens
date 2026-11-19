# PulseLens

**Contactless heart-rate monitoring from a webcam: a deep state-space model vs classical signal processing, benchmarked against a smartwatch.**

A normal webcam can measure your heart rate. With every heartbeat, a little more blood flows into the skin of your face and its colour changes very slightly: too little for the eye to see, but enough for a camera. This technique is called **remote photoplethysmography (rPPG)**.

PulseLens runs two rPPG systems side by side, entirely in the browser and on-device, and compares them:

| | **PulseLens Deep** (`apps/pulselens-deep`) | **PulseLens Classical** (`apps/pulselens-classical`) |
|---|---|---|
| Approach | Deep learning: a pretrained ~4 MB **state-space model** (SSM) | Signal processing: the **POS** algorithm (Plane-Orthogonal-to-Skin) |
| Face tracking | MediaPipe BlazeFace | MediaPipe FaceLandmarker |
| Heart rate from | Model-predicted pulse wave → PSD peak | RGB trace → POS projection → bandpass → FFT + autocorrelation → Kalman filter |
| Extras | Attention map, hidden-state trajectory, signal quality (SQI), session stats | Breathing rate, HRV, live colour/motion amplification |
| Runtime | LiteRT (TFLite) + WebAssembly | TypeScript + WebGL2 |

## Features

- **Contactless:** heart rate from an ordinary webcam, no wearable needed.
- **Private:** all processing runs on-device in the browser; no video or data is uploaded.
- **Real-time:** the deep model takes a few milliseconds per frame.
- **Explainable:** the deep app shows the face crop, attention maps and the model's internal heart state live.
- **Quality-aware:** a signal-quality score hides readings when the signal is unreliable.
- **Benchmark included:** a repeatable protocol and analysis script to compare both methods against a reference sensor.

## Our contributions

- **PulseLens Deep dashboard:** a redesigned, responsive dark UI with a beating-heart BPM display, heart-rate zones, session Min/Avg/Max/HRV* with quality filtering, a signal-quality bar, live/paused states, tooltips and an About panel. The model and its processing pipeline are used unchanged.
- **Integration:** both apps in one repository, consistently named, with one-click Windows launch scripts.
- **Benchmark:** a test protocol across four conditions (good light, dim light, moving/talking, after exercise) and `benchmark/analyze.py`, which scores each method against its own reference reading (MAE, RMSE, bias) and produces charts.
- **Documentation:** `docs/HOW_IT_WORKS.md`, a full explanation of both pipelines with viva-style Q&A.

## Repository structure

```
PulseLens/
├── apps/
│   ├── pulselens-deep/          Deep-learning rPPG (static web app)
│   │   ├── index.html           Dashboard UI
│   │   ├── main.js              Webcam → face detection → ROI crop → workers
│   │   ├── inference_worker.js  Runs the SSM (models/model.tflite) frame by frame
│   │   ├── psd_worker.js        Signal quality + power spectral density → heart rate
│   │   ├── plot_worker.js       Draws waveform, spectrum and trend
│   │   ├── sw.js                Service worker (offline support)
│   │   └── models/              model, proj, sqi, psd, initial state, face detector
│   └── pulselens-classical/     Classical rPPG (Svelte + Vite app)
│       └── src/lib/
│           ├── detection/       face-tracker, rppg (POS), signal, spatial-beamformer,
│           │                    vitals-fusion (Kalman), rate-tracker, breathing
│           ├── engine/          Camera, frame loop, WebGL2 amplification
│           ├── utils/           Maths helpers, constants
│           └── components/      UI (Svelte)
├── benchmark/
│   ├── results.csv              Fill in your measurements here
│   ├── analyze.py               MAE / RMSE / bias + charts
│   └── requirements.txt
├── docs/
│   └── HOW_IT_WORKS.md          How both pipelines work + viva Q&A
├── start-deep.bat               Run PulseLens Deep      → http://localhost:8001
├── start-classical.bat          Run PulseLens Classical → http://localhost:5173/pulse/
└── start-all.bat                Run both
```

## How to run

**Requirements:** a webcam, Google Chrome or Edge, **Python 3.9+** (deep app and benchmark) and **Node.js 18+** (classical app). Internet is needed on the first run to download the MediaPipe/LiteRT runtimes from a CDN; the deep app works offline afterwards.

### Windows (double-click)
- `start-deep.bat` opens **http://localhost:8001**
- `start-classical.bat` opens **http://localhost:5173/pulse/** (runs `npm install` the first time)
- `start-all.bat` runs both

### Manually (any OS)
```bash
# PulseLens Deep
cd apps/pulselens-deep
python -m http.server 8001
# open http://localhost:8001

# PulseLens Classical
cd apps/pulselens-classical
npm install
npm run dev
# open http://localhost:5173/pulse/
```

The browser only allows webcam access on `localhost` or `https`, so open the apps via `localhost`, not by double-clicking `index.html`. Port 8001 is used because 8000 is often taken by Docker.

**Tips for a good reading:** face a light source (lamp or window in front of you, not behind), sit still for 20–30 seconds, and don't talk.

## Running the benchmark

The two apps can't use the webcam at the same time, so run **one app at a time**, each with its **own** reference reading.

1. For each condition (good light, dim light, moving/talking, after exercise) and each trial:
   - Run **PulseLens Deep** (http://localhost:8001) for ~30 s while taking a smartwatch or phone heart-rate reading. Note the app's BPM as `facephys_bpm` and the watch reading as `ref_facephys_bpm`.
   - Close it (or stop its camera), then run **PulseLens Classical** for ~30 s with a fresh watch reading. Note its **Avg** value as `pulse_bpm` and the watch reading as `ref_pulse_bpm`.
2. Fill the numbers into `benchmark/results.csv` (columns: `condition,trial,ref_facephys_bpm,facephys_bpm,ref_pulse_bpm,pulse_bpm`). A row can have only one app filled in; empty cells are skipped.
3. Each method is scored against its own reference: deep error = `facephys_bpm − ref_facephys_bpm`, classical error = `pulse_bpm − ref_pulse_bpm`.
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
- The deep model was not trained by us; it may fail on conditions unlike its training data.
- The reference (smartwatch or phone) is itself approximate.
- **Not a medical device.**


