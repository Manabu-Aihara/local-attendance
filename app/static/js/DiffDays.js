
let formDays = document.getElementsByClassName('notice-day');
const compareDays1 = () => {

  try {
    if(formDays[0].value > formDays[1].value){
      // throw new Error("開始日より前です。");
      alert("開始日より前です。");
      formDays[1].value = "";
      // exit();
    }
  } catch(e) {
    console.log(e);
  }
}

const compareDays2 = () => {
  const now = new Date();
  const today = `${now.getFullYear()}-${now.getMonth()+1}-${now.getDate()}`;
  try {
    console.log(formDays[0].value);
    if (today > formDays[0].value) {
      // throw new Error("前日の申請はできません。");
      alert("前日の申請はできません。");
      formDays[0].value = "";
    } else {
      return true;
    }
  } catch(e) {
    console.log(e);
  }
}

// formDays[0].addEventListener('change', compareDays2);
formDays[1].addEventListener('change', compareDays1);
