let today = new Date(); 
let year = today.getFullYear();
let month = today.getMonth();

function addDateOption(){
  let dateSelectBox = document.getElementsByClassName('search-date')[0];
  // console.log(dateSelectBox.options[0].text);

  if("2024/01" > dateSelectBox.options[0].text){
    console.log(true)
  } else {
    console.log(false)
  }
  //   let optInsert = document.createElement("option");
  //   optInsert.value = dateSelectBox.options[0].value + 1;
  //   optInsert.text = `${year}/${month}`;
  //   dateSelectBox.add(optInsert, dateSelectBox.options[0]);
  // }
}

const showDateButton = document.getElementById('show-date');
showDateButton.addEventListener('click', addDateOption);

