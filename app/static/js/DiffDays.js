
const compareDays = () => {
  const formDays = document.getElementsByClassName('notice-day');

  try {
    if(formDays[0] > formDays[1]){
      throw new Error("開始日より前です。");
      // alert("開始日より前です。");
      // exit();
    }
  } catch(e) {
    console.log(e);
  }
}
