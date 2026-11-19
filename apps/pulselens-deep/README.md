# PulseLens Deep

The deep-learning side of PulseLens. It estimates heart rate from a webcam with a pretrained ~4 MB **state-space model (SSM)** that turns face pixels into a pulse wave, frame by frame, in a few milliseconds. Everything runs on-device in the browser (LiteRT + WebAssembly); no video or data is uploaded, and it works offline after the first load.

## What it does

1. MediaPipe BlazeFace finds the face; a 36×36 face crop (ROI) is taken every frame.
2. The SSM predicts the blood volume pulse (BVP) from each crop, carrying a small hidden state between frames.
3. A power spectral density (PSD) of the recent pulse gives the heart rate: peak Hz × 60 = BPM.
4. A signal-quality model (SQI) hides readings when the signal is unreliable.

The dashboard shows the live heart rate, session min/avg/max, signal quality, latency and FPS, the pulse waveform, the spectrum, a 5-minute trend, and a look inside the model (face ROI, attention map and hidden-state trajectory per layer). Data can be exported as a `.zip` of CSV files.

## How to run

From the repository root, double-click `start-deep.bat`, or:

```bash
cd apps/pulselens-deep
python -m http.server 8001
# open http://localhost:8001 in Chrome
```

Webcam access needs `localhost` or `https`, so don't open `index.html` directly from disk. After updating the files, press Ctrl+Shift+R to bypass the service-worker cache.

## Main files

| File | Role |
|---|---|
| `index.html` | Dashboard UI and the read-only UI enhancement script |
| `main.js` | Webcam, face detection, ROI crop, worker orchestration |
| `inference_worker.js` | Runs the SSM (`models/model.tflite`, `proj.tflite`) per frame |
| `psd_worker.js` | Signal quality and PSD → heart rate (`sqi_model.tflite`, `psd_model.tflite`) |
| `plot_worker.js` | Draws the waveform, spectrum and trend on offscreen canvases |
| `sw.js`, `manifest.json` | Offline support / installable web app |
| `models/` | Model weights, initial hidden state (`state.gz`) and face detector |

## License

The model and original app code are under the MIT License with a Privacy Protection Addendum; see [LICENSE](LICENSE).
