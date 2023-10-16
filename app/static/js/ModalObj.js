class ModalAppear {

	/* ModalFadeクラスのコンストラクタ */
  constructor(under, top, button, form){
    this.bottom_item = under;
    this.top_item = top;
    this.button_item = button;
    this.form = form;
	
    const myself = this;

    const appearModalSubmit = (dialog_phrase, modal_phrase) => {
      if(window.confirm(`${dialog_phrase}宜しいですか？`)){
        setTimeout(function(){
          myself.bottom_item.style.backgroundColor = "burlywood";
          myself.bottom_item.style.opacity = ".5";
          myself.top_item.style.visibility = "visible";
          let modal_p = myself.top_item.children;
          console.log(modal_p);
          modal_p[0].innerText = modal_phrase;
          myself.form.submit();
        }, 1000);
      }else{
        return false;
      }
    }

    this.callModal = function(arg1, arg2){
      myself.button_item.addEventListener('click', (e) => {
        e.preventDefault();
        appearModalSubmit(arg1, arg2);
      });
    }
  }
}
