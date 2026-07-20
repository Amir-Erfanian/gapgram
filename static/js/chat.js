const chatData = document.getElementById("chat-data");

const currentUserId = Number(chatData.dataset.currentUser);
const otherUserId = Number(chatData.dataset.otherUser);

const room =
    "chat_" +
    Math.min(currentUserId, otherUserId) +
    "_" +
    Math.max(currentUserId, otherUserId);

const form = document.getElementById("messageForm");
const input = document.getElementById("messageInput");
const chatBox = document.getElementById("chatBox");

socket.on("connect", () => {

    socket.emit("join", {
        room: room
    });

});

chatBox.scrollTop = chatBox.scrollHeight;

form.addEventListener("submit", function (e) {

    e.preventDefault();

    const text = input.value.trim();

    if (text === "")
        return;

    socket.emit("send_message", {

        room: room,

        sender_id: currentUserId,

        receiver_id: otherUserId,

        text: text

    });

    input.value = "";

});

socket.on("receive_message", function (data) {

    const row = document.createElement("div");

    if (data.sender_id === currentUserId) {

        row.className = "message-row outgoing";

        row.innerHTML = `
            <div class="bubble outgoing-bubble">
                ${data.text}
            </div>
        `;

    } else {

        row.className = "message-row incoming";

        row.innerHTML = `
            <div class="bubble incoming-bubble">
                ${data.text}
            </div>
        `;

    }

    chatBox.appendChild(row);

    chatBox.scrollTop = chatBox.scrollHeight;

});