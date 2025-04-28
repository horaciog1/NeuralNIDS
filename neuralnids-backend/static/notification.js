export function invokeAlert() {
    const scrollY = window.scrollY;
    let alertSound = new Audio("alert.mp3");
    alertSound.volume = 0.30;
    alertSound.play();

    let frame = document.getElementById("screen-frame");
    let messageArea = document.getElementById("message-area");
    let alertText = document.getElementById("message");

    frame.style.display = "block";
    messageArea.style.display = "flex";
    alertText.innerText = "❕ Critical Message ❕";
    alertText.style.color = "whitesmoke";

    window.scrollTo({ top: scrollY });
}

export function clearAlert() {
    let frame = document.getElementById("screen-frame");
    let messageArea = document.getElementById("message-area");
    let alertText = document.getElementById("message");

    frame.style.display = "none";
    alertText.style.color = "transparent";
    messageArea.style.display = "none";
}
