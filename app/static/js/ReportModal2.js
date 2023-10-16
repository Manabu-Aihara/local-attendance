
// お前はもう、宣言されている
// const bottomForm = document.getElementById('form-bottom');
const twoButton = document.getElementsByClassName('two-button')[0];

console.log(twoButton.children);

const ModalSubmit_ok = new ModalAppear(backArea[0], modalElement, twoButton.children[0], bottomForm);
ModalSubmit_ok.callModal("承認します。", "承認されました。");
const ModalSubmit_ng = new ModalAppear(backArea[0], modalElement, twoButton.children[1], bottomForm);
ModalSubmit_ng.callModal("未承認にします。", "未承認です。");
