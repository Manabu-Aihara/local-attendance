const selectForm = document.getElementsByClassName('form-control')[0];
const selectChildren = selectForm.options;
console.log(selectChildren);

const timeForms = document.getElementsByClassName('restrict-form');
const toggleRestrictState = (flag) => {
  if (flag == true) {
    for (let i = 0; i < timeForms.length; i++) {
      timeForms[i].readOnly = true;
      timeForms[i].style.backgroundColor = "gainsboro";
    }
  } else {
    for (let i = 0; i < timeForms.length; i++) {
      timeForms[i].readOnly = false;
      timeForms[i].style.backgroundColor = "";
    }
  }
}

const startTimeForm = timeForms[0];
const endTimeForm = timeForms[1];

const restrictCollection = () => {
  console.log("Called!")
  console.log(selectChildren.selectedIndex - 1);
  // console.log((selectChildren.selectedIndex - 1) === (((((((((3 )|| 5 )|| 7 )|| 8 )|| 9 )|| 17 )|| 18 )|| 19 )|| 20) ? true : false);

  // for(let option in selectChildren){
  //   console.log(option.selectedIndex);
  for (let i = 0; i < selectChildren.length; i++) {
    if ((selectChildren.selectedIndex - 1) === 3 || (selectChildren.selectedIndex - 1) === 5 || (selectChildren.selectedIndex - 1) === 7 || (selectChildren.selectedIndex - 1) === 8 || (selectChildren.selectedIndex - 1) === 9 || (selectChildren.selectedIndex - 1) === 17 || (selectChildren.selectedIndex - 1) === 18 || (selectChildren.selectedIndex - 1) === 19 || (selectChildren.selectedIndex - 1) === 20) {
      toggleRestrictState(true);
    } else if ((selectChildren.selectedIndex - 1) === 10 || (selectChildren.selectedIndex - 1) === 13) {
      toggleRestrictState(false);
      startTimeForm.addEventListener('input', () => {
        let [h, m] = startTimeForm.value.split(':');
        // console.log(0 + h);
        if (h < 10){
          const beforeTen = Number(h) + 1
          // console.log(h.toString().padStart(2, '0'))
          /**
           * 数字を指定した桁数まで0埋めする
              https://gray-code.com/javascript/fill-numbers-with-zeros/
           */
          endTimeForm.value = `${beforeTen.toString().padStart(2, '0')}:${m}`;
        } else {
          endTimeForm.value = `${Number(h) + 1}:${m}`;
        }
      });
    } 
  }
}

selectForm.addEventListener('change', restrictCollection);