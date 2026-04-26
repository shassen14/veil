class Column {
  static CHARS = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789';

  constructor(x, canvasHeight, fontSize) {
    this.x     = x;
    this.speed = 0.6 + Math.random() * 0.8;
    this.drop  = -Math.floor(Math.random() * (canvasHeight / fontSize));
  }

  get screenY() {
    return Math.floor(this.drop) * Column.fontSize;
  }

  advance(speed, restartWait, canvasHeight) {
    this.drop += speed * this.speed;
    if (this.screenY > canvasHeight && Math.random() > 0.975) {
      this.drop = -Math.floor(Math.random() * restartWait);
    }
  }

  randomChar() {
    return Column.CHARS[Math.floor(Math.random() * Column.CHARS.length)];
  }
}


class MatrixRain {
  static config = {
    fontSize:     14,
    leadColor:    'rgba(0,255,65,0.65)',
    fadeColor:    'rgba(10,10,10,0.08)',
    bgColor:      '#0a0a0a',
    frameMs:      60,

    // activity calibration
    rateWindowS:  60,    // rolling window for msg/min
    rateFloor:    8,     // minimum peak (msg/min) — slow streams still use the full range
    emaAlpha:     0.04,  // smoothing per frame (~1.5 s time constant at 60 ms)

    // rain intensity bounds driven by activity [0, 1]
    speedMin:     0.10,  // rows/frame at activity = 0
    speedMax:     0.50,  // rows/frame at activity = 1
    waitMin:      5,     // rows off-screen before restart at activity = 1 (dense)
    waitMax:      45,    // rows off-screen before restart at activity = 0 (sparse)
  };

  #canvas;
  #ctx;
  #columns   = [];
  #stamps    = [];       // message timestamps for rolling rate window
  #peakRate;             // self-calibrating max rate (msg/min), never decreases
  #activity  = 0;        // EMA-smoothed [0, 1]

  constructor() {
    const { rateFloor, fontSize, frameMs } = MatrixRain.config;
    Column.fontSize = fontSize;

    this.#peakRate = rateFloor;
    this.#canvas   = this.#buildCanvas();
    this.#ctx      = this.#canvas.getContext('2d');

    this.#resize();
    window.addEventListener('resize', () => this.#resize());
    setInterval(() => this.#draw(), frameMs);
  }

  // Called on each incoming chat message.
  feed() {
    this.#stamps.push(Date.now());
  }

  // Seed calibration from a server-supplied historical baseline.
  // Uncomment usage in scene scripts once boneless_couch sends chat_rate_baseline
  // in the state.sync payload (see docs/veil.md — Future: server-side calibration).
  setBaseline(msgPerMin) {
    this.#peakRate = Math.max(this.#peakRate, msgPerMin);
  }

  #buildCanvas() {
    const canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0';
    document.body.prepend(canvas);
    return canvas;
  }

  #resize() {
    const { fontSize, bgColor } = MatrixRain.config;
    this.#canvas.width  = window.innerWidth;
    this.#canvas.height = window.innerHeight;

    const count = Math.floor(this.#canvas.width / fontSize);
    this.#columns = Array.from(
      { length: count },
      (_, i) => new Column(i * fontSize, this.#canvas.height, fontSize),
    );

    this.#ctx.fillStyle = bgColor;
    this.#ctx.fillRect(0, 0, this.#canvas.width, this.#canvas.height);
  }

  #updateActivity() {
    const { rateWindowS, rateFloor, emaAlpha } = MatrixRain.config;
    const now    = Date.now();
    const cutoff = now - rateWindowS * 1000;

    while (this.#stamps.length && this.#stamps[0] < cutoff) this.#stamps.shift();

    const rate = (this.#stamps.length / rateWindowS) * 60;
    if (rate > this.#peakRate) this.#peakRate = rate;

    const target   = Math.min(rate / this.#peakRate, 1);
    this.#activity += emaAlpha * (target - this.#activity);
  }

  #draw() {
    this.#updateActivity();

    const { fadeColor, leadColor, fontSize, speedMin, speedMax, waitMin, waitMax } = MatrixRain.config;
    const speed = speedMin + this.#activity * (speedMax - speedMin);
    const wait  = waitMin  + (1 - this.#activity) * (waitMax - waitMin);

    this.#ctx.fillStyle = fadeColor;
    this.#ctx.fillRect(0, 0, this.#canvas.width, this.#canvas.height);
    this.#ctx.fillStyle = leadColor;
    this.#ctx.font = `${fontSize}px monospace`;

    for (const col of this.#columns) {
      col.advance(speed, wait, this.#canvas.height);
      if (col.screenY >= 0) {
        this.#ctx.fillText(col.randomChar(), col.x, col.screenY);
      }
    }
  }
}


const rain = new MatrixRain();
window.feedRain = () => rain.feed();
