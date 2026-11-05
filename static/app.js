const $ = (selector) => document.querySelector(selector);
const money = (amount) => `${amount.toLocaleString('ko-KR')}원`;
let menu = [], cart = {}, category = '전체', submitting = false;

function renderMenu() {
  const categories = ['전체', ...new Set(menu.map(item => item.category))];
  $('#categories').replaceChildren(...categories.map(name => {
    const button = document.createElement('button');
    button.textContent = name; button.className = name === category ? 'active' : '';
    button.onclick = () => { category = name; renderMenu(); };
    return button;
  }));
  $('#menu').replaceChildren(...menu.filter(item => category === '전체' || item.category === category).map(item => {
    const button = document.createElement('button'); button.className = 'product';
    const art = document.createElement('div'); art.className = 'product-art'; art.textContent = item.emoji;
    const name = document.createElement('strong'); name.textContent = item.name;
    const desc = document.createElement('small'); desc.textContent = item.description;
    const bottom = document.createElement('div'); bottom.className = 'product-bottom';
    const price = document.createElement('b'); price.textContent = money(item.price);
    const plus = document.createElement('span'); plus.textContent = '+'; bottom.append(price, plus);
    button.append(art, name, desc, bottom); button.onclick = () => { cart[item.id] = Math.min((cart[item.id] || 0) + 1, 99); renderCart(); }; return button;
  }));
}
function renderCart() {
  const selected = menu.filter(item => cart[item.id]);
  $('#count').textContent = Object.values(cart).reduce((a, b) => a + b, 0);
  $('#total').textContent = money(selected.reduce((sum, item) => sum + item.price * cart[item.id], 0));
  $('#checkout').disabled = !selected.length || submitting;
  if (!selected.length) { $('#cart-items').innerHTML = '<div class="empty"><span>🛒</span><strong>아직 담은 메뉴가 없어요</strong><p>좋아하는 메뉴를 골라주세요!</p></div>'; return; }
  $('#cart-items').replaceChildren(...selected.map(item => {
    const row = document.createElement('div'); row.className = 'cart-row';
    const info = document.createElement('div'); const title = document.createElement('strong'); title.textContent = item.name;
    const price = document.createElement('p'); price.textContent = money(item.price * cart[item.id]); info.append(title, price);
    const controls = document.createElement('div'); controls.className = 'quantity';
    const minus = document.createElement('button'); minus.textContent = '−'; minus.setAttribute('aria-label', `${item.name} 수량 줄이기`); minus.onclick = () => { if (--cart[item.id] === 0) delete cart[item.id]; renderCart(); };
    const number = document.createElement('span'); number.textContent = cart[item.id];
    const plus = document.createElement('button'); plus.textContent = '+'; plus.setAttribute('aria-label', `${item.name} 수량 늘리기`); plus.onclick = () => { cart[item.id] = Math.min(cart[item.id] + 1, 99); renderCart(); };
    controls.append(minus, number, plus); row.append(info, controls); return row;
  }));
}
$('#clear').onclick = () => { cart = {}; renderCart(); };
$('#checkout').onclick = async () => {
  submitting = true; renderCart();
  try {
    const response = await fetch('/api/orders', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({items:Object.entries(cart).map(([menu_id, quantity]) => ({menu_id, quantity}))})});
    if (!response.ok) throw new Error();
    const order = await response.json(); cart = {}; $('#order-number').textContent = String(order.order_number).padStart(3, '0'); $('#complete').showModal();
  } catch { alert('주문을 처리하지 못했어요. 다시 시도해주세요.'); }
  finally { submitting = false; renderCart(); }
};
$('#restart').onclick = () => $('#complete').close();
fetch('/api/menu').then(response => { if (!response.ok) throw new Error(); return response.json(); }).then(data => { menu = data; renderMenu(); renderCart(); }).catch(() => { $('#menu-error').textContent = '메뉴를 불러오지 못했어요. 페이지를 새로고침해주세요.'; });
renderCart();
