const reflectButton = document.getElementById('reflect');
const targetNumber = document.getElementById('target-number');
// edit_data_user
let commentArea = document.querySelector('.dummy-comment');
// console.log(commentArea);

reflectButton.addEventListener('click', (e) => {
  e.preventDefault();
  const subValue = document.getElementsByClassName('test-value')[0];
  console.log(subValue.value);
  // commentArea.textContent = subValue.value;
  fetch(`/admin/edit_data_user/${targetNumber.textContent}/1`, {
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
  // .then(res => res.json())
  .then(res => console.log(res.json))
  // .catch(err => console.log(err.response))
});
