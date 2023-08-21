let today = new Date(); 
let year = today.getFullYear();
let month = today.getMonth();

function addDateOption(){
  // console.log(opt1.text);
  let dateSelectBox = document.getElementsByClassName('date-search');
  console.log(dateSelectBox);

  for(let i = 0; i < dateSelectBox.length; i++){
    let opt1 = document.createElement("option");

    opt1.value = "1";
    opt1.text = `${year}/${month}`;

    dateSelectBox[i].add(opt1);
  }

  // if((`${year}/${month}`) > dateSelectBox.options[0].innerText.split('/')){
  //   let optInsert = document.createElement("option");
  //   optInsert.value = dateSelectBox.options[0].value + 1;
  //   optInsert.text = `${year}/${month}`;
  //   dateSelectBox.add(optInsert, dateSelectBox.options[0]);
  // }
}

const extractDateButton = document.getElementById('extract-date');
extractDateButton.addEventListener('click', addDateOption);

