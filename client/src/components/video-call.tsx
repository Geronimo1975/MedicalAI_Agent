import { useEffect, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Phone, PhoneOff, Video, VideoOff, Mic, MicOff } from "lucide-react";

declare global {
  interface Window {
    JitsiMeetExternalAPI: any;
  }
}

interface VideoCallProps {
  roomId: string;
  username: string;
}

export default function VideoCall({ roomId, username }: VideoCallProps) {
  const apiRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadJitsiScript = () => {
      if (window.JitsiMeetExternalAPI) return;

      const script = document.createElement("script");
      script.src = "https://meet.jit.si/external_api.js";
      script.async = true;
      document.body.appendChild(script);
    };

    loadJitsiScript();
  }, []);

  useEffect(() => {
    const initializeJitsi = () => {
      if (!window.JitsiMeetExternalAPI || !containerRef.current) return;

      const domain = "meet.jit.si";
      const options = {
        roomName: roomId,
        width: "100%",
        height: "100%",
        parentNode: containerRef.current,
        userInfo: {
          displayName: username,
        },
        configOverwrite: {
          startWithAudioMuted: true,
          startWithVideoMuted: false,
          prejoinPageEnabled: false,
        },
        interfaceConfigOverwrite: {
          TOOLBAR_BUTTONS: [
            "microphone",
            "camera",
            "closedcaptions",
            "desktop",
            "fullscreen",
            "fodeviceselection",
            "hangup",
            "profile",
            "recording",
            "shortcuts",
            "tileview",
          ],
        },
      };

      apiRef.current = new window.JitsiMeetExternalAPI(domain, options);

      apiRef.current.addEventListeners({
        readyToClose: handleClose,
        participantLeft: handleParticipantLeft,
        participantJoined: handleParticipantJoined,
        videoConferenceJoined: handleVideoConferenceJoined,
        videoConferenceLeft: handleVideoConferenceLeft,
      });
    };

    if (window.JitsiMeetExternalAPI) {
      initializeJitsi();
    } else {
      const checkJitsiAPI = setInterval(() => {
        if (window.JitsiMeetExternalAPI) {
          clearInterval(checkJitsiAPI);
          initializeJitsi();
        }
      }, 100);
    }

    return () => {
      if (apiRef.current) {
        apiRef.current.dispose();
      }
    };
  }, [roomId, username]);

  const handleClose = () => {
    console.log("Call ended");
  };

  const handleParticipantLeft = (participant: any) => {
    console.log("Participant left:", participant);
  };

  const handleParticipantJoined = (participant: any) => {
    console.log("Participant joined:", participant);
  };

  const handleVideoConferenceJoined = (participant: any) => {
    console.log("Video conference joined:", participant);
  };

  const handleVideoConferenceLeft = () => {
    console.log("Video conference left");
  };

  return (
    <Card className="w-full h-[600px] relative">
      <div ref={containerRef} className="w-full h-full" />
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2">
        <Button 
          variant="destructive" 
          size="icon"
          onClick={() => apiRef.current?.executeCommand('hangup')}
        >
          <PhoneOff className="h-4 w-4" />
        </Button>
        <Button 
          variant="outline" 
          size="icon"
          onClick={() => apiRef.current?.executeCommand('toggleVideo')}
        >
          <Video className="h-4 w-4" />
        </Button>
        <Button 
          variant="outline" 
          size="icon"
          onClick={() => apiRef.current?.executeCommand('toggleAudio')}
        >
          <Mic className="h-4 w-4" />
        </Button>
      </div>
    </Card>
  );
}
