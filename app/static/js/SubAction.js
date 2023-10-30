const reflectButton = document.getElementById('reflect');
const targetNumber = document.getElementById('target-number');
// dummy.html
const summaryElm = document.getElementsByClassName('summary-form')[0];
const ownerElm = document.getElementsByClassName('owner-form')[0];
// const url = `/admin/edit_data_user/${targetNumber.textContent}/1`

reflectButton.addEventListener('click', (e) => {
  e.preventDefault();
  let dom = window.opener.document.getElementById('main-comment');
  dom.value = `${summaryElm.value}  ${ownerElm.value}`;

  fetch('http://127.0.0.1:8000/todo/add', {
    method: 'POST',
    headers: {
      'Access-Control-Allow-Origin': '*',
      // mode: 'no-cors',
      // Accept: 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      summary: summaryElm.value,
      owner: ownerElm.value
    })
  })
  .then(res => res.json())
  .then(json => console.log(`投げた：${json}`))
  // .catch(err => console.log(err.response))
  .finally(() => {
    summaryElm.value = "";
    ownerElm.value = "";
  });
});
// reflectButton.addEventListener('click', () => {
//   let dom = window.opener.document.getElementById('main-comment');
//   dom.value = `${summaryElm.value}  ${ownerElm.value}`;
// });
