# Original PulseLens + lavender theme

This repository is a fork of https://github.com/xan-antx/pulseLens at
`e7bdd94cbe686611eb37f817bbdf48b8d770b057`.

The webcam capture, POS implementation, neural inference, model weights,
workers, visualizations, and benchmarks remain the original upstream code.
The only presentation changes are the added CSS overrides in
`apps/pulselens-deep/index.html` and colour tokens in
`apps/pulselens-classical/src/app.css`.

## Start the original Deep app on macOS

```bash
cd ~/Documents
git clone https://github.com/jaynttx/pulseLens.git pulseLens-original
cd pulseLens-original/apps/pulselens-deep
python3 -m http.server 8001
```

Open http://localhost:8001 in Chrome. If the folder already exists, enter it
and use `git pull` instead of cloning again. Close the older custom app tab
at port 4173 so you are testing this original implementation.

## Start the original Classical app

In another Terminal:

```bash
cd ~/Documents/pulseLens-original/apps/pulselens-classical
npm install
npm run dev
```

Open http://localhost:5173/pulse/. Run one camera app at a time. Original
credits, documentation and model license terms are preserved. Model loading
needs internet access initially. These are research estimates, not a medical
device or a guarantee of accuracy.
