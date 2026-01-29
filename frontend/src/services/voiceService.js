/**
 * VoiceRecorder Service
 * Handles recording audio from the user's microphone
 */

export class VoiceRecorder {
  constructor() {
    this.mediaRecorder = null;
    this.audioStream = null;
    this.chunks = [];
    this.isRecording = false;
  }

  /**
   * Start recording audio from microphone
   * @returns {Promise<void>}
   */
  async start() {
    try {
      this.audioStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      this.mediaRecorder = new MediaRecorder(this.audioStream);
      this.chunks = [];

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.chunks.push(event.data);
        }
      };

      this.mediaRecorder.start();
      this.isRecording = true;
    } catch (error) {
      throw new Error(`Failed to start recording: ${error.message}`);
    }
  }

  /**
   * Stop recording and return audio blob
   * @returns {Promise<Blob>} Audio blob
   */
  async stop() {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        reject(new Error('Recording not started'));
        return;
      }

      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.chunks, { type: 'audio/webm' });
        this.cleanup();
        this.isRecording = false;
        resolve(blob);
      };

      this.mediaRecorder.stop();
    });
  }

  /**
   * Cancel recording and cleanup
   */
  cancel() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.isRecording = false;
    }
    this.cleanup();
  }

  /**
   * Cleanup audio resources
   */
  cleanup() {
    if (this.audioStream) {
      this.audioStream.getTracks().forEach((track) => track.stop());
    }
    this.chunks = [];
  }

  /**
   * Get recording status
   * @returns {boolean}
   */
  getIsRecording() {
    return this.isRecording;
  }
}

/**
 * VoicePlayer Service
 * Handles playing audio responses
 */
export class VoicePlayer {
  constructor() {
    this.audio = null;
    this.isPlaying = false;
  }

  /**
   * Play audio from blob
   * @param {Blob} audioBlob
   * @returns {Promise<void>}
   */
  play(audioBlob) {
    return new Promise((resolve, reject) => {
      try {
        const url = URL.createObjectURL(audioBlob);
        this.audio = new Audio(url);
        this.isPlaying = true;

        this.audio.onended = () => {
          this.isPlaying = false;
          URL.revokeObjectURL(url);
          resolve();
        };

        this.audio.onerror = (error) => {
          this.isPlaying = false;
          URL.revokeObjectURL(url);
          reject(error);
        };

        this.audio.play().catch(reject);
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Play audio from URL
   * @param {string} url
   * @returns {Promise<void>}
   */
  playUrl(url) {
    return new Promise((resolve, reject) => {
      try {
        this.audio = new Audio(url);
        this.isPlaying = true;

        this.audio.onended = () => {
          this.isPlaying = false;
          resolve();
        };

        this.audio.onerror = (error) => {
          this.isPlaying = false;
          reject(error);
        };

        this.audio.play().catch(reject);
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Stop playing audio
   */
  stop() {
    if (this.audio) {
      this.audio.pause();
      this.audio.currentTime = 0;
      this.isPlaying = false;
    }
  }

  /**
   * Get playing status
   * @returns {boolean}
   */
  getIsPlaying() {
    return this.isPlaying;
  }
}
