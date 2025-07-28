const connectBtn = document.getElementById('connect-btn');
const disconnectBtn = document.getElementById('disconnect-btn');
const connectionStatus = document.getElementById('connection-status');
const agentContainer = document.getElementById('agent-container');

// Ensure this URL is correct for your LiveKit project
const wsURL = 'wss://learn-h4ad9frz.livekit.cloud'; 

// This is the address of your local Python token server
const tokenServerURL = 'http://localhost:5000'; 

let room;

async function getToken(roomName, identity) {
    const response = await fetch(`${tokenServerURL}/get-token?room=${roomName}&identity=${identity}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(`Failed to get token: ${error.error}`);
    }
    const data = await response.json();
    return data.token;
}

connectBtn.addEventListener('click', async () => {
    console.log('Connect button clicked. Starting connection process...');
    room = new livekit.Room(); 

    connectionStatus.textContent = 'Connecting...';
    connectBtn.disabled = true;

    try {
        const roomName = 'my-agent-room';
        const identity = `user_${Math.floor(Math.random() * 1000)}`;

        console.log('Requesting token from server...');
        connectionStatus.textContent = 'Requesting token...';
        const token = await getToken(roomName, identity);
        console.log('Token received.');

        console.log('Connecting to LiveKit room...');
        connectionStatus.textContent = 'Connecting to room...';
        await room.connect(wsURL, token);
        console.log('Successfully connected to room:', room.name);

        connectionStatus.textContent = 'Connected';
        disconnectBtn.disabled = false;
        await room.localParticipant.setMicrophoneEnabled(true);
        console.log('Microphone is on.');

        room.on(livekit.RoomEvent.TrackSubscribed, (track) => {
            if (track.kind === 'audio') {
                console.log('Agent audio track subscribed. Attaching...');
                const audioElement = track.attach();
                agentContainer.appendChild(audioElement);
            }
        });

    } catch (error) {
        console.error('Connection process failed:', error);
        connectionStatus.textContent = `Error: ${error.message}`;
        connectBtn.disabled = false;
    }
});

disconnectBtn.addEventListener('click', async () => {
    if (room) {
        await room.disconnect();
        console.log('Disconnected from the room.');
        connectionStatus.textContent = 'Disconnected';
        connectBtn.disabled = false;
        disconnectBtn.disabled = true;
        agentContainer.innerHTML = '';
    }
});

console.log('app.js has been loaded and event listeners are set.');