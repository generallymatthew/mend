// tests/useSymmetricalVideoEngine.test.ts
import { renderHook, act } from '@testing-library/react';
import { useSymmetricalVideoEngine } from '../src/hooks/useSymmetricalVideoEngine';

describe('Symmetrical Video Parity Engine', () => {
  let mockStopTrack: jest.Mock;
  let mockMediaStream: MediaStream;

  beforeEach(() => {
    jest.useFakeTimers();
    mockStopTrack = jest.fn();

    // Mock native WebRTC MediaStream
    mockMediaStream = {
      getVideoTracks: jest.fn().mockReturnValue([
        { stop: mockStopTrack, enabled: true },
      ]),
    } as unknown as MediaStream;
  });

  afterEach(() => {
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  it('initializes in AVATAR_AUDIO_ONLY if only one user consented during intake', () => {
    const { result } = renderHook(() =>
      useSymmetricalVideoEngine(true, false, 'user_a')
    );

    expect(result.current.roomMode).toBe('AVATAR_AUDIO_ONLY');
  });

  it('initializes in VIDEO_ACTIVE only if BOTH users consented during intake', () => {
    const { result } = renderHook(() =>
      useSymmetricalVideoEngine(true, true, 'user_a')
    );

    expect(result.current.roomMode).toBe('VIDEO_ACTIVE');
  });

  it('auto-shuts local hardware and falls back to avatar when local user turns off camera', () => {
    const { result } = renderHook(() =>
      useSymmetricalVideoEngine(true, true, 'user_a')
    );

    act(() => {
      // Simulate local user click
      result.current.handleCameraDrop(true);
    });

    expect(result.current.roomMode).toBe('AVATAR_AUDIO_ONLY');
    expect(result.current.toastMessage).toBe('Session switched to Voice & Avatar mode.');
  });

  it('symmetrically tears down camera and displays neutral toast when remote peer drops video', () => {
    const { result } = renderHook(() =>
      useSymmetricalVideoEngine(true, true, 'user_a')
    );

    act(() => {
      // Triggered by incoming WebSocket 'PEER_CAMERA_DISABLED'
      result.current.handleCameraDrop(false);
    });

    // Verifies immediate remote parity enforcement
    expect(result.current.roomMode).toBe('AVATAR_AUDIO_ONLY');
    expect(result.current.toastMessage).toBe('Session switched to Voice & Avatar mode.');

    // Verifies toast automatically dismisses after 4 seconds
    act(() => {
      jest.advanceTimersByTime(4000);
    });
    expect(result.current.toastMessage).toBeNull();
  });
});