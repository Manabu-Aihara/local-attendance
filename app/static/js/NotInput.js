const currentForm = document.getElementByClass('approval');
const childElements = currentForm.children;
childElements.forEach(element => {
  console.log("何か問題でも：" + element)
  element.disabled = true;
});
