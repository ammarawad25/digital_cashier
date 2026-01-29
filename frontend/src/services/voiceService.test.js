import { describe, it, expect, beforeEach, vi } from 'vitest';
import { VoiceRecorder, VoicePlayer } from '../services/voiceService';

/**
 * Test Suite: VoiceRecorder Service
 */
describe('VoiceRecorder', () => {
  let recorder;

  beforeEach(() => {
    recorder = new VoiceRecorder();
    vi.clearAllMocks();
  });

  it('should initialize with correct properties', () => {
    expect(recorder.mediaRecorder).toBeNull();
    expect(recorder.audioStream).toBeNull();
    expect(recorder.chunks).toEqual([]);
    expect(recorder.isRecording).toBeFalsy();
  });

  it('should start recording when getUserMedia is available', async () => {
    const mockStream = { getTracks: () => [] };
    global.navigator.mediaDevices.getUserMedia.mockResolvedValueOnce(mockStream);

    await recorder.start();

    expect(recorder.isRecording).toBeTruthy();
    expect(recorder.mediaRecorder).toBeTruthy();
  });

  it('should throw error when getUserMedia fails', async () => {
    global.navigator.mediaDevices.getUserMedia.mockRejectedValueOnce(new Error('Permission denied'));

    await expect(recorder.start()).rejects.toThrow('Permission denied');
  });

  it('should stop recording and return audio blob', async () => {
    const mockTrack = { stop: vi.fn() };
    const mockStream = {
      getTracks: () => [mockTrack],
    };
    global.navigator.mediaDevices.getUserMedia.mockResolvedValueOnce(mockStream);

    await recorder.start();

    // Simulate data arrival
    const mockEvent = { data: new Blob(['audio data']) };
    recorder.mediaRecorder.ondataavailable(mockEvent);

    // Immediately call onstop since we're mocking
    const stopPromise = recorder.stop();
    recorder.mediaRecorder.onstop();

    const blob = await stopPromise;

    expect(blob).toBeInstanceOf(Blob);
    expect(recorder.isRecording).toBeFalsy();
  });

  it('should cancel recording properly', async () => {
    const mockStream = {
      getTracks: () => [{ stop: vi.fn() }],
    };
    global.navigator.mediaDevices.getUserMedia.mockResolvedValueOnce(mockStream);

    await recorder.start();
    expect(recorder.isRecording).toBeTruthy();

    recorder.cancel();

    expect(recorder.isRecording).toBeFalsy();
    expect(recorder.chunks).toEqual([]);
  });

  it('should clean up resources on stop', async () => {
    const mockTrack = { stop: vi.fn() };
    const mockStream = {
      getTracks: () => [mockTrack],
    };
    global.navigator.mediaDevices.getUserMedia.mockResolvedValueOnce(mockStream);

    await recorder.start();

    const stopPromise = recorder.stop();
    recorder.mediaRecorder.onstop();

    await stopPromise;

    expect(mockTrack.stop).toHaveBeenCalled();
  });

  it('should collect audio chunks', async () => {
    const mockStream = {
      getTracks: () => [],
    };
    global.navigator.mediaDevices.getUserMedia.mockResolvedValueOnce(mockStream);

    await recorder.start();

    // Simulate multiple data chunks
    const chunk1 = new Blob(['chunk1']);
    const chunk2 = new Blob(['chunk2']);

    recorder.mediaRecorder.ondataavailable({ data: chunk1 });
    recorder.mediaRecorder.ondataavailable({ data: chunk2 });

    expect(recorder.chunks.length).toBe(2);
  });

  it('should request appropriate audio constraints', async () => {
    const mockStream = {
      getTracks: () => [],
    };
    global.navigator.mediaDevices.getUserMedia.mockResolvedValueOnce(mockStream);

    await recorder.start();

    expect(global.navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
      audio: expect.objectContaining({
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      }),
    });
  });

  it('should get recording status', async () => {
    expect(recorder.getIsRecording()).toBeFalsy();

    const mockStream = {
      getTracks: () => [],
    };
    global.navigator.mediaDevices.getUserMedia.mockResolvedValueOnce(mockStream);

    await recorder.start();
    expect(recorder.getIsRecording()).toBeTruthy();
  });
});

/**
 * Test Suite: VoicePlayer Service
 */
describe('VoicePlayer', () => {
  let player;

  beforeEach(() => {
    player = new VoicePlayer();
    vi.clearAllMocks();
  });

  it('should initialize with correct properties', () => {
    expect(player.audio).toBeNull();
    expect(player.isPlaying).toBeFalsy();
  });

  it('should play audio blob', async () => {
    const blob = new Blob(['audio data']);
    const mockAudio = {
      play: vi.fn().mockResolvedValue(undefined),
      pause: vi.fn(),
      onended: null,
      onerror: null,
    };

    global.Audio = vi.fn(() => mockAudio);

    const playPromise = player.play(blob);

    // Trigger onended
    mockAudio.onended();

    await playPromise;

    expect(mockAudio.play).toHaveBeenCalled();
    expect(player.isPlaying).toBeFalsy();
  });

  it('should handle play error', async () => {
    const blob = new Blob(['audio data']);
    const error = new Error('Play failed');
    const mockAudio = {
      play: vi.fn().mockRejectedValue(error),
      pause: vi.fn(),
      onended: null,
      onerror: null,
    };

    global.Audio = vi.fn(() => mockAudio);

    await expect(player.play(blob)).rejects.toThrow('Play failed');
  });

  it('should play audio from URL', async () => {
    const url = 'https://example.com/audio.mp3';
    const mockAudio = {
      play: vi.fn().mockResolvedValue(undefined),
      pause: vi.fn(),
      onended: null,
      onerror: null,
    };

    global.Audio = vi.fn(() => mockAudio);

    const playPromise = player.playUrl(url);

    mockAudio.onended();

    await playPromise;

    expect(global.Audio).toHaveBeenCalledWith(url);
  });

  it('should stop playing audio', () => {
    const mockAudio = {
      play: vi.fn(),
      pause: vi.fn(),
      currentTime: 0,
      onended: null,
      onerror: null,
    };

    player.audio = mockAudio;
    player.isPlaying = true;

    player.stop();

    expect(mockAudio.pause).toHaveBeenCalled();
    expect(player.isPlaying).toBeFalsy();
  });

  it('should get playing status', () => {
    expect(player.getIsPlaying()).toBeFalsy();

    player.isPlaying = true;
    expect(player.getIsPlaying()).toBeTruthy();
  });

  it('should handle audio end event', async () => {
    const blob = new Blob(['audio data']);
    const mockAudio = {
      play: vi.fn().mockResolvedValue(undefined),
      pause: vi.fn(),
      onended: null,
      onerror: null,
    };

    global.Audio = vi.fn(() => mockAudio);

    const playPromise = player.play(blob);

    expect(player.isPlaying).toBeTruthy();

    // Simulate audio ended
    mockAudio.onended();

    await playPromise;

    expect(player.isPlaying).toBeFalsy();
  });

  it('should handle audio error event', async () => {
    const blob = new Blob(['audio data']);
    const mockError = new Error('Audio error');
    const mockAudio = {
      play: vi.fn().mockResolvedValue(undefined),
      pause: vi.fn(),
      onended: null,
      onerror: null,
    };

    global.Audio = vi.fn(() => mockAudio);

    const playPromise = player.play(blob);

    expect(player.isPlaying).toBeTruthy();

    // Simulate audio error
    mockAudio.onerror(mockError);

    await expect(playPromise).rejects.toThrow('Audio error');
    expect(player.isPlaying).toBeFalsy();
  });
});
