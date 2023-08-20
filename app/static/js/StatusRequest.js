const selectRows = (statusNum) => {
  const trRows = document.getElementsByClassName('body-tr');
  /**
  * https://qiita.com/uruha/items/fc9564f5a8564f075391
  * NodeListに対してfilterを使いたい場合、{NodeList} => {Array} にしてやる必要がある
  */
  const convertedTypeArrayRows = [].map.call(trRows, (element) => {
    return element;
  });
  const selectTrs = convertedTypeArrayRows.filter((selectTr) => {
    return selectTr.title == statusNum;
  })
  console.info(selectTrs);
}

const extractStatus = () => {
  let statusSelect = document.getElementById('status').value;
  switch(statusSelect){
    case "0":
      document.getElementById('h4-status').textContent = "申請中リスト";
      // console.log(statusSelect);
      selectRows(statusSelect);
      break;
    case "1":
      document.getElementById('h4-status').textContent = "承認済みリスト";
      // console.log(document.getElementById('status'));
      selectRows(statusSelect);
      break;
    case "2":
      document.getElementById('h4-status').textContent = "未承認リスト";
      selectRows(statusSelect);
      break;
    default:
      document.getElementById('h4-status').textContent = "でふぉると";
  }
}

const extractButton = document.getElementById('extract');
extractButton.addEventListener('click', extractStatus);
