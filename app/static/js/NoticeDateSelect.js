const yearMonthDate = document.getElementsByClassName('month-calender')[0];
const notificationDateList = document.getElementsByClassName('notice-date');
// console.log(NotificationDateList);
const trRows = document.getElementsByClassName('body-tr');

const showRowsByNotificationDate = () => {
  // for(let nd in NotificationDateList){
    // console.log(nd);
  for(let i = 0; i < notificationDateList.length; i++){
    console.log(notificationDateList[i].textContent.match(/^\d{4}-?\d{2}/));
    // ['2023-08', index: 0, input: '2023-08-17 10:17:04', groups: undefined]なので[0]
    if(notificationDateList[i].textContent.match(/^\d{4}-?\d{2}/)[0] === yearMonthDate.value){
      notificationDateList[i].parentElement.style.display = "table-row";
    }else{
      notificationDateList[i].parentElement.style.display = "none";
    }

    if(yearMonthDate.value === ""){
      for(let i = 0; i < trRows.length; i++){
        trRows[i].style.display = "table-row";
      }
    }
  }
}

yearMonthDate.addEventListener('change', showRowsByNotificationDate);
