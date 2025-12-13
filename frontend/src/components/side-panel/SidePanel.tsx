/**
 * Copyright 2024 Google LLC
 *
 * SidePanel / Learning Dashboard
 * Now features a Learning Path view + Developer Console
 */

import cn from "classnames";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
// import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"; // Commented out - not using tabs anymore
// import { ScrollArea } from "@/components/ui/scroll-area"; // Commented out - not using ScrollArea for Journey tab
import { useLiveAPIContext } from "../../contexts/LiveAPIContext";
import { useLoggerStore } from "../../lib/store-logger";
import Logger, { LoggerFilterType } from "../logger/Logger";
import { ArrowRight, Terminal, BookOpen, CheckCircle2, Circle, Lock } from "lucide-react";
import { jwtUtils } from "../../lib/jwt-utils";

const filterOptions = [
  { value: "conversations", label: "Conversations" },
  { value: "tools", label: "Tool Use" },
  { value: "none", label: "All" },
];

// Mock Learning Path Data
const NEXT_STEPS = [
  { id: 1, title: "Intro to Algebra", status: "completed", score: "95%" },
  { id: 2, title: "Linear Equations", status: "completed", score: "88%" },
  { id: 3, title: "Graphing Lines", status: "in-progress", progress: 65 },
  { id: 4, title: "Systems of Equations", status: "locked" },
  { id: 5, title: "Quadratic Foundations", status: "locked" },
  { id: 6, title: "Polynomials", status: "locked" },
];

interface SidePanelProps {
  open: boolean;
  onToggle: () => void;
}

export default function SidePanel({ open }: SidePanelProps) {
  const { connected, client } = useLiveAPIContext();
  const loggerRef = useRef<HTMLDivElement>(null);
  const loggerLastHeightRef = useRef<number>(-1);
  const { log, logs } = useLoggerStore();

  const [textInput, setTextInput] = useState("");
  const [filter, setFilter] = useState<LoggerFilterType>("none");
  const [isPaused, setIsPaused] = useState(false);
  const [learningPath, setLearningPath] = useState<any[]>(NEXT_STEPS); // Initialize with mock data to avoid "Loading..." state

  useEffect(() => {
    // Fetch real learning path data
    const fetchPath = async () => {
      try {
        const token = jwtUtils.getToken(); // Fixed: was using wrong key 'auth_token'
        if (!token) {
          // No token - use fallback mock data
          setLearningPath(NEXT_STEPS);
          return;
        }

        const DASH_API = import.meta.env.VITE_DASH_API_URL || 'http://localhost:8000';

        const res = await fetch(`${DASH_API}/api/learning-path`, {
          headers: {
            "Authorization": `Bearer ${token}`
          }
        });
        if (res.ok) {
          const data = await res.json();
          // If API returns empty array, use fallback
          setLearningPath(data.length > 0 ? data : NEXT_STEPS);
        } else {
          // API error - use fallback
          setLearningPath(NEXT_STEPS);
        }
      } catch (e) {
        console.error("Failed to fetch learning path", e);
        // Fallback to mock data if fetch fails
        setLearningPath(NEXT_STEPS);
      }
    };

    if (open) {
      fetchPath();
    }
  }, [open]);

  // scroll the log to the bottom when new logs come in
  useEffect(() => {
    if (loggerRef.current) {
      const el = loggerRef.current;
      const scrollHeight = el.scrollHeight;
      if (scrollHeight !== loggerLastHeightRef.current) {
        el.scrollTop = scrollHeight;
        loggerLastHeightRef.current = scrollHeight;
      }
    }
  }, [logs]);

  // listen for log events and store them
  useEffect(() => {
    client.on("log", log);
    return () => {
      client.off("log", log);
    };
  }, [client, log]);

  const handleSubmit = () => {
    client.send([{ text: textInput }]);
    setTextInput("");
  };

  return (
    <div
      className={cn(
        "fixed top-[44px] lg:top-[48px] right-0 flex flex-col border-l-[3px] lg:border-l-[4px] border-black dark:border-white bg-[#FFFDF5] dark:bg-[#000000] transition-all duration-500 cubic-bezier(0.16, 1, 0.3, 1) z-50 will-change-transform shadow-[-2px_0_0_0_rgba(0,0,0,1)] lg:shadow-[-2px_0_0_0_rgba(0,0,0,1)] dark:shadow-[-2px_0_0_0_rgba(255,255,255,0.3)]",
        "h-[calc(100vh-44px)] lg:h-[calc(100vh-48px)] w-[300px] lg:w-[320px]", // Widened slightly for content
        open ? "translate-x-0" : "translate-x-full",
        "max-md:hidden"
      )}
    >
      <div className="flex flex-col h-full w-full">
        {/* Header - Simple Console Header */}
        <header className="flex items-center h-[56px] px-4 border-b-[3px] border-black dark:border-white bg-[#C4B5FD] shrink-0">
          <div className="w-6 h-6 border-2 border-black bg-white flex items-center justify-center mr-3">
            <span className="text-black font-mono text-xs font-bold">&gt;_</span>
          </div>
          <span className="text-black font-bold uppercase tracking-tight text-base">CONSOLE</span>
        </header>

        {/* Learning Journey Tab - Commented Out */}
        {/* <TabsContent value="learning" className="flex-grow flex flex-col overflow-hidden data-[state=active]:flex mt-0">
          <ScrollArea className="flex-grow p-4">
            <div className="space-y-6">
              <div className="rounded-xl border-[3px] border-black bg-[#FFD93D] p-4 shadow-[4px_4px_0_0_rgba(0,0,0,1)]">
                <h3 className="text-xs font-black uppercase tracking-wider text-black/70 mb-1">Current Subject</h3>
                <h2 className="text-xl font-black text-black">Algebra I</h2>
                <div className="mt-3 flex items-center gap-2">
                  <div className="h-2 flex-grow rounded-full bg-black/10 overflow-hidden">
                    <div className="h-full bg-black w-[65%]" />
                  </div>
                  <span className="text-xs font-bold text-black">65%</span>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-black uppercase tracking-wider mb-3 px-1">Your Path</h3>
                <div className="relative border-l-[3px] border-dashed border-gray-300 ml-3 space-y-6 pb-2">
                  {learningPath.length === 0 ? (
                    <div className="pl-6 text-sm text-gray-500">Loading path...</div>
                  ) : learningPath.map((step) => (
                    <div key={step.id} className="relative pl-6">
                      <div className={cn(
                        "absolute -left-[10px] top-1 w-5 h-5 rounded-full border-[2px] border-black flex items-center justify-center",
                        step.status === 'completed' ? "bg-[#4ADE80]" :
                          step.status === 'in-progress' ? "bg-[#FFD93D]" : "bg-white"
                      )}>
                        {step.status === 'completed' && <CheckCircle2 className="w-3 h-3 text-black" />}
                        {step.status === 'in-progress' && <div className="w-2 h-2 rounded-full bg-black animate-pulse" />}
                        {step.status === 'locked' && <Lock className="w-2.5 h-2.5 text-gray-400" />}
                      </div>
                      <div className={cn(
                        "p-3 rounded-lg border-[2px] transition-all",
                        step.status === 'in-progress'
                          ? "bg-white border-black shadow-[3px_3px_0_0_rgba(0,0,0,1)]"
                          : "bg-transparent border-transparent opacity-80"
                      )}>
                        <h4 className="font-bold text-sm">{step.title}</h4>
                        {step.status === 'completed' && <span className="text-xs font-bold text-[#16A34A]">{step.score} Score</span>}
                        {step.status === 'in-progress' && <span className="text-xs font-bold text-[#D97706]">Current Topic</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </ScrollArea>
        </TabsContent> */}

        {/* Console Content (Existing Functionality) */}
        <div className="flex-grow flex flex-col overflow-hidden h-full">
          <div className="flex items-center justify-between px-4 py-3 shrink-0 border-b-[3px] border-black dark:border-white bg-[#FFFDF5] dark:bg-[#000000]">
            <Select value={filter} onValueChange={(value) => setFilter(value as LoggerFilterType)}>
              <SelectTrigger className="w-[140px] h-8 text-xs font-bold uppercase border-2 border-black shadow-[2px_2px_0_0_rgba(0,0,0,1)] rounded">
                <SelectValue placeholder="Filter">
                  {filter === "none" ? "ALL" : filterOptions.find(opt => opt.value === filter)?.label || "ALL"}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {filterOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value} className="text-xs font-bold">
                    {option.value === "none" ? "ALL" : option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button
              onClick={() => setIsPaused(!isPaused)}
              className="flex items-center gap-1.5 px-3 py-1.5 h-8 rounded border-2 border-black text-[10px] font-bold uppercase shadow-[2px_2px_0_0_rgba(0,0,0,1)] bg-[#C4B5FD] text-black hover:bg-[#A78BFA]"
            >
              <div className="w-2 h-2 rounded-sm bg-black" />
              PAUSED
            </Button>
          </div>

          <div
            className="flex-grow overflow-y-auto overflow-x-hidden px-4 py-2 scrollbar-thin"
            ref={loggerRef}
          >
            <Logger filter={filter} />
          </div>

          <div className={cn(
            "p-4 border-t-[3px] border-black bg-gray-50",
            { "opacity-50 pointer-events-none": !connected }
          )}>
            <div className="flex gap-2">
              <Textarea
                className="min-h-[40px] h-[40px] resize-none border-2 border-black shadow-[2px_2px_0_0_rgba(0,0,0,1)] text-xs font-medium py-2 rounded"
                placeholder="Type a message..."
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
                onChange={(e) => setTextInput(e.target.value)}
                value={textInput}
              />
              <Button
                size="icon"
                className="h-[40px] w-[40px] border-2 border-black bg-[#C4B5FD] text-black hover:bg-[#A78BFA] shadow-[2px_2px_0_0_rgba(0,0,0,1)]"
                onClick={handleSubmit}
                disabled={!textInput.trim() || !connected}
              >
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
