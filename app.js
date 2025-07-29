// A simplified, audio-only client for debugging.
// Replace your entire app.js with this code.

const connectBtn = document.getElementById('connect-btn');
const disconnectBtn = document.getElementById('disconnect-btn');
const connectionStatus = document.getElementById('connection-status');
const agentContainer = document.getElementById('agent-container');

// --- Your project details ---
const wsURL = 'wss://learn-h4ad9frz.livekit.cloud';
const tokenServerURL = 'http://127.0.0.1:5000';
// --------------------------

let room;

// Function to get a token from your server
async function getToken(roomName, identity) {
    const response = await fetch(`${tokenServerURL}/get-token?room=${roomName}&identity=${identity}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(`Failed to get token: ${error.error}`);
    }
    const data = await response.json();
    return data.token;
}

// --- Main Connection Logic ---
connectBtn.addEventListener('click', async () => {
    console.log('Connect button clicked. Starting audio-only connection...');
    
    // Initialize a new Room object for a clean connection
    room = new LivekitClient.Room();

    connectionStatus.textContent = 'Connecting...';
    connectBtn.disabled = true;
    disconnectBtn.disabled = true;

    try {
        const roomName = 'my-agent-room';
        const identity = `user_${Math.floor(Math.random() * 1000)}`;

        console.log(`[1/5] Requesting token for room '${roomName}'`);
        const token = await getToken(roomName, identity);
        console.log('[2/5] Token received.');

        console.log('[3/5] Connecting to LiveKit room...');
        await room.connect(wsURL, token);
        console.log('[4/5] Successfully connected to room.');

        // This is the most critical part. We ONLY create and publish AUDIO.
        console.log('[5/5] Creating and publishing MICROPHONE track...');
        connectionStatus.textContent = 'Starting microphone...';
        
        // Explicitly create an AUDIO track.
        const audioTrack = await LivekitClient.createLocalAudioTrack();
        
        // Explicitly publish that AUDIO track.
        await room.localParticipant.publishTrack(audioTrack);
        
        console.log('SUCCESS: Microphone audio track has been published.');
        connectionStatus.textContent = 'Connected & Microphone On';
        disconnectBtn.disabled = false;

        // Listener to hear the agent's response
        room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {
            if (track.kind === 'audio') {
                console.log(`Agent audio track subscribed from participant: ${participant.identity}`);
                const audioElement = track.attach();
                agentContainer.appendChild(audioElement);
            }
        });

    } catch (error) {
        console.error('Connection process failed:', error);
        connectionStatus.textContent = `Error: ${error.message}`;
        connectBtn.disabled = false; // Allow retrying on failure
    }
});

// --- Disconnect Logic ---
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

console.log('Audio-only app.js has been loaded.');