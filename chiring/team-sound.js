/* 기운 주파수 소리 (팀 프로토타입용 · magenta.js)
 *
 * magenta.js(@magenta/music 1.23.1, Apache-2.0)의 MusicVAE 두 모델이 상황마다 새로 '생성'해요.
 *  - 선율 모델(mel_4bar_small_q2): 4마디 선율 → 기운 음계(5음)에 맞춰 플럭 소리로
 *  - 드럼 모델(drums_2bar_lokl_small): 2마디 드럼 → 킥·클랩·하이햇·탐으로
 * 그 아래에 기운마다 다른 바탕 주파수(양쪽 귀 4Hz 차이로 일렁임)와 코드 패드가 깔리고,
 * 킥이 칠 때마다 패드가 살짝 눌렸다 올라오는(사이드체인) 요즘 스타일 리듬이에요.
 *
 * 상황마다 생성 온도·박자·코드 진행·바탕 주파수가 달라요
 *  - 문지르기 안내 : 80bpm, 잔잔한 패드 + 성긴 선율, 드럼 없음, 가장 작게
 *  - 문지르는 중   : 96bpm, 문지르는 속도만큼 소리가 커지고 밝아지고(필터가 열림), 빨리 문지를수록 드럼이 들어와요
 *  - 참 등장 후    : 104bpm, 밝은 퓨처베이스풍 (4박 킥·클랩·16비트 하이햇·5도 위 바탕음)
 *  - 다시 듣기 재생: 88bpm, 칠한 로파이 하우스 (스윙 하이햇·오픈햇·서브 베이스)
 * 모델을 불러오는 동안·인터넷이 안 될 때는 같은 규칙으로 만든 패턴으로 대신 연주해요.
 */
(() => {
  const BASE = new URL('.', document.currentScript ? document.currentScript.src : location.href).href
  const MM_SRC = BASE + 'vendor/magentamusic-1.23.1.js'
  const CK = 'https://storage.googleapis.com/magentadata/js/checkpoints/music_vae/'
  const MEL_CKPT = CK + 'mel_4bar_small_q2', DRUM_CKPT = CK + 'drums_2bar_lokl_small'

  // 기운별 바탕음 (팀원 앱 tone.ts의 BASE_HZ와 같은 높이)
  const ENERGY = { fire: { root: 60, hz: 264 }, water: { root: 57, hz: 216 }, wood: { root: 52, hz: 160 }, metal: { root: 54, hz: 185 }, earth: { root: 55, hz: 198 } }
  const PENTA = [0, 2, 4, 7, 9]
  const MAJ7 = [0, 4, 7, 11], MIN7 = [0, 3, 7, 10], ADD9 = [0, 4, 7, 14], SUS2 = [0, 2, 7, 12]
  // 상황별 설정: bpm · 생성 온도(선율/드럼) · 코드 진행[근음, 화음] · 바탕 주파수 배수 · 스윙 · 볼륨(dB) · 필터(Hz)
  const SCENE = {
    quiet:  { bpm: 80,  tMel: 0.3,  tDrum: 0,   prog: [[0, ADD9], [5, MAJ7]],                         droneX: 1,   swing: 0,    db: -30, cut: 1100, drums: false, mel: 0.5,  oct: 0 },
    rub:    { bpm: 96,  tMel: 0.6,  tDrum: 0.7, prog: [[0, SUS2], [5, ADD9]],                         droneX: 1,   swing: 0,    db: null, cut: null, drums: true,  mel: 0.85, oct: 0 },
    done:   { bpm: 104, tMel: 0.85, tDrum: 0.9, prog: [[0, MAJ7], [9, MIN7], [5, MAJ7], [7, ADD9]],   droneX: 1.5, swing: 0,    db: -9,  cut: 9000, drums: true,  mel: 1,    oct: 12 },
    replay: { bpm: 88,  tMel: 0.5,  tDrum: 0.6, prog: [[9, MIN7], [5, MAJ7], [0, MAJ7], [7, SUS2]],   droneX: 1,   swing: 0.22, db: -11, cut: 6500, drums: true,  mel: 0.9,  oct: 0 },
  }
  // 모델이 준비되기 전에 쓰는 드럼 (16칸 = 한 마디)
  const FALLBACK_DRUMS = {
    rub:    { k: [0, 8, 11], c: [], h: [2, 6, 10, 14], o: [], t: [] },
    done:   { k: [0, 4, 8, 12], c: [4, 12], h: [1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15], o: [6, 14], t: [] },
    replay: { k: [0, 7, 10], c: [4, 12], h: [0, 2, 4, 6, 8, 10, 12], o: [14], t: [] },
  }

  let mm = null, mmLoading = null, melVae = null, drumVae = null, modelsLoading = false
  let T = null, master = null, bus = null, filt = null, pump = null, pad = null, pluck = null, sub = null
  let kick = null, clap = null, hat = null, ohat = null, tom = null, drone = null
  let mode = 'off', energy = 'water', loopTimer = 0, bar = 0, nextBarAt = 0, unlocked = false
  let melody = null, melNext = null, drums = null, drumNext = null
  let rubLevel = 0, rubTarget = 0, lastMove = null

  // ── 라이브러리·모델 ─────────────
  function loadMM() {
    if (mm) return Promise.resolve(mm)
    if (mmLoading) return mmLoading
    mmLoading = new Promise((res, rej) => {
      if (window.mm) { mm = window.mm; return res(mm) }
      const s = document.createElement('script'); s.src = MM_SRC; s.async = true
      s.onload = () => { mm = window.mm; mm ? res(mm) : rej(new Error('magenta 없음')) }
      s.onerror = rej
      document.head.appendChild(s)
    })
    return mmLoading
  }
  // 휴대폰에서는 AI 모델(TensorFlow WebGL)을 쓰지 않음: 이미지가 많은 화면 위에 WebGL까지 올리면
  // iOS(특히 카카오톡 같은 앱 안 브라우저)가 그래픽 메모리 부족으로 화면을 통째로 지워 버림.
  // 소리는 같은 규칙의 생성 패턴(fallbackMelody·FALLBACK_DRUMS)으로 계속 상황마다 바뀌며 연주돼요.
  const LITE = (matchMedia('(pointer: coarse)').matches || navigator.maxTouchPoints > 0) && Math.min(screen.width, screen.height) <= 500
  function loadModels() {
    if (modelsLoading || LITE) return
    modelsLoading = true
    ;(async () => { try { const m = new mm.MusicVAE(MEL_CKPT); await m.initialize(); melVae = m } catch (e) {} })()
    ;(async () => { try { const d = new mm.MusicVAE(DRUM_CKPT); await d.initialize(); drumVae = d } catch (e) {} })()
  }

  // ── 소리 장치 ─────────────
  function ensureAudio() {
    if (T) return
    T = mm.Player.tone
    master = new T.Gain(0).toDestination()
    filt = new T.Filter({ frequency: 8000, type: 'lowpass', rolloff: -24, Q: 0.6 }).connect(master)
    bus = new T.Gain(1).connect(filt)
    const reverb = new T.Reverb({ decay: 5, wet: 0.35 }).connect(bus)
    const delay = new T.FeedbackDelay({ delayTime: '8n.', feedback: 0.28, wet: 0.18 }).connect(reverb)
    pump = new T.Gain(1).connect(reverb)                   // 킥마다 눌렸다 올라오는 패드
    pad = new T.PolySynth(T.Synth, { oscillator: { type: 'fatsawtooth', count: 3, spread: 24 }, envelope: { attack: 0.6, decay: 0.4, sustain: 0.7, release: 1.8 } })
    pad.connect(new T.Filter(1300, 'lowpass').connect(pump)); pad.volume.value = -27
    pluck = new T.PolySynth(T.FMSynth, { harmonicity: 3, modulationIndex: 1.1, oscillator: { type: 'sine' }, modulation: { type: 'triangle' },
      envelope: { attack: 0.004, decay: 0.42, sustain: 0.08, release: 0.9 }, modulationEnvelope: { attack: 0.002, decay: 0.25, sustain: 0, release: 0.4 } })
    pluck.connect(delay); pluck.volume.value = -12
    sub = new T.MonoSynth({ oscillator: { type: 'sine' }, envelope: { attack: 0.01, decay: 0.2, sustain: 0.8, release: 0.3 }, filterEnvelope: { baseFrequency: 180, octaves: 1 } })
    sub.connect(pump); sub.volume.value = -13
    kick = new T.MembraneSynth({ pitchDecay: 0.035, octaves: 6, envelope: { attack: 0.001, decay: 0.38, sustain: 0, release: 0.1 } }).connect(bus); kick.volume.value = -7
    clap = new T.NoiseSynth({ noise: { type: 'pink' }, envelope: { attack: 0.001, decay: 0.16, sustain: 0 } })
    clap.connect(new T.Filter(1600, 'bandpass').connect(reverb)); clap.volume.value = -14
    hat = new T.NoiseSynth({ noise: { type: 'white' }, envelope: { attack: 0.001, decay: 0.035, sustain: 0 } })
    hat.connect(new T.Filter(8500, 'highpass').connect(bus)); hat.volume.value = -24
    ohat = new T.NoiseSynth({ noise: { type: 'white' }, envelope: { attack: 0.002, decay: 0.22, sustain: 0 } })
    ohat.connect(new T.Filter(7000, 'highpass').connect(bus)); ohat.volume.value = -27
    tom = new T.MembraneSynth({ pitchDecay: 0.02, octaves: 2, envelope: { attack: 0.001, decay: 0.25, sustain: 0 } }).connect(reverb); tom.volume.value = -18
  }
  function setDrone(hz) {
    if (drone && Math.abs(drone.hz - hz) < 0.5) return
    stopDrone()
    const g = new T.Gain(0).connect(bus)
    const l = new T.Oscillator(hz, 'sine').connect(new T.Panner(-0.7).connect(g))
    const r = new T.Oscillator(hz + 4, 'sine').connect(new T.Panner(0.7).connect(g))   // 4Hz 차이로 일렁이는 주파수
    ;[l, r].forEach((x) => x.start())
    g.gain.rampTo(0.1, 2)
    drone = { g, oscs: [l, r], hz }
  }
  function stopDrone() {
    if (!drone) return
    const d = drone; drone = null
    d.g.gain.rampTo(0, 0.6)
    setTimeout(() => d.oscs.forEach((o) => { try { o.stop(); o.dispose() } catch (e) {} }), 800)
  }

  // ── 생성 (magenta) ─────────────
  const snap = (pitch) => {
    const root = ENERGY[energy].root + 12
    const p = Math.max(root - 5, Math.min(root + 19, pitch))
    const oct = Math.floor((p - root) / 12), d = ((p - root) % 12 + 12) % 12
    const near = PENTA.reduce((a, b) => (Math.abs(b - d) < Math.abs(a - d) ? b : a))
    return root + oct * 12 + near
  }
  function fallbackMelody() {
    const notes = []; let i = 3, step = 0
    while (step < 64) {
      const len = [2, 2, 3, 4, 4, 6][Math.floor(Math.random() * 6)]
      i = Math.max(0, Math.min(9, i + [-2, -1, 1, 1, 2, 0][Math.floor(Math.random() * 6)]))
      if (Math.random() > 0.25) notes.push({ pitch: ENERGY[energy].root + 12 + PENTA[i % 5] + 12 * Math.floor(i / 5), s: step, e: step + len })
      step += len
    }
    return notes
  }
  async function genMelody(sc) {
    if (melVae) {
      try {
        const [s] = await melVae.sample(1, sc.tMel)
        const notes = (s.notes || []).map((n) => ({ pitch: n.pitch, s: n.quantizedStartStep || 0, e: Math.max(n.quantizedEndStep || 0, (n.quantizedStartStep || 0) + 1) }))
        if (notes.length >= 4) return notes
      } catch (e) {}
    }
    return fallbackMelody()
  }
  function drumKind(p) {
    if (p === 35 || p === 36) return 'k'
    if (p === 37 || p === 38 || p === 39 || p === 40) return 'c'
    if (p === 42 || p === 44 || p === 51 || p === 53 || p === 59) return 'h'
    if (p === 46) return 'o'
    if (p >= 41 && p <= 50 && p !== 42 && p !== 44 && p !== 46 && p !== 49) return 't'
    return null
  }
  async function genDrums(name, sc) {
    if (drumVae && sc.drums) {
      try {
        const [s] = await drumVae.sample(1, sc.tDrum)
        const pat = [0, 1].map(() => ({ k: [], c: [], h: [], o: [], t: [] }))
        ;(s.notes || []).forEach((n) => {
          const st = n.quantizedStartStep || 0, k = drumKind(n.pitch)
          if (k && st < 32) pat[Math.floor(st / 16)][k].push(st % 16)
        })
        if (pat[0].k.length + pat[1].k.length >= 2) {
          pat.forEach((b) => { if (!b.k.includes(0)) b.k.push(0) })               // 마디 첫 박은 늘 킥
          if (name === 'done') pat.forEach((b) => { [4, 12].forEach((i) => b.c.includes(i) || b.c.push(i)) })   // 축하: 2·4박 클랩
          pat.forEach((b) => Object.keys(b).forEach((k) => { b[k] = [...new Set(b[k])].sort((x, y) => x - y) }))   // 같은 악기는 시간 순서대로
          return pat
        }
      } catch (e) {}
    }
    const f = FALLBACK_DRUMS[name]
    return f ? [f, f] : null
  }

  // ── 한 마디씩 예약 ─────────────
  // 한 악기(단음 악기)는 앞서 예약한 시각보다 이른 시각에 칠 수 없어서, 악기마다 마지막 시각을 기억해 두고 그보다 늦게만 침
  const lastAt = new Map()
  function hit(inst, fn, t) {
    const prev = lastAt.get(inst) || 0
    if (t <= prev + 0.002) return
    lastAt.set(inst, t)
    try { fn(t) } catch (e) {}
  }
  function scheduleBar() {
    clearTimeout(loopTimer)
    if (mode === 'off') return
    try { scheduleBarInner() } catch (e) {}
    loopTimer = setTimeout(scheduleBar, Math.max(50, (nextBarAt - T.now() - 0.25) * 1000))
  }
  function scheduleBarInner() {
    const sc = SCENE[mode], step = 60 / sc.bpm / 4
    const t0 = Math.max(T.now() + 0.08, nextBarAt)
    const at = (i) => t0 + i * step + (sc.swing && i % 2 === 1 ? sc.swing * step : 0)
    const root = ENERGY[energy].root
    if (bar % 4 === 0) {                                   // 4마디마다 새로 생성한 선율로 교체
      melody = melNext || fallbackMelody(); melNext = null
      genMelody(sc).then((m) => { melNext = m })
    }
    if (bar % 2 === 0) {                                   // 2마디마다 새로 생성한 드럼으로 교체
      drums = drumNext || (FALLBACK_DRUMS[mode] ? [FALLBACK_DRUMS[mode], FALLBACK_DRUMS[mode]] : null); drumNext = null
      genDrums(mode, sc).then((d) => { drumNext = d })
    }
    const lv = mode === 'rub' ? rubLevel : 1                // 문지르는 세기
    // 코드 패드 + 서브 베이스
    const [cr, chord] = sc.prog[bar % sc.prog.length]
    try { pad.triggerAttackRelease(chord.map((iv) => T.Frequency(root + cr + iv, 'midi').toFrequency()), 16 * step * 0.95, t0, mode === 'quiet' ? 0.35 : 0.55) } catch (e) {}
    if (mode !== 'quiet') [0, 6, 10].forEach((i, k) => hit(sub, (t) => sub.triggerAttackRelease(T.Frequency(root - 12 + cr, 'midi').toFrequency(), (k === 0 ? 5 : 3) * step * 0.95, t, 0.8 * Math.max(0.4, lv)), at(i)))
    // 선율
    const lo = (bar % 4) * 16
    ;(melody || []).filter((n) => n.s >= lo && n.s < lo + 16).forEach((n) => {
      if (Math.random() > sc.mel) return
      try { pluck.triggerAttackRelease(T.Frequency(snap(n.pitch) + sc.oct, 'midi').toFrequency(), Math.min(1.2, (n.e - n.s) * step * 1.3), at(n.s - lo), (0.35 + Math.random() * 0.25) * Math.max(0.5, lv)) } catch (e) {}
    })
    // 드럼 (문지르는 중에는 세게·빠르게 문지를수록 하나씩 들어옴)
    const d = sc.drums && drums ? drums[bar % 2] : null
    if (d) {
      const on = (need) => mode !== 'rub' || lv >= need
      if (on(0.3)) d.k.forEach((i) => hit(kick, (t) => { kick.triggerAttackRelease(T.Frequency(root - 24, 'midi').toFrequency(), '16n', t, i === 0 ? 0.95 : 0.65); duck(t, step) }, at(i)))
      if (on(0.55)) d.c.forEach((i) => { hit(clap, (t) => clap.triggerAttackRelease('32n', t, 0.8), at(i)); hit(clap, (t) => clap.triggerAttackRelease('32n', t, 0.5), at(i) + 0.012) })
      if (on(0.15)) d.h.forEach((i) => hit(hat, (t) => hat.triggerAttackRelease('32n', t, (i % 4 === 2 ? 0.9 : 0.55) * (mode === 'rub' ? 0.6 + lv * 0.4 : 1)), at(i)))
      if (on(0.7)) d.o.forEach((i) => hit(ohat, (t) => ohat.triggerAttackRelease('16n', t, 0.6), at(i)))
      if (on(0.5)) d.t.forEach((i) => hit(tom, (t) => tom.triggerAttackRelease(T.Frequency(root - 5 + (i % 3) * 3, 'midi').toFrequency(), '16n', t, 0.5), at(i)))
    }
    bar++; nextBarAt = t0 + 16 * step
  }
  function duck(t, step) {                                 // 사이드체인: 킥 순간 패드·베이스가 눌렸다 올라옴
    pump.gain.cancelScheduledValues(t - 0.006)
    pump.gain.setValueAtTime(1, Math.max(T.now(), t - 0.005))
    pump.gain.linearRampToValueAtTime(0.35, t + 0.02)
    pump.gain.linearRampToValueAtTime(1, t + step * 3)
  }
  function restart() { bar = 0; nextBarAt = Math.max(0, nextBarAt - 0.01); melody = null; melNext = null; drums = null; drumNext = null; scheduleBar() }

  // ── 문지르기: 손가락이 빠를수록 크고 밝게 ─────────────
  addEventListener('pointermove', (e) => {
    if (mode !== 'rub' || !(e.buttons || e.pointerType === 'touch')) { lastMove = null; return }
    const now = performance.now()
    if (lastMove) {
      const dt = Math.max(8, now - lastMove.t), v = Math.hypot(e.clientX - lastMove.x, e.clientY - lastMove.y) / dt * 1000   // px/s
      const k = (document.documentElement.clientWidth || 402) / 402
      rubTarget = Math.max(rubTarget, Math.min(1, v / k / 1400))
    }
    lastMove = { x: e.clientX, y: e.clientY, t: now }
  }, true)
  addEventListener('pointerup', () => { lastMove = null }, true)
  setInterval(() => {
    if (!T || mode !== 'rub') return
    rubLevel += (rubTarget - rubLevel) * (rubTarget > rubLevel ? 0.45 : 0.12)   // 빨리 올라가고 천천히 잦아듦
    rubTarget *= 0.82
    master.gain.rampTo(T.dbToGain(-30 + rubLevel * 23), 0.08)                    // -30dB → -7dB
    filt.frequency.rampTo(380 * Math.pow(2, rubLevel * 4.6), 0.08)               // 380Hz → 약 9000Hz
  }, 50)

  // ── 화면 상태 → 소리 ─────────────
  function hueOf([r, g, b]) {
    r /= 255; g /= 255; b /= 255
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn
    if (!d) return null
    const h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4
    return (h * 60 + 360) % 360
  }
  function energyOf(el) {
    const charm = el.querySelector('[class*="gifted__charm--"]')
    if (charm) { const m = charm.className.match(/gifted__charm--(\w+)/); if (m && ENERGY[m[1]]) return m[1] }
    const c = getComputedStyle(el).getPropertyValue('--wish').trim(), rgb = c.match(/\d+(\.\d+)?/g)
    let hue = null
    if (c.startsWith('#') && c.length >= 7) hue = hueOf([1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16)))
    else if (rgb && rgb.length >= 3) hue = hueOf(rgb.slice(0, 3).map(Number))
    if (hue === null) return energy
    if (hue < 20 || hue >= 290) return 'fire'
    if (hue < 50) return 'earth'
    if (hue < 95) return 'metal'
    if (hue < 165) return 'wood'
    return 'water'
  }
  function wanted() {
    const lp = document.querySelector('.lp.is-playing')
    if (lp) {
      const scene = lp.querySelector('.lp__scene'), h = scene && scene.style.filter.match(/hue-rotate\((-?\d+)/)
      const HUE = { 0: 'water', 125: 'fire', '-40': 'wood', '-115': 'metal', 170: 'earth' }   // 팀원 앱 LISTEN_HUE
      return { mode: 'replay', energy: h ? (HUE[h[1]] || 'water') : 'water' }
    }
    const g = document.querySelector('.gifted')
    if (g) return { mode: g.classList.contains('is-guide') ? 'quiet' : g.querySelector('.gifted__charm') ? 'done' : 'rub', energy: energyOf(g) }
    return { mode: 'off' }
  }
  async function sync() {
    const w = wanted()
    if (w.mode === mode && (w.mode === 'off' || w.energy === energy)) return
    const was = mode; mode = w.mode
    if (mode === 'off') { clearTimeout(loopTimer); if (master) { master.gain.rampTo(0, 0.8); stopDrone() } return }
    try { await loadMM() } catch (e) { return }
    loadModels(); ensureAudio()
    if (!unlocked) { try { await T.start(); unlocked = true } catch (e) {} }
    const changedEnergy = w.energy !== energy; energy = w.energy
    const sc = SCENE[mode]
    if (mode === 'rub') { rubLevel = 0.08; rubTarget = 0 }
    else { master.gain.rampTo(T.dbToGain(sc.db), mode === 'quiet' ? 1.2 : 0.9); filt.frequency.rampTo(sc.cut, 1.2) }
    setDrone(ENERGY[energy].hz * sc.droneX)               // 상황마다 다른 바탕 주파수 (참 등장 후엔 5도 위)
    if (mode === 'replay') stopDrone()                     // 다시 듣기는 팀원 앱의 바탕음이 이미 있어요
    // 상황이 바뀌면 그 상황에 맞게 새로 생성 (다음 마디부터)
    melNext = null; drumNext = null
    if (was === 'off' || changedEnergy) restart()
    else { bar = 0; genMelody(sc).then((m) => { melNext = m }); genDrums(mode, sc).then((d) => { drumNext = d }) }
  }

  // 브라우저는 사람이 화면을 만져야 소리를 켜 줘요 → 첫 터치에 소리 장치를 깨움
  const wake = () => { if (T && !unlocked) T.start().then(() => { unlocked = true }).catch(() => {}) }
  addEventListener('pointerdown', wake, true)
  addEventListener('keydown', wake, true)
  addEventListener('message', (e) => { if (e.data === 'chiring:reset') { mode = 'quiet'; sync() } })   // 팀 프로토타입이 이 화면을 숨기면 조용히
  new MutationObserver(() => sync()).observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] })
  setInterval(sync, 500)
  setTimeout(() => loadMM().catch(() => {}), 1500)           // 기운 충전 화면이 열리면 미리 받아 둠
  // 확인용: 지금 소리 상태
  window.__teamSound = () => ({ lite: LITE, mode, energy, bars: bar, melModel: !!melVae, drumModel: !!drumVae, rub: +rubLevel.toFixed(2),
    volumeDb: master ? Math.round(T.gainToDb(master.gain.value)) : null, cutoff: filt ? Math.round(filt.frequency.value) : null, ctx: T ? T.context.state : null })
})()
