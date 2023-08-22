const fs = require('fs');

// let today = new Date(); 
// let year = today.getFullYear();
// let month = today.getMonth();

// //ファイル読み込み関数
// function readFile(path) {
//   fs.readFile(path, 'utf8', function (err, data) {

//     //エラーの場合はエラーを投げてくれる
//     if (err) {
//         throw err;
//     }
    
//     //ここに処理
//     console.log(data);
//   });
// }

// readFile("select-date.txt");

let dateSelectBox = document.getElementsByClassName('search-date')[0];
let optionArray = [];
for(let innerSelect in dateSelectBox){
  optionArray.push(innerSelect.text);
}
console.log(optionArray);
//ファイルの追記関数
function appendFile(path, data) {
  fs.appendFile(path, data, function (err) {
    if (err) {
        throw err;
    }
  });
}

appendFile("select-date.txt", optionArray);

const inputDateButton = document.getElementById('input-file');
inputDateButton.addEventListener('click', appendFile);
