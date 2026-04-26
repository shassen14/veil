(function () {
  const FS    = 14;
  const CHARS = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789';
  const LEAD  = 'rgba(0,255,65,0.65)';
  const FADE  = 'rgba(10,10,10,0.08)';

  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0';
  document.body.prepend(canvas);

  const ctx = canvas.getContext('2d');
  let cols, drops, speeds, boost = 0;

  function init() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    cols   = Math.floor(canvas.width / FS);
    // stagger initial positions so columns don't all start at top simultaneously
    drops  = Array.from({length: cols}, () => -Math.floor(Math.random() * (canvas.height / FS)));
    speeds = Array.from({length: cols}, () => 0.1 + Math.random() * 0.25);
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  function draw() {
    ctx.fillStyle = FADE;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = LEAD;
    ctx.font = `${FS}px monospace`;

    const m = boost > 0 ? 2.5 : 1;
    if (boost > 0) boost--;

    for (let i = 0; i < cols; i++) {
      drops[i] += speeds[i] * m;
      const y = Math.floor(drops[i]) * FS;
      if (y < 0) continue;
      ctx.fillText(CHARS[Math.random() * CHARS.length | 0], i * FS, y);
      if (y > canvas.height && Math.random() > 0.975) {
        drops[i] = -Math.floor(Math.random() * 20);
      }
    }
  }

  init();
  window.addEventListener('resize', init);
  setInterval(draw, 60);

  // call this on each chat message to briefly speed up the rain
  window.feedRain = function () {
    boost = Math.min(boost + 45, 150);
  };
}());
