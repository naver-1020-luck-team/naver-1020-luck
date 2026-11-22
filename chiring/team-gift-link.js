/* 시연용 바로가기: 주소 끝이 #gift 일 때만 작동 (팀 프로토타입)
 *   …/chiring/index.html#gift  → 'Sumin님께 기운 선물 완료!' 카드 문지르기 화면에서 시작
 * 친구에게 기운 보내기 → Sumin → 내용 → 기운 → 주파수 만들기 → 카드 선택 → 메시지 → 기운 보내기
 * 를 사람 대신 차례로 눌러 줘요. 진행하는 동안은 화면을 어둡게 덮어 두었다가, 도착하면 걷어요.
 * #gift 가 아닌 주소(#frequency, #onboarding, 프로토타입 안의 기운 충전 탭)에서는 아무것도 하지 않아요.
 */
(() => {
  if (!/^#gift/.test(location.hash)) return
  const FRIEND = /sumin/i
  const TEXT = '시험 잘 보길'
  const MESSAGE = '수민아 화이팅!'

  // 진행하는 동안 덮개
  const cover = document.createElement('div')
  cover.style.cssText = 'position:fixed;inset:0;z-index:2147483647;background:#121212;transition:opacity .5s ease;pointer-events:none'
  const addCover = () => document.body && !cover.isConnected && document.body.appendChild(cover)
  addCover()
  const done = () => { cover.style.opacity = '0'; setTimeout(() => cover.remove(), 600); clearInterval(timer) }

  const visible = (el) => !!el && el.offsetParent !== null && !el.disabled
  const btn = (re) => [...document.querySelectorAll('button')].find((b) => visible(b) && re.test((b.innerText || b.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim()))
  const setText = (el, value) => {   // React 입력칸에 값 넣기
    const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value)
    el.dispatchEvent(new Event('input', { bubbles: true }))
  }
  const press = (el) => {   // 실제 손가락처럼 누름 (pointer → mouse → click)
    const r = el.getBoundingClientRect(), o = { bubbles: true, cancelable: true, clientX: r.left + r.width / 2, clientY: r.top + r.height / 2, pointerId: 1, pointerType: 'mouse', isPrimary: true }
    el.dispatchEvent(new PointerEvent('pointerdown', o)); el.dispatchEvent(new MouseEvent('mousedown', o))
    el.dispatchEvent(new PointerEvent('pointerup', o)); el.dispatchEvent(new MouseEvent('mouseup', o)); el.dispatchEvent(new MouseEvent('click', o))
  }
  const once = new Set()
  const step = (key, fn) => { if (once.has(key)) return false; once.add(key); fn(); return true }

  const started = Date.now()
  const timer = setInterval(() => {
    addCover()
    if (document.querySelector('.gifted')) { done(); return }          // 도착
    if (Date.now() - started > 30000) { done(); return }              // 30초가 지나면 덮개만 걷고 멈춤
    let b
    if ((b = btn(/^친구에게 기운 보내기/))) return step('friend-entry', () => press(b))
    if ((b = [...document.querySelectorAll('button')].find((x) => visible(x) && FRIEND.test(x.innerText || '')))
        && !once.has('friend')) return step('friend', () => press(b))
    // 내용 입력 화면: 카드 눌러 입력 → 칩 하나 → 다음
    const compose = document.querySelector('.compose__card')
    if (compose && visible(compose)) {
      const ta = compose.querySelector('textarea')
      if (!ta && !once.has('compose-open')) return step('compose-open', () => press(compose))
      if (ta && !ta.value) { ta.focus(); return setText(ta, TEXT) }
      if (ta && ta.value && !once.has('compose-done')) return step('compose-done', () => { ta.focus(); ta.blur() })   // 입력을 마쳐야 기운 칩이 나타남
      const chip = [...document.querySelectorAll('button')].find((x) => visible(x) && /기운$|집중력|긴장 완화|자신감|꿀잠/.test((x.innerText || '').trim()) && x.innerText.trim().length < 12)
      if (chip && !once.has('chip')) return step('chip', () => press(chip))
    }
    if ((b = btn(/^주파수 만들기$/))) return step('make', () => press(b))
    if ((b = btn(/^선택$/))) return step('pick', () => press(b))
    // 메시지 입력 → 기운 보내기
    const msg = document.querySelector('.gift__message')
    if (msg && visible(msg) && !msg.value) { msg.focus(); setText(msg, MESSAGE); msg.blur(); return }
    if ((b = btn(/^기운 보내기$/))) return step('send', () => press(b))
    if ((b = btn(/^다음$/))) {   // 화면마다 '다음' — 같은 화면에서 두 번 누르지 않도록 화면 글자로 구분
      const key = 'next:' + document.body.innerText.slice(0, 40)
      return step(key, () => press(b))
    }
  }, 350)
})()
