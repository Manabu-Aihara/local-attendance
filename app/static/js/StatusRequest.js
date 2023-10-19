const extractRows = (statusNum) => {
  const trRows = document.getElementsByClassName('body-tr');
  /**
  * https://qiita.com/uruha/items/fc9564f5a8564f075391
  * NodeListに対してfilterを使いたい場合、{NodeList} => {Array} にしてやる必要がある
  */
  // const convertedTypeArrayRows = [].map.call(trRows, (element) => {
  //   return element;
  // });
  // const selectTrs = convertedTypeArrayRows.filter((selectTr) => {
  //   return selectTr.title == statusNum;
  // })
  /**
   * Uncaught TypeError: Cannot set properties of undefined
   */
  // for(let trRow in trRows)
  for(let i = 0; i < trRows.length; i++){
    if (trRows[i].dataset.status != statusNum) {
      // console.log(trRows[i]);
      trRows[i].style.display = "none";
    } else {
      trRows[i].style.display = "table-row";
    }
  }
}

const showRowsByStatus = () => {
  let statusSelect = document.getElementById('status').value;
  switch(statusSelect){
    case "0":
      document.getElementById('h4-status').textContent = "申請中リスト";
      extractRows(statusSelect);
      break;
    case "1":
      document.getElementById('h4-status').textContent = "承認済みリスト";
      extractRows(statusSelect);
      break;
    case "2":
      document.getElementById('h4-status').textContent = "未承認リスト";
      extractRows(statusSelect);
      break;
    default:
      // document.getElementById('h4-status').textContent = "申請中リスト";
      // extractRows("0");
  }
}

window.addEventListener('reload', () => {
  document.getElementById('h4-status').textContent = "申請中リスト";
  extractRows("0");
  console.log("ここ通る");
});

const extractStatusButton = document.getElementById('extract-status');
extractStatusButton.addEventListener('click', showRowsByStatus);
