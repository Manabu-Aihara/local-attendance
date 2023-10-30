const reflectButton = document.getElementById('reflect');
const targetNumber = document.getElementById('target-number');
// edit_data_user
let commentArea = document.querySelector('.dummy-comment');
// console.log(commentArea);
const url = `/admin/edit_data_user/${targetNumber.textContent}/1`

reflectButton.addEventListener('click', (e) => {
  e.preventDefault();
  const subValue = document.getElementsByClassName('test-value')[0];
  console.log(subValue.value);
  // commentArea.textContent = subValue.value;
  fetch(url, {
    method: 'POST',
    headers: {
      'Access-Control-Allow-Origin': '*',
      // mode: 'no-cors',
      // Accept: 'application/json',
      'Content-Type': 'application/json'
    },
    // body: subValue.value
    body: JSON.stringify({
      'comment': subValue.value
    })
  })
  .then(res => res.json())
  .then(json => console.log(`投げた：${json}`));
  // .catch(err => console.log(err.response))
});
