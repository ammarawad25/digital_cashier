#!/usr/bin/env node

/**
 * Voice Test File Generator
 * Generates synthetic audio files for testing
 */

import fs from 'fs';
import path from 'path';

/**
 * Generate a simple WAV file with sine wave tone
 * This is a minimal WAV file generator for testing purposes
 */
function generateWaveFile(frequency, duration, filename) {
  const sampleRate = 16000;
  const numSamples = sampleRate * duration;
  const channelData = new Float32Array(numSamples);

  // Generate sine wave
  for (let i = 0; i < numSamples; i++) {
    channelData[i] = Math.sin((2 * Math.PI * frequency * i) / sampleRate) * 0.3;
  }

  // Convert to WAV format
  const wavBuffer = encodeWAV(channelData, sampleRate);
  
  // Create test-voice-files directory if it doesn't exist
  const dir = path.dirname(filename);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  fs.writeFileSync(filename, wavBuffer);
  console.log(`✓ Generated ${filename}`);
}

function encodeWAV(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  // WAV header
  function writeString(offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  // "RIFF" chunk descriptor
  writeString(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, 'WAVE');

  // "fmt " sub-chunk
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // Mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true); // 16-bit

  // "data" sub-chunk
  writeString(36, 'data');
  view.setUint32(40, samples.length * 2, true);

  // Write audio samples
  let offset = 44;
  for (let i = 0; i < samples.length; i++) {
    const sample = Math.max(-1, Math.min(1, samples[i])); // Clamp
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
    offset += 2;
  }

  return buffer;
}

// Create test voice directory
const testVoiceDir = './public/test-voices';

console.log('🎙️ Generating test voice files...\n');

// Generate test audio files with different tones
// These represent different speech frequencies
generateWaveFile(200, 2, `${testVoiceDir}/greeting.wav`);
generateWaveFile(250, 2, `${testVoiceDir}/order.wav`);
generateWaveFile(150, 2, `${testVoiceDir}/complaint.wav`);
generateWaveFile(300, 2, `${testVoiceDir}/confirmation.wav`);

console.log('\n✅ Test voice files generated successfully!');
console.log(`📁 Files location: ${testVoiceDir}`);
console.log('\nNote: These are synthetic audio files for testing purposes.');
console.log('For production, use real audio recordings.');
