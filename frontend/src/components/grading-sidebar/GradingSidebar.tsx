import React, { useEffect, useRef } from "react";
import cn from "classnames";
import { GraduationCap, ChevronRight, ChevronLeft, TrendingUp, Clock, Target } from "lucide-react";
import data from "../../../data.json";
import { Button } from "@/components/ui/button";
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion";

interface GradingSidebarProps {
    open: boolean;
    onToggle: () => void;
    currentSkill?: string | null;
}



const formatSkillName = (name: string) => {
    return name
        .split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
};

const formatTime = (timestamp: number | null) => {
    if (!timestamp) return "Never";
    const date = new Date(timestamp * 1000);
    return (
        date.toLocaleDateString() +
        " " +
        date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    );
};

export default function GradingSidebar({ open, onToggle, currentSkill }: GradingSidebarProps) {
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const isUserScrollingRef = useRef(false);
    const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const skillStates = data.skill_states as Record<
        string,
        {
            memory_strength: number;
            last_practice_time: number | null;
            practice_count: number;
            correct_count: number;
        }
    >;

    const scrollToSkill = (skill: string) => {
        if (!scrollContainerRef.current) return;

        const element = document.getElementById(`skill-${skill}`);
        if (element) {
            element.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    };

    const prevOpenRef = useRef(open);

    // Auto-scroll when open or currentSkill changes
    useEffect(() => {
        if (open && currentSkill) {
            // If we're transitioning from closed to open, we need to wait for the width transition (500ms)
            // If we're already open and just changing skills, we can scroll faster
            const isOpening = !prevOpenRef.current && open;
            const delay = isOpening ? 600 : 100;

            // Small delay to ensure content is rendered/expanded
            const timeoutId = setTimeout(() => {
                if (!isUserScrollingRef.current) {
                    scrollToSkill(currentSkill);
                }
            }, delay);

            return () => clearTimeout(timeoutId);
        }
        prevOpenRef.current = open;
    }, [open, currentSkill]);

    // Handle user scrolling and inactivity
    useEffect(() => {
        const container = scrollContainerRef.current;
        if (!container) return;

        const handleScroll = () => {
            isUserScrollingRef.current = true;

            if (scrollTimeoutRef.current) {
                clearTimeout(scrollTimeoutRef.current);
            }

            scrollTimeoutRef.current = setTimeout(() => {
                isUserScrollingRef.current = false;
                if (currentSkill && open) {
                    scrollToSkill(currentSkill);
                }
            }, 3000);
        };

        container.addEventListener("scroll", handleScroll);

        return () => {
            container.removeEventListener("scroll", handleScroll);
            if (scrollTimeoutRef.current) {
                clearTimeout(scrollTimeoutRef.current);
            }
        };
    }, [currentSkill, open]);

    // Handle click elsewhere (on the container background) to re-center immediately
    const handleContainerClick = (e: React.MouseEvent) => {
        // If the user clicks directly on the container (not on an interactive child that stops propagation)
        // we assume they want to re-center.
        // However, checking e.target === e.currentTarget might be too strict if there are wrapper divs.
        // Let's just reset the scrolling flag and scroll immediately if they click anywhere in the sidebar
        // (except maybe on the toggle button which is in the header, outside this div).

        // Reset user scrolling flag
        isUserScrollingRef.current = false;
        if (scrollTimeoutRef.current) {
            clearTimeout(scrollTimeoutRef.current);
        }

        if (currentSkill && open) {
            scrollToSkill(currentSkill);
        }
    };

    return (
        <div
            className={cn(
                "fixed top-[56px] left-0 flex flex-col border-r-[4px] md:border-r-[5px] border-black dark:border-white bg-white dark:bg-neutral-900 transition-all duration-500 cubic-bezier(0.16, 1, 0.3, 1) z-50 will-change-transform shadow-[6px_0_0_0_rgba(0,0,0,1)] dark:shadow-[6px_0_0_0_rgba(255,255,255,0.3)]",
                "h-[calc(100vh-56px)]",
                open ? "w-[280px] md:w-[320px]" : "w-[48px]",
                "max-md:hidden" // Hide on mobile
            )}
        >
            <header className={cn(
                "flex items-center h-[56px] border-b-[3px] md:border-b-[4px] border-black dark:border-white shrink-0 overflow-hidden transition-all duration-300 bg-[#FF006E]",
                open ? "justify-between px-4 md:px-6" : "justify-center"
            )}>
                {open ? (
                    <div className="flex items-center gap-3 animate-in fade-in slide-in-from-left-4 duration-300">
                        <div className="p-2 border-[3px] border-black dark:border-white bg-white dark:bg-neutral-900">
                            <GraduationCap className="w-5 h-5 text-black dark:text-white font-bold" />
                        </div>
                        <h2 className="text-lg font-black text-white whitespace-nowrap uppercase tracking-tight">
                            GRADING & SKILLS
                        </h2>
                    </div>
                ) : (
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={onToggle}
                        className="w-12 h-12 border-[3px] border-black dark:border-white bg-white dark:bg-neutral-900 hover:bg-[#FFE500] dark:hover:bg-[#FFE500] transition-colors shadow-[4px_4px_0_0_rgba(0,0,0,1)] dark:shadow-[4px_4px_0_0_rgba(255,255,255,0.3)] hover:shadow-none hover:translate-x-1 hover:translate-y-1"
                    >
                        <GraduationCap className="w-6 h-6 text-black dark:text-white dark:hover:text-black font-bold" />
                    </Button>
                )}

                {open && (
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={onToggle}
                        className="w-10 h-10 border-[3px] border-black dark:border-white bg-white dark:bg-neutral-900 hover:bg-[#FFE500] dark:hover:bg-[#FFE500] text-black dark:text-white dark:hover:text-black transition-all shadow-[4px_4px_0_0_rgba(0,0,0,1)] dark:shadow-[4px_4px_0_0_rgba(255,255,255,0.3)] hover:shadow-none hover:translate-x-1 hover:translate-y-1"
                    >
                        <ChevronLeft className="w-5 h-5 font-bold" />
                    </Button>
                )}
            </header>

            <div className="flex-grow overflow-hidden relative" onClick={handleContainerClick}>
                {open ? (
                    <div
                        ref={scrollContainerRef}
                        className="h-full overflow-y-auto overflow-x-hidden animate-in fade-in duration-500 px-4 py-4"
                    >
                        <Accordion type="single" collapsible className="w-full space-y-3">
                            {Object.entries(skillStates).map(([skillName, stats]) => {
                                const strength = Math.max(-2, Math.min(2, stats.memory_strength ?? 0));
                                const normalizedStrength = ((strength + 2) / 4) * 100; // 0-100%
                                const isPracticed = stats.practice_count > 0;

                                // Determine strength level for color
                                const getStrengthColor = () => {
                                    if (!isPracticed) return "gray";
                                    if (strength >= 1.5) return "emerald";
                                    if (strength >= 0.5) return "green";
                                    if (strength >= -0.5) return "yellow";
                                    if (strength >= -1.5) return "orange";
                                    return "red";
                                };

                                const strengthColor = getStrengthColor();
                                const accuracyPercent = stats.practice_count > 0
                                    ? Math.round((stats.correct_count / stats.practice_count) * 100)
                                    : 0;

                                return (
                                    <AccordionItem
                                        key={skillName}
                                        value={skillName}
                                        id={`skill-${skillName}`}
                                        className="border-none"
                                    >
                                        <div className={cn(
                                            "border-[4px] border-black dark:border-white transition-all duration-200 shadow-[4px_4px_0_0_rgba(0,0,0,1)] dark:shadow-[4px_4px_0_0_rgba(255,255,255,0.2)]",
                                            isPracticed ? "bg-white dark:bg-neutral-800" : "bg-gray-200 dark:bg-neutral-900",
                                            isPracticed && "hover:shadow-[6px_6px_0_0_rgba(0,0,0,1)] dark:hover:shadow-[6px_6px_0_0_rgba(255,255,255,0.3)] hover:translate-x-[-2px] hover:translate-y-[-2px]",
                                            !isPracticed && "opacity-60"
                                        )}>
                                            <AccordionTrigger className="hover:no-underline px-4 py-3 [&>svg]:hidden cursor-pointer group">
                                                <div className="flex flex-col gap-2 w-full">
                                                    <div className="flex items-center justify-between w-full">
                                                        <span className={cn(
                                                            "font-black text-base text-left uppercase tracking-tight",
                                                            isPracticed ? "text-black dark:text-white" : "text-gray-500 dark:text-gray-500"
                                                        )}>
                                                            {formatSkillName(skillName)}
                                                        </span>
                                                        <div className={cn(
                                                            "px-3 py-1 border-[3px] border-black dark:border-white text-xs font-black uppercase",
                                                            strengthColor === "gray" && "bg-gray-300 dark:bg-gray-700 text-black dark:text-white",
                                                            strengthColor === "emerald" && "bg-[#ADFF2F] text-black",
                                                            strengthColor === "green" && "bg-[#ADFF2F] text-black",
                                                            strengthColor === "yellow" && "bg-[#FFE500] text-black",
                                                            strengthColor === "orange" && "bg-[#FF6B35] text-white",
                                                            strengthColor === "red" && "bg-[#FF006E] text-white"
                                                        )}>
                                                            {strength.toFixed(1)}
                                                        </div>
                                                    </div>

                                                    {/* Progress bar */}
                                                    <div className="w-full bg-gray-300 dark:bg-neutral-700 border-[2px] border-black dark:border-white h-3 overflow-hidden">
                                                        <div
                                                            className={cn(
                                                                "h-full transition-all duration-300",
                                                                strengthColor === "gray" && "bg-gray-500 dark:bg-gray-600",
                                                                strengthColor === "emerald" && "bg-[#ADFF2F]",
                                                                strengthColor === "green" && "bg-[#ADFF2F]",
                                                                strengthColor === "yellow" && "bg-[#FFE500]",
                                                                strengthColor === "orange" && "bg-[#FF6B35]",
                                                                strengthColor === "red" && "bg-[#FF006E]"
                                                            )}
                                                            style={{ width: `${normalizedStrength}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            </AccordionTrigger>
                                            <AccordionContent>
                                                <div className="px-4 pb-4 pt-2">
                                                    <div className="grid grid-cols-2 gap-3">
                                                        {/* Accuracy Card */}
                                                        <div className={cn(
                                                            "p-3 border-[3px] border-black dark:border-white shadow-[3px_3px_0_0_rgba(0,0,0,1)] dark:shadow-[3px_3px_0_0_rgba(255,255,255,0.2)]",
                                                            isPracticed
                                                                ? "bg-[#FF006E] dark:bg-[#FF006E]"
                                                                : "bg-gray-200 dark:bg-gray-800"
                                                        )}>
                                                            <div className="flex items-center gap-2 mb-2">
                                                                <Target className={cn(
                                                                    "w-4 h-4 font-bold",
                                                                    isPracticed ? "text-white" : "text-gray-500 dark:text-gray-600"
                                                                )} />
                                                                <span className={cn(
                                                                    "text-xs font-black uppercase",
                                                                    isPracticed ? "text-white" : "text-gray-600 dark:text-gray-500"
                                                                )}>Accuracy</span>
                                                            </div>
                                                            <div className={cn(
                                                                "text-3xl font-black",
                                                                isPracticed ? "text-white" : "text-gray-600 dark:text-gray-500"
                                                            )}>
                                                                {accuracyPercent}%
                                                            </div>
                                                            <div className={cn(
                                                                "text-xs mt-1 font-bold",
                                                                isPracticed ? "text-white" : "text-gray-500 dark:text-gray-600"
                                                            )}>
                                                                {stats.correct_count}/{stats.practice_count} correct
                                                            </div>
                                                        </div>

                                                        {/* Practice Count Card */}
                                                        <div className={cn(
                                                            "p-3 border-[3px] border-black dark:border-white shadow-[3px_3px_0_0_rgba(0,0,0,1)] dark:shadow-[3px_3px_0_0_rgba(255,255,255,0.2)]",
                                                            isPracticed
                                                                ? "bg-[#00F0FF] dark:bg-[#00F0FF]"
                                                                : "bg-gray-200 dark:bg-gray-800"
                                                        )}>
                                                            <div className="flex items-center gap-2 mb-2">
                                                                <TrendingUp className={cn(
                                                                    "w-4 h-4 font-bold",
                                                                    isPracticed ? "text-black" : "text-gray-500 dark:text-gray-600"
                                                                )} />
                                                                <span className={cn(
                                                                    "text-xs font-black uppercase",
                                                                    isPracticed ? "text-black" : "text-gray-600 dark:text-gray-500"
                                                                )}>Practice</span>
                                                            </div>
                                                            <div className={cn(
                                                                "text-3xl font-black",
                                                                isPracticed ? "text-black" : "text-gray-600 dark:text-gray-500"
                                                            )}>
                                                                {stats.practice_count}
                                                            </div>
                                                            <div className={cn(
                                                                "text-xs mt-1 font-bold",
                                                                isPracticed ? "text-black" : "text-gray-500 dark:text-gray-600"
                                                            )}>
                                                                total attempts
                                                            </div>
                                                        </div>
                                                    </div>

                                                    {/* Last Practice */}
                                                    <div className="mt-3 bg-white dark:bg-neutral-800 p-3 border-[3px] border-black dark:border-white">
                                                        <div className={cn(
                                                            "flex items-center gap-2 text-xs font-bold",
                                                            isPracticed ? "text-black dark:text-white" : "text-gray-500 dark:text-gray-600"
                                                        )}>
                                                            <Clock className="w-4 h-4 font-bold" />
                                                            <span className="font-black uppercase">Last:</span>
                                                            <span className="ml-auto">{formatTime(stats.last_practice_time)}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </AccordionContent>
                                        </div>
                                    </AccordionItem>
                                );
                            })}
                        </Accordion>
                    </div>
                ) : (
                    <div className="h-full w-full flex items-center justify-center cursor-pointer hover:bg-[#FFE500]/20 transition-colors pb-[140px]" onClick={onToggle}>
                        <div className="rotate-180 [writing-mode:vertical-rl] text-lg font-black tracking-widest uppercase whitespace-nowrap select-none text-black dark:text-white text-center leading-none">
                            GRADES & SKILLS
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
