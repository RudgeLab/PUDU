import subprocess
import time
from typing import Optional

colors = [
    "#4040BF",   # Blue
    "#BF4040",   # Red
    "#40BF40",   # Green
    "#A640BF",   # Purple
    "#BFBF40",   # Yellow
    "#BF7340",   # Orange
    "#40BFBF",   # Cyan
    "#BF40A6",   # Magenta
    "#73BF40",   # Lime green
    "#4073BF",   # Blue-cyan
    "#BF8C40",   # Orange-yellow
    "#40BF73",   # Green-cyan
    "#7340BF",   # Blue-purple
    "#A6BF40",   # Yellow-green
    "#BF5940",   # Red-orange
    "#40A6BF",   # Cyan-blue
    "#BF4073",   # Red-purple
    "#59BF40",   # Green
    "#BFA640",   # Orange-yellow
    "#40BFA6",   # Cyan-green
    "#8CBF40",   # Yellow-green
    "#40BF59",   # Green
    "#40BF8C",   # Green-cyan
    "#BF40A6"    # Purple-magenta
]

class Camera:
    """
    Camera class for handling picture and video capture during Opentrons protocols.

    This class encapsulates all camera functionality including:
    - Taking snapshots at specific protocol steps
    - Recording video during protocol execution
    - Handling simulation mode gracefully
    - Managing ffmpeg processes
    """

    def __init__(self, video_size: str = "320x240", picture_size: str = "640x480",
                 video_device: str = "/dev/video0", storage_path: str = "/data/user_storage"):
        """
        Initialize Camera with configuration options.

        Args:
            video_size: Resolution for video recording (default: "320x240")
            picture_size: Resolution for picture capture (default: "640x480")
            video_device: Video device path (default: "/dev/video0")
            storage_path: Path where media files will be saved (default: "/data/user_storage")
        """
        self.video_size = video_size
        self.picture_size = picture_size
        self.video_device = video_device
        self.storage_path = storage_path
        self._active_video_process: Optional[subprocess.Popen] = None

    def cleanup_ffmpeg_processes(self) -> None:
        """Clean up any running ffmpeg processes using killall."""
        try:
            subprocess.run(['killall', 'ffmpeg'], capture_output=True, check=False)
        except Exception:
            pass  # Fail silently if cleanup doesn't work

    def capture_picture(self, protocol, when: str = "image") -> None:
        """
        Take a picture at a specific protocol step.

        Args:
            protocol: Opentrons protocol context
            when: Description of when the picture was taken (used in filename)

        Returns:
            Filename of captured image if successful, None if simulation or failed
        """
        if protocol.is_simulating():
            protocol.comment(f'[SIMULATION] Taking picture at protocol step: {when}')
            return

        protocol.comment(f'Taking picture at protocol step: {when}')
        timestamp = int(time.time())
        filename = f'{when}_image_{timestamp}.jpg'
        filepath = f'{self.storage_path}/{filename}'

        try:
            subprocess.check_call([
                'ffmpeg', '-loglevel', 'error', '-y', '-f', 'video4linux2',
                '-s', self.picture_size, '-i', self.video_device, '-ss', '0:0:1',
                '-frames', '1', filepath
            ])
            protocol.comment(f'{when.title()} picture captured: {filename}')

        except subprocess.CalledProcessError as e:
            protocol.comment(f'Warning: Picture capture failed: {e}, continuing protocol')


    def start_video(self, protocol) -> None:
        """
        Start video recording.

        Args:
            protocol: Opentrons protocol context

        Returns:
            Video process handle if successful, None if simulation or failed
        """
        if protocol.is_simulating():
            protocol.comment('[SIMULATION] Starting video recording')
            return

        # Clean up any existing processes
        self.cleanup_ffmpeg_processes()
        time.sleep(0.5)  # Brief pause for cleanup

        timestamp = int(time.time())
        filename = f'video_image_{timestamp}.mp4'
        filepath = f'{self.storage_path}/{filename}'

        try:
            video_process = subprocess.Popen([
                'ffmpeg', '-loglevel', 'error', '-y', '-video_size', self.video_size,
                '-i', self.video_device, filepath
            ])
            self._active_video_process = video_process
            protocol.comment(f"Video recording started: {filename}")
        except Exception as e:
            protocol.comment(f"Warning: Video recording failed: {e}")

    def stop_video(self, protocol) -> None:
        """
        Stop video recording.

        Args:
            protocol: Opentrons protocol context
            video_process: Video process to stop (uses active process if None)
        """
        if protocol.is_simulating():
            protocol.comment('[SIMULATION] Stopping video recording')
            return

        # Use provided process or the active one
        process_to_stop = self._active_video_process

        if process_to_stop is None:
            protocol.comment("No video recording process to stop")
            return

        if process_to_stop.poll() is None:  # Process is still running
            try:
                process_to_stop.terminate()
                process_to_stop.wait(timeout=5)
                protocol.comment("Video recording stopped")
            except subprocess.TimeoutExpired:
                process_to_stop.kill()
                process_to_stop.wait()
                protocol.comment("Video recording force-stopped")
            except Exception as e:
                protocol.comment(f"Warning: Error stopping video: {e}")
        else:
            protocol.comment("Video recording already stopped")

        # Clear active process if it was the one we stopped
        self._active_video_process = None

class SmartPipette:
    """
    Wrapper for automatic volume tracking
    """

    def __init__(self, pipette, protocol):
        self.pipette = pipette
        self.protocol = protocol
        if not hasattr(protocol, 'define_liquid'):
            raise RuntimeError("This class requires API with liquid tracking support")

    def is_conical_tube(self, well, use: bool = False) -> bool:
        """Check if the well is from a conical tube labware or manually set as true"""
        return 'conical' in well.parent.load_name.lower() or use

    def get_well_volume(self, well) -> Optional[float]:
        """Get current volume in well using pure API method"""
        try:
            return well.current_liquid_volume()
        except Exception as e:
            self.protocol.comment(f"ERROR reading volume from {well.well_name}: {e}")
            return None

    def get_well_height(self, well) -> Optional[float]:
        """Get current liquid height using pure API method (if available)"""
        try:
            if hasattr(well, 'current_liquid_height'):
                return well.current_liquid_height()
            else:
                self.protocol.comment("Liquid height method not available in this API version")
                return None
        except Exception as e:
            self.protocol.comment(f"ERROR reading height from {well.well_name}: {e}")
            return None

    def get_conical_tube_aspiration_height(self, well) -> float:
        """
        Calculate safe aspiration height for conical tubes using proven method
        Uses API liquid tracking to get current volume
        """
        # Get current volume from API
        try:
            current_volume = well.current_liquid_volume()
            if current_volume is None:
                raise ValueError("API returned None for liquid volume")
        except Exception as e:
            self.protocol.comment(f"ERROR: Could not get liquid volume from API: {e}")
            return 10.0  # Safe fallback height

        max_volume = well.max_volume
        tube_depth = well.depth - 10  # Account for threads
        min_safe_height = 3  # mm minimum to prevent tip damage
        meniscus_offset = 10  # mm below liquid surface

        # Calculate liquid height based on current volume
        liquid_height = (current_volume / max_volume) * tube_depth
        aspiration_height = max(liquid_height - meniscus_offset, min_safe_height)

        self.protocol.comment(
            f"Conical calculation: {current_volume:.0f}µL remaining = {aspiration_height:.1f}mm height")
        return aspiration_height

    def get_aspiration_location(self, well, use: bool = False) -> float:
        """
        Get intelligent aspiration location using API volume data and proven height calculation
        """
        if not self.is_conical_tube(well, use=use):
            return well

        try:
            current_volume = well.current_liquid_volume()
            if current_volume is None or current_volume < well.max_volume * 0.2:
                # Less than 20% remaining - use standard aspiration
                self.protocol.comment("Low volume detected - using standard aspiration")
                return well

            # Use conical tube calculation
            safe_height = self.get_conical_tube_aspiration_height(well)
            return well.bottom(safe_height)

        except Exception as e:
            self.protocol.comment(f"ERROR getting volume from API: {e}")
            return well  # Fallback to standard aspiration

    def liquid_transfer(self, volume: float, source, destination,
                 asp_rate: float = 0.5, disp_rate: float = 1.0,
                 blow_out: bool = True, touch_tip: bool = False,
                 mix_before: float = 0.0, mix_after: float = 0.0,
                 mix_reps: int = 3, new_tip: bool = True, drop_tip: bool = True, use:bool = False) -> bool:
        """
        Transfer liquid using pure API liquid tracking for volume management

        Returns:
            bool: True if transfer was successful, False if insufficient volume
        """
        # Check volume using API methods only
        try:
            current_volume = source.current_liquid_volume()
            if current_volume is None:
                self.protocol.comment("WARNING: API returned None for source volume")
                return False

            if current_volume < volume:
                self.protocol.comment(f"WARNING: Insufficient volume. "
                                      f"Requested: {volume}µL, Available: {current_volume:.0f}µL")
                return False

        except Exception as e:
            self.protocol.comment(f"ERROR: Could not check source volume: {e}")
            return False

        if new_tip:
            self.pipette.pick_up_tip()

        # Get aspiration location using API data + proven calculation
        aspiration_location = self.get_aspiration_location(source,use)

        # Mix before if requested
        if mix_before > 0:
            # Use current volume to limit mixing
            try:
                safe_mix_volume = min(mix_before, current_volume * 0.8)
                self.pipette.mix(mix_reps, safe_mix_volume, aspiration_location)
            except:
                self.protocol.comment("Skipping mix_before due to API error")

        # Aspirate
        self.pipette.aspirate(volume, aspiration_location, rate=asp_rate)

        # Dispense
        self.pipette.dispense(volume, destination.center(), rate=disp_rate)

        # Mix after if requested
        if mix_after > 0:
            self.pipette.mix(mix_reps, mix_after, destination)

        if blow_out:
            self.pipette.blow_out()

        if touch_tip:
            self.pipette.touch_tip()

        if drop_tip:
            self.pipette.drop_tip()
        return True
