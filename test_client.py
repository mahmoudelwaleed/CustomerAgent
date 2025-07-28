import asyncio
import os
from dotenv import load_dotenv
from livekit import rtc, api

# Load environment variables from .env file
load_dotenv()

# --- LiveKit Cloud Connection Details ---
LIVEKIT_URL = os.environ.get("LIVEKIT_URL")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET")

# --- Test Configuration ---
ROOM_NAME = "customer-support-room"
USER_IDENTITY = "test-customer"


# A helper to create a silent audio track
# --- THIS CLASS IS NOW CORRECTED ---
class SilentAudioSource(rtc.AudioSource):
    def __init__(self, sample_rate=48000, num_channels=1):
        # Pass the required arguments to the parent constructor.
        # The parent class handles setting the internal state.
        super().__init__(sample_rate, num_channels)
        
        # We can still read self.sample_rate and self.num_channels here
        # because the super().__init__() call has set them internally.
        
        bits_per_sample = 16
        
        # Calculate buffer size for a 20ms frame of silence
        samples_per_frame = self.sample_rate // 50
        buffer_size = samples_per_frame * self.num_channels * (bits_per_sample // 8)
        self._silence = b'\x00' * buffer_size
        self._frame = rtc.AudioFrame(
            self._silence, self.sample_rate, self.num_channels, bits_per_sample
        )

    async def capture_frame(self):
        # Return the pre-calculated silent frame
        return self._frame


async def main():
    if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
        print("LiveKit environment variables not set. Please check your .env file.")
        return

    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(USER_IDENTITY)
        .with_name("Test Customer")
        .with_grants(api.VideoGrants(room_join=True, room=ROOM_NAME))
        .to_jwt()
    )

    room = rtc.Room()

    @room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        # This event is triggered when the agent joins and publishes its audio track
        print(f"\n--- Track Subscribed ---")
        print(f"Participant: {participant.identity}")
        print(f"Track ID: {track.sid}, Kind: {track.kind}")
        print(f"------------------------\n")
        if track.kind == rtc.TrackKind.AUDIO:
            print(f"Receiving audio from: {participant.identity}. The agent is ready.")

    try:
        print(f"Connecting to room '{ROOM_NAME}' as '{USER_IDENTITY}'...")
        await room.connect(LIVEKIT_URL, token)
        print("Successfully connected to the room.")

        source = SilentAudioSource()
        track = rtc.LocalAudioTrack.create_audio_track("mic", source)
        await room.local_participant.publish_track(track)
        print("Published silent audio track. Waiting for agent to join...")

        # Keep the script running to maintain the connection and listen for events
        await asyncio.Event().wait()

    except asyncio.CancelledError:
        print("Cancelled, disconnecting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Disconnecting from the room.")
        await room.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")