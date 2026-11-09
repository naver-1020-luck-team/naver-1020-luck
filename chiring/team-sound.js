/* 기운 주파수 소리 (팀 프로토타입용 · magenta.js)
 *
 * magenta.js(@magenta/music 1.23.1, Apache-2.0)의 MusicVAE가 짧은 선율을 만들고,
 * 기운마다 다른 바탕 주파수 위에서 맑은 종소리로 연주해요. 상황마다 박자·리듬이 달라요:
 *  - 문지르기 안내: 느리고 성긴 선율 + 아주 작은 셰이커 (가장 작게)
 *  - 문지르는 중: 조금 빨라지고 아르페지오가 또르르 + 셰이커 8박 + 작은 킥 (기운이 차오르는 느낌)
 *  - 참 등장 후: 밝은 종소리 선율 + 킥·박수 + 베이스 (축하하는 느낌)
 *  - 다시 듣기 재생: 느긋한 로파이 그루브 (킥·림·스윙 셰이커·베이스)
 *  - 기운 충전 → 주파수 다시 듣기 → 주파수 선택 → 재생 중: 보통 크기 (팀원 앱의 바탕음 위에 선율만 얹음)
 *  - 기운 선물 완료: 문지르기 안내(어두운 화면)에서는 가장 작게, 문지르는 중·참 등장 후에는 보통 크기
 * 모델은 처음 소리가 필요할 때 한 번만 불러와요. 불러오는 동안·인터넷이 안 될 때는 같은 음계로 만든 선율로 대신해요.
 */
(() => {
  const BASE = new URL('.', document.currentScript ? document.currentScript.src : location.href).href
  const MM_SRC = BASE + 'vendor/magentamusic-1.23.1.js'
  const CKPT = 'https://storage.googleapis.com/magentadata/js/checkpoints/music_vae/mel_4bar_small_q2'
  const DB = { quiet: -30, normal: -11 }          // 마스터 볼륨 (dB)
  const STEPS = 64                                // 선율 한 바퀴 = 4마디 (16분음표 64칸)
  // 상황별 박자와 리듬 (16칸 = 한 마디. k 킥 · r 림/박수 · h 셰이커 · b 베이스(0 근음, 7 5도) · a 아르페지오 켜기)
  const GROOVE = {
    quiet:  { bpm: 72,  mel: 0.55, octave: 0,  swing: 0,    k: [],           r: [],        h: [4, 12],                    b: [],                    a: false },
    rub:    { bpm: 92,  mel: 0.8,  octave: 0,  swing: 0,    k: [0, 8],       r: [],        h: [2, 6, 10, 14],             b: [[0, 0, 8]],           a: true },
    done:   { bpm: 100, mel: 1,    octave: 12, swing: 0,    k: [0, 7, 8],    r: [4, 12],   h: [2, 6, 10, 14],             b: [[0, 0, 6], [8, 7, 6]], a: false },
    replay: { bpm: 84,  mel: 0.9,  octave: 0,  swing: 0.28, k: [0, 7, 10],   r: [4, 12],   h: [0, 2, 4, 6, 8, 10, 12, 14], b: [[0, 0, 6], [8, 7, 4], [12, 0, 4]], a: false },
  }

  // 기운별 바탕음 (팀원 앱 tone.ts의 BASE_HZ와 같은 높이) + 그 위의 5음 음계
  const ENERGY = {
    fire: { root: 60, hz: 264 }, water: { root: 57, hz: 216 }, wood: { root: 52, hz: 160 },
    metal: { root: 54, hz: 185 }, earth: { root: 55, hz: 198 },
  }
  const PENTA = [0, 2, 4, 7, 9]

  let mm = null, mmLoading = null, vae = null, vaeLoading = null
  let T = null, master = null, synth = null, drone = null, kick = null, rim = null, hat = null, bass = null, arp = null
  let bar = 0, nextBarAt = 0
  let mode = 'off', energy = 'water', loopTimer = 0, seq = null, unlocked = false

  // ── 라이브러리·모델 불러오기 ─────────────
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
  function loadVAE() {
    if (vae || vaeLoading) return
    vaeLoading = (async () => {
      try {
        const m = new mm.MusicVAE(CKPT)
        await m.initialize()
        vae = m
      } catch (e) { vaeLoading = null }   // 인터넷이 안 되면 대신 선율로 계속
    })()
  }

  // ── 소리 장치 ─────────────
  function ensureAudio() {
    if (T) return
    T = mm.Player.tone
    master = new T.Gain(0).toDestination()
    const reverb = new T.Reverb({ decay: 7, wet: 0.45 }).connect(master)
    synth = new T.PolySynth(T.FMSynth, {
      harmonicity: 2, modulationIndex: 1.4,
      oscillator: { type: 'sine' }, modulation: { type: 'sine' },
      envelope: { attack: 0.35, decay: 1.2, sustain: 0.25, release: 3.2 },
      modulationEnvelope: { attack: 0.5, decay: 0.8, sustain: 0.2, release: 2 },
    }).connect(reverb)
    synth.volume.value = -9
    // 리듬: 모두 작고 부드럽게 (주파수 분위기를 해치지 않게)
    kick = new T.MembraneSynth({ pitchDecay: 0.04, octaves: 5, envelope: { attack: 0.002, decay: 0.32, sustain: 0, release: 0.1 } }).connect(master)
    kick.volume.value = -8
    rim = new T.NoiseSynth({ noise: { type: 'pink' }, envelope: { attack: 0.002, decay: 0.09, sustain: 0 } }).connect(new T.Filter(1900, 'bandpass').connect(reverb))
    rim.volume.value = -17
    hat = new T.NoiseSynth({ noise: { type: 'white' }, envelope: { attack: 0.001, decay: 0.045, sustain: 0 } }).connect(new T.Filter(7000, 'highpass').connect(master))
    hat.volume.value = -25
    bass = new T.MonoSynth({ oscillator: { type: 'triangle' }, filter: { Q: 1, type: 'lowpass' }, filterEnvelope: { attack: 0.02, decay: 0.3, sustain: 0.4, release: 0.6, baseFrequency: 120, octaves: 2 },
      envelope: { attack: 0.02, decay: 0.3, sustain: 0.5, release: 0.6 } }).connect(master)
    bass.volume.value = -14
    arp = new T.Synth({ oscillator: { type: 'triangle' }, envelope: { attack: 0.005, decay: 0.18, sustain: 0, release: 0.25 } }).connect(reverb)
    arp.volume.value = -21
  }
  function startDrone() {
    stopDrone()
    const hz = ENERGY[energy].hz, g = new T.Gain(0).connect(master)
    const l = new T.Oscillator(hz, 'sine').connect(new T.Panner(-0.6).connect(g))
    const r = new T.Oscillator(hz + 4, 'sine').connect(new T.Panner(0.6).connect(g))
    const o = new T.Oscillator(hz * 1.5, 'sine').connect(new T.Gain(0.25).connect(g))
    ;[l, r, o].forEach((x) => x.start())
    g.gain.rampTo(0.22, 2)
    drone = { g, oscs: [l, r, o] }
  }
  function stopDrone() {
    if (!drone) return
    const d = drone; drone = null
    d.g.gain.rampTo(0, 0.6)
    setTimeout(() => d.oscs.forEach((o) => { try { o.stop(); o.dispose() } catch (e) {} }), 800)
  }

  // ── 선율: MusicVAE 샘플(없으면 같은 음계의 대신 선율)을 기운 음계에 맞춰 연주 ─────────────
  const snap = (pitch) => {
    const root = ENERGY[energy].root + 12
    let p = Math.max(root - 5, Math.min(root + 19, pitch))
    const oct = Math.floor((p - root) / 12), d = ((p - root) % 12 + 12) % 12
    const near = PENTA.reduce((a, b) => (Math.abs(b - d) < Math.abs(a - d) ? b : a))
    return root + oct * 12 + near
  }
  function fallbackSeq() {   // 모델이 준비되기 전: 음계 안에서 천천히 오르내리는 선율
    const notes = []; let i = 2, step = 0
    while (step < STEPS) {
      const len = [4, 4, 6, 8, 8, 12][Math.floor(Math.random() * 6)]
      i = Math.max(0, Math.min(9, i + [-2, -1, -1, 1, 1, 2][Math.floor(Math.random() * 6)]))
      if (Math.random() > 0.18) notes.push({ pitch: ENERGY[energy].root + 12 + PENTA[i % 5] + 12 * Math.floor(i / 5), s: step, e: step + len })
      step += len
    }
    return notes
  }
  async function nextSeq() {
    if (vae) {
      try {
        const [s] = await vae.sample(1, 0.45)
        const notes = (s.notes || []).map((n) => ({ pitch: n.pitch, s: n.quantizedStartStep || 0, e: Math.max((n.quantizedEndStep || 0), (n.quantizedStartStep || 0) + 2) }))
        if (notes.length >= 3) return notes
      } catch (e) {}
    }
    return fallbackSeq()
  }
  // 한 마디씩 앞당겨 예약 (상황이 바뀌면 다음 마디부터 바로 새 리듬)
  let melody = null
  function scheduleBar() {
    clearTimeout(loopTimer)
    if (mode === 'off') return
    const G = GROOVE[mode] || GROOVE.quiet, step = 60 / G.bpm / 4
    const t0 = Math.max(T.now() + 0.08, nextBarAt)
    const at = (i) => t0 + i * step + (G.swing && i % 2 === 1 ? G.swing * step : 0)
    if (!melody || bar % 4 === 0) {                       // 4마디마다 MusicVAE 새 선율
      melody = seq || fallbackSeq(); seq = null
      nextSeq().then((x) => { seq = x })
    }
    const lo = (bar % 4) * 16, root = ENERGY[energy].root
    melody.filter((n) => n.s >= lo && n.s < lo + 16).forEach((n) => {
      if (Math.random() > G.mel) return
      const dur = Math.min(2.2, (n.e - n.s) * step * 1.5)
      synth.triggerAttackRelease(T.Frequency(snap(n.pitch) + G.octave, 'midi').toFrequency(), dur, at(n.s - lo), 0.3 + Math.random() * 0.2)
    })
    G.k.forEach((i) => kick.triggerAttackRelease(T.Frequency(root - 24, 'midi').toFrequency(), '16n', at(i), i === 0 ? 0.9 : 0.55))
    G.r.forEach((i) => rim.triggerAttackRelease('32n', at(i), 0.7))
    G.h.forEach((i) => hat.triggerAttackRelease('32n', at(i), i % 4 === 2 ? 0.9 : 0.5))
    G.b.forEach(([i, iv, len]) => bass.triggerAttackRelease(T.Frequency(root - 12 + iv, 'midi').toFrequency(), len * step * 0.9, at(i), 0.7))
    if (G.a) for (let i = 0; i < 16; i += 2) {             // 또르르 올라가는 아르페지오 (기운이 차오름)
      const deg = (i / 2 + bar * 2) % 8
      arp.triggerAttackRelease(T.Frequency(root + 12 + PENTA[deg % 5] + 12 * Math.floor(deg / 5), 'midi').toFrequency(), '16n', at(i), 0.5)
    }
    bar++; nextBarAt = t0 + 16 * step
    loopTimer = setTimeout(scheduleBar, Math.max(50, (nextBarAt - T.now() - 0.25) * 1000))
  }
  function playLoop() { bar = 0; nextBarAt = 0; melody = null; scheduleBar() }

  // ── 화면 상태 → 소리 ─────────────
  function energyOf(el, prop) {
    // 선물 완료: 참 이름(…--water) 또는 기운 색(--wish)의 색상(hue)으로 기운을 고름
    const charm = el.querySelector('[class*="gifted__charm--"]')
    if (charm) { const m = charm.className.match(/gifted__charm--(\w+)/); if (m && ENERGY[m[1]]) return m[1] }
    const c = getComputedStyle(el).getPropertyValue(prop).trim()
    const rgb = c.match(/\d+(\.\d+)?/g)
    let hue = null
    if (c.startsWith('#') && c.length >= 7) { const v = [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16)); hue = hueOf(v) }
    else if (rgb && rgb.length >= 3) hue = hueOf(rgb.slice(0, 3).map(Number))
    if (hue === null) return energy
    if (hue < 20 || hue >= 290) return 'fire'
    if (hue < 50) return 'earth'
    if (hue < 95) return 'metal'
    if (hue < 165) return 'wood'
    return 'water'
  }
  function hueOf([r, g, b]) {
    r /= 255; g /= 255; b /= 255
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn
    if (!d) return null
    const h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4
    return (h * 60 + 360) % 360
  }
  function wanted() {
    const lp = document.querySelector('.lp.is-playing')
    if (lp) {
      const scene = lp.querySelector('.lp__scene'), h = scene && scene.style.filter.match(/hue-rotate\((-?\d+)/)
      const HUE = { 0: 'water', 125: 'fire', '-40': 'wood', '-115': 'metal', 170: 'earth' }   // 팀원 앱 LISTEN_HUE
      const e = h ? (HUE[h[1]] || 'water') : 'water'
      return { mode: 'replay', energy: e }
    }
    const g = document.querySelector('.gifted')
    if (g) return { mode: g.classList.contains('is-guide') ? 'quiet' : g.querySelector('.gifted__charm') ? 'done' : 'rub', energy: energyOf(g, '--wish') }
    return { mode: 'off' }
  }
  async function sync() {
    const w = wanted()
    if (w.mode === mode && (w.mode === 'off' || w.energy === energy)) return
    const was = mode; mode = w.mode
    if (mode === 'off') {
      clearTimeout(loopTimer)
      if (master) { master.gain.rampTo(0, 0.8); stopDrone() }
      return
    }
    try { await loadMM() } catch (e) { return }
    loadVAE(); ensureAudio()
    if (!unlocked) { try { await T.start(); unlocked = true } catch (e) {} }
    const changedEnergy = w.energy !== energy
    energy = w.energy
    master.gain.rampTo(T.dbToGain(mode === 'quiet' ? DB.quiet : DB.normal), mode === 'quiet' ? 1.2 : 0.9)
    if (mode === 'replay') stopDrone()                       // 다시 듣기는 팀원 앱의 바탕음이 이미 있어요
    else if (!drone || changedEnergy) startDrone()
    if (was === 'off' || changedEnergy) { seq = null; playLoop() }   // 모드만 바뀌면 다음 마디부터 새 리듬
  }

  // 브라우저는 사람이 화면을 만져야 소리를 켜 줘요 → 첫 터치에 소리 장치를 깨움
  const wake = () => { if (T && !unlocked) T.start().then(() => { unlocked = true }).catch(() => {}) }
  addEventListener('pointerdown', wake, true)
  addEventListener('keydown', wake, true)
  // 팀 프로토타입이 이 화면을 숨기면 바로 조용히
  addEventListener('message', (e) => { if (e.data === 'chiring:reset') { mode = 'quiet'; sync() } })
  new MutationObserver(() => sync()).observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] })
  setInterval(sync, 500)
  // 확인용: 지금 소리 상태
  window.__teamSound = () => ({ mode, energy, bars: bar, model: !!vae, volumeDb: master ? Math.round(T.gainToDb(master.gain.value)) : null, ctx: T ? T.context.state : null })
  // 기운 충전 화면이 열리면 라이브러리를 미리 받아 둠 (재생 시 바로 소리)
  setTimeout(() => loadMM().catch(() => {}), 1500)
})()
