import React, {
  memo,
  RefObject,
  useEffect,
  useRef,
  useState,
  useCallback,
  useMemo,
} from "react";
import Draggable from "react-draggable";
import { useLiveAPIContext } from "../../contexts/LiveAPIContext";
import { useMediaCapture } from "../../hooks/useMediaCapture";
import { AudioRecorder } from "../../lib/audio-recorder";
import SettingsDialog from "../settings-dialog/SettingsDialog";
import cn from "classnames";
import MediaMixerDisplay from "../media-mixer-display/MediaMixerDisplay";
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  Monitor,
  MonitorOff,
  PlayCircle,
  StopCircle,
  Settings,
  PenTool,
  Image as ImageIcon,
  MoreHorizontal,
  ChevronDown,
  ChevronUp,
  Home,
  X,
  Eye,
} from "lucide-react";

export type FloatingControlPanelProps = {
  socket: WebSocket | null;
  videoRef: RefObject<HTMLVideoElement>;
  renderCanvasRef: RefObject<HTMLCanvasElement>;
  supportsVideo: boolean;
  onVideoStreamChange?: (stream: MediaStream | null) => void;
  onMixerStreamChange?: (stream: MediaStream | null) => void;
  enableEditingSettings?: boolean;
  onPaintClick: () => void;
  isPaintActive: boolean;
  videoSocket: WebSocket | null;
};

function FloatingControlPanel({
  socket,
  videoRef,
  renderCanvasRef,
  supportsVideo,
  enableEditingSettings,
  onPaintClick,
  isPaintActive,
  videoSocket,
}: FloatingControlPanelProps) {
  const { client, connected, connect, disconnect } = useLiveAPIContext();
  const { cameraEnabled, screenEnabled, toggleCamera, toggleScreen } =
    useMediaCapture({ socket });
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedAudioDevice, setSelectedAudioDevice] = useState<string>("");
  const [audioRecorder] = useState(() => new AudioRecorder());
  const [muted, setMuted] = useState(false);
  const [activeVideoStream] = useState<MediaStream | null>(null);
  const [sharedMediaOpen, setSharedMediaOpen] = useState(false);
  const [isAnimatingOut, setIsAnimatingOut] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [sessionTime, setSessionTime] = useState(0);
  const [popoverPosition, setPopoverPosition] = useState<"left" | "right">(
    "right",
  );
  const [isDragging, setIsDragging] = useState(false);
  const [mediaMixerStatus, setMediaMixerStatus] = useState<{
    isConnected: boolean;
    error: string | null;
  }>({ isConnected: false, error: null });

  // Timer for session duration
  useEffect(() => {
    if (!connected) {
      setSessionTime(0);
      return;
    }

    const interval = setInterval(() => {
      setSessionTime((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [connected]);

  const formatTime = useCallback((seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }, []);

  useEffect(() => {
    navigator.mediaDevices.enumerateDevices().then((devices) => {
      const audioInputs = devices.filter(
        (device) => device.kind === "audioinput",
      );
      setAudioDevices(audioInputs);
      if (audioInputs.length > 0) {
        setSelectedAudioDevice(audioInputs[0].deviceId);
      }
    });
  }, []);

  useEffect(() => {
    const onData = (base64: string) => {
      client.sendRealtimeInput([
        {
          mimeType: "audio/pcm;rate=16000",
          data: base64,
        },
      ]);
    };
    if (connected && !muted && audioRecorder) {
      audioRecorder.on("data", onData).start(selectedAudioDevice);
    } else {
      audioRecorder.stop();
    }
    return () => {
      audioRecorder.off("data", onData);
    };
  }, [connected, client, muted, audioRecorder, selectedAudioDevice]);

  // Video handling (similar to ControlTray)
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.srcObject = activeVideoStream;
    }

    let timeoutId = -1;

    function sendVideoFrame() {
      const canvas = renderCanvasRef.current;

      if (!canvas) {
        return;
      }

      if (canvas.width + canvas.height > 0) {
        const base64 = canvas.toDataURL("image/jpeg", 1.0);
        const data = base64.slice(base64.indexOf(",") + 1, Infinity);
        client.sendRealtimeInput([{ mimeType: "image/jpeg", data }]);
      }
      if (connected) {
        timeoutId = window.setTimeout(sendVideoFrame, 1000 / 0.5);
      }
    }
    if (connected) {
      requestAnimationFrame(sendVideoFrame);
    }
    return () => {
      clearTimeout(timeoutId);
    };
  }, [connected, activeVideoStream, client, videoRef, renderCanvasRef]);

  // // Video handling - capture full MediaMixer canvas and send to tutor as JPEG
  // useEffect(() => {
  //   if (videoRef.current) {
  //     videoRef.current.srcObject = activeVideoStream;
  //   }
  //
  //   // Only send frames if camera or screen is enabled
  //   if (!connected || (!cameraEnabled && !screenEnabled)) {
  //     return;
  //   }
  //
  //   let rafId: number;
  //   let lastFrameTime = 0;
  //   const frameInterval = 1000 / 0.5; // 0.5 FPS (every 2 seconds)
  //
  //   function sendVideoFrame(timestamp: number) {
  //     const canvas = renderCanvasRef.current;
  //
  //     if (!canvas) {
  //       rafId = requestAnimationFrame(sendVideoFrame);
  //       return;
  //     }
  //
  //     // Throttle to desired FPS
  //     if (timestamp - lastFrameTime < frameInterval) {
  //       rafId = requestAnimationFrame(sendVideoFrame);
  //       return;
  //     }
  //
  //     lastFrameTime = timestamp;
  //
  //     if (canvas.width + canvas.height > 0) {
  //       // Capture the exact MediaMixer output at full resolution for the tutor
  //       const base64 = canvas.toDataURL("image/jpeg", 1.0);
  //       const data = base64.slice(base64.indexOf(",") + 1, Infinity);
  //       client.sendRealtimeInput([{ mimeType: "image/jpeg", data }]);
  //     }
  //
  //     if (connected) {
  //       rafId = requestAnimationFrame(sendVideoFrame);
  //     }
  //   }
  //
  //   if (connected) {
  //     rafId = requestAnimationFrame(sendVideoFrame);
  //   }
  //
  //   return () => {
  //     if (rafId) {
  //       cancelAnimationFrame(rafId);
  //     }
  //   };
  // }, [connected, activeVideoStream, cameraEnabled, screenEnabled, client, videoRef, renderCanvasRef]);

  const handleConnect = useCallback(async () => {
    if (connected) {
      disconnect();
    } else {
      await connect();
    }
  }, [connected, connect, disconnect]);

  const [verticalAlign, setVerticalAlign] = useState<"top" | "bottom">("top");

  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [hasInitialized, setHasInitialized] = useState(false);

  // Initialize position on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      setPosition({ x: window.innerWidth - 380, y: 96 });
      setHasInitialized(true);
    }
  }, []);

  // Memoize popover position calculation to avoid expensive DOM queries
  const calculatePopoverPosition = useCallback(() => {
    if (!panelRef.current) return { side: "right" as const, vertical: "top" as const };

    const panelRect = panelRef.current.getBoundingClientRect();
    const popoverWidth = 360;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const spaceOnRight = viewportWidth - panelRect.right;
    const spaceOnLeft = panelRect.left;
    const preferredMargin = 16;

    let side: "left" | "right" = "right";
    if (spaceOnRight >= popoverWidth + preferredMargin) {
      side = "right";
    } else if (spaceOnLeft >= popoverWidth + preferredMargin) {
      side = "left";
    }

    // Calculate vertical alignment based on panel's center relative to screen center
    const panelCenterY = panelRect.top + panelRect.height / 2;
    const screenCenterY = viewportHeight / 2;
    const vertical: "top" | "bottom" = panelCenterY > screenCenterY ? "bottom" : "top";

    return { side, vertical };
  }, []);

  const updatePopoverPosition = useCallback(() => {
    const { side, vertical } = calculatePopoverPosition();
    setPopoverPosition(side);
    setVerticalAlign(vertical);
  }, [calculatePopoverPosition]);

  const toggleSharedMedia = useCallback(() => {
    if (!sharedMediaOpen) {
      // Opening
      updatePopoverPosition();
      setSharedMediaOpen(true);
      setIsAnimatingOut(false);
    } else {
      // Closing
      setIsAnimatingOut(true);
      setTimeout(() => {
        setSharedMediaOpen(false);
        setIsAnimatingOut(false);
      }, 200); // Match CSS animation duration
    }
  }, [sharedMediaOpen, updatePopoverPosition]);

  const handleCollapse = useCallback(() => {
    setIsCollapsed(!isCollapsed);
  }, [isCollapsed]);

  // Adjust position when collapsing/expanding to prevent overflow
  useEffect(() => {
    if (!hasInitialized || !panelRef.current) return;

    // Use setTimeout to allow layout to update (height change)
    const timer = setTimeout(() => {
      if (!panelRef.current) return;
      const rect = panelRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const viewportWidth = window.innerWidth;
      const margin = 16;

      let newY = position.y;
      let newX = position.x;

      // Check bottom overflow
      if (rect.bottom > viewportHeight - margin) {
        newY = viewportHeight - rect.height - margin;
      }
      // Check top overflow
      if (newY < margin) {
        newY = margin;
      }

      // Check right overflow
      if (rect.right > viewportWidth - margin) {
        newX = viewportWidth - rect.width - margin;
      }
      // Check left overflow
      if (newX < margin) {
        newX = margin;
      }

      if (newY !== position.y || newX !== position.x) {
        setPosition({ x: newX, y: newY });
      }
    }, 50); // Small delay for transition

    return () => clearTimeout(timer);
  }, [isCollapsed, hasInitialized]); // Removed 'position' dependency to avoid loops, relying on rect reading

  const handleMute = useCallback(() => {
    setMuted(!muted);
  }, [muted]);

  // Memoize drag handlers to avoid re-creating functions
  const handleDragStart = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handleDrag = useCallback((e: any, data: { x: number; y: number }) => {
    if (!panelRef.current) return;

    const rect = panelRef.current.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    // Clamp values to keep panel within viewport
    let newX = data.x;
    let newY = data.y;

    // Horizontal boundaries
    if (newX < 0) newX = 0;
    else if (newX + rect.width > viewportWidth) newX = viewportWidth - rect.width;

    // Vertical boundaries
    if (newY < 0) newY = 0;
    else if (newY + rect.height > viewportHeight) newY = viewportHeight - rect.height;

    setPosition({ x: newX, y: newY });
  }, []);

  const handleDragStop = useCallback(() => {
    setIsDragging(false);
    // Recalculate position after drag ends
    if (sharedMediaOpen) {
      updatePopoverPosition();
    }
  }, [sharedMediaOpen, updatePopoverPosition]);

  // Memoize panel classes to avoid recalculating on every render
  const panelClasses = useMemo(
    () =>
      cn(
        "fixed z-[1000] bg-white border-[3px] md:border-[4px] border-black rounded-xl md:rounded-2xl",
        // GPU acceleration hints
        "will-change-transform transform-gpu",
        // Only apply transitions when NOT dragging to prevent layout thrashing
        !isDragging &&
        "transition-all duration-200 ease-out",
        isCollapsed
          ? "w-[60px] md:w-[70px] py-3 md:py-4 px-1.5 md:px-2 shadow-[4px_4px_0_0_rgba(0,0,0,1)] md:shadow-[6px_6px_0_0_rgba(0,0,0,1)]"
          : "w-[280px] md:w-[320px] p-4 md:p-5 shadow-[6px_6px_0_0_rgba(0,0,0,1)] md:shadow-[8px_8px_0_0_rgba(0,0,0,1)]",
        // Ensure origin is top-left for controlled positioning
        "top-0 left-0",
        // Hover effect
        !isDragging &&
        "hover:shadow-[8px_8px_0_0_rgba(0,0,0,1)] md:hover:shadow-[10px_10px_0_0_rgba(0,0,0,1)]",
      ),
    [isCollapsed, isDragging],
  );

  if (!hasInitialized) return null; // Prevent hydration mismatch

  return (
    <Draggable
      handle=".drag-handle"
      nodeRef={panelRef}
      position={position}
      onStart={handleDragStart}
      onDrag={handleDrag}
      onStop={handleDragStop}
    >
      <div
        ref={panelRef}
        className={panelClasses}
        style={{
          // Use transform3d for GPU acceleration
          transform: "translate3d(0, 0, 0)",
        }}
      >
        {/* Drag Handle & Header */}
        <div
          className={cn(
            "drag-handle cursor-grab active:cursor-grabbing flex items-center mb-5",
            !isDragging && "transition-all duration-200 ease-out",
            isCollapsed ? "justify-center mb-3" : "justify-between",
          )}
        >
          {!isCollapsed && (
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 border-[3px] border-black bg-[#FFE500]">
                <span className="material-symbols-outlined text-xl text-black font-black">
                  smart_toy
                </span>
              </div>
              <div>
                <div className="font-black text-sm text-black leading-none mb-1 uppercase">
                  AI TUTOR
                </div>
                <div className="text-[9px] text-black font-bold uppercase tracking-wider bg-[#00F0FF] px-2 py-0.5 border-2 border-black inline-block">
                  CONTROL CENTER
                </div>
              </div>
            </div>
          )}
          <button
            onClick={handleCollapse}
            className="w-8 h-8 flex items-center justify-center border-[3px] border-black bg-white hover:bg-[#ADFF2F] text-black hover:translate-x-0.5 hover:translate-y-0.5 transition-all duration-100"
          >
            {isCollapsed ? (
              <ChevronDown className="w-5 h-5 font-black" />
            ) : (
              <ChevronUp className="w-5 h-5 font-black" />
            )}
          </button>
        </div>

        {isCollapsed ? (
          // COLLAPSED VIEW
          <div className="flex flex-col items-center gap-3">
            <button
              onClick={handleCollapse}
              className="w-12 h-12 border-[3px] border-black bg-white hover:bg-[#FFE500] flex items-center justify-center text-black transition-all hover:translate-x-1 hover:translate-y-1 duration-100 shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none"
              title="Expand"
            >
              <Home className="w-6 h-6 font-bold" />
            </button>

            {/* Start/End Session Button */}
            <button
              onClick={handleConnect}
              className={cn(
                "w-14 h-14 border-[4px] border-black flex items-center justify-center transition-all transform active:translate-x-2 active:translate-y-2 relative group font-black",
                connected
                  ? "bg-[#FF006E] hover:bg-[#FF006E] text-white shadow-[6px_6px_0_0_rgba(0,0,0,1)] hover:shadow-[8px_8px_0_0_rgba(0,0,0,1)]"
                  : "bg-[#00F0FF] hover:bg-[#00F0FF] text-black shadow-[6px_6px_0_0_rgba(0,0,0,1)] hover:shadow-[8px_8px_0_0_rgba(0,0,0,1)]",
              )}
              title={connected ? "End Session" : "Start Session"}
            >
              {connected ? (
                <div className="w-5 h-5 bg-white border-2 border-black" />
              ) : (
                <PlayCircle className="w-8 h-8" />
              )}
              {connected && (
                <span className="absolute -top-2 -right-2 w-4 h-4 bg-[#ADFF2F] border-3 border-black animate-pulse" />
              )}
            </button>

            <div className="w-10 h-[3px] bg-black my-1" />

            <button
              onClick={handleMute}
              className={cn(
                "w-12 h-12 border-[3px] border-black flex items-center justify-center transition-all shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-1 hover:translate-y-1 duration-100",
                muted
                  ? "bg-[#FF006E] text-white"
                  : "bg-white text-black hover:bg-[#ADFF2F]",
              )}
              title={muted ? "Unmute" : "Mute"}
            >
              {muted ? (
                <MicOff className="w-5 h-5 font-bold" />
              ) : (
                <Mic className="w-5 h-5 font-bold" />
              )}
            </button>

            {supportsVideo && (
              <button
                onClick={() => toggleCamera(!cameraEnabled)}
                className={cn(
                  "w-12 h-12 border-[3px] border-black flex items-center justify-center transition-all shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-1 hover:translate-y-1 duration-100",
                  cameraEnabled
                    ? "bg-[#00F0FF] text-black"
                    : "bg-white text-black hover:bg-[#FFE500]",
                )}
                title="Toggle Camera"
              >
                {cameraEnabled ? (
                  <Video className="w-5 h-5 font-bold" />
                ) : (
                  <VideoOff className="w-5 h-5 font-bold" />
                )}
              </button>
            )}

            {supportsVideo && (
              <button
                onClick={() => toggleScreen(!screenEnabled)}
                className={cn(
                  "w-12 h-12 border-[3px] border-black flex items-center justify-center transition-all shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-1 hover:translate-y-1 duration-100",
                  screenEnabled
                    ? "bg-[#ADFF2F] text-black"
                    : "bg-white text-black hover:bg-[#FFE500]",
                )}
                title="Share Screen"
              >
                {screenEnabled ? (
                  <Monitor className="w-5 h-5 font-bold" />
                ) : (
                  <MonitorOff className="w-5 h-5 font-bold" />
                )}
              </button>
            )}

            <div className="w-10 h-[3px] bg-black my-1" />

            {enableEditingSettings && (
              <SettingsDialog
                className="!h-auto !block"
                trigger={
                  <button className="w-12 h-12 border-[3px] border-black bg-white hover:bg-[#FF006E] flex items-center justify-center text-black hover:text-white transition-all shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-1 hover:translate-y-1 duration-100">
                    <Settings className="w-5 h-5 font-bold" />
                  </button>
                }
              />
            )}

            <button
              onClick={onPaintClick}
              className={cn(
                "w-12 h-12 border-[3px] border-black flex items-center justify-center transition-all shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-1 hover:translate-y-1 duration-100",
                isPaintActive
                  ? "bg-[#FFE500] text-black"
                  : "bg-white text-black hover:bg-[#FFE500]",
              )}
              title="Canvas"
            >
              <PenTool className="w-5 h-5 font-bold" />
            </button>

            <button
              onClick={toggleSharedMedia}
              className={cn(
                "w-12 h-12 border-[3px] border-black flex items-center justify-center transition-all shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-1 hover:translate-y-1 duration-100",
                sharedMediaOpen
                  ? "bg-[#00F0FF] text-black"
                  : "bg-white text-black hover:bg-[#00F0FF]",
              )}
              title="View"
            >
              <Eye className="w-5 h-5 font-bold" />
            </button>

            <div
              className={cn(
                "w-14 h-12 flex items-center justify-center text-[11px] font-mono font-black mt-2 transition-colors border-[3px] border-black",
                connected
                  ? "bg-[#ADFF2F] text-black"
                  : "bg-white text-black",
              )}
            >
              {connected ? formatTime(sessionTime) : "--:--"}
            </div>
          </div>
        ) : (
          // EXPANDED VIEW
          <div className="flex flex-col gap-4">
            {/* Audio Control */}
            <div
              onClick={handleMute}
              className={cn(
                "flex items-center justify-between p-4 border-[4px] border-black transition-all duration-100 group cursor-pointer shadow-[6px_6px_0_0_rgba(0,0,0,1)] hover:shadow-[8px_8px_0_0_rgba(0,0,0,1)]",
                !muted
                  ? "bg-white"
                  : "bg-[#FF006E]",
              )}
            >
              <div className="flex items-center gap-3 overflow-hidden">
                <div
                  className={cn(
                    "flex items-center justify-center w-10 h-10 border-[3px] border-black transition-colors",
                    !muted
                      ? "bg-[#00F0FF] text-black"
                      : "bg-white text-black",
                  )}
                >
                  {muted ? (
                    <MicOff className="w-5 h-5 font-bold" />
                  ) : (
                    <Mic className="w-5 h-5 font-bold" />
                  )}
                </div>
                <div className="flex flex-col">
                  <span className={cn("text-[10px] font-bold uppercase tracking-wide", muted ? "text-white" : "text-black")}>
                    Microphone
                  </span>
                  <select
                    className={cn("bg-transparent border-none text-sm outline-none cursor-pointer w-[140px] truncate p-0 font-black", muted ? "text-white" : "text-black")}
                    value={selectedAudioDevice}
                    onChange={(e) => {
                      e.stopPropagation();
                      setSelectedAudioDevice(e.target.value);
                    }}
                    onClick={(e) => e.stopPropagation()}
                    disabled={connected}
                  >
                    {audioDevices.map((device) => (
                      <option
                        key={device.deviceId}
                        value={device.deviceId}
                        className="bg-white text-black font-bold"
                      >
                        {device.label || `Mic ${device.deviceId.slice(0, 4)}`}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleMute();
                }}
                className={cn(
                  "text-xs font-black px-4 py-2 transition-all border-[3px] border-black uppercase tracking-wide",
                  !muted
                    ? "bg-[#ADFF2F] text-black hover:translate-x-1 hover:translate-y-1 shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none"
                    : "bg-white text-black hover:translate-x-1 hover:translate-y-1 shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none",
                )}
              >
                {muted ? "Unmute" : "Mute"}
              </button>
            </div>

            {/* Camera Control */}
            {supportsVideo && (
              <div
                onClick={() => toggleCamera(!cameraEnabled)}
                className={cn(
                  "flex items-center justify-between p-4 border-[4px] border-black transition-all duration-100 cursor-pointer shadow-[6px_6px_0_0_rgba(0,0,0,1)] hover:shadow-[8px_8px_0_0_rgba(0,0,0,1)]",
                  cameraEnabled
                    ? "bg-[#FFE500]"
                    : "bg-white",
                )}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "flex items-center justify-center w-10 h-10 border-[3px] border-black transition-colors",
                      cameraEnabled
                        ? "bg-white text-black"
                        : "bg-[#00F0FF] text-black",
                    )}
                  >
                    {cameraEnabled ? (
                      <Video className="w-5 h-5 font-bold" />
                    ) : (
                      <VideoOff className="w-5 h-5 font-bold" />
                    )}
                  </div>
                  <span className="text-sm font-black text-black uppercase tracking-wide">
                    Camera
                  </span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleCamera(!cameraEnabled);
                  }}
                  className={cn(
                    "text-xs font-black px-4 py-2 transition-all border-[3px] border-black uppercase tracking-wide",
                    cameraEnabled
                      ? "bg-[#FF006E] text-white hover:translate-x-1 hover:translate-y-1 shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none"
                      : "bg-[#ADFF2F] text-black hover:translate-x-1 hover:translate-y-1 shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none",
                  )}
                >
                  {cameraEnabled ? "Off" : "On"}
                </button>
              </div>
            )}

            {/* Screen Share Control */}
            {supportsVideo && (
              <div
                onClick={() => toggleScreen(!screenEnabled)}
                className={cn(
                  "flex items-center justify-between p-4 border-[4px] border-black transition-all duration-100 cursor-pointer shadow-[6px_6px_0_0_rgba(0,0,0,1)] hover:shadow-[8px_8px_0_0_rgba(0,0,0,1)]",
                  screenEnabled
                    ? "bg-[#ADFF2F]"
                    : "bg-white",
                )}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "flex items-center justify-center w-10 h-10 border-[3px] border-black transition-colors",
                      screenEnabled
                        ? "bg-white text-black"
                        : "bg-[#FFE500] text-black",
                    )}
                  >
                    {screenEnabled ? (
                      <Monitor className="w-5 h-5 font-bold" />
                    ) : (
                      <MonitorOff className="w-5 h-5 font-bold" />
                    )}
                  </div>
                  <span className="text-sm font-black text-black uppercase tracking-wide">
                    Screen Share
                  </span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleScreen(!screenEnabled);
                  }}
                  className={cn(
                    "text-xs font-black px-4 py-2 transition-all border-[3px] border-black uppercase tracking-wide",
                    screenEnabled
                      ? "bg-[#FF006E] text-white hover:translate-x-1 hover:translate-y-1 shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none"
                      : "bg-[#00F0FF] text-black hover:translate-x-1 hover:translate-y-1 shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none",
                  )}
                >
                  {screenEnabled ? "Stop" : "Share"}
                </button>
              </div>
            )}

            {/* Main Action Button */}
            <button
              onClick={handleConnect}
              className={cn(
                "w-full py-4 font-black border-[5px] border-black dark:border-white transition-all transform active:translate-x-2 active:translate-y-2 active:shadow-none flex items-center justify-center gap-2 mt-2 uppercase tracking-wider text-sm",
                connected
                  ? "bg-[#FF006E] text-white hover:bg-[#FF006E] shadow-[8px_8px_0_0_rgba(0,0,0,1)] dark:shadow-[8px_8px_0_0_rgba(255,255,255,0.3)] hover:shadow-[10px_10px_0_0_rgba(0,0,0,1)] dark:hover:shadow-[10px_10px_0_0_rgba(255,255,255,0.3)]"
                  : "bg-[#00F0FF] text-black hover:bg-[#00F0FF] shadow-[8px_8px_0_0_rgba(0,0,0,1)] dark:shadow-[8px_8px_0_0_rgba(255,255,255,0.3)] hover:shadow-[10px_10px_0_0_rgba(0,0,0,1)] dark:hover:shadow-[10px_10px_0_0_rgba(255,255,255,0.3)]",
              )}
            >
              {connected ? (
                <>
                  <div className="w-4 h-4 bg-white border-2 border-black" />
                  End Session
                </>
              ) : (
                <>
                  <PlayCircle className="w-6 h-6" />
                  Start Session
                </>
              )}
            </button>

            {/* Bottom Actions */}
            <div className="grid grid-cols-4 gap-3 pt-4 border-t-[3px] border-black">
              {enableEditingSettings && (
                <SettingsDialog
                  className="!h-auto !block"
                  trigger={
                    <button className="flex flex-col items-center gap-2 p-2 transition-all group hover:translate-y-0.5">
                      <div className="p-2 border-[3px] border-black bg-white group-hover:bg-[#FF006E] transition-colors shadow-[3px_3px_0_0_rgba(0,0,0,1)] group-hover:shadow-none">
                        <Settings className="w-5 h-5 text-black group-hover:text-white font-bold" />
                      </div>
                      <span className="text-[9px] font-black uppercase">Set</span>
                    </button>
                  }
                />
              )}
              <button
                onClick={onPaintClick}
                className={cn(
                  "flex flex-col items-center gap-2 p-2 transition-all group hover:translate-y-0.5",
                )}
              >
                <div
                  className={cn(
                    "p-2 border-[3px] border-black transition-all shadow-[3px_3px_0_0_rgba(0,0,0,1)] group-hover:shadow-none",
                    isPaintActive
                      ? "bg-[#FFE500] text-black"
                      : "bg-white text-black group-hover:bg-[#FFE500]",
                  )}
                >
                  <PenTool className="w-5 h-5 font-bold" />
                </div>
                <span className="text-[9px] font-black text-black uppercase">Draw</span>
              </button>
              <button
                onClick={toggleSharedMedia}
                className={cn(
                  "flex flex-col items-center gap-2 p-2 transition-all group hover:translate-y-0.5",
                )}
              >
                <div
                  className={cn(
                    "p-2 border-[3px] border-black transition-all shadow-[3px_3px_0_0_rgba(0,0,0,1)] group-hover:shadow-none",
                    sharedMediaOpen
                      ? "bg-[#00F0FF] text-black"
                      : "bg-white text-black group-hover:bg-[#00F0FF]",
                  )}
                >
                  <Eye className="w-5 h-5 font-bold" />
                </div>
                <span className="text-[9px] font-black text-black uppercase">View</span>
              </button>
              <button className="flex flex-col items-center gap-2 p-2 transition-all group hover:translate-y-0.5">
                <div className="p-2 border-[3px] border-black bg-white group-hover:bg-[#ADFF2F] transition-colors shadow-[3px_3px_0_0_rgba(0,0,0,1)] group-hover:shadow-none">
                  <MoreHorizontal className="w-5 h-5 text-black font-bold" />
                </div>
                <span className="text-[9px] font-black text-black uppercase">More</span>
              </button>
            </div>
          </div>
        )}

        {/* Popover for Shared Media */}
        {sharedMediaOpen && (
          <div
            className={cn(
              "absolute w-[400px] h-auto flex flex-col bg-white border-[5px] border-black rounded-2xl shadow-[8px_8px_0_0_rgba(0,0,0,1)] overflow-hidden z-[1001]",
              isAnimatingOut ? "animate-popover-out" : "animate-popover-in",
              popoverPosition === "right"
                ? "left-full ml-6"
                : "right-full mr-6",
              verticalAlign === "bottom" ? "bottom-0" : "top-0",
            )}
          >
            <div className="flex items-center justify-between p-4 border-b-[4px] border-black bg-[#FFE500]">
              <div className="flex items-center gap-3">
                <div className="p-2 border-[3px] border-black bg-white">
                  <ImageIcon className="w-5 h-5 text-black font-bold" />
                </div>
                <h3 className="font-black text-black uppercase text-sm">
                  ADAM'S VIEW
                </h3>
                <span
                  className={cn(
                    "px-3 py-1 text-[10px] font-black uppercase tracking-wider border-[3px] border-black",
                    {
                      "bg-[#ADFF2F] text-black":
                        mediaMixerStatus.isConnected && !mediaMixerStatus.error,
                      "bg-[#FF006E] text-white":
                        !!mediaMixerStatus.error,
                      "bg-white text-black":
                        !mediaMixerStatus.isConnected &&
                        !mediaMixerStatus.error,
                    },
                  )}
                >
                  {mediaMixerStatus.error
                    ? "OFF"
                    : mediaMixerStatus.isConnected
                      ? "LIVE"
                      : "..."}
                </span>
              </div>
              <button
                onClick={toggleSharedMedia}
                className="w-10 h-10 flex items-center justify-center border-[3px] border-black bg-white hover:bg-[#FF006E] text-black hover:text-white transition-all shadow-[4px_4px_0_0_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-1 hover:translate-y-1"
              >
                <X className="w-5 h-5 font-bold" />
              </button>
            </div>
            <div className="flex-1 h-auto w-full">
              <MediaMixerDisplay
                socket={videoSocket}
                renderCanvasRef={renderCanvasRef}
                onStatusChange={setMediaMixerStatus}
                isCameraEnabled={cameraEnabled}
                isScreenShareEnabled={screenEnabled}
                isCanvasEnabled={isPaintActive}
              />
            </div>
          </div>
        )}
      </div>
    </Draggable>
  );
}
export default memo(FloatingControlPanel);
