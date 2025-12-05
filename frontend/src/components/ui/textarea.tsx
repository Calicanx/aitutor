import * as React from "react"

import { cn } from "@/lib/utils"

const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.ComponentProps<"textarea">
>(({ className, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        "flex min-h-[100px] w-full bg-[#FFFDF5] dark:bg-[#1a1a1a] border-[3px] border-black dark:border-white px-4 py-3 text-base font-bold text-black dark:text-white shadow-[4px_4px_0px_0px_#000] dark:shadow-[4px_4px_0px_0px_rgba(255,255,255,0.3)] transition-all duration-100 placeholder:text-black/40 dark:placeholder:text-white/40 placeholder:font-bold focus-visible:outline-none focus-visible:bg-[#FFD93D] focus-visible:shadow-[6px_6px_0px_0px_#000] dark:focus-visible:shadow-[6px_6px_0px_0px_rgba(255,255,255,0.3)] focus-visible:ring-0 disabled:cursor-not-allowed disabled:opacity-50 resize-none",
        className
      )}
      ref={ref}
      {...props}
    />
  )
})
Textarea.displayName = "Textarea"

export { Textarea }
