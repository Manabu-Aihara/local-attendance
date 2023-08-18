const selectRow = () => {
  const trRows = document.getElementsByClassName('body-tr');
  // for(let i=0; i <= trRows.length; i++){
  //   if(trRows[i].title == 0){
  //     console.log(trRows[i]);
  //   }
  // }
  console.info(trRows[0].title);
}

const extractStatus = () => {
  let statusSelect = document.getElementById('status').value;
  switch(statusSelect){
    case "0":
      document.getElementById('h4-status').textContent = "申請中リスト";
      // console.log(statusSelect);
      selectRow(statusSelect);
      break;
    case "1":
      document.getElementById('h4-status').textContent = "承認済みリスト";
      // console.log(document.getElementById('status'));
      selectRow(statusSelect);
      break;
    case "2":
      document.getElementById('h4-status').textContent = "未承認リスト";
      selectRow(statusSelect);
      break;
    default:
      document.getElementById('h4-status').textContent = "でふぉると";
  }
}

const extractButton = document.getElementById('extract');
extractButton.addEventListener('click', selectRow);
