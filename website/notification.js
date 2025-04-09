function invokeAlert() {
    const scrollY = window.scrollY;       // Save scroll position
    let alertSound = new Audio("alert.mp3");
    alertSound.volume = 0.30; // Set volume to 30%

    // retrieve the elements needed throughout the function
    let page = document.getElementById("page");
    let messageArea = document.getElementById("message-area");
    let alertText = document.getElementById("message");

    // sound alert 
    alertSound.play();

    // higlight site border
    page.style.border = "5px solid red";

    // make message area visible
    messageArea.style.backgroundColor = "red";
    messageArea.style.borderRadius = "10px";
    messageArea.style.height = "20px";
    messageArea.style.width = "200px";

    alertText.style.color = "whitesmoke";
    window.scrollTo({ top: scrollY });      // Restore scroll position
}

function clearAlert() {

    // retrieve the elements needed throughout the function
    let page = document.getElementById("page");
    let messageArea = document.getElementById("message-area");
    let alertText = document.getElementById("message");

    // make visual alert elements invisible until next alert
    page.style.border = "none";
    messageArea.style.backgroundColor = "transparent";
    alertText.style.color = "transparent";
}
