function invokeAlert() {
    let alertSound = new Audio("alert.mp3");
    alertSound.volume = 0.30; // Set volume to 50%
    let page = document.getElementById("page");
    let messageArea = document.getElementById("message-area");
    let alertText = document.getElementById("message");

    alertSound.play();
    page.style.border = "5px solid red";

    messageArea.style.backgroundColor = "red";
    messageArea.style.borderRadius = "10px";
    messageArea.style.height = "20px";
    messageArea.style.width = "200px";

    alertText.style.color = "whitesmoke";

}

function clearAlert() {
    let page = document.getElementById("page");
    let messageArea = document.getElementById("message-area");
    let alertText = document.getElementById("message");

    page.style.border = "none";
    messageArea.style.backgroundColor = "transparent";
    alertText.style.color = "transparent";
}
